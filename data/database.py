# data/database.py
import psycopg2
from psycopg2 import sql, errors
import pandas as pd
import os
from dotenv import load_dotenv
from typing import Optional

# Загрузка переменных окружения из .env файла
load_dotenv()

class PostgreSQLManager:
    def __init__(self):
        self.conn: Optional[psycopg2.extensions.connection] = None
        self._connect()
        self._create_tables()

    def _connect(self) -> None:
        """Установить соединение с PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD")
            )
        except psycopg2.OperationalError as e:
            raise ConnectionError(f"Ошибка подключения к PostgreSQL: {str(e)}") from e

    def _create_tables(self) -> None:
        """Создать таблицы для сырых данных и результатов"""
        try:
            with self.conn.cursor() as cursor:
                # Таблица для сырых данных
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS raw_data (
                        id SERIAL PRIMARY KEY,
                        upload_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        analysis_type VARCHAR(7) NOT NULL CHECK (analysis_type IN ('static', 'dynamic')),
                        data JSONB NOT NULL
                    );
                """)
                
                # Таблица для результатов анализа
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_results (
                        id SERIAL PRIMARY KEY,
                        calculation_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        analysis_type VARCHAR(7) NOT NULL CHECK (analysis_type IN ('static', 'dynamic')),
                        parameters JSONB NOT NULL,
                        results JSONB NOT NULL
                    );
                """)
                
                # Индексы для оптимизации
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_raw_data_type 
                    ON raw_data (analysis_type);
                """)
                
                self.conn.commit()
                
        except psycopg2.Error as e:
            self.conn.rollback()
            raise RuntimeError(f"Ошибка создания таблиц: {str(e)}") from e

    def save_raw_data(self, df: pd.DataFrame, analysis_type: str) -> None:
        """Сохранение сырых данных с указанием типа анализа"""
        if analysis_type not in ('static', 'dynamic'):
            raise ValueError("Недопустимый тип анализа. Допустимые значения: 'static', 'dynamic'")

        try:
            data_json = df.to_json(orient='records', date_format='iso')
            
            with self.conn.cursor() as cursor:
                cursor.execute(
                    sql.SQL("""
                        INSERT INTO raw_data (analysis_type, data)
                        VALUES (%s, %s)
                    """),
                    (analysis_type, data_json)
                )
                self.conn.commit()
                
        except psycopg2.Error as e:
            self.conn.rollback()
            raise RuntimeError(f"Ошибка сохранения данных: {str(e)}") from e

    def save_results(self, params: dict, results: dict, analysis_type: str) -> None:
        """Сохранение результатов расчета"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    sql.SQL("""
                        INSERT INTO analysis_results 
                            (analysis_type, parameters, results)
                        VALUES (%s, %s, %s)
                    """),
                    (analysis_type, 
                     psycopg2.extras.Json(params), 
                     psycopg2.extras.Json(results))
                )
                self.conn.commit()
                
        except psycopg2.Error as e:
            self.conn.rollback()
            raise RuntimeError(f"Ошибка сохранения результатов: {str(e)}") from e

    def close(self) -> None:
        """Безопасное закрытие соединения"""
        if self.conn and not self.conn.closed:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        self.close()