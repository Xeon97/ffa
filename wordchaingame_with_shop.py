
# -*- coding: utf-8 -*-
# meta developer: @YourUsername
# meta banner: https://example.com/banner.jpg

from telethon import events
from .. import loader, utils
from datetime import datetime, timedelta
import random

class WordChainGameMod(loader.Module):
    """Модуль для игры 'Словесная цепочка' с профилями, магазином и бонусами"""
    strings = {"name": "WordChainGame"}

    def __init__(self):
        self.active_games = {}
        self.words_used = set()
        self.profiles = {}

    async def client_ready(self, client, db):
        self.client = client

    async def startchaincmd(self, message):
        """Начать игру 'Словесная цепочка'"""
        chat_id = utils.get_chat_id(message)
        if chat_id in self.active_games:
            await message.edit("Игра уже идет!")
            return

        self.active_games[chat_id] = {
            "last_word": None,
            "players": {}
        }
        self.words_used.clear()
        await message.edit(
            "🎮 Игра 'Словесная цепочка' началась!\n\nПервый игрок, напишите любое слово!"
        )

    @loader.unrestricted
    async def watcher(self, message):
        chat_id = utils.get_chat_id(message)
        if chat_id not in self.active_games:
            return

        game = self.active_games[chat_id]
        text = message.text.strip().lower()
        user_id = message.sender_id

        if user_id not in self.profiles:
            self.profiles[user_id] = {
                "points": 0,
                "inventory": {"skip_turn": 0, "transfer_turn": 0},
                "last_bonus_time": datetime.min
            }

        if game["last_word"]:
            last_letter = game["last_word"][-1]
            if text[0] != last_letter:
                await message.respond(f"❌ Слово должно начинаться на букву '{last_letter.upper()}'!")
                return

        if text in self.words_used:
            await message.respond("❌ Это слово уже использовалось!")
            return

        self.words_used.add(text)
        game["last_word"] = text
        game["players"][user_id] = game["players"].get(user_id, 0) + 1

        self.profiles[user_id]["points"] += 1

        await message.respond(
            f"✅ {text.capitalize()} принято! Ваш ход записан.\n\nСледующий игрок должен придумать слово на букву '{text[-1].upper()}'."
        )

    async def stopchaincmd(self, message):
        """Остановить игру 'Словесная цепочка'"""
        chat_id = utils.get_chat_id(message)
        if chat_id not in self.active_games:
            await message.edit("Игра не запущена!")
            return

        game = self.active_games.pop(chat_id)
        results = "\n".join(
            [
                f"{(await self.client.get_entity(uid)).first_name}: {score} слов"
                for uid, score in game["players"].items()
            ]
        )
        await message.edit(f"Игра завершена! Итоги:\n\n{results}")

    async def profilecmd(self, message):
        """Посмотреть профиль игрока"""
        user_id = message.sender_id
        profile = self.profiles.get(user_id, {"points": 0, "inventory": {}, "last_bonus_time": datetime.min})
        inventory = profile["inventory"]
        await message.edit(
            f"📊 Ваш профиль:\n"
            f"• Очки: {profile['points']}\n"
            f"• Пропуски хода: {inventory.get('skip_turn', 0)}\n"
            f"• Передачи хода: {inventory.get('transfer_turn', 0)}"
        )

    async def shopcmd(self, message):
        """Посмотреть магазин"""
        await message.edit(
            "🛒 Магазин:\n"
            "1. Пропуск хода — 5 очков (команда: .buy skip_turn)\n"
            "2. Передача хода — 10 очков (команда: .buy transfer_turn)"
        )

    async def buycmd(self, message):
        """Купить предмет в магазине"""
        args = utils.get_args_raw(message)
        user_id = message.sender_id

        if user_id not in self.profiles:
            self.profiles[user_id] = {
                "points": 0,
                "inventory": {"skip_turn": 0, "transfer_turn": 0},
                "last_bonus_time": datetime.min
            }

        profile = self.profiles[user_id]

        if args == "skip_turn":
            if profile["points"] >= 5:
                profile["points"] -= 5
                profile["inventory"]["skip_turn"] += 1
                await message.edit("✅ Вы купили пропуск хода!")
            else:
                await message.edit("❌ У вас недостаточно очков!")
        elif args == "transfer_turn":
            if profile["points"] >= 10:
                profile["points"] -= 10
                profile["inventory"]["transfer_turn"] += 1
                await message.edit("✅ Вы купили передачу хода!")
            else:
                await message.edit("❌ У вас недостаточно очков!")
        else:
            await message.edit("❌ Неверный предмет! Используйте .shop, чтобы посмотреть доступные предметы.")

    async def bonuscmd(self, message):
        """Получить бонус (раз в час)"""
        user_id = message.sender_id

        if user_id not in self.profiles:
            self.profiles[user_id] = {
                "points": 0,
                "inventory": {"skip_turn": 0, "transfer_turn": 0},
                "last_bonus_time": datetime.min
            }

        profile = self.profiles[user_id]
        now = datetime.now()

        if now - profile["last_bonus_time"] >= timedelta(hours=1):
            bonus_points = random.randint(1, 5)
            profile["points"] += bonus_points
            profile["last_bonus_time"] = now
            await message.edit(f"🎉 Вы получили {bonus_points} бонусных очков!")
        else:
            remaining_time = timedelta(hours=1) - (now - profile["last_bonus_time"])
            await message.edit(f"❌ Бонус уже получен. Попробуйте через {remaining_time.seconds // 60} минут.")
