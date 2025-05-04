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

class InputPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Заголовок
        header = QLabel("Ввод данных и ограничений")
        header.setFont(QFont('Georgia', 16))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            background-color: #666666;
            color: #ffffff;
            padding: 15px;
            border-radius: 10px;
        """)
        
        # Селектор типа анализа
        self.analysis_type = QComboBox()
        self.analysis_type.addItems(["Статический анализ", "Динамический анализ"])
        self.analysis_type.currentIndexChanged.connect(self.switch_analysis_type)
        
        # Контейнеры для разных типов анализа
        self.static_widget = self.create_static_widget()
        self.dynamic_widget = self.create_dynamic_widget()
        self.dynamic_widget.setVisible(False)
        
        layout.addWidget(header)
        layout.addWidget(self.analysis_type)
        layout.addWidget(self.static_widget)
        layout.addWidget(self.dynamic_widget)
        
        self.setLayout(layout)
    
    def switch_analysis_type(self):
        index = self.analysis_type.currentIndex()
        self.static_widget.setVisible(index == 0)
        self.dynamic_widget.setVisible(index == 1)
    
    def create_static_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Кнопки статического анализа
        btn_layout = QHBoxLayout()
        self.btn_load_static = QPushButton("Загрузить данные")
        self.btn_process_static = QPushButton("Обработать")
        self.btn_calculate_static = QPushButton("Рассчитать индекс")
        
        btn_layout.addWidget(self.btn_load_static)
        btn_layout.addWidget(self.btn_process_static)
        btn_layout.addWidget(self.btn_calculate_static)
        
        # Таблица и график
        self.static_table = TableWidget()
        self.static_plot = PlotWidget("static")
        
        layout.addLayout(btn_layout)
        layout.addWidget(self.static_table)
        layout.addWidget(self.static_plot)
        
        widget.setLayout(layout)
        return widget
    
    def create_dynamic_widget(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Кнопки динамического анализа
        btn_layout = QHBoxLayout()
        self.btn_load_dynamic = QPushButton("Загрузить данные")
        self.btn_process_dynamic = QPushButton("Обработать")
        self.btn_calculate_dynamic = QPushButton("Рассчитать индекс")
        
        btn_layout.addWidget(self.btn_load_dynamic)
        btn_layout.addWidget(self.btn_process_dynamic)
        btn_layout.addWidget(self.btn_calculate_dynamic)
        
        # Таблица и график
        self.dynamic_table = TableWidget()
        self.dynamic_plot = PlotWidget("dynamic")
        
        layout.addLayout(btn_layout)
        layout.addWidget(self.dynamic_table)
        layout.addWidget(self.dynamic_plot)
        
        widget.setLayout(layout)
        return widget

    def load_data(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл данных", "", "Data Files (*.csv *.xlsx)")
        
        if file_path:
            try:
                self.parent.df = DataManager.load_data(file_path)
                self.parent.db = PostgreSQLManager()
                self.parent.db.save_raw_data(self.parent.df)
                
                self.show_preview(self.parent.df)
                self.btn_next.setEnabled(True)
                QMessageBox.information(self, "Успех", "Данные успешно загружены!")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки: {str(e)}")

    def show_preview(self, df, max_rows=10):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Таблица
        self.static_table = TableWidget()
        self.static_table.setMinimumWidth(800)

    def process_data(self, analysis_type):
        try:
            if analysis_type == "static" and self.current_static_data is not None:
                processed_df = DataProcessor.preprocess_data(self.current_static_data)
                self.current_static_data = processed_df
                self.static_table.display_data(processed_df)
            elif analysis_type == "dynamic" and self.current_dynamic_data is not None:
                processed_df = DataProcessor.preprocess_data(self.current_dynamic_data)
                self.current_dynamic_data = processed_df
                self.dynamic_table.display_data(processed_df)
            else:
                raise ValueError("Данные не загружены")
                
            QMessageBox.information(self, "Успех", "Данные обработаны!")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка обработки: {str(e)}")

    def calculate_index(self, analysis_type):
        try:
            if analysis_type == "static" and self.current_static_data is not None:
                result_df = QualityCalculator.calculate_quality_index(
                    self.current_static_data,
                    constraints=self.constraints,
                    analysis_type="static"
                )
                self.static_plot.update_plot(result_df)
            elif analysis_type == "dynamic" and self.current_dynamic_data is not None:
                result_df = QualityCalculator.calculate_quality_index(
                    self.current_dynamic_data,
                    constraints=self.constraints,
                    analysis_type="dynamic"
                )
                self.dynamic_plot.update_plot(result_df)
            else:
                raise ValueError("Данные не загружены")
                
            QMessageBox.information(self, "Успех", "Индекс качества рассчитан!")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка расчета: {str(e)}")
    
    def create_constraints_panel(self):
        scroll = QScrollArea()
        group = QGroupBox("Управление ограничениями параметров")
        layout = QGridLayout()

        # Создание меток с уникальными идентификаторами
        self.min_label = QLabel("Мин:")
        self.max_label = QLabel("Макс:")
        self.fixed_label = QLabel("Фикс:")

        # Выбор параметра
        self.param_selector = QComboBox()
        self.param_selector.currentIndexChanged.connect(self.update_param_fields)
        layout.addWidget(QLabel("Параметр:"), 0, 0)
        layout.addWidget(self.param_selector, 0, 1)

        # Тип ограничения
        self.constraint_type = QComboBox()
        self.constraint_type.addItems([
            "Допустимый диапазон",
            "Минимальное значение",
            "Максимальное значение",
            "Фиксированное значение"
        ])
        layout.addWidget(QLabel("Тип ограничения:"), 1, 0)
        layout.addWidget(self.constraint_type, 1, 1)

        # Поля ввода значений
        self.min_input = QLineEdit()
        self.max_input = QLineEdit()
        self.fixed_input = QLineEdit()
        
        value_layout = QHBoxLayout()
        value_layout.addWidget(self.min_label)
        value_layout.addWidget(self.min_input)
        value_layout.addWidget(self.max_label)
        value_layout.addWidget(self.max_input)
        value_layout.addWidget(self.fixed_label)
        value_layout.addWidget(self.fixed_input)
        layout.addLayout(value_layout, 2, 0, 1, 2)

        # Кнопки управления
        self.btn_add_constraint = QPushButton("Добавить ограничение")
        self.btn_add_constraint.clicked.connect(self.add_constraint)
        self.btn_clear_constraints = QPushButton("Очистить все")
        self.btn_clear_constraints.clicked.connect(self.clear_constraints)
        
        layout.addWidget(self.btn_add_constraint, 3, 0)
        layout.addWidget(self.btn_clear_constraints, 3, 1)

        # Таблица активных ограничений
        self.constraints_table = QTableWidget()
        self.constraints_table.setColumnCount(3)
        self.constraints_table.setHorizontalHeaderLabels(["Параметр", "Тип", "Значения"])
        self.constraints_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.constraints_table, 4, 0, 1, 2)

        group.setLayout(layout)
        scroll.setWidget(group)
        scroll.setWidgetResizable(True)

        # Инициализация видимости полей
        self.min_input.setVisible(False)
        self.max_input.setVisible(False)
        self.fixed_input.setVisible(False)

        # Инициализация видимости
        self.min_label.setVisible(False)
        self.max_label.setVisible(False)
        self.fixed_label.setVisible(False)
        
        # Привязка обработчика изменения типа ограничения
        self.constraint_type.currentIndexChanged.connect(self.update_input_visibility)
        
        # Первоначальное обновление
        self.update_input_visibility()

        

        return scroll
    
    def update_input_visibility(self):
        """Обновление видимости полей ввода в зависимости от типа ограничения"""
        constraint_type = self.constraint_type.currentText()
        
        # Скрываем все поля
        self.min_input.setVisible(False)
        self.max_input.setVisible(False)
        self.fixed_input.setVisible(False)
        
        # Очищаем неиспользуемые поля
        self.min_input.clear()
        self.max_input.clear()
        self.fixed_input.clear()

        # Показываем нужные поля
        if constraint_type == "Допустимый диапазон":
            self.min_input.setVisible(True)
            self.max_input.setVisible(True)
            self.min_input.setPlaceholderText("Минимальное значение")
            self.max_input.setPlaceholderText("Максимальное значение")
            
        elif constraint_type == "Минимальное значение":
            self.min_input.setVisible(True)
            self.min_input.setPlaceholderText("Минимальное значение")
            
        elif constraint_type == "Максимальное значение":
            self.max_input.setVisible(True)
            self.max_input.setPlaceholderText("Максимальное значение")
            
        elif constraint_type == "Фиксированное значение":
            self.fixed_input.setVisible(True)
            self.fixed_input.setPlaceholderText("Фиксированное значение")

        # Обновляем подписи
        self.adjust_labels_visibility(constraint_type)
    
    def adjust_labels_visibility(self, constraint_type):
        """Обновление видимости меток"""
        # Сначала скрываем все метки
        self.min_label.setVisible(False)
        self.max_label.setVisible(False)
        self.fixed_label.setVisible(False)

        # Показываем нужные метки
        if constraint_type == "Допустимый диапазон":
            self.min_label.setVisible(True)
            self.max_label.setVisible(True)
        elif constraint_type == "Минимальное значение":
            self.min_label.setVisible(True)
        elif constraint_type == "Максимальное значение":
            self.max_label.setVisible(True)
        elif constraint_type == "Фиксированное значение":
            self.fixed_label.setVisible(True)

    def update_param_fields(self):
        """Обновление доступных полей ввода в зависимости от типа ограничения"""
        constraint_type = self.constraint_type.currentText()
        
        self.min_input.setVisible(constraint_type in ["Допустимый диапазон", "Минимальное значение"])
        self.max_input.setVisible(constraint_type in ["Допустимый диапазон", "Максимальное значение"])
        self.fixed_input.setVisible(constraint_type == "Фиксированное значение")

    def add_constraint(self):
        """Добавление нового ограничения"""
        param = self.param_selector.currentText()
        c_type = self.constraint_type.currentText()
        
        try:
            if c_type == "Допустимый диапазон":
                min_val = float(self.min_input.text())
                max_val = float(self.max_input.text())
                self.constraints[param] = {'type': 'range', 'min': min_val, 'max': max_val}
                display_value = f"[{min_val} - {max_val}]"
                
            elif c_type == "Минимальное значение":
                min_val = float(self.min_input.text())
                self.constraints[param] = {'type': 'min', 'value': min_val}
                display_value = f"≥ {min_val}"
                
            elif c_type == "Максимальное значение":
                max_val = float(self.max_input.text())
                self.constraints[param] = {'type': 'max', 'value': max_val}
                display_value = f"≤ {max_val}"
                
            elif c_type == "Фиксированное значение":
                fixed_val = float(self.fixed_input.text())
                self.constraints[param] = {'type': 'fixed', 'value': fixed_val}
                display_value = f"= {fixed_val}"
                
            self._update_constraints_table(param, c_type, display_value)
            
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Некорректные значения ограничений")

    def _update_constraints_table(self, param, c_type, values):
        row = self.constraints_table.rowCount()
        self.constraints_table.insertRow(row)
        
        self.constraints_table.setItem(row, 0, QTableWidgetItem(param))
        self.constraints_table.setItem(row, 1, QTableWidgetItem(c_type))
        self.constraints_table.setItem(row, 2, QTableWidgetItem(values))
        
        # Автоматическое выравнивание столбцов
        self.constraints_table.resizeColumnsToContents()

    def clear_constraints(self):
        """Очистка всех ограничений"""
        self.constraints.clear()
        self.constraints_table.setRowCount(0)

class ResultsPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Заголовок
        header = QLabel("Результаты анализа")
        header.setFont(QFont('Georgia', 16))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            background-color: #666666;
            color: #ffffff;
            padding: 15px;
            border-radius: 10px;
        """)
        
        # Вкладки анализа
        self.tabs = QTabWidget()
        self.static_tab = self.create_static_tab()
        self.dynamic_tab = self.create_dynamic_tab()
        self.tabs.addTab(self.static_tab, "Статический анализ")
        self.tabs.addTab(self.dynamic_tab, "Динамический анализ")
        
        # Кнопка возврата
        self.btn_back = QPushButton("← Назад к вводу")
        self.btn_back.clicked.connect(self.parent.show_input)
        
        layout.addWidget(header)
        layout.addWidget(self.tabs)
        layout.addWidget(self.btn_back)
        
        self.setLayout(layout)
    
    def create_static_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Таблица
        self.static_table = TableWidget()
        self.static_table.setMinimumWidth(800)
        
        # График
        self.static_plot = PlotWidget(analysis_type="static")
        
        layout.addWidget(self.static_table)
        layout.addWidget(self.static_plot)
        widget.setLayout(layout)
        return widget
    
    def create_dynamic_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Таблица
        self.dynamic_table = TableWidget()
        self.dynamic_table.setMinimumWidth(800)
        
        # График
        self.dynamic_plot = PlotWidget(analysis_type="dynamic")
        
        layout.addWidget(self.dynamic_table)
        layout.addWidget(self.dynamic_plot)
        widget.setLayout(layout)
        return widget
    
    def update_results(self):
        try:
            # Обработка данных
            static_df = DataProcessor.preprocess_data(self.parent.df)
            dynamic_df = DataProcessor.preprocess_data(self.parent.df)
            
            # Расчет индексов
            static_results = QualityCalculator.calculate_quality_index(
                static_df, self.parent.constraints, "static")
            dynamic_results = QualityCalculator.calculate_quality_index(
                dynamic_df, self.parent.constraints, "dynamic")
            
            # Обновление интерфейса
            self.static_table.display_data(static_results)
            self.dynamic_table.display_data(dynamic_results)
            self.static_plot.update_plot(static_results)
            self.dynamic_plot.update_plot(dynamic_results)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка анализа: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Анализ качества продукции")
        self.setGeometry(600, 300, 1000, 800)
        self.setWindowIcon(QIcon('resources/icon.png'))
        
        # Инициализация данных
        self.df = None
        self.constraints = {}
        self.db = None
        
        # Инициализация интерфейса
        self.init_ui()
    
    def init_ui(self):
        # Создаем стек виджетов
        self.stacked_widget = QStackedWidget()
        
        # Страницы
        self.input_page = InputPage(self)
        self.results_page = ResultsPage(self)
        
        self.stacked_widget.addWidget(self.input_page)
        self.stacked_widget.addWidget(self.results_page)
        
        self.setCentralWidget(self.stacked_widget)
    
    def show_results(self):
        if self.df is not None:
            self.results_page.update_results()
            self.stacked_widget.setCurrentIndex(1)
    
    def show_input(self):
        self.stacked_widget.setCurrentIndex(0)