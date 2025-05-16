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

class DynamicResultsPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.current_param = None
        self.current_batch = None
        self.arima_predictor = ARIMAPredictor(self)
        self.init_ui()
        self.setStyleSheet("background-color: #f0f0f0;")

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Заголовок
        self.header = QLabel("Результаты динамического анализа", self)
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

        # Панель управления
        control_panel = QWidget()
        control_layout = QGridLayout()
        
        # Выбор параметра
        self.param_label = QLabel("Параметр:")
        self.param_selector = QComboBox()
        self.param_selector.currentIndexChanged.connect(self.update_plots)
        
        # Выбор партии
        self.batch_label = QLabel("Партия:")
        self.batch_selector = QComboBox()
        self.batch_selector.addItem("Все партии")
        self.batch_selector.setCurrentIndex(0)
        self.batch_selector.currentIndexChanged.connect(self.update_plots)
        
        # Кнопка прогноза
        self.btn_forecast = QPushButton("Построить прогноз")
        self.btn_forecast.clicked.connect(self.run_forecast)
        self.btn_forecast.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)

        control_layout.addWidget(self.param_label, 0, 0)
        control_layout.addWidget(self.param_selector, 0, 1)
        control_layout.addWidget(self.batch_label, 1, 0)
        control_layout.addWidget(self.batch_selector, 1, 1)
        control_layout.addWidget(self.btn_forecast, 0, 2, 2, 1)
        control_panel.setLayout(control_layout)
        main_layout.addWidget(control_panel)

        # График
        self.plot_container = QWebEngineView()
        self.plot_container.setMinimumSize(800, 500)
        main_layout.addWidget(self.plot_container)

        # Кнопка возврата
        self.btn_back = QPushButton("← Назад к вводу")
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: #FF6B6B;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #FF5252; }
        """)
        self.btn_back.clicked.connect(self.parent.show_input)
        main_layout.addWidget(self.btn_back, alignment=Qt.AlignRight)

        self.setLayout(main_layout)

    def update_params_list(self):
        """Обновляет списки параметров и партий"""
        df = self.parent.current_dynamic_data
        if df is not None:
            # Обновление параметров
            numeric_params = [
                col for col in df.columns 
                if pd.api.types.is_numeric_dtype(df[col])
                and col.lower() not in ['id', 'timestamp', 'time', 'date', 'batch_id', 'batch','date']
            ]
            self.param_selector.clear()
            self.param_selector.addItems(numeric_params)
            
            # Обновление партий
            self.batch_selector.clear()

            self.batch_selector.addItem("Все партии")
            
            # Поиск колонки с партиями
            batch_col = next((col for col in df.columns if col.lower() in ['batch_id', 'batch']), None)
            if batch_col:
                batches = [str(b) for b in df[batch_col].unique()]
                self.batch_selector.addItems(batches)

    def get_param_constraints(self, param):
        """Получает ограничения для параметра"""
        constraints = self.parent.dynamic_constraints.get(param, {})
        
        # Возвращаем в формате: (min, max)
        if constraints.get('type') == 'range':
            return (constraints.get('min'), constraints.get('max'))
        elif constraints.get('type') == 'min':
            return (constraints.get('value'), None)
        elif constraints.get('type') == 'max':
            return (None, constraints.get('value'))
        return (None, None)

    def filter_data(self):
        """Фильтрация с проверкой существования колонки и значений"""
        df = self.parent.current_dynamic_data
        if df is None:
            return None

        batch = self.batch_selector.currentText()
        if batch == "Все партии" or batch == "":
            return df

        # Поиск колонки с партиями с учетом возможных вариантов
        batch_col = None
        possible_names = ['batch_id', 'batch', 'lot', 'партия', 'lot_id', 'part_number']
        for col in df.columns:
            if col.lower() in possible_names:
                batch_col = col
                break

        if not batch_col:
            QMessageBox.warning(self, "Ошибка", 
                f"Колонка с партиями не найдена! Доступные колонки:\n{', '.join(df.columns)}")
            return df

        # Проверка существования выбранной партии
        try:
            available_batches = df[batch_col].astype(str).unique()
            if batch not in available_batches:
                QMessageBox.warning(self, "Ошибка", 
                    f"Партия '{batch}' не найдена в колонке '{batch_col}'\n"
                    f"Доступные партии:\n{', '.join(available_batches)}")
                return df[df[batch_col].astype(str) == batch]
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка проверки партий: {str(e)}")
            return df

        # Фильтрация данных
        try:
            filtered_df = df[df[batch_col].astype(str) == batch]
            if filtered_df.empty:
                QMessageBox.warning(self, "Ошибка", 
                    f"Нет данных для партии '{batch}' в колонке '{batch_col}'")
            return filtered_df
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка фильтрации: {str(e)}")
            return df

    def update_plots(self, index=None):
        """Обновляет график временных рядов"""
        try:
            param = self.param_selector.currentText()
            df = self.filter_data()
            
            if df is None or param not in df.columns:
                return

            # Поиск временной колонки
            time_col = next((col for col in df.columns if col.lower() in ['timestamp', 'time', 'date']), None)
            if not time_col:
                QMessageBox.warning(self, "Ошибка", "Временная колонка не найдена")
                return

            # Конвертация времени
            df[time_col] = pd.to_datetime(df[time_col])
            df = df.sort_values(time_col)

            # Подготовка данных
            time_series = df.groupby(time_col)[param].mean()
            
            # Создание графика
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=time_series.index,
                y=time_series.values,
                mode='lines+markers',
                name='Исторические данные',
                line=dict(color='#1f77b4'))
            )
            
            # Настройка макета
            fig.update_layout(
                title=f'Динамика параметра {param}',
                xaxis_title='Время',
                yaxis_title=param,
                hovermode='x unified',
                margin=dict(l=50, r=50, t=60, b=50)
            )
            
            min_limit, max_limit = self.get_param_constraints(param)

            # Добавляем линии ограничений
            if min_limit is not None:
                fig.add_hline(
                    y=min_limit,
                    line=dict(color='red', width=2, dash='dash'),
                    annotation_text=f"Min: {min_limit}",
                    annotation_position="bottom right"
                )

            if max_limit is not None:
                fig.add_hline(
                    y=max_limit,
                    line=dict(color='red', width=2, dash='dash'),
                    annotation_text=f"Max: {max_limit}",
                    annotation_position="top right"
                )

            print("# Добавляем линии ограничений")

            self.plot_container.setHtml(fig.to_html(include_plotlyjs='cdn'))
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка построения графика: {str(e)}")

    def run_forecast(self):
        """Запускает прогнозирование ARIMA с ограничениями"""
        try:
            param = self.param_selector.currentText()
            df = self.filter_data()
            
            if df is None or param not in df.columns:
                return

            # Поиск и проверка временной колонки
            time_col = next((col for col in df.columns if col.lower() in ['timestamp', 'time', 'date']), None)
            if not time_col:
                QMessageBox.warning(self, "Ошибка", "Временная колонка не найдена!")
                return

            time_series = df.groupby(time_col)[param].mean().reset_index()
            
            # Прогноз
            result = self.arima_predictor.predict(time_series, param, time_col=time_col)

            if result is None:
                return

            # Проверка данных прогноза
            if len(result['forecast']) == 0:
                QMessageBox.warning(self, "Ошибка", "Невозможно построить прогноз: недостаточно данных")
                return

            # Создаем график
            fig = go.Figure()
            
            # 1. Исторические данные
            fig.add_trace(go.Scatter(
                x=result['history'].index,
                y=result['history'].values,
                mode='lines+markers',
                name='История',
                line=dict(color='#1f77b4', width=2)
            ))

            # 2. Прогноз с соединением последней точки истории
            if not result['history'].empty and not result['forecast'].empty:
                # Создаем переходную точку: последнее историческое значение + первый прогноз
                transition_point = pd.Series(
                    [result['history'].iloc[-1], result['forecast'].iloc[0]],
                    index=[result['history'].index[-1], result['forecast'].index[0]]
                )
                forecast_with_transition = pd.concat([transition_point, result['forecast'].iloc[1:]])
            else:
                forecast_with_transition = result['forecast']

            # график прогноза
            fig.add_trace(go.Scatter(
                x=forecast_with_transition.index,
                y=forecast_with_transition.values,
                mode='lines+markers',
                name='Прогноз',
                line=dict(color='#ff7f0e', width=3, dash='solid'),
                marker=dict(size=8, symbol='diamond')
            ))

             # 3. Доверительный интервал с переходной точкой
            if not result['history'].empty and not result['conf_int'].empty:
                # Добавляем последнюю историческую точку в доверительный интервал
                last_hist_value = result['history'].iloc[-1]
                last_hist_date = result['history'].index[-1]
                
                # Создаем "искусственную" точку доверительного интервала
                hist_conf_row = pd.DataFrame(
                    {'lower': [last_hist_value], 'upper': [last_hist_value]},
                    index=[last_hist_date]
                )
                # Объединяем с оригинальным интервалом
                extended_conf_int = pd.concat([hist_conf_row, result['conf_int']])
            else:
                extended_conf_int = result['conf_int']

            fig.add_trace(go.Scatter(
                x=extended_conf_int.index.tolist() + extended_conf_int.index[::-1].tolist(),
                y=extended_conf_int['lower'].tolist() + extended_conf_int['upper'][::-1].tolist(),
                fill='toself',
                fillcolor='rgba(255,127,14,0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                name='95% ДИ'
            ))

            min_limit, max_limit = self.get_param_constraints(param)
            
            # Добавляем линии ограничений
            if min_limit is not None:
                fig.add_hline(
                    y=min_limit,
                    line=dict(color='red', width=2, dash='dash'),
                    annotation_text=f"Min: {min_limit}",
                    annotation_position="bottom right"
                )

            print("# Добавляем линии ограничений")
            
            if max_limit is not None:
                fig.add_hline(
                    y=max_limit,
                    line=dict(color='red', width=2, dash='dash'),
                    annotation_text=f"Max: {max_limit}",
                    annotation_position="top right"
                )

            print("# Добавляем линии ограничений")

            # Настройка макета
            fig.update_layout(
                title=f'Прогноз {param} с ограничениями',
                xaxis_title='Дата',
                yaxis_title=param,
                hovermode='x unified',
                margin=dict(l=50, r=50, t=80, b=50),
                legend=dict(orientation="h", yanchor="bottom", y=1.02)
            )
        
            self.plot_container.setHtml(fig.to_html(include_plotlyjs='cdn'))

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка прогноза: {str(e)}")
