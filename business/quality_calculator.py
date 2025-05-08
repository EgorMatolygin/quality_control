class QualityCalculator:
    
    @staticmethod
    def quality_index(df, constraints):
        for param, config in constraints.items():
            if config['type'] == 'range':
                pass
                ## обработка диапазона
            if config['type'] == 'min':
                ## обработка левой границы
                pass
            if config['type'] == 'max':
                ## обработка правой границы
                pass
            if config['type'] == 'fixed':
                ## обработка конкретного значения
                pass
    
    @staticmethod
    def calculate_quality_index(df, constraints, analysis_type):    
        
        if analysis_type == "static":
            vector = quality_index(df,constraints)
            
        else:
            # Формулы для динамики
            # цикл по датам
                vector = quality_index(df,constraints)
        return df