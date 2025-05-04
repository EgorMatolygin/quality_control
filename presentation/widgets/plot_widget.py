# presentation/widgets/plot_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import pandas as pd

class PlotWidget(QWidget):
    def __init__(self, analysis_type):
        super().__init__()
        self.analysis_type = analysis_type
        self.init_ui()
        
    def init_ui(self):
        # Создание контейнера для графика
        self.layout = QVBoxLayout(self)
        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

    def update_plot(self, data):
        """Обновить график в зависимости от типа анализа"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        if self.analysis_type == "static":
            self._plot_static(ax, data)
        else:
            self._plot_dynamic(ax, data)
            
        self.canvas.draw()

    def _plot_static(self, ax, data):
        """Построение box-plot для статического анализа"""
        columns = data.select_dtypes(include='number').columns
        ax.boxplot([data[col].dropna() for col in columns], labels=columns)
        ax.set_title("Распределение параметров качества")
        ax.set_ylabel("Значения параметров")
        ax.grid(True)
        
        # Добавление аннотаций
        stats = data.describe().transpose()
        for i, col in enumerate(columns):
            ax.text(
                i+1, stats.loc[col, 'max']*1.05,
                f"Медиана: {stats.loc[col, '50%']:.2f}\nВыбросы:",
                ha='center'
            )

    def _plot_dynamic(self, ax, data):
        """Построение временного ряда для динамического анализа"""
        if 'timestamp' not in data.columns:
            raise ValueError("Для динамического анализа требуется столбец 'timestamp'")
            
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data.sort_values('timestamp', inplace=True)
        
        ax.plot(data['timestamp'], data['quality_index'], marker='o')
        ax.set_title("Динамика индекса качества")
        ax.set_xlabel("Дата")
        ax.set_ylabel("Индекс качества")
        ax.grid(True)
        
        # Добавление метрик
        mae = (data['quality_index'] - data['quality_index'].mean()).abs().mean()
        ax.annotate(
            f"MAE: {mae:.2f}\nСреднее: {data['quality_index'].mean():.2f}",
            xy=(0.05, 0.95),
            xycoords='axes fraction',
            bbox=dict(boxstyle="round", alpha=0.8, facecolor='white')
        )

    def clear_plot(self):
        """Очистить график"""
        self.figure.clear()
        self.canvas.draw()