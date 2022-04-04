import re

from telegram import (ForceReply,
                      KeyboardButton, LabeledPrice, ParseMode,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove, Update)
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          Filters, MessageHandler)
from tgbot.models import Allergy, MenuType, Subscribe, User
from dtb.settings import PROVIDER_TOKEN


def keyboard_row_divider(full_list, row_width=2):
    """Divide list into rows for keyboard"""
    for i in range(0, len(full_list), row_width):
        yield full_list[i: i + row_width]


def escape_characters(text: str) -> str:
    """Screen characters for Markdown V2"""
    text = text.replace('\\', '')

    characters = ['.', '+']
    for character in characters:
        text = text.replace(character, f'\{character}')
    return text


def start_handler(update: Update, context: CallbackContext) -> str:
    if 'allergy_ids' not in context.user_data:
        context.user_data['allergy_ids'] = list()

    return choosing_user_actions(update, context)


def choosing_user_actions(update: Update, context: CallbackContext):
    user, created = User.get_user_and_created(update, context)

    if created:
        update.message.reply_text(
            'Здравствуйте, для продолжения необходимо заполнить профиль.',
            reply_markup=ReplyKeyboardRemove()
        )
        return get_surname(update, context)
    else:
        subscribe = Subscribe.objects.filter(user=user).first()

        if subscribe and subscribe.subscription_paid:
            reply_keyboard = list(keyboard_row_divider(
                ['🍽 Получить блюдо дня',
                 '👤 Профиль',
                 '📨 Подписка'],
                1
            ))

            update.message.reply_text(
                'Выберите действие:',
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard,
                    input_field_placeholder='',
                    resize_keyboard=True,)
            )
            return 'process_user_selection'
        else:
            update.message.reply_text(
                'Для продолжения необходимо оформить подписку.',
                reply_markup=ReplyKeyboardRemove()
            )
            return get_allergy(update, context)


def process_user_selection(update: Update, context: CallbackContext):
    text = update.message.text

    user = User.get_user(update, context)
    subscribe = Subscribe.objects.get(user=user)

    if text == '🍽 Получить блюдо дня':
        update.message.reply_text(f'🍽 {subscribe.get_subscribe_dish()}')
        return choosing_user_actions(update, context)

    elif text == '👤 Профиль':
        update.message.reply_text(
            f'{user.get_description()}',
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return choosing_user_actions(update, context)

    elif text == '📨 Подписка':
        update.message.reply_text(
            '📨 Ваша подписка:\n'
            f'{subscribe.get_subscribe_description()}'
        )
        return choosing_user_actions(update, context)


def get_surname(update: Update, context: CallbackContext):
    """Получение фамилии."""
    update.message.reply_text(
        'Ваша фамилия:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='Фамилия',
                                selective=True)
    )
    return 'get_user_name'


def get_user_name(update: Update, context: CallbackContext):
    """Получение имени."""
    context.user_data['last_name'] = update.message.text

    update.message.reply_text(
        'Ваше имя:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='Имя',
                                selective=True)
    )
    return 'select_input_phone'


def select_input_phone(update: Update, context: CallbackContext):
    """Отображение способа получения номера телефона."""
    context.user_data['first_name'] = update.message.text

    enter_phone = KeyboardButton('Ввести номер вручную ☎️',
                                 request_contact=False)
    send_phone = KeyboardButton('Отправить свой контакт ☎️',
                                request_contact=True)

    reply_keyboard = list(keyboard_row_divider([enter_phone, send_phone], 1))

    update.message.reply_text(
        'Каким способом ввести номер телефона ?',
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            one_time_keyboard=True,
            input_field_placeholder='',
            resize_keyboard=True,)
    )

    return 'get_telephone'


def get_telephone(update: Update, context: CallbackContext):
    """Получение номера телефона."""
    contact = update.effective_message.contact

    if contact:
        contact = update.effective_message.contact
        update.message.text = contact.phone_number
        return save_user_data(update, context)

    update.message.reply_text(
        'Ваш телефон:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='Телефон',
                                selective=True)
    )
    return 'save_user_data'


def save_user_data(update: Update, context: CallbackContext):
    """Сохранение данных пользователя"""
    user = User.get_user(update, context)

    if context.user_data['last_name']:
        user.last_name = context.user_data['last_name']
    if context.user_data['first_name']:
        user.first_name = context.user_data['first_name']
    if update.message.text:
        user.phone = escape_characters(update.message.text)

    user.save()

    update.message.reply_text('Данные профиля сохранены.',
                              reply_markup=ReplyKeyboardRemove())

    return choosing_user_actions(update, context)


def get_allergy(update: Update, context: CallbackContext):
    """"""
    reply_keyboard = list()
    reply_keyboard.append(['💾 Сохранить'])

    for allergy_name in Allergy.objects.all():
        mark = ''

        if allergy_name.id in context.user_data['allergy_ids']:
            mark = '☑️'

        reply_keyboard.append(
            [f'{allergy_name.id}. {allergy_name.name} {mark}']
        )

    update.message.reply_text(
        'Если у Вас есть аллергия, выберите:',
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            # one_time_keyboard=True,
            input_field_placeholder='',
            resize_keyboard=True,)
    )
    return 'process_allergies_selection'


def process_allergies_selection(update: Update, context: CallbackContext):
    text = update.message.text

    if text == '💾 Сохранить':
        return get_number_of_meals(update, context)

    else:
        allergy_id = int(re.sub(r'[^0-9]', '', text))

        if allergy_id in context.user_data['allergy_ids']:
            context.user_data['allergy_ids'].remove(allergy_id)
        else:
            context.user_data['allergy_ids'].append(allergy_id)

        return get_allergy(update, context)


def get_number_of_meals(update: Update, context: CallbackContext):
    """"""
    update.message.reply_text(
        'Количество приёмов пищи за день:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='1 - 3',
                                selective=True)
    )
    return 'get_number_of_person'


def get_number_of_person(update: Update, context: CallbackContext):
    """"""
    context.user_data['number_of_meals'] = update.message.text

    update.message.reply_text(
        'Количество персон:',
        reply_markup=ForceReply(force_reply=True,
                                input_field_placeholder='1 - 4',
                                selective=True)
    )
    return 'get_menu_type'


def get_menu_type(update: Update, context: CallbackContext):
    """"""
    context.user_data['number_of_person'] = update.message.text

    reply_keyboard = list()

    for menu_type in MenuType.objects.all():
        reply_keyboard.append([f'{menu_type.id}. {menu_type.name}'])

    update.message.reply_text(
        'Выберите тип меню:',
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            # one_time_keyboard=True,
            input_field_placeholder='',
            resize_keyboard=True,)
    )

    return 'process_menu_type_selection'


def process_menu_type_selection(update: Update, context: CallbackContext):
    text = update.message.text

    if text:
        menu_type_id = int(re.sub(r'[^0-9]', '', text))

        context.user_data['menu_type'] = menu_type_id

        return get_duration(update, context)
    else:
        return get_menu_type(update, context)


def get_duration(update: Update, context: CallbackContext):
    """"""
    reply_keyboard = list(keyboard_row_divider(
        ['1️⃣',
         '3️⃣',
         '6️⃣',
         '1️⃣2️⃣'],
        2
    ))

    update.message.reply_text(
        'Выберите  длительность подписки в месяцах:',
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard,
            # one_time_keyboard=True,
            input_field_placeholder='',
            resize_keyboard=True,)
    )

    return 'process_duration_selection'


def process_duration_selection(update: Update, context: CallbackContext):
    text = update.message.text

    duration = 0

    if text == '1️⃣':
        duration = 1
    elif text == '3️⃣':
        duration = 3
    elif text == '6️⃣':
        duration = 6
    elif text == '1️⃣2️⃣':
        duration = 12
    else:
        return get_duration(update, context)

    context.user_data['duration'] = duration

    return start_invoice(update, context)


def start_invoice(update: Update, context: CallbackContext) -> None:
    """Send an invoice"""
    duration = int(context.user_data['duration'])
    price = (duration * 100) * 100
    chat_id = update.message.chat_id
    title = 'Подписка на FoodPlan8'
    description = f'Подписка на FoodPlan8: {duration} месяцев.'
    payload = "FoodPlan8"
    provider_token = PROVIDER_TOKEN
    currency = "rub"
    prices = [LabeledPrice("FoodPlan8", price)]

    update.message.reply_text('Мы ожидаем от Вас оплату...',
                              reply_markup=ReplyKeyboardRemove())

    context.bot.send_invoice(
        chat_id, title, description, payload, provider_token, currency, prices
    )


def precheckout_callback(update: Update, context: CallbackContext):
    """Answer the PreQecheckoutQuery"""
    query = update.pre_checkout_query
    if query.invoice_payload != 'FoodPlan8':
        query.answer(ok=False, error_message="Something went wrong...")
    else:
        query.answer(ok=True)


def successful_payment_callback(update: Update, context: CallbackContext):
    """Confirms the successful payment"""
    update.message.reply_text('Мы получили от Вас оплату',
                              reply_markup=ReplyKeyboardRemove())

    user = User.get_user(update, context)

    subscribe = Subscribe(user=user)
    subscribe.number_of_meals = context.user_data['number_of_meals']
    subscribe.number_of_person = context.user_data['number_of_person']

    menu_type = MenuType.objects.get(pk=context.user_data['menu_type'])
    subscribe.menu_type = menu_type

    subscribe.duration = context.user_data['duration']

    subscribe.subscription_paid = True

    subscribe.save()

    for allergy_id in context.user_data['allergy_ids']:
        subscribe.allergy.add(
            Allergy.objects.get(pk=allergy_id)
        )

    return choosing_user_actions(update, context)


def cancel(update: Update, context: CallbackContext):
    """Прекращает работу очереди разговора."""
    return ConversationHandler.END


def get_handler_person():
    """Возвращает обработчик разговоров."""
    return ConversationHandler(
        entry_points=[CommandHandler('start', start_handler)],
        states={
            # "inline_button_agreement": [
            #     CallbackQueryHandler(
            #         inline_button_agreement
            #     )
            # ],
            'choosing_user_actions': [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    choosing_user_actions
                )
            ],
            'process_user_selection': [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    process_user_selection
                )
            ],
            'get_surname': [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    get_surname
                )
            ],
            'get_user_name': [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    get_user_name
                )
            ],
            'select_input_phone': [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    select_input_phone
                )
            ],
            'get_telephone': [
                MessageHandler(
                    (Filters.text | Filters.contact) & ~Filters.command,
                    get_telephone
                )
            ],
            'save_user_data': [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    save_user_data
                )
            ],
            'get_allergy': [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    get_allergy
                )
            ],
            'process_allergies_selection': [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    process_allergies_selection
                )
            ],
            'get_number_of_meals': [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    get_number_of_meals
                )
            ],
            'get_number_of_person': [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    get_number_of_person
                )
            ],
            'get_menu_type': [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    get_menu_type
                )
            ],
            'process_menu_type_selection': [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    process_menu_type_selection
                )
            ],
            'get_duration': [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    get_duration
                )
            ],
            'process_duration_selection': [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    process_duration_selection
                )
            ],
        },
        fallbacks=[
            MessageHandler(Filters.successful_payment,
                           successful_payment_callback),
            CommandHandler('cancel', cancel)
        ]
    )
