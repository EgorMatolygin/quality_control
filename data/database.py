# data/database.py
import psycopg2
from psycopg2 import sql, errors
import pandas as pd
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

class PostgreSQLManager:
    def __init__(self):
        self.conn = None
        self._connect()
        self._create_table()

    def _connect(self):
        """Установить соединение с PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD")
            )
            print("Успешное подключение к PostgreSQL")
        except Exception as e:
            print(f"Ошибка подключения к PostgreSQL: {e}")
            raise

    def _create_table(self):
        """Создать таблицу для сырых данных, если не существует"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS raw_data (
            id SERIAL PRIMARY KEY,
            upload_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            data JSONB NOT NULL
        );
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(create_table_query)
                self.conn.commit()
        except Exception as e:
            print(f"Ошибка создания таблицы: {e}")
            self.conn.rollback()

    def save_raw_data(self, df):
        """Автоматическое сохранение данных при загрузке через интерфейс"""
        try:
            # Конвертация DataFrame в JSON
            data_json = df.to_json(orient='records')
            
            insert_query = sql.SQL("""
                INSERT INTO raw_data (data)
                VALUES (%s)
            """)
            
            with self.conn.cursor() as cursor:
                cursor.execute(insert_query, (data_json,))
                self.conn.commit()
                print("Данные успешно сохранены в PostgreSQL")
                
        except Exception as e:
            print(f"Ошибка сохранения данных: {e}")
            self.conn.rollback()

    def __del__(self):
        """Закрыть соединение при уничтожении объекта"""
        if self.conn:
            self.conn.close()
            print("Соединение с PostgreSQL закрыто")