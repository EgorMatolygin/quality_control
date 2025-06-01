import pandas as pd

class QualityCalculator:
    
    @staticmethod
    def calculate_quality_index(df, constraints, analysis_type="static"):
        normalized_scores = {}
        
        # Проход по всем параметрам с ограничениями
        for param, config in constraints.items():
            values = df[param]
            constraint_type = config['type']
            gamma = config.get('gamma', 1)  # Параметр из конфига

            print(123)

            # Агрегация значений
            if constraint_type == 'range':
                a, b = config['min'], config['max']
                mid = (a + b)/2
                aggregated = values.loc[values.apply(lambda p: abs(p - mid)).idxmax()]
                
            elif constraint_type == 'min':
                print('прием как слышно:',config )
                a = config['value']
                aggregated = values.min()
                print(aggregated)
                
            elif constraint_type == 'max':
                b = config['value']
                aggregated = values.max()
                
            elif constraint_type == 'fixed':
                aggregated = values.all()  # Логическое И для булевых

            print('# Нормализация')   
            # Нормализация
            if constraint_type == 'range':
                a, b = config['min'], config['max']
                c = (a + b)/2
                if a < aggregated < b:
                    score = ((c - abs(aggregated - c))**gamma) / c
                else:
                    score = 0.0
                    
            elif constraint_type == 'min':
                a = config['value']
                score = 1 - (1/(aggregated - a + 1))**gamma if aggregated >= a else 0.0
                
            elif constraint_type == 'max':
                b = config['value']
                score = 1 - (1/(1 + b - aggregated))**gamma if aggregated <= b else 0.0
                
            elif constraint_type == 'fixed':
                score = float(aggregated)  # Булевы -> 0.0/1.0
                
            normalized_scores[param] = score

        # Возвращаем вектор нормализованных значений
        return pd.Series(normalized_scores)
    
    @staticmethod
    def calculate_actual_best_worst(df, constraints):
        best_worst = {}
        
        for param, config in constraints.items():
            values = df[param]
            constraint_type = config['type']
            
            if constraint_type == 'range':
                a, b = config['min'], config['max']
                mid = (a + b) / 2
                # Худшее значение: максимальное отклонение от центра
                worst_idx = values.apply(lambda p: abs(p - mid)).idxmax()
                best = mid
                worst = values.loc[worst_idx]
                
            elif constraint_type == 'min':
                print("Прием как слышно")
                best = values.max()
                worst = values.min()
                
            elif constraint_type == 'max':
                best = values.min()
                worst = values.max()
                
            elif constraint_type == 'fixed':
                best = True
                worst = False
                
            best_worst[param] = {'best': best, 'worst': worst}
            
        return best_worst