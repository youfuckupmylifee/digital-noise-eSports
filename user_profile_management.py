import sqlite3
import os
import time


# Путь к файлу базы данных
DB_PATH = 'instance/user_profiles.db'


# Добавление нового пользователя в базу данных
def add_user(user_id, username=None, role='user'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO user (user_id, username, role, balance) VALUES (?, ?, ?, 0)
    ''', (user_id, username, role))
    conn.commit()
    conn.close()

# Получение профиля пользователя по user_id
def get_user_profile(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE user_id = ?", (user_id,))
    profile = cursor.fetchone()
    conn.close()
    return profile

# Получение профиля пользователя по username
def get_user_profile_by_username(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM user WHERE username = ?
    ''', (username,))
    profile = cursor.fetchone()
    conn.close()
    return profile

# Обновление баланса пользователя
def update_balance(user_id, new_balance, update_request_time=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if update_request_time:
        # Обновляем баланс и время последнего запроса
        cursor.execute("UPDATE user SET balance = ?, last_request_time = ? WHERE user_id = ?", (new_balance, int(time.time()), user_id))
    else:
        # Обновляем только баланс
        cursor.execute("UPDATE user SET balance = ? WHERE user_id = ?", (new_balance, user_id))
    conn.commit()
    conn.close()

# Обновление результата матча
def update_match_result(match_id, result):
    conn = sqlite3.connect('instance/tournaments.db')
    cursor = conn.cursor()

    # Обновляем только статус матча
    cursor.execute("UPDATE match SET status = ? WHERE id = ?", (result, match_id))

    conn.commit()
    conn.close()

# Обновление статуса пользователя
def update_user_status(user_id, new_status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE user SET status = ? WHERE user_id = ?", (new_status, user_id))
    conn.commit()
    conn.close()

# Получение истории ставок
def get_bet_history(user_id):
    conn = sqlite3.connect('instance/tournaments.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT b.amount, b.bet_type, b.coefficient, b.status, m.status, b.match_id
        FROM bet b
        INNER JOIN match m ON b.match_id = m.id
        WHERE b.user_id = ?
        ORDER BY b.id DESC
    ''', (user_id,))

    bets = cursor.fetchall()
    conn.close()
    return bets

