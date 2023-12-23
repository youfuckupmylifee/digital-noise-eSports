import sqlite3

# Путь к файлу базы данных
DB_PATH = 'instance/user_profiles.db'

def create_database():
    print("Creating database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Создание таблицы "user", если она еще не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            username TEXT,
            balance INTEGER DEFAULT 0,
            role TEXT DEFAULT 'user',
            last_request_time INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Домашний'
        )
    ''')

    # Сохранение изменений и закрытие соединения
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_database()