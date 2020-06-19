#!/usr/bin/env python
# -*- coding: utf-8 -*-




from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Bot, User
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, Filters
import logging
from functools import partial
from main import extract_video_id, get_available_lang, fetch_man_chosen, fetch_auto_chosen
from Token import TOKEN


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


FIRST, SECOND = range(2)

bot = Bot(TOKEN)

VIDEO_ID = ''
LANGS = ''
LAN_CODES = ''
STATE_LANG = ''
conv_handler = {}

def start(update, context):
    """Send message on `/start`."""
    user = update.message.from_user
    logger.info("User %s started the conversation.", user.first_name)
    update.message.reply_text('Шалом, я допоможу тобі скочати субтитри з ютуба.\n Закинь сюди силкуя.🐱‍')


def entry_dialog(update, context):
    global VIDEO_ID, LANGS, LAN_CODES, STATE_LANG, conv_handler
    VIDEO_ID = extract_video_id(update.message.text)
    LANGS, LAN_CODES = get_available_lang(VIDEO_ID)
    if not LANGS:
        update.message.reply_text("Для цього відео субтитри недоступні")
    else:
        print(f"LANGS: {LANGS}")
        print(f"LAN_codes: {LAN_CODES}")
        reply_keyboard = form_keyboard(LANGS, LAN_CODES) + [[InlineKeyboardButton("Автоматично створені", callback_data="auto")]]

        reply_markup = InlineKeyboardMarkup(reply_keyboard)
        # Send message with text and appended InlineKeyboard\
        update.message.reply_text(
            "Виберіть субтири",
            reply_markup=reply_markup
        )
        print("ETAP 1 DONE")
        for lan in LAN_CODES:
            dp.add_handler(CallbackQueryHandler(partial(push_manual, lan_code=lan), pattern=f'^{lan}$'))
        dp.add_handler(CallbackQueryHandler(partial(push_auto, lan_code='uk'), pattern="^auto$"))

    return FIRST


def form_keyboard(lags, lancodes):
    res = []
    for lan, code in zip(lags, lancodes):
        res.append([InlineKeyboardButton(lan, callback_data=code)])
    return res


def push_manual(update, context, lan_code=None):
    query = update.callback_query
    query.answer()
    query.edit_message_text("Завантаження")
    print(f"CHAT_ID {update}")
    print(f"CHAT_ID {query.message.chat_id}")
    bot.send_document(query.message.chat_id, document=open(fetch_man_chosen(VIDEO_ID, lan_code), 'rb'))
    query.edit_message_text("Готово")

    return SECOND


def push_auto(update, context, lan_code=None):
    query = update.callback_query
    query.answer()
    res = fetch_auto_chosen(VIDEO_ID, lan_code)
    if res:
        query.edit_message_text("Завантаження")
        bot.send_document(query.message.chat_id, document=open(res, 'rb'))
        query.edit_message_text("Готово")
    else:
        query.edit_message_text("Немає доступних субтитрів")
    return SECOND


def end(update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        text="До зустрічі!"
    )
    return ConversationHandler.END


def main():
    global dp, conv_handler
    yt_video_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?(?P<id>[A-Za-z0-9\-=_]{11})'
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    #dp.add_handler(MessageHandler(Filters.regex(yt_video_regex), get_video_id))

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.regex(yt_video_regex), entry_dialog)],
        states={
            FIRST: [],
            SECOND: [CallbackQueryHandler(end)]

        },
        fallbacks=[MessageHandler(Filters.regex(yt_video_regex), entry_dialog)]
    )

    dp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()