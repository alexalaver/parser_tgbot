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

    def add_user(self, id, first_name, username, ids):
        with self.connect:
            self.cursor.execute("INSERT INTO users(id, first_name, username, ids) VALUES(%s, %s, %s, %s)", (id, first_name, username, ids,))
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

    def check_date_tarife_for_number(self, number_group):
        with self.connect:
            self.cursor.execute("SELECT data_end FROM groups WHERE number_group=%s", (number_group,))
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

    def check_numbers_ids(self):
        with self.connect:
            self.cursor.execute("SELECT ids FROM users ORDER BY ids DESC LIMIT 1;")
            a = self.cursor.fetchone()
            if a is None:
                return 0
            else:
                return a[0]

    def update_balance(self, id, oplata):
        with self.connect:
            self.cursor.execute(f"UPDATE users SET balance=balance-{oplata} WHERE id=%s", (id,))
            self.connect.commit()

    def popolnenie_balance(self, id, oplata):
        with self.connect:
            self.cursor.execute(f"UPDATE users SET balance=balance+{oplata} WHERE id=%s", (id,))
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

    def check_numbers_group(self):
        with self.connect:
            self.cursor.execute("SELECT number_group FROM groups ORDER BY number_group DESC LIMIT 1;")
            a = self.cursor.fetchone()
            if a is None:
                return 0
            else:
                return a[0]

    def add_channels(self, id, number_group, keyword, channels, group_name, channels_title):
        with self.connect:
            self.cursor.execute("INSERT INTO groups (id, number_group, keyword, channels, group_name, channels_title) VALUES (%s, %s, %s, %s, %s, %s)", (id, number_group, keyword, channels, group_name, channels_title, ))
            self.connect.commit()

    def add_cashe_group_name_parsing(self, id, group_name):
        with self.connect:
            self.cursor.execute("INSERT INTO cash_parsing (id, group_name) VALUES(%s, %s)", (id, group_name,))
            self.connect.commit()




    def select_group_name(self, id):
        with self.connect:
            self.cursor.execute("SELECT group_name FROM groups WHERE id=%s", (id,))
            a = self.cursor.fetchall()
            result_list = [item[0] for item in a]
            return result_list

    def select_all_group_name(self):
        with self.connect:
            self.cursor.execute("SELECT group_name FROM groups")
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

    def select_channels_name(self, id, group_name):
        with self.connect:
            self.cursor.execute("SELECT channels_title FROM groups WHERE id=%s AND group_name=%s", (id, group_name,))
            a = self.cursor.fetchone()[0]
            return a

    def select_all_off_channels(self, id, group_name):
        with self.connect:
            self.cursor.execute("SELECT off_channels FROM groups WHERE id=%s AND group_name=%s", (id, group_name,))
            a = self.cursor.fetchone()
            if a:
                return a[0]
            else:
                return []


    def select_channels_for_number(self, id, number_group):
        with self.connect:
            self.cursor.execute("SELECT channels FROM groups WHERE id=%s AND number_group=%s", (id, number_group,))
            a = self.cursor.fetchone()[0]
            return a

    def select_channels_with_number(self, number_group):
        with self.connect:
            self.cursor.execute("SELECT channels FROM groups WHERE number_group=%s", (number_group,))
            a = self.cursor.fetchone()[0]
            return a

    def select_channels_name_with_number(self, number_group):
        with self.connect:
            self.cursor.execute("SELECT channels_title FROM groups WHERE number_group=%s", (number_group,))
            a = self.cursor.fetchone()[0]
            return a


    def select_number_group(self, id, group_name):
        with self.connect:
            self.cursor.execute("SELECT number_group FROM groups WHERE id=%s AND group_name=%s", (id, group_name,))
            a = self.cursor.fetchone()[0]
            return a


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

    def select_all_channels_group(self):
        with self.connect:
            self.cursor.execute("SELECT * FROM groups WHERE data_end IS NOT NULL")
            a = self.cursor.fetchall()
            return a

    def select_all_keyword(self, id):
        with self.connect:
            self.cursor.execute("SELECT keyword FROM groups WHERE id=%s AND data_end IS NOT NULL", (id,))
            a = self.cursor.fetchall()
            combined_list = list(itertools.chain(*a))
            return combined_list

    def select_channels_number_group(self, number_group):
        with self.connect:
            self.cursor.execute("SELECT channels FROM groups WHERE number_group=%s AND data_end IS NOT NULL", (number_group,))
            a = self.cursor.fetchone()[0]
            return a

    def select_off_channels(self, number_group):
        with self.connect:
            self.cursor.execute("SELECT off_channels FROM groups WHERE number_group=%s", (number_group,))
            a = self.cursor.fetchone()
            if a:
                return a[0]
            else:
                return []

    def update_all_channels(self, number_group, channels):
        with self.connect:
            self.cursor.execute("UPDATE groups SET channels=%s WHERE number_group=%s", (channels, number_group,))
            self.connect.commit()

    def update_all_channels_name(self, number_group, channels_name):
        with self.connect:
            self.cursor.execute("UPDATE groups SET channels_title=%s WHERE number_group=%s", (channels_name, number_group,))
            self.connect.commit()

    def update_off_channels(self, number_group, channels):
        with self.connect:
            self.cursor.execute("UPDATE groups SET off_channels=%s WHERE number_group=%s", (channels, number_group,))
            self.connect.commit()

    def update_keywords(self, keyword, number_group):
        with self.connect:
            self.cursor.execute("UPDATE groups SET keyword=%s WHERE number_group=%s", (keyword, number_group,))
            self.connect.commit()

    def get_group_name_number(self, number_group):
        with self.connect:
            self.cursor.execute("SELECT group_name FROM groups WHERE number_group=%s", (number_group,))
            return self.cursor.fetchone()[0]

    def update_message_id(self, message_ids):
        with self.connect:
            self.cursor.execute("UPDATE message_id SET message_ids = %s", (message_ids,))
            self.connect.commit()

    def select_message_id(self, number_group):
        with self.connect:
            self.cursor.execute("SELECT message_ids FROM groups WHERE number_group=%s", (number_group,))
            record = self.cursor.fetchone()[0]
            return record

    def update_all_message_ids(self, number_group, message_key):
        self.cursor.execute("SELECT message_ids FROM groups WHERE number_group = %s", (number_group,))
        current_message_ids = self.cursor.fetchone()[0]

        if current_message_ids is None:
            current_message_ids = []

        updated_message_ids = current_message_ids + [[message_key[0], message_key[1]]]

        with self.connect:
            self.cursor.execute("UPDATE groups SET message_ids = %s WHERE number_group = %s",
                                (updated_message_ids, number_group))
            self.connect.commit()

    def add_chat_ids(self, number_group, ids):
        with self.connect:
            self.cursor.execute("UPDATE groups SET channels_id=%s WHERE number_group=%s", (ids, number_group,))
            self.connect.commit()

    def select_chat_ids(self, number_group):
        with self.connect:
            self.cursor.execute("SELECT channels_id FROM groups WHERE number_group=%s", (number_group,))
            a = self.cursor.fetchone()
            if a is None:
                return []
            else:
                return a[0]


    def select_autoposting_group_name(self, id):
        with self.connect:
            self.cursor.execute("SELECT group_name FROM autoposting_groups WHERE id=%s", (id,))
            a = self.cursor.fetchall()
            result_list = [item[0] for item in a]
            return result_list

    def check_numbers_autoposting_group(self, id):
        with self.connect:
            self.cursor.execute("SELECT id FROM autoposting_groups WHERE id=%s", (id,))
            a = self.cursor.fetchall()
            b = [row for row in a]
            if a is None:
                return 0
            else:
                return len(b)

    def check_numbers_account_autoposting(self):
        with self.connect:
            self.cursor.execute("SELECT id FROM autoposting_groups")
            a = self.cursor.fetchall()
            b = [row for row in a]
            if a is None:
                return 0
            else:
                return len(b)

    def add_autoposting_account(self, id, number_group, number_phone, string_session, group_name):
        with self.connect:
            self.cursor.execute("INSERT INTO autoposting_groups(id, number_group, number_phone, string_session, group_name) VALUES(%s, %s, %s, %s, %s)", (id, number_group, number_phone, string_session, group_name))
            self.connect.commit()

    def sms_get_add(self, id):
        with self.connect:
            self.cursor.execute("INSERT INTO sms_get(id, states) VALUES(%s, %s)", (id, 1,))
            self.connect.commit()

    def get_states_sms(self, id):
        with self.connect:
            self.cursor.execute("SELECT states FROM sms_get WHERE id=%s", (id,))
            return self.cursor.fetchone()[0]

    def update_states_sms(self, id, num):
        with self.connect:
            self.cursor.execute("UPDATE sms_get SET states=%s WHERE id=%s", (num, id,))
            self.connect.commit()

    def delete_sms_get(self, id):
        with self.connect:
            self.cursor.execute("DELETE FROM sms_get WHERE id=%s", (id,))
            self.connect.commit()

    def select_all_channels_autoposting_group(self):
        with self.connect:
            self.cursor.execute("SELECT * FROM autoposting_groups")
            a = self.cursor.fetchall()
            return a

    def select_date_betw(self, number_group):
        with self.connect:
            self.cursor.execute("SELECT date_betw FROM autoposting_post WHERE number_post=%s", (number_group,))
            a = self.cursor.fetchone()[0]
            return a

    def update_date_betw(self, data, number_group):
        with self.connect:
            self.cursor.execute("UPDATE autoposting_post SET date_betw=%s WHERE number_post=%s", (data, number_group,))
            self.connect.commit()

    def select_account_name(self, id):
        with self.connect:
            self.cursor.execute("SELECT group_name FROM autoposting_groups WHERE id=%s", (id,))
            a = self.cursor.fetchall()
            result_list = [item[0] for item in a]
            return result_list

    def select_number_account(self, id, group_name):
        with self.connect:
            self.cursor.execute("SELECT number_group FROM autoposting_groups WHERE id=%s AND group_name=%s", (id, group_name,))
            a = self.cursor.fetchone()[0]
            return a

    def select_chats_post(self, id, post_id):
        with self.connect:
            self.cursor.execute("SELECT chats FROM autoposting_post WHERE id=%s AND post_name=%s", (id, post_id,))
            a = self.cursor.fetchone()[0]
            first_elements = [sublist[0] for sublist in a]
            return first_elements

    def select_chats_name_post(self, id, post_id):
        with self.connect:
            self.cursor.execute("SELECT channels_title FROM autoposting_post WHERE id=%s AND post_name=%s", (id, post_id,))
            a = self.cursor.fetchone()[0]
            return a

    def check_date_tarife_account(self, id, post_id):
        with self.connect:
            self.cursor.execute("SELECT data_end FROM autoposting_post WHERE id=%s AND post_name=%s", (id, post_id,))
            a = self.cursor.fetchone()[0]
            return a

    def select_chats_account_with_number(self, number_post):
        with self.connect:
            self.cursor.execute("SELECT chats FROM autoposting_post WHERE number_post=%s", (number_post,))
            a = self.cursor.fetchone()[0]
            first_elements = [sublist[0] for sublist in a]
            return first_elements

    def select_chats_account_with_number_autoposting(self, number_post):
        with self.connect:
            self.cursor.execute("SELECT chats FROM autoposting_post WHERE number_post=%s", (number_post,))
            a = self.cursor.fetchone()[0]
            return a

    def select_chats_account_with_number_confirm_oplata(self, number_post):
        with self.connect:
            self.cursor.execute("SELECT chats FROM autoposting_post WHERE number_post=%s", (number_post,))
            a = self.cursor.fetchone()[0]
            return a

    def select_chats_name_account_with_number(self, number_post):
        with self.connect:
            self.cursor.execute("SELECT channels_title FROM autoposting_post WHERE number_post=%s", (number_post,))
            a = self.cursor.fetchone()
            return a[0]


    def check_date_tarife_account_for_number(self, number_post):
        with self.connect:
            self.cursor.execute("SELECT data_end FROM autoposting_post WHERE number_post=%s", (number_post,))
            a = self.cursor.fetchone()
            if a is None:
                return None
            else:
                return a[0]

    def select_account_name_for_number_group(self, number_post):
        with self.connect:
            self.cursor.execute("SELECT post FROM autoposting_post WHERE number_post=%s", (number_post,))
            a = self.cursor.fetchone()
            return a[0]

    def update_all_chats_account(self, number_post, channels):
        with self.connect:
            self.cursor.execute("UPDATE autoposting_post SET chats=%s WHERE number_post=%s", (channels, number_post,))
            self.connect.commit()

    def update_all_chats_name_account(self, number_post, channels):
        with self.connect:
            self.cursor.execute("UPDATE autoposting_post SET channels_title=%s WHERE number_post=%s", (channels, number_post,))
            self.connect.commit()


    def add_date_tariffe_autoposting(self, id, data, number_group):
        with self.connect:
            self.cursor.execute("UPDATE autoposting_post SET data_end=%s WHERE id=%s AND number_post=%s", (data, id, number_group,))
            self.connect.commit()

    def select_autoposting_post_name(self, id):
        with self.connect:
            self.cursor.execute("SELECT post_name FROM autoposting_post WHERE id=%s", (id,))
            a = self.cursor.fetchall()
            result_list = [item[0] for item in a]
            return result_list

    def select_number_post(self, id, account_name):
        with self.connect:
            self.cursor.execute("SELECT number_post FROM autoposting_post WHERE id=%s AND post_name=%s", (id, account_name,))
            a = self.cursor.fetchone()[0]
            return a

    def select_account_number(self, id, group_name):
        with self.connect:
            self.cursor.execute("SELECT number_group FROM autoposting_groups WHERE id=%s AND group_name=%s", (id, group_name,))
            a = self.cursor.fetchone()
            return a[0]

    def select_autoposting_post_name_for_number(self, id, number_account):
        with self.connect:
            self.cursor.execute("SELECT post_name FROM autoposting_post WHERE id=%s AND number_account=%s", (id, number_account,))
            a = self.cursor.fetchall()
            result_list = [item[0] for item in a]
            return result_list

    def check_numbers_account_post(self):
        with self.connect:
            self.cursor.execute("SELECT id FROM autoposting_post")
            a = self.cursor.fetchall()
            b = [row for row in a]
            if a is None:
                return 0
            else:
                return len(b)

    def add_post_account(self, id, post, string_session, chats, time_betw, number_post, number_account, channel_tag, message_id_bot, channels_title, days, post_name):
        with self.connect:
            self.cursor.execute("INSERT INTO autoposting_post(id, post, string_session, chats, time_betw, number_post, number_account, channel_tag, message_id_bot, channels_title, days, post_name) VALUES(%s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s, %s, %s)", (id, post, string_session, chats, time_betw, number_post, number_account, channel_tag, message_id_bot, channels_title, days, post_name,))
            self.connect.commit()

    def get_string_session(self, number_account):
        with self.connect:
            self.cursor.execute("SELECT string_session FROM autoposting_groups WHERE number_group=%s", (number_account,))
            a = self.cursor.fetchone()
            return a[0]

    def select_all_channels_autoposting_post(self):
        with self.connect:
            self.cursor.execute("SELECT * FROM autoposting_post")
            a = self.cursor.fetchall()
            return a

    def select_time_betw(self, number_post):
        with self.connect:
            self.cursor.execute("SELECT time_betw FROM autoposting_post WHERE number_post=%s", (number_post,))
            a = self.cursor.fetchone()
            return a[0]

    def select_all_channels_autoposting_post_not_null(self):
        with self.connect:
            self.cursor.execute("SELECT * FROM autoposting_post WHERE data_end IS NOT NULL")
            a = self.cursor.fetchall()
            return a

    def delete_data_end_post(self, number_post):
        with self.connect:
            self.cursor.execute("UPDATE autoposting_post SET data_end=Null WHERE number_post=%s", (number_post,))
            self.connect.commit()

    def update_chats_post(self, chats, number_post):
        with self.connect:
            self.cursor.execute("UPDATE autoposting_post SET chats=%s WHERE number_post=%s", (chats, number_post,))
            self.connect.commit()

    def delete_data_end_group(self, number_group):
        with self.connect:
            self.cursor.execute("UPDATE groups SET data_end=Null WHERE number_group=%s", (number_group,))
            self.connect.commit()

    def check_autoposting_group_name(self, id):
        with self.connect:
            self.cursor.execute("SELECT group_name FROM autoposting_groups WHERE id=%s", (id,))
            a = self.cursor.fetchone()
            return a

    def select_post_name(self, post):
        with self.connect:
            self.cursor.execute("SELECT message_id_bot FROM autoposting_post WHERE post_name=%s", (post,))
            a = self.cursor.fetchone()
            return a[0]

    def select_post_name_autoposting(self, number):
        with self.connect:
            self.cursor.execute("SELECT post_name FROM autoposting_post WHERE number_post=%s", (number,))
            a = self.cursor.fetchone()
            return a[0]

    def delete_post(self, post):
        with self.connect:
            self.cursor.execute("DELETE FROM autoposting_post WHERE post=%s", (post,))
            self.connect.commit()

    def update_chat_idn_autoposting(self, chats, number_post):
        with self.connect:
            self.cursor.execute("UPDATE autoposting_post SET chats=%s::jsonb WHERE number_post=%s", (chats, number_post,))
            self.connect.commit()

    def update_chat_name_autoposting(self, chats, number_post):
        with self.connect:
            self.cursor.execute("UPDATE autoposting_post SET channels_title=%s WHERE number_post=%s", (chats, number_post,))
            self.connect.commit()

    def delete_data_end_autoposting_post(self, number_post):
        with self.connect:
            self.cursor.execute("UPDATE autoposting_post SET data_end=Null WHERE number_post=%s", (number_post,))
            self.connect.commit()

    def select_days_autoposting_post(self, number_post):
        with self.connect:
            self.cursor.execute("SELECT days FROM autoposting_post WHERE number_post=%s", (number_post,))
            a = self.cursor.fetchone()[0]
            return a

    def select_channels_id_parser(self):
        with self.connect:
            self.cursor.execute("SELECT channels_id FROM groups")
            a = self.cursor.fetchall()
            return a

    def select_all_post_name(self):
        with self.connect:
            self.cursor.execute("SELECT post_name FROM autoposting_post")
            a = self.cursor.fetchall()
            result_list = [item[0] for item in a]
            return result_list

    def select_settings_all_proxy(self):
        with self.connect:
            self.cursor.execute("SELECT proxy FROM settings_bot")
            a = self.cursor.fetchone()
            if a is None:
                return []
            else:
                return a[0]

    def update_proxy_settings(self, proxy):
        with self.connect:
            self.cursor.execute("UPDATE settings_bot SET proxy=%s", (proxy,))
            self.connect.commit()

    def add_proxy_settings(self, proxy):
        with self.connect:
            self.cursor.execute("INSERT INTO settings_bot(proxy) VALUES(%s)", (proxy,))
            self.connect.commit()

    def select_number_account_with_post(self, number_post):
        with self.connect:
            self.cursor.execute("SELECT number_account FROM autoposting_post WHERE number_post=%s", (number_post,))
            a = self.cursor.fetchone()[0]
            return a

    def update_proxy_autoposting_account(self, proxy, number_account):
        with self.connect:
            self.cursor.execute("UPDATE autoposting_groups SET proxy=%s WHERE number_group=%s", (proxy, number_account,))
            self.connect.commit()

    def delete_proxy_settings_bot(self):
        with self.connect:
            self.cursor.execute("UPDATE settings_bot SET proxy=Null")
            self.connect.commit()

    def select_proxy_autoposting_account(self, number_account):
        with self.connect:
            self.cursor.execute("SELECT proxy FROM autoposting_groups WHERE number_group=%s", (number_account,))
            a = self.cursor.fetchone()[0]
            return a

    def select_all_admin_id(self):
        with self.connect:
            self.cursor.execute("SELECT id FROM users WHERE adm > 0")
            a = self.cursor.fetchall()
            flattened_list = [item[0] for item in a]
            return flattened_list

    def select_all_chats_groups(self):
        with self.connect:
            self.cursor.execute("SELECT groups FROM all_chats")
            groups = self.cursor.fetchone()
            if groups is None:
                return False
            else:
                return groups[0]

    def select_time_all_chats_groups(self):
        with self.connect:
            self.cursor.execute("SELECT time_update_all_groups FROM settings_bot")
            times = self.cursor.fetchone()
            if times is None:
                return False
            else:
                return times[0]

    def update_time_all_chats_groups(self, time):
        with self.connect:
            self.cursor.execute("UPDATE settings_bot SET time_update_all_groups=%s", (time,))
            self.connect.commit()

    def update_all_chats_groups(self, groups):
        with self.connect:
            self.cursor.execute("UPDATE all_chats SET groups=%s::jsonb", (groups,))
            self.connect.commit()