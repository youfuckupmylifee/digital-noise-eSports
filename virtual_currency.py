import sqlite3
import time


class VirtualCurrency:

    def __init__(self, name, initial_amount, recovery_interval_seconds):
        self.name = name
        self.initial_amount = initial_amount
        self.recovery_interval = recovery_interval_seconds
        self.db_path = 'instance/user_profiles.db'

    def get_balance(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM user WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    def update_balance(self, user_id, new_balance):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE user SET balance = ? WHERE user_id = ?", (new_balance, user_id))
        conn.commit()
        conn.close()

    def grant_initial_amount(self, user_id):
        balance = self.get_balance(user_id)
        if balance == 0:
            self.update_balance(user_id, self.initial_amount)
            return True
        return False

    def can_request_currency(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT last_request_time FROM user WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            last_request_time = result[0]
            current_time = time.time()
            return current_time - last_request_time >= 86400  # 24 часа в секундах
        else:
            return False

    def request_currency(self, user_id):
        if self.can_request_currency(user_id):
            self.update_balance(user_id, self.initial_amount)
            current_time = int(time.time())
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE user SET last_request_time = ? WHERE user_id = ?", (current_time, user_id))
            conn.commit()
            conn.close()
            return True
        else:
            return False

    def recover_currency(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        recovery_amount = 10
        cursor.execute("UPDATE user SET balance = balance + ?", (recovery_amount,))
        conn.commit()
        conn.close()