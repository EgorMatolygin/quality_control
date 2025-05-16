# presentation/main_window.py
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QMessageBox, QLabel, QGroupBox, QFormLayout, QComboBox, QLineEdit, 
                            QGridLayout, QScrollArea, QCheckBox, QTableWidget,QTableWidgetItem, QStackedWidget, QHeaderView, QSizePolicy)
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

        # Кнопки
        btn_layout = QHBoxLayout()
        self.btn_back = QPushButton("← Назад")
        self.btn_back.clicked.connect(lambda: self.parent.show_results('static'))
        btn_layout.addWidget(self.btn_back)
        main_layout.addLayout(btn_layout)

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Анализ качества продукции")
        self.setGeometry(400, 200, 800, 600)
        self.setWindowIcon(QIcon('resources/icon.png'))
        
        # Инициализируем данные ДО создания страниц
        self.current_static_data = None
        self.current_dynamic_data = None
        self.static_constraints = {}
        self.dynamic_constraints = {}
        
        # Создаем страницы результатов ПЕРЕД вызовом init_ui()
        self.input_page = InputPage(self)
        self.static_results_page = StaticResultsPage(self)
        self.dynamic_results_page = DynamicResultsPage(self)

        # Добавляем новую страницу
        self.metrics_table_page = MetricsTablePage(self)

        self.static_quality_index = None
        self.static_best_worst = None
        self.dynamic_quality_index = None
        self.dynamic_best_worst = None
        
        # Инициализация UI
        self.init_ui()

    def init_ui(self):
        # Создаем стек виджетов
        self.stacked_widget = QStackedWidget()
        
        # Добавляем ВСЕ страницы
        self.stacked_widget.addWidget(self.input_page)
        self.stacked_widget.addWidget(self.static_results_page)
        self.stacked_widget.addWidget(self.dynamic_results_page)
        self.stacked_widget.addWidget(self.metrics_table_page)
        
        self.setCentralWidget(self.stacked_widget)


    def show_results(self, analysis_type):
        try:
            if analysis_type == 'static':
                page = self.static_results_page
                self.input_page.process_data("static")
                data = self.current_static_data
                page.update_params_list()
                page.update_plots()
                self.stacked_widget.setCurrentIndex(1)
            elif analysis_type == 'dynamic':
                page = self.dynamic_results_page
                self.input_page.process_data("dynamic")
                data = self.current_dynamic_data
                page.update_params_list()
                page.update_plots()
                self.stacked_widget.setCurrentIndex(2)
                
            if data is None or data.empty:
                QMessageBox.warning(self, "Ошибка", "Данные не загружены")
                return

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка отображения: {str(e)}")
            self.stacked_widget.setCurrentIndex(0)

    def show_input(self):
        self.stacked_widget.setCurrentIndex(0)

    def show_metrics_table(self):
        """Показывает страницу с таблицей метрик"""
        self.metrics_table_page.update_batches()
        self.metrics_table_page.update_table()
        self.stacked_widget.setCurrentWidget(self.metrics_table_page)