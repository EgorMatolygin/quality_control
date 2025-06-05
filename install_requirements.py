import subprocess
import sys

required_packages = [
    "pandas",
    "numpy",
    "scikit-learn",
    "statsmodels",
    "pmdarima",
    "PyQt5",
    "PyQtWebEngine",
    "psycopg2-binary",
    "python-dotenv",
    "plotly",
    "openpyxl",
    "seaborn"
]

def install_packages():
    for package in required_packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"Успешно установлено: {package}")
        except subprocess.CalledProcessError:
            print(f"Ошибка при установке {package}")
            print("Попробуйте установить вручную: pip install", package)

if __name__ == "__main__":
    print("Начинается установка необходимых библиотек...")
    install_packages()
    print("\nВсе зависимости установлены!")
    print("Для работы с PostgreSQL убедитесь, что у вас установлен и запущен сервер PostgreSQL")