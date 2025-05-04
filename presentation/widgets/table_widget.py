# presentation/widgets/table_widget.py
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from data.data_manager import DataManager
from business.data_processor import DataProcessor

class TableWidget(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setEditTriggers(QTableWidget.NoEditTriggers)  # Блокировка редактирования
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # Авто-ширина
        self.horizontalHeader().setStretchLastSection(True)  # Растягивание последнего столбца
        self.verticalHeader().setVisible(False)  # Скрыть вертикальные заголовки
        self.setAlternatingRowColors(True)  # Чередование цветов строк
        self.setStyleSheet("""
            QTableWidget {
                font: 10pt "Segoe UI";
                gridline-color: #E0E0E0;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                color: #000000;
                padding: 4px;
            }
        """)

    def display_data(self, df, max_rows=15):
        self.clear()
        self.setColumnCount(len(df.columns))
        self.setRowCount(min(max_rows, len(df)))
        self.setHorizontalHeaderLabels(df.columns)
        
        # Заполнение данными
        for row in range(min(max_rows, len(df))):
            for col in range(len(df.columns)):
                item = QTableWidgetItem(str(df.iloc[row, col]))
                
                # Дополнительные настройки для запрета редактирования
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignCenter)
                
                self.setItem(row, col, item)
        
        # Оптимизация ширины столбцов
        self.resizeColumnsToContents()
        self.horizontalHeader().setMinimumSectionSize(100)  # Минимальная ширина
        
        # Установка разумных пределов
        for col in range(self.columnCount()):
            current_width = self.columnWidth(col)
            self.setColumnWidth(col, min(current_width, 300))