import sqlite3

# Путь к файлу базы данных
DB_PATH = 'instance/tournaments.db'

# Создание базы данных
def create_tournaments_db():
    print("Creating tournaments database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Создание таблицы "tournament"
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tournament (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            teams TEXT
        )
    ''')

    # Создание таблицы "team"
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS team (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER,
            name TEXT,
            FOREIGN KEY(tournament_id) REFERENCES tournament(id)
        )
    ''')

    # Создание таблицы "player"
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS player (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER,
            name TEXT,
            FOREIGN KEY(team_id) REFERENCES team(id)
        )
    ''')

    # Модифицирование таблицы "match" для добавления коэффициентов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS match (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tournament_id INTEGER,
            team1 TEXT,
            team2 TEXT,
            match_time TEXT,
            status TEXT,
            coefficient_win REAL,
            coefficient_draw REAL,
            coefficient_lose REAL,
            FOREIGN KEY(tournament_id) REFERENCES tournament(id)
        )
    ''')

    # Создание таблицы "bet"
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            match_id INTEGER,
            bet_type TEXT,
            amount REAL,
            coefficient REAL,
            status TEXT,
            FOREIGN KEY(match_id) REFERENCES match(id),
            FOREIGN KEY(user_id) REFERENCES user(user_id)
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tournaments_db()
