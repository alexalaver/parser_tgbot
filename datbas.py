import psycopg2

class Data:
    def __init__(self, host1, port1, data, user1, password1):
        self.connect = psycopg2.connect(
            host=host1,
            port=port1,
            database=data,
            user=user1,
            password=password1
        )
        self.cursor = self.connect.cursor()

    def add_user(self, id, first_name, username):
        with self.connect:
            self.cursor.execute("INSERT INTO users(id, first_name, username) VALUES(%s, %s, %s)", (id, first_name, username,))
            self.connect.commit()

    def check_user(self, id):
        with self.connect:
            self.cursor.execute("SELECT id FROM users WHERE id=%s", (id,))
            return bool(len(self.cursor.fetchall()))
    def select_balance(self, id):
        with self.connect:
            self.cursor.execute("SELECT balance FROM users WHERE id=%s", (id,))
            a = self.cursor.fetchone()[0]
            if a is None:
                return "0$"
            else:
                return f"{a}$"

    def select_tariffe(self, id):
        with self.connect:
            self.cursor.execute("SELECT tariffe FROM users WHERE id=%s", (id,))
            a = self.cursor.fetchone()[0]
            if a is None:
                return "Нет действующего тариффа."
            elif a == 1:
                return f"Стартовый"
            elif a == 2:
                return f"Стандарт"
            elif a == 3:
                return f"Премиум"


    # def select_tariffe(self, id):
    #     with self.connect:
    #         self.cursor.execute("SELECT tariffe FROM users WHERE id=%s", (id,))
    #         a = self.cursor.fetchone()[0]
    #         if a is None:
    #             return "0 чатов."
    #         else:
    #             return f"{a} чатов"

    def add_admin(self, id):
        with self.connect:
            self.cursor.execute("UPDATE users SET adm=1 WHERE id=%s", (id,))
            self.connect.commit()

    def select_admin(self, id):
        with self.connect:
            self.cursor.execute("SELECT adm FROM users WHERE id=%s", (id,))
            return self.cursor.fetchone()[0]

    def addbalance(self, id, balanceadd):
        with self.connect:
            self.cursor.execute(f"UPDATE users SET balance=balance+{balanceadd} WHERE id=%s", (id,))
            self.connect.commit()

    def rembalance(self, id, balancerem):
        with self.connect:
            self.cursor.execute(f"UPDATE users SET balance=balance-{balancerem} WHERE id=%s", (id,))
            self.connect.commit()