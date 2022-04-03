import datetime
import re

from django.utils import timezone
from telegram import (ForceReply, InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ParseMode, ReplyKeyboardMarkup,
                      ReplyKeyboardRemove, Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler)
from tgbot.handlers.onboarding import static_text
from tgbot.handlers.onboarding.keyboards import make_keyboard_for_start_command
from tgbot.handlers.utils.info import extract_user_data_from_update
from tgbot.models import Allergy, Subscribe, User


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
    u, created = User.get_user_and_created(update, context)

    # if created:
    update.message.reply_text(
        'Здравствуйте, для продолжения необходимо оформить подписку.',
        reply_markup=ReplyKeyboardRemove()
    )

    return get_allergy(update, context)

    # reply_keyboard = list(keyboard_row_divider(
    #     ['🍽 Получить блюдо дня',
    #      '👤 Профиль',
    #      '📨 Подписка'],
    #     2
    # ))

    # update.message.reply_text(
    #     'Выберите действие:',
    #     parse_mode=ParseMode.MARKDOWN_V2,
    #     reply_markup=ReplyKeyboardMarkup(
    #         reply_keyboard,
    #         # one_time_keyboard=True,
    #         input_field_placeholder='',
    #         resize_keyboard=True,)
    # )
    # return 'process_user_selection'


def process_user_selection(update: Update, context: CallbackContext):
    text = update.message.text

    if text == '🍽 Получить блюдо дня':
        update.message.reply_text('🍽 Кушайте манную кашу.')
        return choosing_user_actions(update, context)

    elif text == '👤 Профиль':
        update.message.reply_text('👤 Данные Вашего профиля.')
        return choosing_user_actions(update, context)

    elif text == '📨 Подписка':
        update.message.reply_text('📨 Данные Вашей подписки.')
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
        user.phone = update.message.text
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
    pass


def get_number_of_person(update: Update, context: CallbackContext):
    """"""
    pass


def get_menu_type(update: Update, context: CallbackContext):
    """"""
    pass


def get_duration(update: Update, context: CallbackContext):
    """"""
    pass


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
            'get_duration': [
                MessageHandler(
                    Filters.text & ~Filters.command,
                    get_duration
                )
            ],
            # "process_answer_yes_no": [
            #     MessageHandler(
            #         Filters.text & ~Filters.command,
            #         process_answer_yes_no
            #     )
            # ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
