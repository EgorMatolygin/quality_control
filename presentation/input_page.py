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

class InputPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent  # MainWindow instance
        self.init_ui()

    def init_ui(self):
        # Заголовок
        self.setMaximumHeight(1000)
        self.header = QLabel("Система анализа качества продукции", self)
        self.header.setFont(QFont('Georgia', 16))
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setStyleSheet("""
            background-color: #666666;
            color: #ffffff;
            padding: 15px;
            border-radius: 10px;
        """)
        
        # Вкладки
        self.tabs = QTabWidget()
        self.static_tab = self.create_static_tab()
        self.dynamic_tab = self.create_dynamic_tab()
        
        self.tabs.addTab(self.static_tab, "Статический анализ") 
        self.tabs.addTab(self.dynamic_tab, "Динамический анализ")
        
        # Основной лейаут
        layout = QVBoxLayout()
        layout.addWidget(self.header)
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def create_static_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.btn_load_static = QPushButton("Загрузить CSV/Excel")
        self.btn_load_static.clicked.connect(lambda: self.load_data("static"))
        self.btn_calculate_static = QPushButton("Рассчитать индекс")
        self.btn_calculate_static.clicked.connect(lambda: self.calculate_index("static"))
        self.btn_next_static = QPushButton("Анализировать →")
        self.btn_next_static.clicked.connect(lambda: self.parent.show_results('static'))
        self.btn_next_static.setEnabled(False)
        
        btn_layout.addWidget(self.btn_load_static)
        btn_layout.addWidget(self.btn_calculate_static)

        # Панель ограничений и таблица
        self.static_table = TableWidget()
        self.static_table.setMinimumWidth(800)
        self.static_table.setMaximumHeight(300)
        self.static_constraints_panel = ConstraintsPanel("static", self)
        
        layout.addLayout(btn_layout)
        layout.addWidget(self.static_table)
        layout.addWidget(self.static_constraints_panel)
        layout.addWidget(self.btn_next_static)
        #layout.addStretch(1)  # Добавляем растягивающееся пространство
        widget.setLayout(layout)
        return widget

    def create_dynamic_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.btn_load_dynamic = QPushButton("Загрузить CSV/Excel")
        self.btn_load_dynamic.clicked.connect(lambda: self.load_data("dynamic"))
        self.btn_calculate_dynamic = QPushButton("Рассчитать индекс")
        self.btn_calculate_dynamic.clicked.connect(lambda: self.calculate_index("dynamic"))
        self.btn_next_dynamic = QPushButton("Анализировать →")
        self.btn_next_dynamic.clicked.connect(lambda: self.parent.show_results('dynamic'))
        self.btn_next_dynamic.setEnabled(False)
        
        btn_layout.addWidget(self.btn_load_dynamic)
        btn_layout.addWidget(self.btn_calculate_dynamic)

        # Панель ограничений и таблица
        self.dynamic_table = TableWidget()
        self.dynamic_table.setMinimumWidth(800)
        self.dynamic_table.setMaximumHeight(300)
        self.dynamic_constraints_panel = ConstraintsPanel("dynamic", self)
        
        layout.addLayout(btn_layout)
        layout.addWidget(self.dynamic_table)
        layout.addWidget(self.dynamic_constraints_panel)
        layout.addWidget(self.btn_next_dynamic)
        
        widget.setLayout(layout)
        return widget

    def load_data(self, analysis_type):
        """Загрузка и обработка данных для выбранного типа анализа"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл данных",
            "",
            "Data Files (*.csv *.xlsx)"
        )
        
        if not file_path:
            return  # Пользователь отменил выбор файла

        try:
            # Загрузка данных из файла
            df = DataManager.load_data(file_path)
            
            # Извлечение списка параметров (исключая служебные колонки)
            params = [col for col in df.columns 
                    if col.lower() not in ['id', 'timestamp', 'time', 'date',"batch_id", 'product_id']]
            
            # Обновление интерфейса для соответствующего типа анализа
            if analysis_type == "static":
                # Обновление панели ограничений
                self.static_constraints_panel.update_params(params)
                
                # Сохранение данных и обновление таблицы
                self.parent.current_static_data = df
                self.btn_next_static.setEnabled(True)
                self.static_table.display_data(df, max_rows=50)
                
                # Очистка предыдущих ограничений при новой загрузке
                self.static_constraints_panel.clear_constraints()
            else:
                # Обновление панели ограничений
                self.dynamic_constraints_panel.update_params(params)
                
                # Сохранение данных и обновление таблицы
                self.parent.current_dynamic_data = df
                self.btn_next_dynamic.setEnabled(True)
                self.dynamic_table.display_data(df, max_rows=50)
                
                # Очистка предыдущих ограничений при новой загрузке
                self.dynamic_constraints_panel.clear_constraints()

            # Автоматическое сохранение сырых данных в PostgreSQL
            db = None
            try:
                db = PostgreSQLManager()
                db.save_raw_data(df, analysis_type)
            except Exception as e:
                QMessageBox.warning(self, "Database Warning", 
                                f"Ошибка сохранения в базу данных: {str(e)}")
            finally:
                if db:
                    db.close()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Критическая ошибка",
                f"Непредвиденная ошибка: {str(e)}\n\n"
            )

    def process_data(self, analysis_type):
        try:
            if analysis_type == "static":
                if self.parent.current_static_data is None:
                    raise ValueError("Нет данных для обработки")
                processed_df = DataProcessor.preprocess_data(self.parent.current_static_data)
                self.parent.current_static_data = processed_df
                self.static_table.display_data(processed_df, max_rows=50)
                self.calculate_index('static')
            else:
                if self.parent.current_dynamic_data is None:
                    raise ValueError("Нет данных для обработки")
                processed_df = DataProcessor.preprocess_data(self.parent.current_dynamic_data)
                self.parent.current_dynamic_data = processed_df
                self.dynamic_table.display_data(processed_df, max_rows=50)
                self.calculate_index('dynamic')
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка обработки: {str(e)}")

    def calculate_index(self, analysis_type):
        try:
            constraints = self.parent.static_constraints if analysis_type == "static" else self.parent.dynamic_constraints
            data = self.parent.current_static_data if analysis_type == "static" else self.parent.current_dynamic_data
        
            if data is None:
                raise ValueError("Сначала загрузите данные")

            # Преобразуем результат в DataFrame
            result_series = QualityCalculator.calculate_quality_index(
                data,
                constraints=constraints,
                analysis_type=analysis_type
            )
            result_df = result_series.to_frame().T  # Конвертируем Series в DataFrame

            # Сохраняем результаты расчета
            if analysis_type == "static":
                self.parent.static_quality_index = result_df
                self.parent.static_best_worst = QualityCalculator.calculate_actual_best_worst(data, constraints)
            else:
                self.parent.dynamic_quality_index = result_df
                self.parent.dynamic_best_worst = QualityCalculator.calculate_actual_best_worst(data, constraints)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка расчета: {str(e)}")
