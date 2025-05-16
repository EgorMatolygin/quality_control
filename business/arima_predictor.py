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
            if df.empty:
                raise ValueError("Нет данных для прогнозирования")
                
            df = df.set_index(pd.to_datetime(df[time_col])).sort_index()
            series = df[target_col].dropna()
            
            if len(series) < 10:
                raise ValueError(f"Недостаточно данных ({len(series)} точек)")
                
            model = auto_arima(
                series,
                seasonal=False,
                trace=False,
                stepwise=True
            )
            
            forecast, conf_int = model.predict(
                n_periods=forecast_steps,
                return_conf_int=True
            )

            last_date = series.index[-1]
            freq = pd.infer_freq(series.index) or 'D'
            
            # Генерируем даты, включая последнюю дату истории
            future_dates = pd.date_range(
                start=last_date,
                periods=forecast_steps + 1,  # +1 чтобы включить последнюю дату
                freq=freq
            )
            
            # Добавляем последнее значение истории в прогноз и доверительный интервал
            last_value = series.iloc[-1]
            forecast = pd.Series(
                [last_value] + list(forecast),
                index=future_dates
            )
            
            conf_int = pd.DataFrame(
                np.vstack(([[last_value, last_value]], conf_int)),
                index=future_dates,
                columns=['lower', 'upper']
            )

            return {
                'history': series,
                'forecast': forecast,
                'conf_int': conf_int
            }
            
        except Exception as e:
            QMessageBox.warning(self.parent, "ARIMA Error", str(e))
            return None