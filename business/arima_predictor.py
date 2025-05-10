#arima_predictory.py

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
            # Подготовка данных
            df = df.set_index(pd.to_datetime(df[time_col])).sort_index()
            series = df[target_col].dropna()
            
            if len(series) < 30:
                raise ValueError("Недостаточно данных для прогноза (минимум 30 точек)")

            # Автоподбор параметров ARIMA
            model = auto_arima(
                series,
                seasonal=False,
                trace=True,  # Включаем логгирование для диагностики
                error_action='ignore',
                suppress_warnings=True
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
                start=last_date + pd.Timedelta(1, freq[0]), 
                periods=forecast_steps, 
                freq=freq
            )
            print("ARIMA raw forecast:", forecast)
            print("ARIMA forecast:", pd.Series(forecast, index=future_dates))
            
            return {
                'history': series,
                'forecast': pd.Series(forecast, index=future_dates),
                'conf_int': pd.DataFrame(conf_int, index=future_dates)
            }
            
        except Exception as e:
            QMessageBox.warning(self.parent, "Ошибка ARIMA", str(e))
            return None