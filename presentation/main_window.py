# presentation/main_window.py
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QMessageBox, QLabel, QGroupBox, QFormLayout, QComboBox, QLineEdit, 
                            QGridLayout, QScrollArea, QCheckBox, QTableWidget,QTableWidgetItem, QStackedWidget, QHeaderView)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt
from presentation.widgets.table_widget import TableWidget
from presentation.widgets.plot_widget import PlotWidget
from business.data_processor import DataProcessor
from business.quality_calculator import QualityCalculator
from data.data_manager import DataManager
from data.database import PostgreSQLManager

from presentation.widgets.constraints_panel import ConstraintsPanel

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px  
from PyQt5.QtWebEngineWidgets import QWebEngineView
import pandas as pd

class InputPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent  # MainWindow instance
        self.init_ui()

    def init_ui(self):
        # Заголовок
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
        self.static_constraints_panel = ConstraintsPanel("static", self)
        
        layout.addLayout(btn_layout)
        layout.addWidget(self.static_table)
        layout.addWidget(self.static_constraints_panel)
        layout.addWidget(self.btn_next_static)
        
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
                    if col.lower() not in ['id', 'timestamp', 'time', 'date']]
            
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
            else:
                if self.parent.current_dynamic_data is None:
                    raise ValueError("Нет данных для обработки")
                processed_df = DataProcessor.preprocess_data(self.parent.current_dynamic_data)
                self.parent.current_dynamic_data = processed_df
                self.dynamic_table.display_data(processed_df, max_rows=50)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка обработки: {str(e)}")

    def calculate_index(self, analysis_type):
        try:
            constraints = self.parent.static_constraints if analysis_type == "static" else self.parent.dynamic_constraints
            data = self.parent.current_static_data if analysis_type == "static" else self.parent.current_dynamic_data
        
            if data is None:
                raise ValueError("Сначала загрузите данные")

            result_df = QualityCalculator.calculate_quality_index(
                data,
                constraints=constraints,
                analysis_type=analysis_type
            )

            # Сохранение результатов
            DataManager.save_results(result_df, analysis_type)
            
            QMessageBox.information(self, "Успех", 
                f"Индекс качества для {analysis_type} анализа рассчитан!\n"
                f"Сохранено в: results/{analysis_type}_results.csv")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка расчета: {str(e)}")

class StaticResultsPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.current_param = None
        self.stats_cache = {}
        self.init_ui()
        self.setStyleSheet("background-color: #f0f0f0;")

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Заголовок с фиксированным размером
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

        # Панель управления с фиксированной высотой
        control_panel = QWidget()
        control_layout = QHBoxLayout()
        
        self.param_label = QLabel("Выберите параметр:")
        self.param_label.setFont(QFont('Arial', 12))
        
        self.param_selector = QComboBox()
        self.param_selector.setFont(QFont('Arial', 12))
        self.param_selector.setMinimumWidth(300)
        self.param_selector.currentIndexChanged.connect(self.update_plots)
        
        control_layout.addWidget(self.param_label)
        control_layout.addWidget(self.param_selector)
        control_panel.setLayout(control_layout)
        main_layout.addWidget(control_panel)

        # Основная область с графиком и статистикой
        content_widget = QWidget()
        content_layout = QHBoxLayout()
        
        # Контейнер для графика (70% ширины)
        self.plot_container = QWebEngineView()
        self.plot_container.setMinimumSize(800, 500)
        content_layout.addWidget(self.plot_container, 70)

        # Панель статистики (30% ширины)
        stats_panel = QWidget()
        stats_layout = QVBoxLayout()
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(2)
        self.stats_table.setHorizontalHeaderLabels(["Метрика", "Значение"])
        self.stats_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.stats_table.verticalHeader().setVisible(False)
        
        stats_layout.addWidget(QLabel("Статистические показатели:"))
        stats_layout.addWidget(self.stats_table)
        stats_panel.setLayout(stats_layout)
        content_layout.addWidget(stats_panel, 30)

        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget)

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
        """Обновляет список параметров на странице результатов"""

        data = self.parent.current_static_data

        if data is not None:
            params = [col for col in data.columns if col not in ['id', 'timestamp']]
            self.param_selector.clear()
            self.param_selector.addItems(params)
            if params:
                self.current_param = params[0]
        else:
            self.param_selector.clear()

    def update_plots(self, index):
        param = self.param_selector.currentText()

        if (not param or 
            self.parent.current_static_data is None or 
            self.parent.current_static_data.empty):
            return
        
        df = self.parent.current_static_data
        constraints = self.parent.static_constraints.get(param, {})
        dtype = 'numeric'

        if pd.api.types.is_string_dtype(df[param]) or pd.api.types.is_categorical_dtype(df[param]):
            dtype = 'categorical'
            unique_values = df[param].nunique()
        
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
            self._add_categorical_visualizations(fig, df, param, constraints, unique_values)
        
        num_batches = len(df['batch_id'].unique()) if 'batch_id' in df.columns else 1
        subplot_height = max(400, 50 * num_batches)
        
        fig.update_layout(
            height=subplot_height*2,  # Для 2 рядов
            margin=dict(l=50, r=50, t=80, b=50),
            hovermode='x unified'
        )
        self.plot_container.setHtml(fig.to_html(include_plotlyjs='cdn'))
        self._update_stats_table(df, param, dtype)


    def _get_titles(self, param, dtype):
        base = [
            f"Общее распределение {param}",
            f"Box-plot {param}",
            f"Гистограмма по партиям",
            f"Сравнение партий"
        ]
        return base

    def _add_numeric_visualizations(self, fig, df, param, constraints):
        # Новый порядок графиков:
        self._add_main_histogram(fig, df, param, constraints, row=1, col=1)
        self._add_boxplot(fig, df, param, constraints, row=1, col=2)
        self._add_batch_histograms(fig, df, param, constraints, row=2, col=1)
        self._add_batch_comparison(fig, df, param, constraints, row=2, col=2)

    def _add_main_histogram(self, fig, df, param, constraints, row, col):
        # Расчет базовой статистики
        stats = df[param].describe()
        self.stats_cache[param] = {
            'mean': stats['mean'],
            'std': stats['std'],
            'min': stats['min'],
            'max': stats['max']
        }

        fig.add_trace(go.Histogram(
            x=df[param],
            name="Все данные",
            marker_color='#2A3F5F',
            opacity=0.8,
            hoverinfo='x+y',
            histnorm='probability density',
            marker=dict(
                line=dict(
                    width=1,
                    color='rgba(0,0,0,0.4)'
                )
            )
        ), row=row, col=col)

        # Настройка осей
        fig.update_xaxes(
            title_text=param,
            row=row,
            col=col,
            showgrid=True,
            gridwidth=0.5,
            gridcolor='LightGrey'
        )
        fig.update_yaxes(
            title_text="Плотность распределения",
            row=row,
            col=col,
            tickformat=".1%",
            showgrid=True,
            gridwidth=0.5,
            gridcolor='LightGrey'
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

    def _add_boxplot(self, fig, df, param, constraints, row, col):
        
        fig.add_trace(go.Box(
            y=df[param],
            name=param,
            boxpoints='outliers',
            marker_color='#00CC96',
            line_color='#2A3F5F',
            hoverinfo='y+name',
            jitter=0.5,
            whiskerwidth=0.5,
            boxmean=True
        ), row=row, col=col)

        fig.update_layout(
            boxmode='group',
            boxgap=0.2,
            boxgroupgap=0.3
        )
        
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

    def _add_batch_comparison(self, fig, df, param, constraints, row, col):
        if 'batch_id' not in df.columns:
            return
        
        # Создаем violin plot для сравнения распределений
        fig.add_trace(go.Violin(
            x=df['batch_id'],
            y=df[param],
            name=param,
            box_visible=True,
            meanline_visible=True,
            points='outliers',
            marker_color='#636EFA',
            line_color='#2A3F5F'
        ), row=row, col=col)

        # Настройка осей
        fig.update_xaxes(
            title_text="Номер партии",
            row=row,
            col=col,
            type='category',
            showgrid=True,
            gridwidth=0.5,
            gridcolor='LightGrey'
        )
        fig.update_yaxes(
            title_text=param,
            row=row,
            col=col,
            showgrid=True,
            gridwidth=0.5,
            gridcolor='LightGrey'
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
    
    def _add_batch_histograms(self, fig, df, param, constraints, row, col):
        if 'batch_id' not in df.columns:
            return

        batches = df['batch_id'].unique()
        colors = px.colors.qualitative.Dark24
        
        # Создаем групповые гистограммы с нормализацией
        for i, batch in enumerate(batches):
            batch_data = df[df['batch_id'] == batch][param]
            fig.add_trace(go.Histogram(
                x=batch_data,
                name=f"Партия {batch}",
                marker_color=colors[i % len(colors)],
                opacity=0.6,
                histnorm='probability density',
                hoverinfo='x+y+name',
                showlegend=True
            ), row=row, col=col)

        # Настройка осей и внешнего вида
        fig.update_xaxes(
            title_text=param,
            row=row,
            col=col,
            showgrid=True,
            gridwidth=0.5,
            gridcolor='LightGrey'
        )
        fig.update_yaxes(
            title_text="Плотность распределения",
            row=row,
            col=col,
            tickformat=".1%",
            showgrid=True,
            gridwidth=0.5,
            gridcolor='LightGrey'
        )
        fig.update_layout(
            barmode='overlay',
            bargap=0.1,
            bargroupgap=0.05
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
        if dtype == 'numeric':
            stats = {
                'Среднее': df[param].mean(),
                'Медиана': df[param].median(),
                'Ст. отклонение': df[param].std(),
                'Минимум': df[param].min(),
                'Максимум': df[param].max(),
                'Количество': df[param].count(),
                'За пределами норм': self.stats_cache.get(param, {}).get('out_of_bounds', 0)
            }
        else:
            counts = df[param].value_counts()
            stats = {
                'Уникальных значений': counts.shape[0],
                'Наиболее частый': counts.index[0],
                'Частота моды': counts.values[0],
                'Всего записей': counts.sum(),
                'Недопустимых значений': self.stats_cache.get(param, {}).get('out_of_bounds', 0)
            }
        
        self.stats_table.setRowCount(len(stats))
        for i, (key, value) in enumerate(stats.items()):
            self.stats_table.setItem(i, 0, QTableWidgetItem(str(key)))
            self.stats_table.setItem(i, 1, QTableWidgetItem(
                f"{value:.2f}" if isinstance(value, (float, int)) and not isinstance(value, bool) else str(value)
            ))


class DynamicResultsPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.current_param = None
        self.stats_cache = {}
        self.init_ui()
        self.setStyleSheet("background-color: #f0f0f0;")

    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Заголовок
        self.header = QLabel("Результаты динамического анализа", self)
        self.header.setFont(QFont('Arial', 18, QFont.Bold))
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setStyleSheet("""
            background-color: #00AA00;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        """)
        
        # Панель управления
        control_panel = QWidget()
        control_layout = QHBoxLayout()
        
        self.param_label = QLabel("Выберите параметр:")
        self.param_selector = QComboBox()
        self.time_selector = QComboBox()
        self.time_selector.addItems(["Час", "День", "Неделя", "Месяц"])
        
        control_layout.addWidget(self.param_label)
        control_layout.addWidget(self.param_selector)
        control_layout.addWidget(QLabel("Группировка:"))
        control_layout.addWidget(self.time_selector)
        control_panel.setLayout(control_layout)
        
        # Контейнер для графиков
        self.plot_container = QWebEngineView()
        self.plot_container.setMinimumSize(800, 600)
        
        # Кнопка возврата
        self.btn_back = QPushButton("← Назад к вводу")
        self.btn_back.clicked.connect(self.parent.show_input)
        
        main_layout.addWidget(self.header)
        main_layout.addWidget(control_panel)
        main_layout.addWidget(self.plot_container)
        main_layout.addWidget(self.btn_back, alignment=Qt.AlignRight)
        
        self.setLayout(main_layout)
        
        # Подключение сигналов
        self.param_selector.currentIndexChanged.connect(self.update_plots)
        self.time_selector.currentIndexChanged.connect(self.update_plots)

    def update_params_list(self):
        data = self.parent.current_dynamic_data
        if data is not None:
            params = [col for col in data.columns if col not in ['id', 'timestamp', 'time', 'date']]
            self.param_selector.clear()
            self.param_selector.addItems(params)

    def update_plots(self):
        param = self.param_selector.currentText()
        time_group = self.time_selector.currentText()
        df = self.parent.current_dynamic_data
        
        if df is None or param not in df.columns:
            return
        
        # Преобразование временных меток
        time_col = 'timestamp' if 'timestamp' in df.columns else 'date'
        df[time_col] = pd.to_datetime(df[time_col])
        
        # Группировка данных
        freq_map = {'Час': 'H', 'День': 'D', 'Неделя': 'W', 'Месяц': 'M'}
        grouped = df.groupby(pd.Grouper(key=time_col, freq=freq_map[time_group]))[param].mean()
        
        # Создание графиков
        fig = make_subplots(rows=2, cols=1, subplot_titles=[
            f"Динамика параметра {param}",
            "Контрольная карта"
        ])
        
        # Временной ряд
        fig.add_trace(go.Scatter(
            x=grouped.index,
            y=grouped.values,
            mode='lines+markers',
            name=param,
            line=dict(color='#FFA15A')
        ), row=1, col=1)
        
        # Контрольная карта
        mean = grouped.mean()
        std = grouped.std()
        
        fig.add_trace(go.Scatter(
            x=grouped.index,
            y=grouped.values,
            mode='lines+markers',
            name=param,
            line=dict(color='#00CC96')
        ), row=2, col=1)
        
        fig.add_hline(y=mean, line_dash="dot", line_color="blue", row=2, col=1)
        fig.add_hline(y=mean + 3*std, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=mean - 3*std, line_dash="dash", line_color="red", row=2, col=1)
        
        fig.update_layout(height=800, showlegend=False)
        self.plot_container.setHtml(fig.to_html(include_plotlyjs='cdn'))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Анализ качества продукции")
        self.setGeometry(600, 300, 1000, 800)
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
        
        # Инициализация UI
        self.init_ui()

    def init_ui(self):
        # Создаем стек виджетов
        self.stacked_widget = QStackedWidget()
        
        # Добавляем ВСЕ страницы
        self.stacked_widget.addWidget(self.input_page)
        self.stacked_widget.addWidget(self.static_results_page)
        self.stacked_widget.addWidget(self.dynamic_results_page)
        
        self.setCentralWidget(self.stacked_widget)


    def show_results(self, analysis_type):
        try:
            if analysis_type == 'static':
                page = self.static_results_page
                self.input_page.process_data("static")
                data = self.current_static_data
                page.update_params_list()
                page.update_plots(0)
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