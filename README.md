Что нужно сделать чтобы запустить приложение:

1. Запустить install_requirements.py при помощи команды:
    `python install_requirements.py`

2. Установка PostgreSQL сервера

    Для Windows:
    * Скачайте инсталлятор с официального сайта: https://www.postgresql.org/download/windows/
    * Запустите инсталлятор:
    * Выберите компоненты (оставьте все по умолчанию)
    * Укажите директорию установки
    * Установите пароль для суперпользователя postgres
    * Укажите порт (по умолчанию 5432)
    * Выберите локаль (рекомендуется "Russian, Russia")
    * Завершите установку

3. Настройка PostgreSQL
    
    * Подключитесь к серверу при помощи команды в терминале:
        `sudo -u postgres psql`

    * Создайте базу данных и пользователя:
        ``` 
        CREATE DATABASE quality_db;
            CREATE USER quality_user WITH PASSWORD 'your_secure_password';
            GRANT ALL PRIVILEGES ON DATABASE quality_db TO quality_user;
        ```

4. Настройка окружения для Python приложения
    Вставьте в .env в корне проекта свои данные
    
    ```
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=quality_db
    DB_USER=quality_user
    DB_PASSWORD=your_secure_password
    ```
