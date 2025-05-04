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