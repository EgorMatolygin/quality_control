import sys
from PyQt5.QtWidgets import QApplication,QMainWindow, QLabel
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App")
        self.setGeometry(600,300,500,500)
        self.setWindowIcon(QIcon('resources/icon.png'))

        label = QLabel("hello", self)
        label.setFont(QFont('Georgia',40))
        label.setGeometry(0,0,500,100)
        label.setStyleSheet("color: #FEC4A7;"
                            "background-color: #581845;"
                            "border-bottom-left-radius: 30px;"
                            "border-bottom-right-radius: 30px;")
        label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter )
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
