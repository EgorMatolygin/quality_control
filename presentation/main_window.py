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
from presentation.input_page import InputPage
from presentation.dynamic_result_page import DynamicResultsPage
from presentation.metrics_table_page import MetricsTablePage
from presentation.static_result_page import StaticResultsPage

from presentation.widgets.constraints_panel import ConstraintsPanel

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px  
from PyQt5.QtWebEngineWidgets import QWebEngineView
import pandas as pd
import numpy as np

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