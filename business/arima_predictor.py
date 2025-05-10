# arima_predictory.py

import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from pmdarima import auto_arima
from PyQt5.QtWidgets import QMessageBox

class ARIMAPredictor:
    def __init__(self, parent):
        self.parent = parent

    def predict(self, df, target_col, time_col='timestamp', forecast_steps=5):
        try:
            # Проверка входных данных
            if df.empty:
                raise ValueError("Переданы пустые данные для прогнозирования")
                
            # Проверка наличия временной колонки
            if time_col not in df.columns:
                raise ValueError(f"Колонка времени '{time_col}' не найдена в данных")

            # Подготовка данных с проверкой уникальности временных меток
            df = df.set_index(pd.to_datetime(df[time_col])).sort_index()
            
            # Проверка на наличие нескольких партий в данных
            batch_candidates = ['batch_id', 'batch', 'lot', 'partia', 'партия', 'lot_id']
            batch_col = next((col for col in df.columns if col.lower() in batch_candidates), None)
            if batch_col and df[batch_col].nunique() > 1:
                raise ValueError("Обнаружено несколько партий в данных для прогноза!")

            # Извлечение временного ряда
            series = df[target_col].dropna()
            
            if len(series) < 30:
                raise ValueError(f"Недостаточно данных для прогноза (требуется 30 точек, получено {len(series)})")

            # Автоподбор параметров ARIMA
            model = auto_arima(
                series,
                seasonal=False,
                trace=True,
                error_action='ignore',
                suppress_warnings=True,
                stepwise=True
            )
            
            # Прогнозирование
            forecast, conf_int = model.predict(
                n_periods=forecast_steps,
                return_conf_int=True
            )

            # Генерация дат прогноза
            last_date = series.index[-1]
            freq = pd.infer_freq(series.index) or 'D'
            
            future_dates = pd.date_range(
                start=last_date,
                periods=forecast_steps + 1,
                freq=freq
            )[1:]

            # Создание результата
            return {
                'history': series,
                'forecast': pd.Series(forecast.to_list(), index=future_dates),
                'conf_int': pd.DataFrame(conf_int, index=future_dates, columns=['lower', 'upper'])
            }
            
        except Exception as e:
            QMessageBox.warning(self.parent, "Ошибка ARIMA", str(e))
            return None