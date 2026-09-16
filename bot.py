import asyncio
import json
import os
import random
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

# ============================================
TOKEN = "8292718249:AAFpU2tpxRHJKpKicJnV1RtnS-9alJ1wPYc"
ADMIN_ID = 8570961249
BOT_USERNAME = "AngelGiveawayBot"

# Канал для проверки подписки
CHANNEL_ID = "@AngelGiveawayBot"
CHANNEL_LINK = "https://t.me/AngelGiveawayBot"

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "giveaways": {}}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

data = load_data()

def get_user(uid):
    uid = str(uid)
    if uid not in data["users"]:
        data["users"][uid] = {"refs": [], "boosts": 0, "chance": 0, "done": [], "joined": 0}
        save_data()
    return data["users"][uid]

bot = Bot(token=TOKEN)
dp = Dispatcher()

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Поделиться ссылкой", callback_data="share")],
        [InlineKeyboardButton(text="⚡ Забустить", callback_data="boost"),
         InlineKeyboardButton(text="✅ Проверить", callback_data="check")],
        [InlineKeyboardButton(text="📋 Скопировать ссылку", callback_data="copy")],
    ])

@dp.message(Command("start"))
async def start(message: types.Message):
    uid = str(message.from_user.id)
    user = get_user(uid)

    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        parts = args[1].split("_")
        if len(parts) >= 3:
            inviter_id = parts[-1]
            if inviter_id != uid and uid not in data["users"].get(inviter_id, {}).get("refs", []):
                if inviter_id in data["users"]:
                    data["users"][inviter_id]["refs"].append(uid)
                    data["users"][inviter_id]["chance"] += 5
                    save_data()

    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{message.from_user.id}"

    await message.answer(
        f"💎 **Чтобы участвовать, пригласите друзей по своей ссылке.**\n\n"
        f"Приглашено: **{len(user['refs'])}/1**\n\n"
        f"*Ваша ссылка:*\n`{ref_link}`\n\n"
        f"📢 Канал: {CHANNEL_LINK}\n"
        f"💎 Приглашайте друзей — повышает шансы на победу.",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@dp.message(Command("menu"))
async def menu(message: types.Message):
    await message.answer("🎁 **Главное меню**\n\nВыбери действие:", reply_markup=main_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "share")
async def share(callback: types.CallbackQuery):
    uid = callback.from_user.id
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{uid}"
    await callback.message.answer(f"🔗 **Твоя ссылка:**\n\n`{link}`\n\nПриглашай друзей — +5% шанс!", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "boost")
async def boost(callback: types.CallbackQuery):
    await callback.message.answer(f"⚡ Забусть канал {CHANNEL_LINK} и получи **+20% к шансам**!\n\nПосле буста нажми **✅ Проверить**.", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "check")
async def check(callback: types.CallbackQuery):
    uid = str(callback.from_user.id)
    user = get_user(uid)
    try:
        member = await bot.get_chat_member(CHANNEL_ID, int(uid))
        if member.status in ["member", "administrator", "creator"]:
            if "boost" not in user.get("done", []):
                user["chance"] += 20
                user["done"] = user.get("done", []) + ["boost"]
                save_data()
            await callback.message.answer(f"✅ **Вы участвуете!**\n\n💎 Ваш шанс: **{user['chance']}%**", parse_mode="Markdown")
        else:
            await callback.message.answer(f"❌ **Вы не подписаны!**\n\nПодпишитесь: {CHANNEL_LINK}", parse_mode="Markdown")
    except:
        await callback.message.answer(f"✅ Проверка пройдена!\n\n💎 Ваш шанс: **{user['chance']}%**", parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "copy")
async def copy_link(callback: types.CallbackQuery):
    uid = callback.from_user.id
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{uid}"
    await callback.message.answer(f"📋 Ссылка:\n`{link}`", parse_mode="Markdown")
    await callback.answer()

@dp.message(Command("newgiveaway"))
async def new_giveaway(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split(maxsplit=3)
    if len(args) < 4:
        await message.answer("Использование:\n`/newgiveaway <название> <приз> <кол-во>`", parse_mode="Markdown")
        return
    name, prize, winners = args[1], args[2], int(args[3])
    gid = str(int(time.time()))
    data["giveaways"][gid] = {"name": name, "prize": prize, "winners": winners, "created": time.strftime("%d.%m.%Y %H:%M"), "active": True}
    save_data()
    await message.answer(f"✅ Розыгрыш создан!\n\n🎁 {name}\n🏆 Приз: {prize}\n👥 Победителей: {winners}")

@dp.message(Command("endgiveaway"))
async def end_giveaway(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: `/endgiveaway <id>`", parse_mode="Markdown")
        return
    gid = args[1]
    if gid not in data["giveaways"]:
        await message.answer("❌ Не найден")
        return
    g = data["giveaways"][gid]
    users = list(data["users"].keys())
    if not users:
        await message.answer("❌ Нет участников")
        return
    weighted = []
    for u in users:
        chance = max(1, data["users"][u].get("chance", 0))
        weighted.extend([u] * chance)
    winners = list(set(random.sample(weighted, min(g["winners"], len(weighted)))))
    text = f"🎉 **Розыгрыш завершён!**\n\n🎁 {g['name']}\n🏆 Приз: {g['prize']}\n\n👑 Победители:\n"
    for w in winners:
        text += f"• [ID{w}](tg://user?id={w})\n"
    await message.answer(text, parse_mode="Markdown")
    g["active"] = False
    save_data()

@dp.message(Command("stats"))
async def stats(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    await message.answer(f"📊 Юзеров: {len(data['users'])}\n🎁 Розыгрышей: {len(data['giveaways'])}")

async def main():
    print("🚀 Angel Giveaway бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
