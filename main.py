from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from virtual_currency import VirtualCurrency
from user_profile_management import *
from tournament_management import *
import schedule
import time
import config
import sqlite3


# Магазин статусов
STATUSES = {
    "Скорлупа": 0,
    "Кащей": 1500,
    "Ералаш": 3000,
    "Зима": 5000,
    "Турбо": 10000,
    "Пальто": 25000,
    "Адидас младший": 50000,
    "Адидас": 100000,
}


# Инициализация бота и объекта VirtualCurrency
updater = Updater(token=config.TELEGRAM_TOKEN)
dispatcher = updater.dispatcher
virtual_currency = VirtualCurrency(config.CURRENCY_NAME, config.INITIAL_CURRENCY_AMOUNT, config.RECOVERY_INTERVAL_SECONDS)


# Функция для проверки, является ли пользователь администратором
def is_admin(user_id):
    profile = get_user_profile(user_id)
    return profile and profile[4] == 'admin'

#  Функция для приветствия
def start(update, context, from_button=False):
    user_id = update.effective_user.id
    username = update.effective_user.username

    # Проверяем, есть ли пользователь в базе данных
    profile = get_user_profile(user_id)

    if not profile:
        # Новый пользователь, регистрируем и показываем приветственное сообщение
        add_user(user_id, username)
        context.bot.send_message(chat_id=user_id, text=f"Привет, браток! Теперь ты с нами в боте digital noise eSports. Твое клеймо {username}")
    
    # Показываем главное меню (для нового пользователя и для повторных визитов)
    show_main_menu(update, context, username, from_button)

# Отображние главного меню
def show_main_menu(update, context, username, from_button):

    reply_text = f"| Общий сбор, {username}! |"
    keyboard = [
        [InlineKeyboardButton("Мой профиль", callback_data='view_profile')],
        [InlineKeyboardButton("Ставки", callback_data='bets')],
        [InlineKeyboardButton("Магазин статусов", callback_data='shop')],
        [InlineKeyboardButton("История ставок", callback_data='bet_history')],
        [InlineKeyboardButton("Пацанский подгон (раз в 24 часа)", callback_data='get_currency')],
        [InlineKeyboardButton("Администрирование", callback_data='admin_panel')] if is_admin(update.effective_user.id) else [],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с клавиатурой
    if from_button:
        update.callback_query.edit_message_text(reply_text, reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=update.effective_user.id, text=reply_text, reply_markup=reply_markup)

# Отображние исттории ставок
def show_bet_history(update, context):
    user_id = update.effective_user.id
    query = update.callback_query

    bet_history = get_bet_history(user_id)
    if bet_history:
        message = "Ваша история ставок:\n"
        for bet in bet_history:
            message += f"Матч ID: {bet[5]}, Ставка: {bet[0]}, Тип: {bet[1]}, Коэффициент: {bet[2]}, Статус: {bet[3]}, Результат матча: {bet[4]}\n"
    else:
        message = "История ставок пуста."

    # Кнопка для возвращения в главное меню
    keyboard = [[InlineKeyboardButton("Назад в меню", callback_data='back_to_main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        query.edit_message_text(message, reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=user_id, text=message, reply_markup=reply_markup)

# Отображние магазина
def show_shop(update, context):
    chat_id = update.effective_user.id
    message = "Доступные статусы для покупки:\n"
    for status, price in STATUSES.items():
        message += f"{status} - {price} {virtual_currency.name}\n"
    
    # Добавляем кнопки для выбора статуса и кнопку "Назад"
    keyboard = [[InlineKeyboardButton(status, callback_data=f"buy_{status}") for status in STATUSES]]
    keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)

# Отображние admin panel
def show_admin_panel(update, context):
    query = update.callback_query
    user_id = query.from_user.id if query else update.effective_user.id

    if not is_admin(user_id):
        text = "Доступ запрещен."
        if query:
            query.edit_message_text(text)
        else:
            context.bot.send_message(chat_id=user_id, text=text)
        return

    keyboard = [
        [InlineKeyboardButton("Добавить турнир", callback_data='add_tournament')],
        [InlineKeyboardButton("Добавить команды", callback_data='add_team')],
        [InlineKeyboardButton("Добавить игрока", callback_data='add_player')],
        [InlineKeyboardButton("Добавить матч", callback_data='add_match')],
        [InlineKeyboardButton("Установить Результат Матча", callback_data='set_match_result')],
        [InlineKeyboardButton("Назад", callback_data='back_to_main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "Admin Panel:"

    if query:
        query.edit_message_text(text, reply_markup=reply_markup)
    else:
        context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)

# Отображние ставок
def bets_menu(update, context):
    query = update.callback_query
    query.answer()

    matches = get_current_matches()
    if not matches:
        query.edit_message_text(text="На данный момент нет доступных матчей для ставок.")
        return

    # Сначала определяем keyboard
    keyboard = []

    message = "Выберите матч для ставки:\n"
    for match in matches:
        message += (f"№ {match[0]}: {match[1]} vs {match[2]} в {match[3]}, Статус: {match[4]}\n"
                    f"Коэффициенты - П1: {match[5]}, Ничья: {match[6]}, П2: {match[7]}\n")
    message += "\nДля совершения ставки используйте команду /bet"

    # Добавляем кнопку "Назад" в клавиатуру
    keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_main_menu')])
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(text=message, reply_markup=reply_markup)

# Обработчик кнопок
def button(update, context):
    query = update.callback_query
    query.answer()
    data = query.data

    if data == 'get_currency':
        get_currency(update, context)
    elif data == 'view_profile':
        profile(update, context)
    elif data == 'view_other_profile':
        query.edit_message_text("Введите username пользователя для просмотра профиля:")
        context.user_data['action'] = 'view_other_profile'
    elif data == 'admin_panel':
        user_id = query.from_user.id
        if is_admin(user_id):
            show_admin_panel(update, context)
        else:
            query.message.reply_text("Доступ запрещен.")
    elif data == 'add_tournament':
        context.user_data['action'] = data
        query.message.reply_text("Введите данные турнира в формате: 'Tournament Name;Teams'")

    elif data == 'add_team':
        context.user_data['action'] = data
        query.message.reply_text("Введите данные команды в формате: 'Tournament ID;Name'")

    elif data == 'add_player':
        context.user_data['action'] = data
        query.message.reply_text("Введите данные игрока в формате: 'Team ID;Name'")
    elif data == 'back_to_main_menu':
        start(update, context, from_button=True)
    elif data == 'back_to_main_menu':
        show_main_menu(update, context, query.from_user.username, from_button=True)
    elif data == 'back_to_main_menu':
        show_main_menu(update, context, query.from_user.username, from_button=True)
    elif data == 'bets':
        bets_menu(update, context)
    elif data == 'set_match_result':
        # Только администратор может установить результат матча
        user_id = query.from_user.id
        if is_admin(user_id):
            query.message.reply_text("Введите команду в формате: /set_match_result <match_id> <result>")
        else:
            query.message.reply_text("Доступ запрещен.")
    elif data == 'add_match':
        context.user_data['action'] = 'add_match'
        query.message.reply_text("Введите данные матча в формате: '	Tournament Id;Team1;Team2;Match Time;Status;Coefficient Win;Coefficient Draw;Coefficient Lose'")
    elif data == 'bet_history':
        show_bet_history(update, context)
    elif data == 'shop':
        show_shop(update, context)
    elif "buy_" in data:
        buy_status(update, context)
        show_shop(update, context)
    elif data == 'apologize':
        context.bot.send_message(chat_id=query.message.chat_id, text="Пацаны не извиняются!")
        # Затем отправляем новое сообщение с главным меню профиля
        show_main_menu(update, context, query.from_user.username, from_button=False)

# Обработчик текстовых сообщений
def handle_message(update, context):
    user_id = update.effective_user.id
    chat_id = update.message.chat_id  # Сохраняем chat_id
    text = update.message.text
    action = context.user_data.get('action')

    if action == 'add_tournament':
        try:
            name, teams = text.split(';')
            add_tournament_to_db(name, teams)
            context.bot.send_message(chat_id=chat_id, text="Турнир успешно добавлен.")
            show_admin_panel(update, context)  # Используйте update вместо context
        except Exception as e:
            context.bot.send_message(chat_id=chat_id, text=f"Ошибка при добавлении турнира: {e}")


    elif action == 'add_team':
        try:
            tournament_id, name = text.split(';')
            add_team_to_db(tournament_id, name)
            context.bot.send_message(chat_id=chat_id, text="Команда успешно добавлена.")
            show_admin_panel(update, context)  # Используйте update вместо context
        except Exception as e:
            context.bot.send_message(chat_id=chat_id, text=f"Ошибка при добавлении команды: {e}")


    elif action == 'add_player':
        try:
            team_id, name = text.split(';')
            add_player_to_db(team_id, name)
            context.bot.send_message(chat_id=chat_id, text="Игрок успешно добавлен.")
            show_admin_panel(update, context)  # Используйте update вместо context
        except Exception as e:
            context.bot.send_message(chat_id=chat_id, text=f"Ошибка при добавлении игрока: {e}")

    elif action == 'add_match':
        try:
            tournament_id, team1, team2, match_time, status, coef_win, coef_draw, coef_lose = text.split(';')
            add_match_to_db(tournament_id, team1, team2, match_time, status, coef_win, coef_draw, coef_lose)
            context.bot.send_message(chat_id=chat_id, text="Матч успешно добавлен.")
            show_admin_panel(update, context)  # Показать admin panel
        except Exception as e:
            context.bot.send_message(chat_id=chat_id, text=f"Ошибка при добавлении матча: {e}")

    elif action == 'view_other_profile':
        username = update.message.text
        profile(update, context, username)
        context.user_data.pop('action', None)

    context.user_data.clear()

# Функция для совершения ставок
def bet(update, context):
    args = context.args
    if len(args) != 3:
        update.message.reply_text("Используйте: /bet [ID матча] [сумма] [П1/П2/Ничья]")
        return

    user_id = update.effective_user.id
    match_id, amount, bet_type = args
    try:
        amount = float(amount)
        place_bet(user_id, int(match_id), bet_type, amount)
        update.message.reply_text(f"Ставка сделана: матч {match_id}, {bet_type}, сумма {amount}")
        # Показываем главное меню после совершения ставки
        show_main_menu(update, context, update.effective_user.username, from_button=False)
    except ValueError:
        update.message.reply_text("Пожалуйста, введите корректные значения суммы.")
        show_main_menu(update, context, update.effective_user.username, from_button=False)
    except Exception as e:
        update.message.reply_text(str(e))
        show_main_menu(update, context, update.effective_user.username, from_button=False)

# Функция для установки результата матча
def set_match_result(update, context):
    user_id = update.effective_user.id
    query = update.callback_query if hasattr(update, 'callback_query') else None

    if not is_admin(user_id):
        text = "Только администраторы могут устанавливать результат матча."
        if query:
            query.edit_message_text(text)
        else:
            context.bot.send_message(chat_id=user_id, text=text)
        return

    args = context.args
    if len(args) != 2:
        text = "Используйте: /set_match_result <match_id> <result>"
        if query:
            query.edit_message_text(text)
        else:
            context.bot.send_message(chat_id=user_id, text=text)
        return

    match_id, result = args
    try:
        match_id = int(match_id)
        update_match_result(match_id, result)
        process_match_result(match_id, result)
        success_text = f"Результат матча {match_id} установлен как {result}"
        if query:
            query.edit_message_text(success_text)
            show_admin_panel(update, context)
        else:
            context.bot.send_message(chat_id=user_id, text=success_text)
            show_admin_panel(update, context)
    except Exception as e:
        error_text = str(e)
        if query:
            query.edit_message_text(error_text)
        else:
            context.bot.send_message(chat_id=user_id, text=error_text)

# Обработчик команды /get_currency
def get_currency(update, context):
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)

    if profile:
        current_time = int(time.time())
        last_request_time = profile[5]
        if current_time - last_request_time >= 86400:  # 86400 секунд в дне
            if virtual_currency.can_request_currency(user_id):
                virtual_currency.request_currency(user_id)
                new_balance = virtual_currency.get_balance(user_id)
                update_balance(user_id, new_balance, update_request_time=True)
                message = f"Вы успешно запросили валюту. Твой новый баланс: {new_balance} {virtual_currency.name}"
            else:
                message = "Вы уже запросили валюту сегодня. Попробуйте снова завтра."
        else:
            remaining_time = 86400 - (current_time - last_request_time)
            hours, remainder = divmod(remaining_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            message = f"Вы можете запросить валюту через {int(hours)} часов, {int(minutes)} минут и {int(seconds)} секунд."
    else:
        message = "Произошла ошибка при обработке вашего запроса."

    context.bot.send_message(chat_id=user_id, text=message)
    show_main_menu(update, context, update.effective_user.username, from_button=False)

# Обработчик команды /profile
def profile(update, context, username=None):
    # Если username предоставлен, используем его, иначе - id текущего пользователя
    user_id = update.effective_user.id
    query = update.callback_query

    if username:
        target_profile = get_user_profile_by_username(username)
    else:
        target_profile = get_user_profile(user_id)

    if target_profile:
        target_username = target_profile[2]
        target_balance = target_profile[3]
        target_role = target_profile[4]
        target_status = target_profile[6]  # Добавлено получение статуса из профиля

        profile_text = (f"Профиль пользователя {target_username if target_username else user_id}:\n"
                        f"Баланс: {target_balance} {virtual_currency.name}\n"
                        f"Роль: {target_role}\n"
                        f"Статус: {target_status}")

        keyboard = [
            [InlineKeyboardButton("Подглядеть", callback_data='view_other_profile')],
            [InlineKeyboardButton("Извини", callback_data='apologize')],
            [InlineKeyboardButton("Назад", callback_data='back_to_main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if query:
            query.edit_message_text(profile_text, reply_markup=reply_markup)
        else:
            context.bot.send_message(chat_id=user_id, text=profile_text, reply_markup=reply_markup)
    else:
        message = "Профиль пользователя не найден."
        if query:
            query.edit_message_text(message)
        else:
            context.bot.send_message(chat_id=user_id, text=message)

# Функция обработчика команды /add_tournament
def add_tournament(update, context):
    user_id = update.effective_user.id
    query = update.callback_query if hasattr(update, 'callback_query') else None

    if not is_admin(user_id):
        text = "Только администраторы могут добавлять турниры."
        if query:
            query.edit_message_text(text)
        else:
            context.bot.send_message(chat_id=user_id, text=text)
        return

    if len(context.args) < 1:
        text = "Пожалуйста, укажите имя турнира."
        if query:
            query.edit_message_text(text)
        else:
            context.bot.send_message(chat_id=user_id, text=text)
        return

    name = context.args[0]
    try:
        add_tournament_to_db(name)
        success_text = "Турнир успешно добавлен."
        if query:
            query.edit_message_text(success_text)
            show_admin_panel(update, context)
        else:
            context.bot.send_message(chat_id=user_id, text=success_text)
            show_admin_panel(update, context)
    except Exception as e:
        error_text = f"Произошла ошибка: {e}"
        if query:
            query.edit_message_text(error_text)
        else:
            context.bot.send_message(chat_id=user_id, text=error_text)

# Функция обработчика команды /add_team
def add_team(update, context):
    user_id = update.effective_user.id
    query = update.callback_query if hasattr(update, 'callback_query') else None

    if not is_admin(user_id):
        text = "Только администраторы могут добавлять команды."
        if query:
            query.edit_message_text(text)
        else:
            context.bot.send_message(chat_id=user_id, text=text)
        return

    if len(context.args) < 2:
        text = "Пожалуйста, укажите ID турнира и название команды."
        if query:
            query.edit_message_text(text)
        else:
            context.bot.send_message(chat_id=user_id, text=text)
        return

    tournament_id, name = context.args[0], context.args[1]
    try:
        add_team_to_db(tournament_id, name)
        success_text = "Команда успешно добавлена."
        if query:
            query.edit_message_text(success_text)
            show_admin_panel(update, context)
        else:
            context.bot.send_message(chat_id=user_id, text=success_text)
            show_admin_panel(update, context)
    except Exception as e:
        error_text = f"Произошла ошибка: {e}"
        if query:
            query.edit_message_text(error_text)
        else:
            context.bot.send_message(chat_id=user_id, text=error_text)

# Функция обработчика команды /add_player
def add_player(update, context):
    user_id = update.effective_user.id
    query = update.callback_query

    if not is_admin(user_id):
        text = "Только администраторы могут добавлять игроков."
        if query:
            query.edit_message_text(text)
        else:
            context.bot.send_message(chat_id=user_id, text=text)
        return

    if len(context.args) < 2:
        text = "Пожалуйста, укажите ID команды и имя игрока."
        if query:
            query.edit_message_text(text)
        else:
            context.bot.send_message(chat_id=user_id, text=text)
        return

    team_id, name = context.args[0], context.args[1]
    try:
        add_player_to_db(team_id, name)
        success_text = "Игрок успешно добавлен."
        if query:
            query.edit_message_text(success_text)
            show_admin_panel(update, context)
        else:
            context.bot.send_message(chat_id=user_id, text=success_text)
            show_admin_panel(update, context)
    except Exception as e:
        error_text = f"Произошла ошибка: {e}"
        if query:
            query.edit_message_text(error_text)
        else:
            context.bot.send_message(chat_id=user_id, text=error_text)

# Функция для отображения списка текущих и предстоящих матчей
def view_matches(update, context):
    matches = get_current_matches()
    message = "Текущие и предстоящие матчи:\n"
    for match in matches:
        message += f"{match[0]}: {match[2]} vs {match[3]} в {match[4]}, Статус: {match[5]}\n"
    update.message.reply_text(message)

# Функция для покупки статусов
def buy_status(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    status_to_buy = query.data.replace("buy_", "")

    profile = get_user_profile(user_id)
    current_status = profile[6]

    if current_status == status_to_buy:
        query.edit_message_text(f"У вас уже есть статус {status_to_buy}.")
        return

    balance = virtual_currency.get_balance(user_id)
    cost = STATUSES.get(status_to_buy)
    if balance >= cost:
        new_balance = balance - cost
        update_balance(user_id, new_balance)
        update_user_status(user_id, status_to_buy)
        query.edit_message_text(f"Вы успешно приобрели статус {status_to_buy}.")
        # Отображение главного меню после покупки статуса
        show_main_menu(update, context, update.effective_user.username, from_button=False)
    else:
        query.edit_message_text("Недостаточно средств для покупки этого статуса.")


# Обновление обработчиков
dispatcher.add_handler(CommandHandler('start', start)) # /start
dispatcher.add_handler(CallbackQueryHandler(button)) # /button
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message)) # /handle_message
dispatcher.add_handler(CommandHandler('profile', profile, pass_args=True)) # /profile
dispatcher.add_handler(CommandHandler('get_currency', get_currency)) # /get_currency
dispatcher.add_handler(CommandHandler('add_tournament', add_tournament)) # /add_tournament
dispatcher.add_handler(CommandHandler('add_team', add_team)) # /add_team
dispatcher.add_handler(CommandHandler('add_player', add_player)) # /add_player
dispatcher.add_handler(CommandHandler('matches', view_matches)) # /matches
dispatcher.add_handler(CommandHandler('bet', bet, pass_args=True)) # /bet
dispatcher.add_handler(CommandHandler('set_match_result', set_match_result, pass_args=True)) # /set_match_result


# Планирование ежедневной выдачи валюты
schedule.every().day.at("00:00").do(virtual_currency.recover_currency)

# Запуск бота
updater.start_polling()

# Запуск в ожидании событий
updater.idle()