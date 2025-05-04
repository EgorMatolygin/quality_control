from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from business.data_processor import DataProcessor

class TableWidget(QTableWidget):
    def __init__(self):
        super().__init__()
        self.df = None
        
    def load_data(self, file_path):
        self.df = DataManager.load_data(file_path)
        self.df = DataProcessor.preprocess_data(self.df)
        self.display_data()
        
    def display_data(self, max_rows=15):
        self.setColumnCount(len(self.df.columns))
        self.setRowCount(min(max_rows, len(self.df)))
        self.setHorizontalHeaderLabels(self.df.columns)
        
        for row in range(min(max_rows, len(self.df))):
            for col in range(len(self.df.columns)):
                self.setItem(row, col, QTableWidgetItem(str(self.df.iloc[row, col])))