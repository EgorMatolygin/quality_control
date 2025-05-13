from business.quality_calculator import QualityCalculator
import pandas as pd

constraints = {
    'temperature': {'type': 'range', 'min': 20, 'max': 30},
    'pressure': {'type': 'max', 'max': 100},
    'defect': {'type': 'fixed'}
}

df = pd.DataFrame({
    'temperature': [25, 28, 32],
    'pressure': [90, 95, 98],
    'defect': [True, True, False]
})

calculator = QualityCalculator()
result = calculator.calculate_quality_index(df, constraints)
print(result)