import sqlite3
from user_profile_management import get_user_profile, update_balance # Взаимодействуем с user


# Функция для добавления турнира
def add_tournament_to_db(name, teams):
    conn = sqlite3.connect('instance/tournaments.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tournament (name, teams) VALUES (?, ?)", (name, teams))
    conn.commit()
    conn.close()

# Функция для добавления команды
def add_team_to_db(tournament_id, name):
    conn = sqlite3.connect('instance/tournaments.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO team (tournament_id, name) VALUES (?, ?)", (tournament_id, name))
    conn.commit()
    conn.close()

# Функция для добавления игрока
def add_player_to_db(team_id, name):
    conn = sqlite3.connect('instance/tournaments.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO player (team_id, name) VALUES (?, ?)", (team_id, name))
    conn.commit()
    conn.close()

# Добавление нового матча
def add_match_to_db(tournament_id, team1, team2, match_time, status, coef_win, coef_draw, coef_lose):
    conn = sqlite3.connect('instance/tournaments.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO match (tournament_id, team1, team2, match_time, status, coefficient_win, coefficient_draw, coefficient_lose) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (tournament_id, team1, team2, match_time, status, coef_win, coef_draw, coef_lose)
    )
    conn.commit()
    conn.close()

# Получение текущего матча
def get_current_matches():
    conn = sqlite3.connect('instance/tournaments.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, team1, team2, match_time, status, coefficient_win, coefficient_draw, coefficient_lose FROM match")
    matches = cursor.fetchall()
    conn.close()
    return matches

# Функция для совершения ставки
def place_bet(user_id, match_id, bet_type, amount):
    conn = sqlite3.connect('instance/tournaments.db')
    cursor = conn.cursor()

    # Проверяем баланс пользователя
    profile = get_user_profile(user_id)
    if profile and profile[3] >= amount:
        # Пересчитываем коэффициенты перед размещением ставки
        calculate_coefficients(match_id)

        # Получаем обновленный коэффициент для данного исхода
        cursor.execute("SELECT coefficient_win, coefficient_draw, coefficient_lose FROM match WHERE id = ?", (match_id,))
        row = cursor.fetchone()
        coefficients = {
            "П1": row[0],
            "Ничья": row[1],
            "П2": row[2]
        }
        coefficient = coefficients[bet_type]

        # Списание средств со счета пользователя
        new_balance = profile[3] - amount
        update_balance(user_id, new_balance)

        # Размещение ставки
        cursor.execute("INSERT INTO bet (user_id, match_id, bet_type, amount, coefficient, status) VALUES (?, ?, ?, ?, ?, 'ожидает')", (user_id, match_id, bet_type, amount, coefficient))
        conn.commit()
    else:
        raise Exception("Недостаточно средств на счете.")

    conn.close()

# Обновление статуса ставки
def update_bet_status(bet_id, new_status):
    conn = sqlite3.connect('instance/tournaments.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE bet SET status = ? WHERE id = ?", (new_status, bet_id))
    conn.commit()
    conn.close()

# Получение коэффициента для ставки
def get_coefficient(match_id, bet_type):
    conn = sqlite3.connect('instance/tournaments.db')
    cursor = conn.cursor()
    cursor.execute("SELECT coefficient_win, coefficient_draw, coefficient_lose FROM match WHERE id = ?", (match_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise Exception("Матч не найден.")

    coefficients = {
        "П1": row[0],
        "Ничья": row[1],
        "П2": row[2]
    }

    if bet_type not in coefficients:
        raise Exception("Неверный тип ставки.")

    return coefficients[bet_type]

# Функция для расчета результатов после завершения матча
def process_match_result(match_id, result):
    conn = sqlite3.connect('instance/tournaments.db')
    cursor = conn.cursor()

    # Получение всех ставок для данного матча
    cursor.execute("SELECT id, user_id, bet_type, amount, coefficient FROM bet WHERE match_id = ? AND status = 'ожидает'", (match_id,))
    bets = cursor.fetchall()

    for bet_id, user_id, bet_type, amount, coefficient in bets:
        if bet_type == result:
            # Выигрыш
            winnings = amount * coefficient
            profile = get_user_profile(user_id)
            if profile:
                new_balance = profile[3] + winnings
                update_balance(user_id, new_balance)
                cursor.execute("UPDATE bet SET status = 'выигрыш' WHERE id = ?", (bet_id,))
        else:
            # Проигрыш
            cursor.execute("UPDATE bet SET status = 'проигрыш' WHERE id = ?", (bet_id,))

    conn.commit()
    conn.close()

# Функция для динамических коэффициентов
def calculate_coefficients(match_id):
    conn = sqlite3.connect('instance/tournaments.db')
    cursor = conn.cursor()

    # Получаем суммы ставок на каждый исход
    cursor.execute("SELECT SUM(amount) FROM bet WHERE match_id = ? AND bet_type = 'П1'", (match_id,))
    total_bet_p1 = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM bet WHERE match_id = ? AND bet_type = 'П2'", (match_id,))
    total_bet_p2 = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM bet WHERE match_id = ? AND bet_type = 'Ничья'", (match_id,))
    total_bet_draw = cursor.fetchone()[0] or 0

    # Базовые коэффициенты
    base_coef_p1 = 1.8
    base_coef_p2 = 3.2
    base_coef_draw = 1.8

    # Вычисление изменения коэффициентов на основе общей суммы ставок
    total_bets = total_bet_p1 + total_bet_p2 + total_bet_draw
    change_factor = 0.5

    coef_p1 = base_coef_p1 - change_factor * (total_bet_p1 / max(total_bets, 1))
    coef_p2 = base_coef_p2 - change_factor * (total_bet_p2 / max(total_bets, 1))
    coef_draw = base_coef_draw - change_factor * (total_bet_draw / max(total_bets, 1))

    # Округление коэффициентов до двух знаков после запятой
    coef_p1 = round(max(coef_p1, 1.05), 2)
    coef_p2 = round(max(coef_p2, 1.05), 2)
    coef_draw = round(max(coef_draw, 1.05), 2)

    # Обновляем коэффициенты в базе данных
    cursor.execute("UPDATE match SET coefficient_win = ?, coefficient_draw = ?, coefficient_lose = ? WHERE id = ?", (coef_p1, coef_draw, coef_p2, match_id))

    conn.commit()
    conn.close()