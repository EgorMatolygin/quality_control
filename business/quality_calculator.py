class QualityCalculator:
    @staticmethod
    def calculate_quality_index(df, analysis_type):
        if analysis_type == "static":
            # Формулы из раздела 2.2 для статики
            df['quality_index'] = ...
        else:
            # Формулы для динамики
            df['quality_index'] = ...
        return df