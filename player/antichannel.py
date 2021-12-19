import os
import config
import motor.motor_asyncio
import config
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class Database:
    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.col = self.db.users

    async def add_chat_list(self, chat_id, ch_id=None):
        get_chat = await self.is_chat_exist(chat_id)
        if get_chat:
            chat_list = list(get_chat.get("chats"))
            if ch_id != None and int(ch_id) in chat_list:
                return True, f"{ch_id} already in white list."
            elif ch_id == None:
                return False,""
            elif ch_id is not None:
                chat_list.append(int(ch_id))
                await self.col.update_one({'id': chat_id}, {'$set': {'chats': chat_list}})
                return True, f"{ch_id}, added into white list"
        a_chat = {"id":int(chat_id),"chats":[ch_id]}
        await self.col.insert_one(a_chat)
        return False,""

    async def is_chat_exist(self, id):
        user = await self.col.find_one({'id': int(id)})
        return user if user else False

    async def get_chat_list(self, chat_id):
        get_chat = await self.is_chat_exist(chat_id)
        if get_chat:
            return get_chat.get("chats",[])
        else:
            return False

    async def del_chat_list(self, chat_id, ch_id=None):
        get_chat = await self.is_chat_exist(chat_id)
        if get_chat:
            chat_list = list(get_chat.get("chats"))
            if ch_id != None and ch_id in chat_list:
                chat_list.remove(int(ch_id))
                await self.col.update_one({'id': chat_id}, {'$set': {'chats': chat_list}})
                return True, f"{ch_id}, removed from white list"
            elif int(ch_id) not in chat_list:
                return True, f"{ch_id}, not found in white list."

    async def delete_chat_list(self, chat_id):
        await self.col.delete_many({"id": int(chat_id)})

DB_URL = config.DB_URL
DB_NAME = config.DB_NAME

db = Database(DB_URL, DB_NAME)

async def whitelist_check(chat_id,channel_id=0):
    if not await db.is_chat_exist(chat_id):
        return True
    _chat_list = await db.get_chat_list(chat_id)
    if int(channel_id) in _chat_list:
        return True
    else:
        return False

async def get_channel_id_from_input(bot, message):
    try:
        a_id = message.text.split(" ",1)[1]
    except:
        await message.reply_text("Send cmd along with channel id")
        return False
    if not str(a_id).startswith("-"):
        try:
            a_id = await bot.get_chat(a_id)
            a_id = a_id.id
        except:
            await message.reply_text("Inavalid channel id")
            return False
    return a_id



custom_message_filter = filters.create(lambda _, __, message: False if message.forward_from_chat or message.from_user else True)
custom_chat_filter = filters.create(lambda _, __, message: True if message.sender_chat else False)

@Client.on_message(custom_message_filter & filters.group & custom_chat_filter)
async def main_handler(bot, message):
    chat_id = message.chat.id
    a_id = message.sender_chat.id
    if (await whitelist_check(chat_id, a_id)):
        return
    try:
        res = await bot.kick_chat_member(chat_id, a_id)
    except:
        return await message.reply_text("Promote me as admin, to use me")
    if res:
        mention = f"@{message.sender_chat.username}" if message.sender_chat.username else message.chat_data.title
        await message.reply_text(text=f"{mention} has been banned.\n\n💡 He can write only with his profile but not through other channels.",
                                 reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Unban", callback_data=f"unban_{chat_id}_{a_id}")]]),
                              )
    await message.delete()


@Client.on_callback_query()
async def cb_handler(bot, query):
    cb_data = query.data
    if cb_data.startswith("unban_"):
        an_id = cb_data.split("_")[-1]
        chat_id = cb_data.split("_")[-2]
        user = await bot.get_chat_member(chat_id, query.from_user.id)
        if user.status == "creator" or user.status == "administrator":
            pass
        else:
            return await query.answer("This Message is Not For You!", show_alert=True)
        await bot.resolve_peer(an_id)
        res = await query.message.chat.unban_member(an_id)
        chat_data = await bot.get_chat(an_id)
        mention = f"@{chat_data.username}" if chat_data.username else chat_data.title
        if res:
            await query.message.reply_text(f"{mention} has been unbanned by {query.from_user.mention}")
            await query.message.edit_reply_markup(reply_markup=None)


@Client.on_message(filters.command(["antichannel"]) & filters.group)
async def cban_handler(bot, message):
    chat_id = message.chat.id
    try:
        saf = message.text.split(" ",1)[1]
    except:
        await message.reply_text("Send cmd along with on/off")
        return
    if saf == 'on':
        await db.add_chat_list(chat_id)
        await message.reply_text("Antichannel enabled!")
    elif saf == 'off':
        await db.delete_chat_list(chat_id)
        await message.reply_text("Antichannel disabled!")


@Client.on_message(filters.command(["add_whitelist"]) & filters.group)
async def add_whitelist_handler(bot, message):
    chat_id = message.chat.id
    user = await bot.get_chat_member(chat_id, message.from_user.id)
    if user.status == "creator" or user.status == "administrator":
        pass
    else:
        return
    try:
        a_id = await get_channel_id_from_input(bot, message)
        if not a_id:
            return
        if (await whitelist_check(chat_id, a_id)):
            return await message.reply_text("Channel Id already found in whitelist")
        chk,msg = await db.add_chat_list(chat_id, a_id)
        if chk and msg != "":
            await message.reply_text(msg)
        else:
            await message.reply_text("Something wrong happend")
    except Exception as e:
        print(e)


@Client.on_message(filters.command(["del_whitelist"]) & filters.group)
async def del_whitelist_handler(bot, message):
    chat_id = message.chat.id
    user = await bot.get_chat_member(chat_id, message.from_user.id)
    if user.status == "creator" or user.status == "administrator":
        pass
    else:
        return
    try:
        a_id = await get_channel_id_from_input(bot, message)
        if not a_id:
            return
        if not (await whitelist_check(chat_id, a_id)):
            return await message.reply_text("Channel Id not found in whitelist")
        chk,msg = await db.del_chat_list(message.chat.id, a_id)
        if chk:
            await message.reply_text(msg)
        else:
            await message.reply_text("Something wrong happend")
    except Exception as e:
        print(e)


@Client.on_message(filters.command(["show_whitelist"]) & filters.group)
async def del_whitelist_handler(bot, message):
    chat_id = message.chat.id
    user = await bot.get_chat_member(chat_id, message.from_user.id)
    if user.status == "creator" or user.status == "administrator":
        pass
    else:
        return
    show_wl = await db.get_chat_list(chat_id)
    if show_wl:
        await message.reply_text(f"This ids found in whitelist\n\n{show_wl}")
    else:
        await message.reply_text("White list not found.")
 
