# presentation/main_window.py
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QMessageBox, QLabel, QGroupBox, QFormLayout, QComboBox, QLineEdit, 
                            QGridLayout, QScrollArea, QCheckBox, QTableWidget,QTableWidgetItem, QStackedWidget)
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
                self._log_action(f"Data saved to DB: {analysis_type}")
            except Exception as e:
                QMessageBox.warning(self, "Database Warning", 
                                f"Ошибка сохранения в базу данных: {str(e)}")
            finally:
                if db:
                    db.close()

            # Визуальная обратная связь
            QMessageBox.information(
                self,
                "Данные загружены",
                f"Успешно загружено {len(df)} записей\n"
                f"Обнаружено параметров: {len(params)}\n"
                f"Тип анализа: {analysis_type}"
            )

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
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Заголовок
        self.header = QLabel("Результаты анализа", self)
        self.header.setFont(QFont('Georgia', 16))
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setStyleSheet("""
            background-color: #666666;
            color: #ffffff;
            padding: 15px;
            border-radius: 10px;
        """)

        # Контейнер для графиков
        self.tabs = QTabWidget()
        self.plot_container_static = QWebEngineView()
        self.plot_container_dynamic = QWebEngineView()
        
        self.tabs.addTab(self.plot_container_static, "Статические показатели")
        self.tabs.addTab(self.plot_container_dynamic, "Динамические показатели")

        # Кнопка возврата
        self.btn_back = QPushButton("← Назад к вводу")
        self.btn_back.clicked.connect(self.parent.show_input)

        layout.addWidget(self.header)
        layout.addWidget(self.tabs)
        layout.addWidget(self.btn_back)
        
        self.setLayout(layout)

    def update_plots(self, analysis_type):
        if analysis_type == 'static':
            self._create_static_plots()
        else:
            self._create_dynamic_plots()

    def _create_static_plots(self):
        # Пример статических графиков
        df = self.parent.current_static_data
        
        # График 1: Распределение параметров
        fig1 = make_subplots(rows=1, cols=2)
        
        for i, col in enumerate(df.columns[:2]):
            fig1.add_trace(
                go.Histogram(x=df[col], name=col),
                row=1, col=i+1
            )
        fig1.update_layout(title_text="Распределение параметров")
        
        # График 2: Box plot
        fig2 = go.Figure()
        for col in df.columns[:3]:
            fig2.add_trace(go.Box(y=df[col], name=col))
        fig2.update_layout(title_text="Сравнение параметров")

        # Создаем отдельные виджеты для каждого графика
        hist_view = QWebEngineView()
        hist_view.setHtml(fig1.to_html(include_plotlyjs='cdn'))
        
        box_view = QWebEngineView()
        box_view.setHtml(fig2.to_html(include_plotlyjs='cdn'))

        # Добавляем вкладки
        self.tabs.addTab(hist_view, "Распределение")
        self.tabs.addTab(box_view, "Box plot")

    def _create_dynamic_plots(self):
        # Пример динамических графиков
        df = self.parent.current_dynamic_data
        
        # Линейный график
        fig = go.Figure()
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp')
            for col in df.columns[1:3]:
                fig.add_trace(go.Scatter(
                    x=df['timestamp'], 
                    y=df[col],
                    mode='lines+markers',
                    name=col
                ))
        fig.update_layout(
            title="Динамика показателей",
            xaxis_title="Время",
            yaxis_title="Значение"
        )
        
        self._show_plot(fig, self.plot_container_dynamic)

    def _show_plot(self, figure, container):
        # Сохраняем график во временный HTML
        html = '<html><body>'
        html += figure.to_html(include_plotlyjs='cdn')
        html += '</body></html>'
        
        # Отображаем в WebEngineView
        container.setHtml(html)

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
        if (analysis_type == 'static' and self.current_static_data is not None) or \
        (analysis_type == 'dynamic' and self.current_dynamic_data is not None):
            
            try:
                self.results_page.update_plots(analysis_type)
                self.stacked_widget.setCurrentIndex(1)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка визуализации: {str(e)}")
                self.stacked_widget.setCurrentIndex(0)

    def show_input(self):
        self.stacked_widget.setCurrentIndex(0)