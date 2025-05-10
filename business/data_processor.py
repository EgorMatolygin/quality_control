import pandas as pd
import numpy as np

class DataProcessor:
    @staticmethod
    def preprocess_data(df):
        # Удаление дубликатов
        df = df.drop_duplicates()
        
        # Заполнение пропусков медианой
        for col in df.select_dtypes(include=np.number).columns:
            df[col].fillna(df[col].median(), inplace=True)
        
        # Фильтрация выбросов
        for col in df.select_dtypes(include=np.number).columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            df = df[(df[col] >= q1 - 1.5*iqr) & (df[col] <= q3 + 1.5*iqr)]
        
        return df
    
    @staticmethod
    def _preprocess_time_data(df, time_col, param):
        """Предварительная обработка временных данных"""
        # Конвертация в datetime
        df = df.copy()
        df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
        
        # Удаление строк с некорректными датами
        df = df.dropna(subset=[time_col])
        
        # Обработка дубликатов временных меток
        if df[time_col].duplicated().any():
            df = df.groupby(time_col).agg({param: 'mean'}).reset_index()
        
        # Установка индекса и сортировка
        df = df.set_index(time_col).sort_index()
        
        # Проверка регулярности временного ряда
        if not df.index.is_unique:
            df = df[~df.index.duplicated(keep='first')]
        
        # Автоматическое определение частоты
        try:
            df = df.asfreq(df.index.inferred_freq or 'D')
        except ValueError:
            df = df.resample('D').mean().ffill()
        
        return df