# presentation/main_window.py
from PyQt5.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QFileDialog, QMessageBox, QLabel)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt
from presentation.widgets.table_widget import TableWidget
from presentation.widgets.plot_widget import PlotWidget
from business.data_processor import DataProcessor
from business.quality_calculator import QualityCalculator
from data.data_manager import DataManager
from data.database import PostgreSQLManager

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
        
        # Центральный виджет
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def create_static_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Кнопки
        btn_layout = QHBoxLayout()
        self.btn_load_static = QPushButton("Загрузить CSV/Excel")
        self.btn_load_static.clicked.connect(lambda: self.load_data("static"))
        self.btn_process_static = QPushButton("Обработать данные")
        self.btn_process_static.clicked.connect(lambda: self.process_data("static"))
        self.btn_calculate_static = QPushButton("Рассчитать индекс")
        self.btn_calculate_static.clicked.connect(lambda: self.calculate_index("static"))
        
        btn_layout.addWidget(self.btn_load_static)
        btn_layout.addWidget(self.btn_process_static)
        btn_layout.addWidget(self.btn_calculate_static)
        
        # Таблица и график
        self.static_table = TableWidget()
        self.static_table.setMinimumWidth(800)
        self.static_plot = PlotWidget(analysis_type="static")
        
        layout.addLayout(btn_layout)
        layout.addWidget(self.static_table)
        layout.addWidget(self.static_plot)
        
        widget.setLayout(layout)
        return widget

    def create_dynamic_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Кнопки
        btn_layout = QHBoxLayout()
        self.btn_load_dynamic = QPushButton("Загрузить CSV/Excel")
        self.btn_load_dynamic.clicked.connect(lambda: self.load_data("dynamic"))
        self.btn_process_dynamic = QPushButton("Обработать данные")
        self.btn_process_dynamic.clicked.connect(lambda: self.process_data("dynamic"))
        self.btn_calculate_dynamic = QPushButton("Рассчитать индекс")
        self.btn_calculate_dynamic.clicked.connect(lambda: self.calculate_index("dynamic"))
        
        btn_layout.addWidget(self.btn_load_dynamic)
        btn_layout.addWidget(self.btn_process_dynamic)
        btn_layout.addWidget(self.btn_calculate_dynamic)
        
        # Таблица и график
        self.dynamic_table = TableWidget()
        self.dynamic_table.setMinimumWidth(800)
        self.dynamic_plot = PlotWidget(analysis_type="dynamic")
        
        layout.addLayout(btn_layout)
        layout.addWidget(self.dynamic_table)
        layout.addWidget(self.dynamic_plot)
        
        widget.setLayout(layout)
        return widget

    def load_data(self, analysis_type):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл данных",
            "",
            "Data Files (*.csv *.xlsx)"
        )
        
        if file_path:
            try:
                df = DataManager.load_data(file_path)

                # Автоматическое сохранение в PostgreSQL
                db = PostgreSQLManager()
                db.save_raw_data(df)

                if analysis_type == "static":
                    self.current_static_data = df
                    self.static_table.display_data(df, 50)
                else:
                    self.current_dynamic_data = df
                    self.dynamic_table.display_data(df, 50)
                    
                QMessageBox.information(self, "Успех", "Данные успешно загружены!")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки: {str(e)}")

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
                    analysis_type="static"
                )
                self.static_plot.update_plot(result_df)
            elif analysis_type == "dynamic" and self.current_dynamic_data is not None:
                result_df = QualityCalculator.calculate_quality_index(
                    self.current_dynamic_data, 
                    analysis_type="dynamic"
                )
                self.dynamic_plot.update_plot(result_df)
            else:
                raise ValueError("Данные не загружены")
                
            QMessageBox.information(self, "Успех", "Индекс качества рассчитан!")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка расчета: {str(e)}")