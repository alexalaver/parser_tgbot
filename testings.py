@dp.message_handler(state=Create_account_autoposting.create_autoposting_3)
async def group_post_autoposting(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        if message.text == cfg.cancel_creategroup:
            user_id = message.from_user.id
            markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
            markup_reply.add(cfg.autoposting)
            markup_reply.add(cfg.parser)
            markup_reply.row(cfg.my_profile, cfg.support)
            if db.select_admin(user_id) > 0:
                markup_reply.add(cfg.admin_panel_button)
            await message.answer(cfg.back_text, reply_markup=markup_reply)
            await state.reset_state()
        else:
            if message.forward_from or message.forward_from_chat:
                await state.update_data(forwarded_message_id=message.forward_from_message_id)
                await message.answer(cfg.create_account_autoposting_5)
                await Create_account_autoposting.create_autoposting_4.set()
            else:
                await message.answer("Вы должны переслать сообщение из канала, попробуйте ещё раз:")

@dp.message_handler(state=Create_account_autoposting.create_autoposting_4)
async def autoposting_time_betw(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        if message.text == cfg.cancel_creategroup:
            user_id = message.from_user.id
            markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
            markup_reply.add(cfg.autoposting)
            markup_reply.add(cfg.parser)
            markup_reply.row(cfg.my_profile, cfg.support)
            if db.select_admin(user_id) > 0:
                markup_reply.add(cfg.admin_panel_button)
            await message.answer(cfg.back_text, reply_markup=markup_reply)
            await state.reset_state()
        else:
            if int(message.text):
                if int(message.text) >= 60:
                    current_time = datetime.datetime.now()
                    time_in_60_minutes = current_time + timedelta(minutes=60)
                    await state.update_data(time_betw=int(message.text))
                    await state.update_data(date_betw=time_in_60_minutes)
                    await message.answer(cfg.create_account_autoposting_6)
                    await Create_account_autoposting.create_autoposting_5.set()
                else:
                    await message.answer(cfg.minimum_time_error)
            else:
                await message.answer("Ошибка! Промежуток времени должен быть цифрой, повторите ещё раз:")

@dp.message_handler(state=Create_account_autoposting.create_autoposting_5)
async def group_chats_autoposting(message: types.Message, state: FSMContext):
    if message.chat.type == types.ChatType.PRIVATE:
        user_id = message.from_user.id
        textsing = message.text
        text_line = textsing.strip().split('\n')
        text_lines = list(dict.fromkeys([element + ' ⚠' for element in text_line]))
        if message.text == cfg.cancel_creategroup:
            user_id = message.from_user.id
            markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
            markup_reply.add(cfg.autoposting)
            markup_reply.add(cfg.parser)
            markup_reply.row(cfg.my_profile, cfg.support)
            if db.select_admin(user_id) > 0:
                markup_reply.add(cfg.admin_panel_button)
            await message.answer(cfg.back_text, reply_markup=markup_reply)
            await state.reset_state()
        else:
            if 2 <= len(message.text) <= 1000:
                if 5 <= len(text_lines) <= 50:
                    try:
                        check_number_group = db.check_numbers_account_autoposting()
                        new_number_group = check_number_group + 1
                        data = await state.get_data()
                        phone = data.get('phone')
                        string_session = data.get('string_session')
                        group_name = data.get('group_name')
                        forwarded_message_id = data.get('forwarded_message_id')
                        time_betw = data.get('time_betw')
                        date_betw = data.get('date_betw')
                        db.add_autoposting_account(user_id, new_number_group, phone, string_session, text_lines, group_name, forwarded_message_id, time_betw, date_betw)
                        markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                        markup_reply.add(cfg.autoposting)
                        markup_reply.add(cfg.parser)
                        markup_reply.row(cfg.my_profile, cfg.support)
                        if db.select_admin(user_id) > 0:
                            markup_reply.add(cfg.admin_panel_button)
                        await message.answer(cfg.right_create_group, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
                        await state.finish()
                    except Exception as es:
                        await state.reset_state()
                        markup_reply = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
                        markup_reply.add(cfg.autoposting)
                        markup_reply.add(cfg.parser)
                        markup_reply.row(cfg.my_profile, cfg.support)
                        if db.select_admin(user_id) > 0:
                            markup_reply.add(cfg.admin_panel_button)
                        await message.answer(cfg.error_create_group, reply_markup=markup_reply, parse_mode=types.ParseMode.MARKDOWN)
                        print(f"[ERROR] {es}")
                else:
                    await message.answer(cfg.error_len_channels_create, parse_mode=types.ParseMode.MARKDOWN)
            else:
                await message.answer(cfg.error_len_channels, parse_mode=types.ParseMode.MARKDOWN)