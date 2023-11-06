import psycopg2
import itertools

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


    def add_date_tariffe(self, id, data, number_group):
        with self.connect:
            self.cursor.execute("UPDATE groups SET data_end=%s WHERE id=%s AND number_group=%s", (data, id, number_group,))
            self.connect.commit()

    def check_date_tarife(self, id, group_name):
        with self.connect:
            self.cursor.execute("SELECT data_end FROM groups WHERE id=%s AND group_name=%s", (id, group_name,))
            a = self.cursor.fetchone()[0]
            return a

    def check_date_tarife_for_number(self, id, number_group):
        with self.connect:
            self.cursor.execute("SELECT data_end FROM groups WHERE id=%s AND number_group=%s", (id, number_group,))
            a = self.cursor.fetchone()
            if a is None:
                return None
            else:
                return a[0]

    def delete_old_tariffe(self, id, number_group):
        with self.connect:
            self.cursor.execute("DELETE data_end FROM groups WHERE id=%s AND number_group=%s", (id, number_group,))
            self.connect.commit()

    def add_chats(self, id, chats):
        with self.connect:
            self.cursor.execute(f"UPDATE users SET chats=chats+{chats} WHERE id=%s", (id,))
            self.connect.commit()

    def check_balance(self, id):
        with self.connect:
            self.cursor.execute("SELECT balance FROM users WHERE id=%s", (id,))
            a = self.cursor.fetchone()[0]
            return a

    def update_balance(self, id, oplata):
        with self.connect:
            self.cursor.execute(f"UPDATE users SET balance=balance-{oplata} WHERE id=%s", (id,))
            self.connect.commit()

    def check_number_group(self, id):
        with self.connect:
            self.cursor.execute("SELECT id FROM groups WHERE id=%s", (id,))
            a = self.cursor.fetchall()
            b = [row for row in a]
            if a is None:
                return 0
            else:
                return len(b)

    def check_numbers_group(self, id):
        with self.connect:
            self.cursor.execute("SELECT number_group FROM groups WHERE id=%s", (id,))
            a = self.cursor.fetchone()
            if a is None:
                return 0
            else:
                return a[0]

    def add_channels(self, id, number_group, keyword, channels, group_name):
        with self.connect:
            self.cursor.execute("INSERT INTO groups (id, number_group, keyword, channels, group_name) VALUES (%s, %s, %s, %s, %s)", (id, number_group, keyword, channels, group_name,))
            self.connect.commit()

    def add_cashe_group_name_parsing(self, id, group_name):
        with self.connect:
            self.cursor.execute("INSERT INTO cash_parsing (id, group_name) VALUES(%s, %s)", (id, group_name,))
            self.connect.commit()

    def add_cashe_keyword_parsing(self, id, keyword):
        with self.connect:
            self.cursor.execute("UPDATE cash_parsing SET keyword=%s WHERE id=%s", (keyword, id,))
            self.connect.commit()

    def delete_cashe_parsing(self, id):
        with self.connect:
            self.cursor.execute("DELETE FROM cash_parsing WHERE id=%s", (id,))
            self.connect.commit()

    def select_cashe_parsing(self, id):
        with self.connect:
            self.cursor.execute("SELECT group_name, keyword FROM cash_parsing WHERE id=%s", (id,))
            a = self.cursor.fetchone()
            b = [row for row in a]
            return b

    def select_group_name(self, id):
        with self.connect:
            self.cursor.execute("SELECT group_name FROM groups WHERE id=%s", (id,))
            a = self.cursor.fetchall()
            result_list = [item[0] for item in a]
            return result_list

    def select_group_name_for_number_group(self, id, number_group):
        with self.connect:
            self.cursor.execute("SELECT group_name FROM groups WHERE id=%s AND number_group=%s", (id, number_group,))
            a = self.cursor.fetchone()[0]
            return a


    def select_channels(self, id, group_name):
        with self.connect:
            self.cursor.execute("SELECT channels FROM groups WHERE id=%s AND group_name=%s", (id, group_name,))
            a = self.cursor.fetchone()[0]
            return a

    def select_channels_for_number(self, id, number_group):
        with self.connect:
            self.cursor.execute("SELECT channels FROM groups WHERE id=%s AND number_group=%s", (id, number_group,))
            a = self.cursor.fetchone()[0]
            return a

    def select_channels_with_number(self, id, number_group):
        with self.connect:
            self.cursor.execute("SELECT channels FROM groups WHERE id=%s AND number_group=%s", (id, number_group,))
            a = self.cursor.fetchone()[0]
            return a

    def select_number_group(self, id, group_name):
        with self.connect:
            self.cursor.execute("SELECT number_group FROM groups WHERE id=%s AND group_name=%s", (id, group_name,))
            a = self.cursor.fetchone()[0]
            return a

    def delete_cash_parsing_use(self, id):
        with self.connect:
            self.cursor.execute("DELETE FROM cash_parsing_use WHERE id=%s", (id,))
            self.connect.commit()

    def add_cash_parsing_use(self, id, number_group):
        with self.connect:
            self.cursor.execute("INSERT INTO cash_parsing_use (id, number_group) VALUES(%s, %s)", (id, number_group,))
            self.connect.commit()

    def select_keyword(self, id, number_group):
        with self.connect:
            self.cursor.execute("SELECT keyword FROM groups WHERE id=%s AND number_group=%s", (id, number_group,))
            a = self.cursor.fetchone()[0]
            return a

    def select_number_group_parser(self, id):
        with self.connect:
            self.cursor.execute("SELECT number_group FROM cash_parsing_use WHERE id=%s", (id,))
            a = self.cursor.fetchone()[0]
            return a

    def select_all_channels(self, id):
        with self.connect:
            self.cursor.execute("SELECT channels FROM groups WHERE id=%s AND data_end IS NOT NULL", (id,))
            a = self.cursor.fetchall()
            combined_list = list(itertools.chain(*a))
            return combined_list
