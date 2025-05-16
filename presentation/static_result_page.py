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


class StaticResultsPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.current_param = None
        self.stats_cache = {}
        self.params = []  # Список доступных параметров
        self.init_ui()
        self.setStyleSheet("background-color: #f0f0f0;")

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)  # Общие отступы
        main_layout.setSpacing(12)
        
        # Заголовок
        self.header = QLabel("Результаты статического анализа", self)
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

        # Вкладки с параметрами
        self.param_tabs = QTabWidget()
        self.param_tabs.currentChanged.connect(self.on_tab_changed)
        self.param_tabs.setDocumentMode(True) 
        self.param_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                background: white;
                margin-top: 4px;
            }
        """)
        main_layout.addWidget(self.param_tabs)

        # Основной контент
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)
            
        # Контейнер для графика
        plot_wrapper = QWidget()
        plot_wrapper.setLayout(QVBoxLayout())
        plot_wrapper.layout().setContentsMargins(0, 0, 0, 0)
        
        self.plot_container = QWebEngineView()
        self.plot_container.setSizePolicy(
            QSizePolicy.Expanding, 
            QSizePolicy.Expanding
        )
        plot_wrapper.layout().addWidget(self.plot_container)

        # Панель статистики
        stats_panel = QWidget()
        stats_panel.setSizePolicy(
            QSizePolicy.Fixed,  # Фиксированная ширина
            QSizePolicy.Expanding
        )
        stats_panel.setMinimumWidth(320)  # Оптимальная ширина для таблицы
        stats_panel.setMaximumWidth(400)
        
        stats_layout = QVBoxLayout(stats_panel)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stats_table = QTableWidget()
        self.stats_table.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Метрика", "Значение"])
        self.stats_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.stats_table.verticalHeader().setVisible(False)
        
        stats_layout.addWidget(QLabel("Статистические показатели:"))
        stats_layout.addWidget(self.stats_table)
        stats_panel.setLayout(stats_layout)

        content_layout.addWidget(plot_wrapper, 1)  # Растягиваемый график
        content_layout.addWidget(stats_panel)      # Фиксированная таблица

        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget, 1)

        # Кнопки навигации
        self.btn_back = QPushButton("← Назад к вводу")
        self.btn_metrics = QPushButton("Таблица метрик →")
        
        # Общий стиль для кнопок
        button_style = """
            QPushButton {
                background-color: #4A90E2;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                border: none;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
            QPushButton:pressed {
                background-color: #2A5F8F;
            }
        """
        self.btn_back.setStyleSheet(button_style)
        self.btn_metrics.setStyleSheet(button_style)

        # Контейнер для кнопок
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(self.btn_back)
        button_layout.addStretch()  # Растягивающееся пространство между кнопками
        button_layout.addWidget(self.btn_metrics)

        self.btn_back.clicked.connect(self.parent.show_input)
        self.btn_metrics.clicked.connect(self.parent.show_metrics_table)

        # Общие стили
        self.setStyleSheet("""
            QWidget {
                background: #f0f0f0;
            }
            QTableWidget {
                background: white;
                border-radius: 6px;
                padding: 8px;
            }
            QWebEngineView {
                background: white;
                border-radius: 6px;
            }
        """)
       
        main_layout.addWidget(button_container)

        self.setLayout(main_layout)

    def update_params_list(self):
        """Обновляет список параметров во вкладках"""
        data = self.parent.current_static_data
        self.param_tabs.clear()
        self.params = []

        if data is not None:
            self.params = [col for col in data.columns if col not in ['id', 'timestamp', "batch_id", 'product_id', 'date']]
            
            for param in self.params:
                tab = QWidget()
                tab.setObjectName(param)
                self.param_tabs.addTab(tab, param)
            
            if self.params:
                # Настройка размеров вкладок после их создания
                self.adjust_tab_sizes()
                self.param_tabs.setCurrentIndex(0)
                self.current_param = self.params[0]
                self.update_plots()

    def adjust_tab_sizes(self):
        tab_bar = self.param_tabs.tabBar()
        metrics = QFontMetrics(tab_bar.font())
        padding = 20
        
        # Принудительные настройки для корректного отображения
        tab_bar.setUsesScrollButtons(True)
        tab_bar.setElideMode(Qt.ElideNone)
        tab_bar.setExpanding(False)  # Отключаем автоматическое растяжение
        
        style_sheet = []
        for i in range(tab_bar.count()):
            text = tab_bar.tabText(i)
            text_width = metrics.horizontalAdvance(text) + 2*padding
            
            style_sheet.append(f"""
                QTabBar::tab:nth-child({i+1}) {{
                    min-width: {text_width}px;
                    max-width: {text_width}px;  # Фиксируем ширину
                    padding: 6px {padding}px;
                    font-size: 12px;
                }}
            """)
        
        base_style = f"""
            QTabBar {{
                min-width: {sum([metrics.horizontalAdvance(tab_bar.tabText(i)) + 2*padding for i in range(tab_bar.count())])}px;
                background: transparent;
            }}
            QTabWidget::pane {{
                border: 1px solid #d0d0d0;
                margin-top: -1px;
            }}  
            QTabBar::tab:selected {{
                background: white;
                color: #2c3e50;
                border-color: #d0d0d0;
                font-weight: bold;
            }}            
            QTabBar::tab {{
                background: #e8e8e8;
                color: #505050;
                border: 1px solid #d0d0d0;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                margin-right: 4px;
            }}
            QTabBar::tab:hover {{
                background: #f0f0f0;
            }}
            QTabBar::tab:!selected {{
                margin-top: 2px;
            }}
            
            QTabBar QToolButton {{
                background: #f0f0f0;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }}
            QTabWidget::pane {{
                border-top: 2px solid #4A90E2; 
                margin: 0;  
                padding: 12px;  
            }}
        """
        
        tab_bar.setStyleSheet('\n'.join(style_sheet) + base_style)
        
        # Принудительное обновление layout
        self.param_tabs.updateGeometry()
        tab_bar.updateGeometry()
        tab_bar.update()
        pass

    def on_tab_changed(self, index):
        """Обработчик смены вкладки"""
        if 0 <= index < len(self.params):
            self.current_param = self.params[index]
            self.update_plots()

    def update_plots(self):
        """Обновляет графики для текущего параметра"""
        if not self.current_param:
            return

        param = self.current_param
        df = self.parent.current_static_data

        if df is None or param not in df.columns:
            return

        constraints = self.parent.static_constraints.get(param, {})
        dtype = 'numeric' if pd.api.types.is_numeric_dtype(df[param]) else 'categorical'

        # Остальной код визуализации остается без изменений
        specs = [[{"type": "xy"}, {"type": "xy"}],
                [{"type": "xy"}, {"type": "xy"}]] if dtype == 'numeric' else \
               [[{"type": "xy"}, {"type": "domain"}],
                [{"type": "xy"}, {"type": "xy"}]]
        
        fig = make_subplots(
            rows=2, cols=2,
            specs=specs,
            subplot_titles=self._get_titles(param, dtype)
        )
        
        if dtype == 'numeric':
            self._add_numeric_visualizations(fig, df, param, constraints)
        else:
            unique_values = df[param].nunique()
            self._add_categorical_visualizations(fig, df, param, constraints, unique_values)
        
        num_batches = len(df['batch_id'].unique()) if 'batch_id' in df.columns else 1
        subplot_height = max(400, 50 * num_batches)
        
        fig.update_layout(
            height=subplot_height*2,
            margin=dict(l=50, r=50, t=80, b=50),
            hovermode='x unified'
        )
        self.plot_container.setHtml(fig.to_html(include_plotlyjs='cdn'))
        self._update_stats_table(df, param, dtype)


    def _get_titles(self, param, dtype):
        base = [
            f"Распределение {param}",
            f"Box-plot {param}" if dtype == 'numeric' else "Соотношение категорий",
            f"Распределение по партиям",  # Новый заголовок
            f"Контрольные пределы {param}" if dtype == 'numeric' else ""
        ]
        return base

    def _add_numeric_visualizations(self, fig, df, param, constraints):
        # Гистограмма с ограничениями
        self._add_histogram(fig, df, param, constraints, row=1, col=1)
        # Box-plot с ограничениями
        self._add_boxplot(fig, df, param, constraints, row=1, col=2)
        # Сравнение партий
        self._add_box_batch_comparison(fig, df, param, constraints, row=2, col=1)
        # Диаграмма рассеивания с ограничениями
        self._add_hist_batch_comparison(fig, df, param, constraints, row=2, col=2)

    def _add_histogram(self, fig, df, param, constraints, row, col):
        # Расчет выходящих за пределы значений
        out_of_bounds = 0
        if constraints:
            if constraints['type'] == 'range':
                min_val = constraints['min']
                max_val = constraints['max']
                out_of_bounds = df[(df[param] < min_val) | (df[param] > max_val)].shape[0]
            elif constraints['type'] == 'min':
                out_of_bounds = df[df[param] < constraints['value']].shape[0]
            elif constraints['type'] == 'max':
                out_of_bounds = df[df[param] > constraints['value']].shape[0]
        
        fig.add_trace(go.Histogram(
            x=df[param],
            name=param,
            marker_color='#636efa',
            opacity=0.7,
            hovertemplate=f"<b>{param}</b>: %{{x}}<br>Count: %{{y}}<extra></extra>"
        ), row=row, col=col)
        
        # Добавляем подписи осей
        fig.update_xaxes(title_text=param, row=row, col=col)
        fig.update_yaxes(title_text="Количество", row=row, col=col)
        
        # Сохраняем метрики для отображения в таблице
        self.stats_cache[param] = self.stats_cache.get(param, {})
        self.stats_cache[param]['out_of_bounds'] = int(out_of_bounds)

        # Добавляем линии ограничений
        if constraints.get('type') == 'range':
            fig.add_vline(
                x=constraints['min'],
                line=dict(color='red', dash='dash', width=2),
                row=row, col=col
            )
            fig.add_vline(
                x=constraints['max'],
                line=dict(color='red', dash='dash', width=2),
                row=row, col=col
            )
        elif constraints.get('type') == 'min':
            fig.add_vline(
                x=constraints['value'],
                line=dict(color='red', dash='dash', width=2),
                row=row, col=col
            )
        elif constraints.get('type') == 'max':
            fig.add_vline(
                x=constraints['value'],
                line=dict(color='red', dash='dash', width=2),
                row=row, col=col
            )

    def _add_boxplot(self, fig, df, param, constraints, row, col):
        fig.add_trace(go.Box(
            y=df[param],
            name=param,
            boxpoints='outliers',
            marker_color='#00cc96'
        ), row=row, col=col)

        # fig.update_xaxes(title_text=param, row=row, col=col)
        fig.update_yaxes(title_text="Значение", row=row, col=col)
        
        # Добавляем горизонтальные линии ограничений
        if constraints.get('type') == 'range':
            fig.add_hline(
                y=constraints['min'],
                line=dict(color='red', dash='dash', width=2),
                row=row, col=col
            )
            fig.add_hline(
                y=constraints['max'],
                line=dict(color='red', dash='dash', width=2),
                row=row, col=col
            )
        elif constraints.get('type') in ['min', 'max']:
            fig.add_hline(
                y=constraints['value'],
                line=dict(color='red', dash='dash', width=2),
                row=row, col=col
            )

    def _add_box_batch_comparison(self, fig, df, param, constraints, row, col):
        if 'batch_id' not in df.columns:
            return
        
        batches = df['batch_id'].unique()
        colors = px.colors.qualitative.Plotly
        
        for i, batch in enumerate(batches):
            batch_data = df[df['batch_id'] == batch][param]
            fig.add_trace(go.Box(
                y=batch_data,
                name=str(batch),
                marker_color=colors[i % len(colors)]),
                row=row,
                col=col
            )

        fig.update_xaxes(title_text="Партия", row=row, col=col)
        fig.update_yaxes(title_text=param, row=row, col=col)
        
        # Добавляем линии ограничений
        if constraints.get('type') == 'range':
            fig.add_hline(
                y=constraints['min'],
                line=dict(color='red', dash='dash', width=2),
                row=row, col=col
            )
            fig.add_hline(
                y=constraints['max'],
                line=dict(color='red', dash='dash', width=2),
                row=row, col=col
            )
        elif constraints.get('type') == 'min':
            fig.add_hline(
                y=constraints['value'],
                line=dict(color='red', dash='dash', width=2),
                row=row, col=col
            )
        elif constraints.get('type') == 'max':
            fig.add_hline(
                y=constraints['value'],
                line=dict(color='red', dash='dash', width=2),
                row=row, col=col
            )
    
    def _add_hist_batch_comparison(self, fig, df, param, constraints, row, col):
        if 'batch_id' not in df.columns:
            return
        
        batches = df['batch_id'].unique()
        colors = px.colors.qualitative.Plotly
        
        # Рассчитываем общие границы для бинов
        x_min = df[param].min()
        x_max = df[param].max()
        n_bins = 20
        bin_size = (x_max - x_min)/n_bins

        # Добавляем гистограммы для каждого батча
        for i, batch in enumerate(batches):
            batch_data = df[df['batch_id'] == batch][param]
            fig.add_trace(go.Histogram(
                x=batch_data,
                name=f'Партия {batch}',
                marker_color=colors[i % len(colors)],
                opacity=0.6,
                xbins=dict(
                    start=x_min,
                    end=x_max,
                    size=bin_size
                ),
                hoverinfo='y+name'
            ), row=row, col=col)

        # Настраиваем оси и внешний вид
        fig.update_xaxes(
            title_text=param, 
            row=row, 
            col=col,
        )
        fig.update_yaxes(title_text="Количество", row=row, col=col)
        fig.update_layout(
            barmode='overlay',
            bargap=0.1,
            hovermode='x unified'
        )

        # Добавляем линии ограничений
        if constraints.get('type') == 'range':
            fig.add_vline(
                x=constraints['min'],
                line=dict(color='red', dash='dash', width=2),
                row=row, col=col
            )
            fig.add_vline(
                x=constraints['max'],
                line=dict(color='red', dash='dash', width=2),
                row=row, col=col
            )
        elif constraints.get('type') == 'min':
            fig.add_vline(
                x=constraints['value'],
                line=dict(color='red', dash='dash', width=2),
                row=row, col=col
            )
        elif constraints.get('type') == 'max':
            fig.add_vline(
                x=constraints['value'],
                line=dict(color='red', dash='dash', width=2),
                row=row, col=col
            )

    def _add_categorical_visualizations(self, fig, df, param, constraints, unique_values):
        # Столбчатая диаграмма с выделением недопустимых категорий
        self._add_bar_chart(fig, df, param, constraints, row=1, col=1)
        
        # Круговой график
        if unique_values <= 10:
            self._add_pie_chart(fig, df, param, constraints, row=1, col=2)
        
        # Сравнение по партиям
        self._add_category_barchart(fig, df, param, constraints, row=2, col=1)

    def _add_bar_chart(self, fig, df, param, constraints, row, col):
        counts = df[param].value_counts().reset_index()
        allowed = constraints.get('allowed', [])
        
        # Генерация цветов
        colors = []
        for category in counts[param]:
            if allowed and category not in allowed:
                colors.append('#ff7f0e')  # Недопустимые категории
            else:
                colors.append('#636efa')  # Стандартный цвет
        
        fig.add_trace(go.Bar(
            x=counts[param],
            y=counts['count'],
            name=param,
            marker_color=colors,
            text=counts['count'],
            textposition='auto'
        ), row=row, col=col)
        
        # Добавляем аннотации для недопустимых категорий
        if allowed:
            for i, category in enumerate(counts[param]):
                if category not in allowed:
                    fig.add_annotation(
                        x=category,
                        y=counts['count'][i],
                        text="Недопустимо",
                        showarrow=True,
                        arrowhead=1,
                        ax=0,
                        ay=-40,
                        row=row,
                        col=col
                    )
        
        fig.update_xaxes(title_text=param, row=row, col=col)
        fig.update_yaxes(title_text="Количество", row=row, col=col)

    def _add_category_barchart(self, fig, df, param, constraints, row, col):
        if 'batch_id' not in df.columns:
            return
        
        allowed = constraints.get('allowed', [])
        counts = df.groupby(['batch_id', param]).size().unstack()
        
        for i, category in enumerate(counts.columns):
            # Определяем цвет категории
            if allowed and category not in allowed:
                color = '#ff7f0e'  # Оранжевый для недопустимых
            else:
                color = px.colors.qualitative.Plotly[i % 10]
                
            fig.add_trace(go.Bar(
                x=counts.index,
                y=counts[category],
                name=category,
                marker_color=color,
                opacity=0.8 if allowed and category not in allowed else 1
            ), row=row, col=col)
        
        fig.update_xaxes(title_text="Партия", row=row, col=col)
        fig.update_yaxes(title_text="Количество", row=row, col=col)
        fig.update_layout(barmode='stack')

    def _add_pie_chart(self, fig, df, param, constraints, row, col):
        counts = df[param].value_counts()
        allowed = constraints.get('allowed', [])
        
        # Создаем цвета для категорий
        colors = []
        for category in counts.index:
            if allowed and category not in allowed:
                colors.append('#ff7f0e')  # Оранжевый для недопустимых
            else:
                colors.append(px.colors.qualitative.Plotly[len(colors) % 10])
        
        fig.add_trace(go.Pie(
            labels=counts.index,
            values=counts.values,
            hole=0.3,
            marker_colors=colors,
            textinfo='percent+label',
            hoverinfo='value'
        ), row=row, col=col)
        fig.update_traces(
            textposition='inside',
            insidetextorientation='radial',
            row=row, 
            col=col
        )

    def _update_stats_table(self, df, param, dtype):
        stats = {}
        best = ''
        worst = ''
        spread = ''
        quality_index = ''

        # Получаем данные из расчетов
        if self.parent.static_best_worst and param in self.parent.static_best_worst:
            best = self.parent.static_best_worst[param].get('best', '')
            worst = self.parent.static_best_worst[param].get('worst', '')
            if isinstance(best, (int, float)) and isinstance(worst, (int, float)):
                spread = best - worst

        if self.parent.static_quality_index is not None and param in self.parent.static_quality_index.columns:
            quality_index = self.parent.static_quality_index[param].iloc[0]  # Доступ через .columns

        if dtype == 'numeric':
            stats = {
                'Среднее': df[param].mean(),
                'Медиана': df[param].median(),
                'Ст. отклонение': df[param].std(),
                'Минимум': df[param].min(),
                'Максимум': df[param].max(),
                'Количество': df[param].count(),
                'За пределами норм': self.stats_cache.get(param, {}).get('out_of_bounds', 0),
                'Лучшее значение': best,
                'Худшее значение': worst,
                'Разброс': spread,
                'Индекс качества': quality_index
            }
        
        self.stats_table.setRowCount(len(stats))
        for i, (key, value) in enumerate(stats.items()):
            self.stats_table.setItem(i, 0, QTableWidgetItem(str(key)))
            if isinstance(value, (float, int)) and not isinstance(value, bool):
                value_str = f"{value:.2f}"
            else:
                value_str = str(value)
            self.stats_table.setItem(i, 1, QTableWidgetItem(value_str))
