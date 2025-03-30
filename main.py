import sys
from PyQt5.QtWidgets import QApplication,QMainWindow, QLabel, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt
import pandas as pd

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App")
        self.setGeometry(600,300,500,500)
        self.setWindowIcon(QIcon('resources/icon.png'))

        label = QLabel("hello", self)
        label.setFont(QFont('Georgia',40))
        label.setGeometry(0, 0, 500, 100)
        label.setStyleSheet("color: #FEC4A7;"
                            "background-color: #581845;"
                            "border-bottom-left-radius: 30px;"
                            "border-bottom-right-radius: 30px;")
        label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter )

        self.drawTable('/Users/egormatolygin/Desktop/прошлое/7/ММПА/пр1/data/wether.csv',15)

    def drawTable(self,path,rowsNumberMax):
        
        df = pd.read_csv(path).reset_index()
        
        table = QTableWidget(self)
        table.setGeometry(0, 100, 1000, 500)
        table.setColumnCount(len(df.columns))
        rowNumber = min(rowsNumberMax,len(df))
        table.setRowCount(rowNumber)

        for i in range(len(df.columns)):
            table.setColumnWidth(i,100)

        for rowIndex, dataRow in df.iterrows():
            if rowIndex >= rowsNumberMax:
                break
            for colIndex, dataItem in enumerate(dataRow):
                print(rowIndex, colIndex, dataItem)
                table.setItem(rowIndex, colIndex, QTableWidgetItem(str(dataItem)))

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
