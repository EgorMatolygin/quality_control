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
        """Фильтрация данных с учетом выбора партии"""
        df = self.parent.current_dynamic_data
        if df is None:
            return None

        batch = self.batch_selector.currentText()
        batch_col = next((col for col in df.columns if col.lower() in ['batch_id', 'batch']), None)

        if not batch_col or batch == "Все партии":
            return df

        return df[df[batch_col].astype(str) == batch]

    def update_plots(self, index=None):
        """Обновляет график временных рядов для всех партий"""
        try:
            param = self.param_selector.currentText()
            df = self.filter_data()
            
            if df is None or param not in df.columns:
                return

            time_col = next((col for col in df.columns if col.lower() in ['timestamp', 'time', 'date']), None)
            batch_col = next((col for col in df.columns if col.lower() in ['batch_id', 'batch']), None)

            fig = go.Figure()
            colors = px.colors.qualitative.Plotly

            # Отображаем все партии если выбрано "Все"
            batches = df[batch_col].unique() if self.batch_selector.currentText() == "Все партии" else [None]

            for i, batch in enumerate(batches):
                if batch is not None:
                    batch_df = df[df[batch_col] == batch]
                    label = str(batch)
                else:
                    batch_df = df
                    label = "Все данные"

                time_series = batch_df.groupby(time_col)[param].mean()
                
                fig.add_trace(go.Scatter(
                    x=time_series.index,
                    y=time_series.values,
                    mode='lines+markers',
                    name=label,
                    line=dict(color=colors[i % len(colors)])
                ))

            fig.update_layout(
                title=f'Динамика {param}',
                xaxis_title='Время',
                yaxis_title=param,
                hovermode='x unified'
            )
            self.plot_container.setHtml(fig.to_html(include_plotlyjs='cdn'))

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка построения графика: {str(e)}")

    def run_forecast(self):
        """Запускает прогнозирование ARIMA с доверительными интервалами"""
        try:
            param = self.param_selector.currentText()
            df = self.parent.current_dynamic_data
            
            if df is None or param not in df.columns:
                return

            # Определяем колонки
            time_col = next((col for col in df.columns if col.lower() in ['timestamp', 'time', 'date']), None)
            batch_col = next((col for col in df.columns if col.lower() in ['batch_id', 'batch']), None)
            
            if not time_col or not batch_col:
                QMessageBox.warning(self, "Ошибка", "Не найдены временная или партийная колонки")
                return

            # Создаем график
            fig = go.Figure()
            colors = px.colors.qualitative.Plotly
            
            # Получаем список партий
            selected_batch = self.batch_selector.currentText()
            batches = [selected_batch] if selected_batch != "Все партии" else df[batch_col].unique()

            for i, batch in enumerate(batches):
                # Фильтруем данные для партии
                batch_df = df[df[batch_col].astype(str) == str(batch)]
                time_series = batch_df.groupby(time_col)[param].mean().reset_index()
                
                if time_series.empty:
                    continue

                # Прогнозирование
                result = self.arima_predictor.predict(time_series, param, time_col=time_col)
                if not result or result['forecast'].empty:
                    continue

                # Цвет для текущей партии
                line_color = colors[i % len(colors)]
                fill_color = f'rgba{(self.hex_to_rgb(line_color), 0.2)}'

                # Исторические данные
                fig.add_trace(go.Scatter(
                    x=result['history'].index,
                    y=result['history'].values,
                    mode='lines+markers',
                    name=f'{batch} История',
                    line=dict(color=line_color, width=2))
                )

                # Прогноз
                forecast = result['forecast']
                fig.add_trace(go.Scatter(
                    x=forecast.index,
                    y=forecast.values,
                    mode='lines+markers',
                    name=f'{batch} Прогноз',
                    line=dict(color=line_color, width=2, dash='dash'),
                    marker=dict(symbol='diamond'))
                )

                # Доверительный интервал
                if not result['conf_int'].empty:
                    # Соединяем последнюю точку истории с первым прогнозом
                    extended_index = [result['history'].index[-1]] + forecast.index.tolist()
                    extended_lower = [result['history'].iloc[-1]] + result['conf_int']['lower'].tolist()
                    extended_upper = [result['history'].iloc[-1]] + result['conf_int']['upper'].tolist()

                    fig.add_trace(go.Scatter(
                        x=extended_index + extended_index[::-1],
                        y=extended_upper + extended_lower[::-1],
                        fill='toself',
                        fillcolor=fill_color,
                        line=dict(color='rgba(255,255,255,0)'),
                        name=f'{batch} 95% ДИ',
                        hoverinfo='none'
                    ))

            # Ограничения
            min_limit, max_limit = self.get_param_constraints(param)
            if min_limit is not None:
                fig.add_hline(y=min_limit, line=dict(color='red', dash='dash'), annotation_text="Min Limit")
            if max_limit is not None:
                fig.add_hline(y=max_limit, line=dict(color='red', dash='dash'), annotation_text="Max Limit")

            fig.update_layout(
                title=f'Прогноз {param} с доверительными интервалами',
                xaxis_title='Дата',
                yaxis_title=param,
                hovermode='x unified'
            )
            self.plot_container.setHtml(fig.to_html(include_plotlyjs='cdn'))

            # Добавляем ограничения
            min_limit, max_limit = self.get_param_constraints(param)
            if min_limit is not None:
                fig.add_hline(y=min_limit, line=dict(color='red', dash='dash'), annotation_text="Min Limit")
            if max_limit is not None:
                fig.add_hline(y=max_limit, line=dict(color='red', dash='dash'), annotation_text="Max Limit")

            # Настройка отображения
            fig.update_layout(
                title=f'Прогноз {param} по партиям',
                xaxis_title='Дата',
                yaxis_title=param,
                hovermode='x unified',
                margin=dict(t=40)
            )
            self.plot_container.setHtml(fig.to_html(include_plotlyjs='cdn'))

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка прогноза: {str(e)}")
    
    def hex_to_rgb(self, hex_color):
        """Конвертирует hex в RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))