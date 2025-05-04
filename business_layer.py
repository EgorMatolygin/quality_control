# business_layer.py (бизнес-логика)
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

class QualityAnalyzer:
    def preprocess_data(self, df):
        # Обработка дубликатов
        df = df.drop_duplicates()
        
        # Заполнение пропусков
        for col in df.select_dtypes(include=np.number).columns:
            df[col].fillna(df[col].median(), inplace=True)
        
        # Фильтрация выбросов
        for col in df.select_dtypes(include=np.number).columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            df = df[(df[col] >= q1 - 1.5*iqr) & (df[col] <= q3 + 1.5*iqr)]
        
        return df

    def calculate_quality_index(self, df):
        # Реализация формул из раздела 2.2 практики
        result = {
            'data': df,
            'metrics': pd.DataFrame({
                'Parameter': df.columns,
                'Quality Score': df.mean().values
            })
        }
        return result

    def generate_plots(self, result, session_id):
        plt.figure(figsize=(10, 6))
        
        if 'date' in result['data'].columns:
            # Динамический анализ
            plt.plot(result['data']['date'], result['data']['quality_index'])
            plt.title('Динамика индекса качества')
        else:
            # Статический анализ
            plt.boxplot([result['data'][col] for col in result['data'].columns])
            plt.title('Распределение параметров')
        
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        return base64.b64encode(img.getvalue()).decode()