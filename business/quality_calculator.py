import numpy as np
import pandas as pd

class QualityCalculator:
    
    @staticmethod
    def calculate_quality_index(df, constraints, analysis_type="static"):
        aggregated_params = {}
        
        # Агрегация параметров
        for param, config in constraints.items():
            values = df[param]
            constraint_type = config['type']
            
            # Выбор функции агрегации
            if constraint_type == 'range':
                a, b = config['min'], config['max']
                mid = (a + b) / 2
                aggregated = values.apply(lambda p: abs(p - mid)).idxmax()
                
            elif constraint_type == 'min':
                a = config['min']
                aggregated = values.min()
                
            elif constraint_type == 'max':
                b = config['max']
                aggregated = values.max()
                
            elif constraint_type == 'fixed':
                aggregated = values.all()  # Для булевых значений
                
            aggregated_params[param] = aggregated

        # Нормализация агрегированных значений
        normalized_scores = []
        gamma = 1  # Параметр может настраиваться
        
        for param, value in aggregated_params.items():
            config = constraints[param]
            constraint_type = config['type']
            
            if constraint_type == 'range':
                a, b = config['min'], config['max']
                c = (a + b)/2
                if a < value < b:
                    score = ((c - abs(value - c))**gamma) / c
                else:
                    score = 0
                    
            elif constraint_type == 'min':
                a = config['min']
                if value >= a:
                    score = 1 - (1/(value - a + 1))**gamma
                else:
                    score = 0
                    
            elif constraint_type == 'max':
                b = config['max']
                if value <= b:
                    score = 1 - (1/(1 + b - value))**gamma
                else:
                    score = 0
                    
            elif constraint_type == 'fixed':
                score = float(value)  # Булевы в [0,1]
                
            normalized_scores.append(score)

        # Интегральный индекс качества
        if analysis_type == "static":
            quality_index = normalized_scores
        else:
            # Для динамики - взвешенное среднее по времени
            time_weights = df['timestamp'].rank()
            quality_index = np.average(normalized_scores, weights=time_weights)
            
        return pd.Series([quality_index], index=['quality_index'])