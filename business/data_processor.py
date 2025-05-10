import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

class DataProcessor:
    @staticmethod
    def preprocess_data(df, analysis_type='static'):
        try:
            df = df.drop_duplicates()

            if analysis_type == 'dynamic':
                time_col = next((col for col in ['timestamp', 'date', 'time'] 
                               if col in df.columns), None)
                
                if time_col:
                    df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
                    df = df.dropna(subset=[time_col]).sort_values(time_col)
                    date_mask = df[time_col].between('2000-01-01', '2030-12-31')
                    df = df[date_mask]
                    
                    numeric_cols = df.select_dtypes(include=np.number).columns
                    if not numeric_cols.empty:
                        df = df.set_index(time_col)[numeric_cols].resample('D').mean()
                        df = df.interpolate(method='time')

            numeric_cols = df.select_dtypes(include=np.number).columns
            for col in numeric_cols:
                df[col].fillna(df[col].median(), inplace=True)
                q1 = df[col].quantile(0.05)
                q3 = df[col].quantile(0.95)
                iqr = q3 - q1
                df = df[(df[col] >= q1 - 1.5*iqr) & (df[col] <= q3 + 1.5*iqr)]

            scaler = StandardScaler()
            df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
            return df

        except Exception as e:
            raise ValueError(f"Ошибка предобработки: {str(e)}")