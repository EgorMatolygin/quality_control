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
from PyQt5.QtWebEngineWidgets import QWebEngineView

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
        self.btn_process_static = QPushButton("Обработать данные")
        self.btn_process_static.clicked.connect(lambda: self.process_data("static"))
        self.btn_calculate_static = QPushButton("Рассчитать индекс")
        self.btn_calculate_static.clicked.connect(lambda: self.calculate_index("static"))
        self.btn_next_static = QPushButton("Анализировать →")
        self.btn_next_static.clicked.connect(lambda: self.parent.show_results('static'))
        self.btn_next_static.setEnabled(False)
        
        btn_layout.addWidget(self.btn_load_static)
        btn_layout.addWidget(self.btn_process_static)
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
        self.btn_process_dynamic = QPushButton("Обработать данные")
        self.btn_process_dynamic.clicked.connect(lambda: self.process_data("dynamic"))
        self.btn_calculate_dynamic = QPushButton("Рассчитать индекс")
        self.btn_calculate_dynamic.clicked.connect(lambda: self.calculate_index("dynamic"))
        self.btn_next_dynamic = QPushButton("Анализировать →")
        self.btn_next_dynamic.clicked.connect(lambda: self.parent.show_results('dynamic'))
        self.btn_next_dynamic.setEnabled(False)
        
        btn_layout.addWidget(self.btn_load_dynamic)
        btn_layout.addWidget(self.btn_process_dynamic)
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
                
            QMessageBox.information(self, "Успех", "Данные обработаны!")
            
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

class ResultsPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.current_param = None
        self.init_ui()
        
        # Кэш для хранения расчетных статистик
        self.stats_cache = {}

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

    def update_params_list(self, analysis_type):
        """Обновляет список параметров на странице результатов"""
        if analysis_type == 'static':
            data = self.parent.current_static_data
        else:
            data = self.parent.current_dynamic_data

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
        
        # Создаем комбинированный график
        fig = make_subplots(rows=2, cols=2,
                          subplot_titles=[
                              f"Распределение {param}",
                              f"Box-plot {param}",
                              f"Сравнение партий",
                              f"Корреляция с толщиной"
                          ],
                          specs=[[{"type": "xy"}, {"type": "xy"}],
                                 [{"type": "xy"}, {"type": "xy"}]])
        
        # Гистограмма с ограничениями
        self._add_histogram(fig, df, param, constraints, row=1, col=1)
        
        # Box-plot
        self._add_boxplot(fig, df, param, row=1, col=2)
        
        # Сравнение партий
        self._add_batch_comparison(fig, df, param, row=2, col=1)
        
        # Диаграмма рассеивания
        self._add_scatterplot(fig, df, param, row=2, col=2)
        
        # Обновление статистик
        self._update_stats_table(df, param, constraints)
        
        fig.update_layout(height=1000, showlegend=False)
        self.plot_container.setHtml(fig.to_html(include_plotlyjs='cdn'))

    def _add_histogram(self, fig, df, param, constraints, row, col):
        # Добавление гистограммы
        fig.add_trace(go.Histogram(
            x=df[param],
            name=param,
            marker_color='#636efa',
            opacity=0.7
        ), row=row, col=col)
        
        # Линии ограничений
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

    def _add_boxplot(self, fig, df, param, row, col):
        # Box-plot
        fig.add_trace(go.Box(
            y=df[param],
            name=param,
            boxpoints='outliers',
            marker_color='#00cc96'
        ), row=row, col=col)

    def _add_batch_comparison(self, fig, df, param, row, col):
        # Сравнение по партиям
        batches = df['batch_id'].unique()[:3]  # Первые 3 партии
        for batch in batches:
            fig.add_trace(go.Box(
                y=df[df['batch_id'] == batch][param],
                name=batch,
                boxpoints='outliers'
            ), row=row, col=col)

    def _add_scatterplot(self, fig, df, param, row, col):
        # Диаграмма рассеивания с толщиной
        if 'thickness' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['thickness'],
                y=df[param],
                mode='markers',
                marker=dict(color='#ffa600', size=8)
            ), row=row, col=col)

    def _update_stats_table(self, df, param, constraints):
        stats = {
            'Среднее': df[param].mean(),
            'Медиана': df[param].median(),
            'Ст. отклонение': df[param].std(),
            'Минимум': df[param].min(),
            'Максимум': df[param].max(),
            'Количество': df[param].count()
        }
        
        if constraints.get('type') == 'range':
            stats['Допустимый минимум'] = constraints['min']
            stats['Допустимый максимум'] = constraints['max']
        
        self.stats_table.setRowCount(len(stats))
        for i, (key, value) in enumerate(stats.items()):
            self.stats_table.setItem(i, 0, QTableWidgetItem(str(key)))
            self.stats_table.setItem(i, 1, QTableWidgetItem(f"{value:.2f}"))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Анализ качества продукции")
        self.setGeometry(600, 300, 1000, 800)
        self.setWindowIcon(QIcon('resources/icon.png'))
        
        # Инициализация компонентов
        self.init_ui()
        
        # Данные текущей сессии
        self.current_static_data = None
        self.current_dynamic_data = None

        self.static_constraints = {}
        self.dynamic_constraints = {}

        self.constraints = {}
        self.current_params = []

        self.results_page = ResultsPage(self)

    def init_ui(self):
        # Создаем стек виджетов
        self.stacked_widget = QStackedWidget()
        
        # Страницы
        self.input_page = InputPage(self)
        self.results_page = ResultsPage(self)
        
        self.stacked_widget.addWidget(self.input_page)
        self.stacked_widget.addWidget(self.results_page)
        
        self.setCentralWidget(self.stacked_widget)

    def show_results(self, analysis_type):
        try:
            # Определение данных по типу анализа
            data = None
            if analysis_type == 'static':
                data = self.current_static_data
            elif analysis_type == 'dynamic':
                data = self.current_dynamic_data
            else:
                QMessageBox.warning(self, "Ошибка", "Неизвестный тип анализа")
                return

            # Проверка наличия данных
            if data is None or data.empty:
                QMessageBox.warning(self, "Ошибка", "Данные не загружены. Сначала загрузите данные.")
                return

            # Обновление интерфейса результатов
            self.results_page.update_params_list(analysis_type)  # Обновляем список параметров
            self.results_page.update_plots(0)  # Строим графики для первого параметра

            # Переключение на страницу результатов
            self.stacked_widget.setCurrentIndex(1)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Критическая ошибка",
                f"Ошибка при отображении результатов:\n{str(e)}"
            )
            self.stacked_widget.setCurrentIndex(0)

    def show_input(self):
        self.stacked_widget.setCurrentIndex(0)