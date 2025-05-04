import sys
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
                            QLabel, QMessageBox)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class AnalysisTab(QWidget):
    def __init__(self, analysis_type):
        super().__init__()
        self.analysis_type = analysis_type
        self.df = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        # Кнопки загрузки и обработки
        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton("Загрузить данные")
        self.btn_load.clicked.connect(self.load_data)
        self.btn_process = QPushButton("Обработать данные")
        self.btn_process.clicked.connect(self.preprocess_data)
        self.btn_calculate = QPushButton("Рассчитать индекс")
        self.btn_calculate.clicked.connect(self.calculate_index)
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_process)
        btn_layout.addWidget(self.btn_calculate)
        
        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(0)
        self.table.setRowCount(0)
        
        # График
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def load_data(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", "CSV/Excel (*.csv *.xlsx)")
        if file_path:
            try:
                if file_path.endswith('.csv'):
                    self.df = pd.read_csv(file_path)
                else:
                    self.df = pd.read_excel(file_path)
                self.show_table()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл: {str(e)}")

    def show_table(self, max_rows=15):
        self.table.setColumnCount(len(self.df.columns))
        self.table.setRowCount(min(max_rows, len(self.df)))
        self.table.setHorizontalHeaderLabels(self.df.columns)
        
        for row in range(min(max_rows, len(self.df))):
            for col in range(len(self.df.columns)):
                item = QTableWidgetItem(str(self.df.iloc[row, col]))
                self.table.setItem(row, col, item)

    def preprocess_data(self):
        try:
            # Обработка дубликатов
            self.df = self.df.drop_duplicates()
            
            # Заполнение пропусков медианой
            for col in self.df.select_dtypes(include=np.number).columns:
                self.df[col].fillna(self.df[col].median(), inplace=True)
                
            # Фильтрация выбросов (межквартильный размах)
            for col in self.df.select_dtypes(include=np.number).columns:
                q1 = self.df[col].quantile(0.25)
                q3 = self.df[col].quantile(0.75)
                iqr = q3 - q1
                self.df = self.df[(self.df[col] >= q1 - 1.5*iqr) & (self.df[col] <= q3 + 1.5*iqr)]
            
            self.show_table()
            QMessageBox.information(self, "Успех", "Данные обработаны!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка обработки: {str(e)}")

    def calculate_index(self):
        try:
            # Пример расчета индекса качества (адаптируйте под ваши формулы)
            self.df['quality_index'] = (
                self.df['critical_param'] / self.df['critical_param'].max() * 100
            )
            self.plot_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка расчета: {str(e)}")

    def plot_data(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if self.analysis_type == "static":
            ax.boxplot([self.df['param1'], self.df['param2']])
            ax.set_title("Статический анализ")
        else:
            ax.plot(self.df['date'], self.df['quality_index'])
            ax.set_title("Динамический анализ")
            
        self.canvas.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Анализ качества продукции")
        self.setGeometry(600, 300, 1000, 800)
        self.setWindowIcon(QIcon('icon.png'))
        
        # Создаем вкладки
        tabs = QTabWidget()
        self.static_tab = AnalysisTab("static")
        self.dynamic_tab = AnalysisTab("dynamic")
        
        tabs.addTab(self.static_tab, "Статический анализ")
        tabs.addTab(self.dynamic_tab, "Динамический анализ")
        
        self.setCentralWidget(tabs)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()