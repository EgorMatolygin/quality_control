# presentation/main_window.py
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QMessageBox, QLabel, QGroupBox, QFormLayout, QComboBox, QLineEdit, 
                            QGridLayout, QScrollArea, QCheckBox, QTableWidget,QTableWidgetItem, QStackedWidget, QHeaderView, QSizePolicy, QProgressDialog)
from PyQt5.QtGui import QIcon, QFont, QFontMetrics
from PyQt5.QtCore import Qt
from presentation.widgets.table_widget import TableWidget
from presentation.widgets.plot_widget import PlotWidget
from business.data_processor import DataProcessor
from business.quality_calculator import QualityCalculator
from data.data_manager import DataManager
from data.database import PostgreSQLManager
from business.arima_predictor import ARIMAPredictor

from presentation.widgets.constraints_panel import ConstraintsPanel

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px  
from PyQt5.QtWebEngineWidgets import QWebEngineView
import pandas as pd
import numpy as np

import tempfile
import shutil
import zipfile
import os
import re

class MetricsTablePage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
        self.setStyleSheet("background-color: #f0f0f0;")

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Заголовок
        self.header = QLabel("Перекрестная таблица метрик", self)
        self.header.setFont(QFont('Arial', 18, QFont.Bold))
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setStyleSheet("""
            background-color: #4A90E2;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        """)
        main_layout.addWidget(self.header)

        # Селектор партий
        self.batch_combo = QComboBox()
        self.batch_combo.currentIndexChanged.connect(self.update_table)
        main_layout.addWidget(self.batch_combo)

        # Таблица
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget {
                background: white;
                border-radius: 6px;
                gridline-color: #e0e0e0;
            }
            QHeaderView::section {
                background: #f8f8f8;
                padding: 6px;
            }
        """)
        main_layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_back = QPushButton("← Назад")
        self.btn_back.clicked.connect(lambda: self.parent.show_results('static'))
        
        self.btn_export = QPushButton("Экспортировать все партии в ZIP")
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.btn_export.clicked.connect(self.export_all_batches)
        
        self.cb_include_all = QCheckBox("Включая сводку по всем партиям")
        self.cb_include_all.setChecked(True)
        
        btn_layout.addWidget(self.btn_back)
        btn_layout.addStretch()
        # btn_layout.addWidget(self.cb_include_all)
        btn_layout.addWidget(self.btn_export)
        
        main_layout.addLayout(btn_layout)

        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)

        # self.format_combo.setStyleSheet("""
        #     QComboBox {
        #         padding: 5px;
        #         min-width: 120px;
        #     }
        # """)

    def update_batches(self):
        """Обновляет список партий"""
        self.batch_combo.clear()
        df = self.parent.current_static_data
        if df is not None and 'batch_id' in df.columns:
            self.batch_combo.addItem("Все партии")
            batches = df['batch_id'].astype(str).unique().tolist()
            self.batch_combo.addItems(batches)

    def update_table(self):
        df = self.parent.current_static_data
        if df is None:
            return

        # Фильтрация по партии
        batch = self.batch_combo.currentText()
        if batch != "Все партии" and 'batch_id' in df.columns:
            df = df[df['batch_id'].astype(str) == batch]

        # Рассчет метрик индекса качества
        constraints = self.parent.static_constraints
        result_series = QualityCalculator.calculate_quality_index(
            df,
            constraints=constraints,
            analysis_type='static'
        )
        result_df = result_series.to_frame().T 
        self.parent.static_quality_index = result_df
        self.parent.static_best_worst = QualityCalculator.calculate_actual_best_worst(df, constraints)

        quality_indexes = self.parent.static_quality_index
        best_worst = self.parent.static_best_worst

        # Подготовка данных
        params = [col for col in df.columns 
                if col not in ['id', 'timestamp', 'batch_id', 'product_id', 'date']]
        metrics = [
            'Среднее', 'Медиана', 'Ст. отклонение', 
            'Минимум', 'Максимум', 'Количество',
            'За пределами норм', 'Лучшее значение', 
            'Худшее значение', 'Разброс', 'Индекс качества'
        ]

        # Настройка таблицы
        self.table.setRowCount(len(metrics))
        self.table.setColumnCount(len(params))
        self.table.setHorizontalHeaderLabels(params)
        self.table.setVerticalHeaderLabels(metrics)

        # Заполнение данных
        for col_idx, param in enumerate(params):
            if pd.api.types.is_numeric_dtype(df[param]):
                data = df[param]
                constraints = self.parent.static_constraints.get(param, {})
                
                # Базовые метрики
                self.table.setItem(0, col_idx, QTableWidgetItem(f"{data.mean():.2f}"))
                self.table.setItem(1, col_idx, QTableWidgetItem(f"{data.median():.2f}"))
                self.table.setItem(2, col_idx, QTableWidgetItem(f"{data.std():.2f}"))
                self.table.setItem(3, col_idx, QTableWidgetItem(f"{data.min():.2f}"))
                self.table.setItem(4, col_idx, QTableWidgetItem(f"{data.max():.2f}"))
                self.table.setItem(5, col_idx, QTableWidgetItem(str(data.count())))
                
                # За пределами норм
                out_of_bounds = self.calculate_out_of_bounds(data, constraints)
                self.table.setItem(6, col_idx, QTableWidgetItem(str(out_of_bounds)))
                
                # Лучшее/худшее
                best = best_worst.get(param, {}).get('best', '')
                worst_val = best_worst.get(param, {}).get('worst', '')
                self.table.setItem(7, col_idx, QTableWidgetItem(str(best)))
                self.table.setItem(8, col_idx, QTableWidgetItem(str(worst_val)))
                
                # Разброс
                spread = ''
                if isinstance(best, (int, float)) and isinstance(worst_val, (int, float)):
                    spread = f"{best - worst_val:.2f}"
                self.table.setItem(9, col_idx, QTableWidgetItem(spread))
                
                # Индекс качества
                if quality_indexes is not None and param in quality_indexes.columns:
                    self.table.setItem(10, col_idx, QTableWidgetItem(f"{quality_indexes[param].values[0]:.2f}"))
            else:
                for row_idx in range(len(metrics)):
                    self.table.setItem(row_idx, col_idx, QTableWidgetItem(""))

        self.table.resizeColumnsToContents()

    def calculate_out_of_bounds(self, data, constraints):
        """Рассчитывает количество значений за пределами ограничений"""
        if not constraints:
            return 0
            
        if constraints.get('type') == 'range':
            min_val = constraints.get('min', -np.inf)
            max_val = constraints.get('max', np.inf)
            return ((data < min_val) | (data > max_val)).sum()
            
        elif constraints.get('type') == 'min':
            return (data < constraints['value']).sum()
            
        elif constraints.get('type') == 'max':
            return (data > constraints['value']).sum()
            
        return 0

    def get_table_data(self):
        """Преобразует данные таблицы в DataFrame"""
        try:
            # Получаем заголовки
            columns = [
                self.table.horizontalHeaderItem(i).text() 
                for i in range(self.table.columnCount())
            ]
            
            # Собираем данные
            data = []
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            
            # Создаем DataFrame
            df = pd.DataFrame(data, columns=columns)
            
            # Добавляем метрики в первый столбец
            metrics = [
                self.table.verticalHeaderItem(i).text() 
                for i in range(self.table.rowCount())
            ]
            df.insert(0, "Метрика", metrics)
            
            return df
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка данных",
                f"Ошибка преобразования данных таблицы:\n{str(e)}"
            )
            return pd.DataFrame()
    
    def export_all_batches(self):
        """Экспорт метрик для всех партий в ZIP-архив"""
        try:
            # Получаем список всех партий
            batches = self.get_available_batches()
            
            # Создаем временную директорию
            temp_dir = tempfile.mkdtemp()
            exported_files = []

            # Прогресс-диалог
            progress = QProgressDialog("Экспорт данных...", "Отмена", 0, len(batches), self)
            progress.setWindowModality(Qt.WindowModal)

            for i, batch in enumerate(batches):
                progress.setValue(i)
                progress.setLabelText(f"Обработка партии: {batch}...")
                
                if progress.wasCanceled():
                    break

                # Генерируем данные для партии
                df = self.generate_batch_metrics(batch)
                
                # Создаем безопасное имя файла
                safe_name = self.sanitize_filename(batch)
                file_path = os.path.join(temp_dir, f"{safe_name}.xlsx")
                
                # Сохраняем в Excel
                df.to_excel(file_path, index=False, engine='openpyxl')
                exported_files.append(file_path)

            # Добавляем общую сводку
            if self.cb_include_all.isChecked():
                df_all = self.generate_batch_metrics("Все партии")
                file_path = os.path.join(temp_dir, "Все_партии.xlsx")
                df_all.to_excel(file_path, index=False, engine='openpyxl')
                exported_files.append(file_path)

            progress.close()

            # Предлагаем сохранить архив
            zip_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить архив с метриками",
                "",
                "ZIP Archives (*.zip)"
            )
            
            if not zip_path:
                shutil.rmtree(temp_dir)
                return

            # Создаем ZIP-архив
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file in exported_files:
                    zipf.write(file, os.path.basename(file))

            # Удаляем временные файлы
            shutil.rmtree(temp_dir)

            QMessageBox.information(
                self,
                "Экспорт завершен",
                f"Архив успешно сохранен:\n{zip_path}\n\n"
                f"Экспортировано партий: {len(exported_files)}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка экспорта",
                f"Произошла ошибка при создании архива:\n{str(e)}"
            )
            if 'temp_dir' in locals():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def get_available_batches(self):
        """Возвращает список всех уникальных партий"""
        df = self.parent.current_static_data
        batches = []
        
        if df is not None and 'batch_id' in df.columns:
            batches = df['batch_id'].astype(str).unique().tolist()
        
        return batches
    
    def generate_batch_metrics(self, batch_name):
        """Генерирует DataFrame с метриками для указанной партии"""
        df = self.parent.current_static_data.copy()
        
        if batch_name != "Все партии" and 'batch_id' in df.columns:
            df = df[df['batch_id'].astype(str) == batch_name]

        # Рассчет метрик
        constraints = self.parent.static_constraints
        quality_index = QualityCalculator.calculate_quality_index(
            df, constraints, 'static'
        )
        best_worst = QualityCalculator.calculate_actual_best_worst(df, constraints)

        # Сбор данных
        metrics = []
        params = [col for col in df.columns 
                if col not in ['id', 'timestamp', 'batch_id', 'product_id', 'date']]
        
        for param in params:
            param_metrics = {
                'Параметр': param,
                'Тип данных': 'Числовой' if pd.api.types.is_numeric_dtype(df[param]) else 'Категориальный'
            }
            
            if pd.api.types.is_numeric_dtype(df[param]):
                data = df[param]
                param_metrics.update({
                    'Среднее': data.mean(),
                    'Медиана': data.median(),
                    'Ст. отклонение': data.std(),
                    'Минимум': data.min(),
                    'Максимум': data.max(),
                    'Количество': data.count(),
                    'За пределами норм': self.calculate_out_of_bounds(data, constraints.get(param, {})),
                    'Лучшее значение': best_worst.get(param, {}).get('best', ''),
                    'Худшее значение': best_worst.get(param, {}).get('worst', ''),
                    'Разброс': best_worst.get(param, {}).get('best', 0) - best_worst.get(param, {}).get('worst', 0),
                    'Индекс качества': quality_index.get(param, '')
                })
            else:
                param_metrics.update({
                    'Количество категорий': df[param].nunique(),
                    'Самая частая категория': df[param].mode()[0] if not df[param].empty else '',
                    'Количество значений': df[param].count()
                })
            
            metrics.append(param_metrics)
        
        return pd.DataFrame(metrics)

    def sanitize_filename(self, name):
        """Очищает имя файла от недопустимых символов"""
        cleaned = re.sub(r'[\\/*?:"<>|]', "_", str(name))
        return cleaned[:50].strip()