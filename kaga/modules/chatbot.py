import html
# AI module using Intellivoid's Coffeehouse API by @TheRealPhoenix
from time import sleep, time

import kaga.modules.sql.chatbot_sql as sql
from coffeehouse.api import API
from coffeehouse.exception import CoffeeHouseError as CFError
from coffeehouse.lydia import LydiaAI
from kaga import AI_API_KEY, OWNER_ID, SUPPORT_CHAT, dispatcher
from kaga.modules.helper_funcs.chat_status import user_admin
from kaga.modules.helper_funcs.filters import CustomFilters
from kaga.modules.helper_funcs.alternate import typing_action
from kaga.modules.log_channel import gloggable
from telegram import Update
from telegram.error import BadRequest, RetryAfter, Unauthorized
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler)
from telegram.utils.helpers import mention_html

CoffeeHouseAPI = API(AI_API_KEY)
api_client = LydiaAI(CoffeeHouseAPI)


@typing_action
@user_admin
@gloggable
def add_chat(update, context):
    global api_client
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    is_chat = sql.is_chat(chat.id)
    if not is_chat:
        ses = api_client.create_session()
        ses_id = str(ses.id)
        expires = str(ses.expires)
        sql.set_ses(chat.id, ses_id, expires)
        msg.reply_text("AI berhasil diaktifkan untuk obrolan ini!")
        message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#AI_ENABLED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        )
        return message
    else:
        msg.reply_text("AI sudah diaktifkan untuk obrolan ini!")
        return ""


@typing_action
@user_admin
@gloggable
def remove_chat(update, context):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    is_chat = sql.is_chat(chat.id)
    if not is_chat:
        msg.reply_text("AI tidak diaktifkan di sini sejak awal!")
        return ""
    else:
        sql.rem_chat(chat.id)
        msg.reply_text("AI berhasil dinonaktifkan!")
        message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#AI_DISABLED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        )
        return message


def check_message(context, message):
    reply_msg = message.reply_to_message
    if message.text.lower() == "Cutiepii":
        return True
    if reply_msg:
        if reply_msg.from_user.id == context.bot.get_me().id:
            return True
    else:
        return False


@typing_action
def chatbot(update, context):
    global api_client
    msg = update.effective_message
    chat_id = update.effective_chat.id
    is_chat = sql.is_chat(chat_id)
    bot = context.bot
    if not is_chat:
        return
    if msg.text and not msg.document:
        if not check_message(context, msg):
            return
        sesh, exp = sql.get_ses(chat_id)
        query = msg.text
        try:
            if int(exp) < time():
                ses = api_client.create_session()
                ses_id = str(ses.id)
                expires = str(ses.expires)
                sql.set_ses(chat_id, ses_id, expires)
                sesh, exp = sql.get_ses(chat_id)
        except ValueError:
            pass
        try:
            bot.send_chat_action(chat_id, action='typing')
            rep = api_client.think_thought(sesh, query)
            sleep(0.3)
            msg.reply_text(rep, timeout=60)
        except CFError as e:
            bot.send_message(OWNER_ID,
                             f"Kesalahan Chatbot: {e} terjadi di {chat_id}!")


@typing_action
def list_chatbot_chats(update, context):
    chats = sql.get_all_chats()
    text = "<b>AI-Enabled Chats</b>\n"
    for chat in chats:
        try:
            x = context.bot.get_chat(int(*chat))
            name = x.title if x.title else x.first_name
            text += f"• <code>{name}</code>\n"
        except BadRequest:
            sql.rem_chat(*chat)
        except Unauthorized:
            sql.rem_chat(*chat)
        except RetryAfter as e:
            sleep(e.retry_after)
    update.effective_message.reply_text(text, parse_mode="HTML")


__help__ = f"""
Chatbot menggunakan API CoffeeHouse dan memungkinkan Cutiepii untuk berbicara dan memberikan pengalaman obrolan grup yang lebih interaktif.
*Perintah:* 
*Khusus Admin:*
 • `/addchat`*:* Mengaktifkan mode Chatbot di obrolan.
 • `/rmchat`*:* Menonaktifkan mode Chatbot di obrolan.
Melaporkan bug di @{SUPPORT_CHAT}
*Powered by CoffeeHouse* (https://coffeehouse.intellivoid.net/) from @Intellivoid
"""

ADD_CHAT_HANDLER = CommandHandler("addchat", add_chat, run_async=True)
REMOVE_CHAT_HANDLER = CommandHandler("rmchat", remove_chat, run_async=True)
CHATBOT_HANDLER = MessageHandler(
    Filters.text & (~Filters.regex(r"^#[^\s]+") & ~Filters.regex(r"^!")
                    & ~Filters.regex(r"^\/")), chatbot, run_async=True)
LIST_CB_CHATS_HANDLER = CommandHandler(
    "listaichats", list_chatbot_chats, filters=CustomFilters.dev_filter, run_async=True)
# Filters for ignoring #note messages, !commands and sed.

dispatcher.add_handler(ADD_CHAT_HANDLER)
dispatcher.add_handler(REMOVE_CHAT_HANDLER)
dispatcher.add_handler(CHATBOT_HANDLER)
dispatcher.add_handler(LIST_CB_CHATS_HANDLER)

__mod_name__ = "Chatbot"
__command_list__ = ["addchat", "rmchat", "listaichats"]
__handlers__ = [
    ADD_CHAT_HANDLER, REMOVE_CHAT_HANDLER, CHATBOT_HANDLER,
    LIST_CB_CHATS_HANDLER
]
