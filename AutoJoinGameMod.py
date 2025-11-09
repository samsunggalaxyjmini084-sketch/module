# meta developer: @Androfon_AI
# meta name: AutoJoinGame
# meta version: 1.8.2

import asyncio
import re
import random
from telethon.tl.types import Message
from telethon import events
from .. import loader, utils


@loader.tds
class AutoJoinGameMod(loader.Module):
    """Модуль для автоматического нажатия кнопки при наборе в игру"""

    strings = {
        "name": "AutoJoinGame",
        "_cls_doc": "Модуль для автоматического нажатия кнопки при наборе в игру",
        "enabled": "✅ Автовход в игру включен. <emoji document_id=5339236706522511703>🌟</emoji>",
        "disabled": "❌ Автовход в игру выключен. <emoji document_id=5319049445403286578>👎</emoji>",
        "status": "📊 Статус автовхода:\nСтатус: {status} <emoji document_id=5931621672846103580>💫</emoji>\nЗадержка (секунды): {delay_display} <emoji document_id=5778158488450502097>⏲</emoji>\nБоты для отслеживания: {bot_ids} <emoji document_id=5931415565955503486>🤖</emoji>\nРазрешенные чаты: {allowed_chats} <emoji document_id=5886666250158870040>💬</emoji>",
        "error": "❌ Ошибка при нажатии кнопки: {} <emoji document_id=5879813604068298387>❗️</emoji>",
        "no_button": "⚠️ Кнопка не найдена под сообщением <emoji document_id=5881702736843511327>⚠️</emoji>",
        "help_text": """🤖 AutoJoinGame - Помощь <emoji document_id=5931614414351372818>🤖</emoji>

🎮 Команды:
.ajgon - Включить автовход в игру
.ajgoff - Выключить автовход в игру
.ajgstatus - Показать статус
.ajghelp - Эта справка
.ajgtest - Проверить последнее сообщение с набором в текущем чате

⚙️ Как работает:
Ждет сообщение "Ведётся набор в игру" от указанных ботов (или от любого бота, если список пуст).
Автоматически переходит по URL кнопки и отправляет /start.
Работает только когда включен.

💡 Настройки:
В конфиге модуля можно изменить задержку(и) перед нажатием. Если указано несколько значений, будет выбрано случайное.
Можно указать список ID ботов, от которых ожидать сообщения о наборе.
Можно указать список ID чатов, в которых модуль будет активен. Если список пуст, модуль будет работать во всех чатах.""",
    }

    strings_ru = {
        "_cls_doc": "Модуль для автоматического нажатия кнопки при наборе в игру",
        "enabled": "✅ Автовход в игру включен. <emoji document_id=5339236706522511703>🌟</emoji>",
        "disabled": "❌ Автовход в игру выключен. <emoji document_id=5319049445403286578>👎</emoji>",
        "status": "📊 Статус автовхода:\nСтатус: {status} <emoji document_id=5931621672846103580>💫</emoji>\nЗадержка (секунды): {delay_display} <emoji document_id=5778158488450502097>⏲</emoji>\nБоты для отслеживания: {bot_ids} <emoji document_id=5931415565955503486>🤖</emoji>\nРазрешенные чаты: {allowed_chats} <emoji document_id=5886666250158870040>💬</emoji>",
        "error": "❌ Ошибка при нажатии кнопки: {} <emoji document_id=5879813604068298387>❗️</emoji>",
        "no_button": "⚠️ Кнопка не найдена под сообщением <emoji document_id=5881702736843511327>⚠️</emoji>",
        "help_text": """🤖 AutoJoinGame - Помощь <emoji document_id=5931614414351372818>🤖</emoji>

🎮 Команды:
.ajgon - Включить автовход в игру
.ajgoff - Выключить автовход в игру
.ajgstatus - Показать статус
.ajghelp - Эта справка
.ajgtest - Проверить последнее сообщение с набором в текущем чате

⚙️ Как работает:
Ждет сообщение "Ведётся набор в игру" от указанных ботов (или от любого бота, если список пуст).
Автоматически переходит по URL кнопки и отправляет /start.
Работает только когда включен.

💡 Настройки:
В конфиге модуля можно изменить задержку(и) перед нажатием. Если указано несколько значений, будет выбрано случайное.
Можно указать список ID ботов, от которых ожидать сообщения о наборе.
Можно указать список ID чатов, в которых модуль будет активен. Если список пуст, модуль будет работать во всех чатах.""",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "enabled",
                False,
                lambda: "Включен ли автовход в игру",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "delays",
                [0.5],
                lambda: "Список задержек перед нажатием кнопки (секунды). Если указано несколько, будет выбрано случайное.",
                validator=loader.validators.Series(loader.validators.Float(minimum=0.1, maximum=10.0))
            ),
            loader.ConfigValue(
                "bot_ids",
                [],
                lambda: "Список ID ботов, от которых ожидается сообщение о наборе в игру. Если список пуст, сообщения будут отслеживаться от любого бота.",
                validator=loader.validators.Series(loader.validators.Integer())
            ),
            loader.ConfigValue(
                "allowed_chats",
                [],
                lambda: "Список ID чатов, в которых модуль будет активен. Если список пуст, модуль будет работать во всех чатах.",
                validator=loader.validators.Series(loader.validators.Integer())
            ),
        )
        
        self.last_processed_msg = None

    async def client_ready(self, client, db):
        self._client = client
        self._db = db

    @loader.command(ru_doc="Включить автовход в игру")
    async def ajgon(self, message: Message):
        """Включить автовход в игру"""
        self.config["enabled"] = True
        await utils.answer(message, self.strings("enabled"))

    @loader.command(ru_doc="Выключить автовход в игру")
    async def ajgoff(self, message: Message):
        """Выключить автовход в игру"""
        self.config["enabled"] = False
        await utils.answer(message, self.strings("disabled"))

    @loader.command(ru_doc="Показать статус автовхода")
    async def ajgstatus(self, message: Message):
        """Показать статус автовхода"""
        status = "🟢 Включен" if self.config["enabled"] else "🔴 Выключен"
        delays = self.config["delays"]
        delay_display = f"[{', '.join(map(str, delays))}]" if len(delays) > 1 else str(delays[0])
        
        bot_ids = ", ".join(map(str, self.config["bot_ids"])) if self.config["bot_ids"] else "Не указаны (любой бот)"
        
        allowed_chats = ", ".join(map(str, self.config["allowed_chats"])) if self.config["allowed_chats"] else "Все чаты"
        
        await utils.answer(message, self.strings("status").format(status=status, delay_display=delay_display, bot_ids=bot_ids, allowed_chats=allowed_chats))
        
    @loader.command(ru_doc="Показать справку")
    async def ajghelp(self, message: Message):
        """Показать справку"""
        await utils.answer(message, self.strings("help_text"))

    @loader.command(ru_doc="Проверить последнее сообщение с набором")
    async def ajgtest(self, message: Message):
        """Проверить последнее сообщение с набором в текущем чате"""
        current_chat_id = message.chat_id
        configured_bot_ids = self.config["bot_ids"]
        bot_ids_str = ", ".join(map(str, configured_bot_ids)) if configured_bot_ids else "Не указаны (любой бот)"
        
        await utils.answer(message, f"🔍 Ищу сообщение с набором в последних 500 сообщениях в текущем чате (ID: `{current_chat_id}`) от ботов: `{bot_ids_str}`... <emoji document_id=5874960879434338403>🔎</emoji>")
        
        try:
            found = False
            count = 0
            
            async for msg in self._client.iter_messages(current_chat_id, limit=500):
                count += 1
                
                if not getattr(msg, 'text', None):
                    continue
                
                sender_id = getattr(msg, 'sender_id', None)
                if configured_bot_ids and (sender_id is None or sender_id not in configured_bot_ids):
                    continue
                    
                try:
                    msg_text = str(msg.text)
                except Exception:
                    self.logger.debug(f"Could not convert message text to string for msg_id: {msg.id} during ajgtest.")
                    continue
                    
                if "Ведётся набор в игру" in msg_text:
                    info = "✅ Найдено сообщение:\n\n"
                    info += f"📝 ID сообщения: `{msg.id}`\n"
                    info += f"👤 От: `{sender_id if sender_id is not None else 'Неизвестно'}`\n"
                    
                    text_preview = msg_text[:100] + "..." if len(msg_text) > 100 else msg_text
                    info += f"💬 Текст: `{text_preview}`\n\n"
                    
                    if getattr(msg, 'buttons', None):
                        info += "🔘 Есть кнопки: Да\n"
                        info += "Список кнопок:\n"
                        for row_idx, row in enumerate(msg.buttons):
                            for btn_idx, btn in enumerate(row):
                                try:
                                    btn_text = str(getattr(btn, 'text', f'Кнопка {btn_idx}'))
                                    btn_url = getattr(btn, 'url', None)
                                    info += f"  • `{btn_text}`"
                                    if btn_url:
                                        info += f" (URL: `{btn_url[:50]}...`)" if len(btn_url) > 50 else f" (URL: `{btn_url}`)"
                                    else:
                                        info += " (URL: Нет)"
                                    info += "\n"
                                except Exception:
                                    info += f"  • Кнопка {btn_idx} (не удалось получить текст/URL)\n"
                    else:
                        info += "🔘 Есть кнопки: Нет\n"
                    
                    info += f"\n📊 Проверено сообщений: {count}"
                    
                    await utils.answer(message, info)
                    found = True
                    break
            
            if not found:
                await utils.answer(message, f"❌ Сообщение с набором от настроенных ботов не найдено в текущем чате ID `{current_chat_id}`\n📊 Проверено сообщений: {count} <emoji document_id=5778527486270770928>❌</emoji>")
                
        except Exception as e:
            self.logger.exception(f"Error in ajgtest: {e}")
            error_text = str(e) if str(e) else "Неизвестная ошибка"
            await utils.answer(message, f"❌ Ошибка: {error_text} <emoji document_id=5879813604068298387>❗️</emoji>")

    @loader.watcher(incoming=True, outgoing=False)
    async def watcher(self, message: Message):
        """Обработчик всех входящих сообщений для автовхода в игру."""
        try:
            if not self.config["enabled"]:
                self.logger.debug("AutoJoinGame: Модуль выключен. Пропускаю сообщение.")
                return
            
            allowed_chats = self.config["allowed_chats"]
            if allowed_chats and message.chat_id not in allowed_chats:
                self.logger.debug(f"AutoJoinGame: Чат {message.chat_id} не в списке разрешенных чатов ({allowed_chats}). Пропускаю сообщение {message.id}.")
                return

            if not getattr(message, 'text', None):
                self.logger.debug(f"AutoJoinGame: Сообщение {message.id} не содержит текста. Пропускаю.")
                return
            
            if self.config["bot_ids"] and (not getattr(message, 'sender_id', None) or message.sender_id not in self.config["bot_ids"]):
                self.logger.debug(f"AutoJoinGame: Сообщение {message.id} не от одного из настроенных ботов (ожидаем ID из {self.config['bot_ids']}, получили {getattr(message, 'sender_id', 'N/A')}). Пропускаю.")
                return
            
            try:
                msg_text = str(message.text)
            except Exception:
                self.logger.debug(f"AutoJoinGame: Не удалось преобразовать текст сообщения {message.id} в строку. Пропускаю.")
                return
            
            if "Ведётся набор в игру" not in msg_text:
                self.logger.debug(f"AutoJoinGame: Сообщение {message.id} не содержит фразу 'Ведётся набор в игру'. Пропускаю.")
                return
            
            if self.last_processed_msg == message.id:
                self.logger.debug(f"AutoJoinGame: Сообщение {message.id} уже было обработано. Пропускаю.")
                return
            
            self.last_processed_msg = message.id
            
            self.logger.info(f"🎮 AutoJoinGame: Найдено сообщение с набором! <emoji document_id=5931621672846103580>💫</emoji> (msg_id: {message.id}, chat_id: {message.chat_id})")
            
            if not getattr(message, 'buttons', None):
                self.logger.warning(f"⚠️ AutoJoinGame: Сообщение с набором найдено (msg_id: {message.id}), но кнопок нет. Пропускаю. <emoji document_id=5881702736843511327>⚠️</emoji>")
                return
            
            delays = self.config["delays"]
            if delays:
                chosen_delay = random.choice(delays)
            else:
                chosen_delay = 0.5
            
            self.logger.info(f"⏳ AutoJoinGame: Ожидание {chosen_delay} секунд перед обработкой сообщения {message.id} (выбрано из {delays})... <emoji document_id=5778158488450502097>⏲</emoji>")
            await asyncio.sleep(chosen_delay)
            
            button_found = False
            for row in message.buttons:
                for button in row:
                    try:
                        button_text = str(getattr(button, 'text', ''))
                    except Exception:
                        button_text = ''
                    
                    self.logger.debug(f"🔍 AutoJoinGame: Проверка кнопки: '{button_text}'")
                    
                    if any(keyword in button_text.lower() for keyword in ["присоединиться", "играть", "🙋", "🎮", "✅"]): 
                        self.logger.info(f"✅ AutoJoinGame: Найдена кнопка присоединения: '{button_text}' <emoji document_id=5825794181183836432>✔️</emoji>")
                        
                        if getattr(button, 'url', None):
                            button_url = button.url
                            self.logger.info(f"🔗 AutoJoinGame: URL кнопки: {button_url} <emoji document_id=5877738786971979125>🔗</emoji>")
                            
                            match = re.search(r't\.me/([^?]+)\?start=(.+)', button_url)
                            
                            if match:
                                bot_username = match.group(1)
                                start_param = match.group(2)
                                
                                self.logger.info(f"📤 AutoJoinGame: Отправка /start {start_param} боту @{bot_username} <emoji document_id=5877540355187937244>📤</emoji>")
                                
                                await self._client.send_message(
                                    bot_username, 
                                    f'/start {start_param}'
                                )
                                
                                self.logger.info("🎉 AutoJoinGame: Успешно отправлена команда /start (уведомление в чат не отправлено). <emoji document_id=5321458101717585855>🎉</emoji>")
                                button_found = True
                            else:
                                self.logger.warning(f"❌ AutoJoinGame: Не удалось распарсить URL кнопки как deep-link: {button_url}. Пропускаю. <emoji document_id=5879813604068298387>❗️</emoji>")
                        else:
                            self.logger.warning(f"⚠️ AutoJoinGame: Найдена кнопка '{button_text}', но у нее нет URL. Пропускаю. <emoji document_id=5881702736843511327>⚠️</emoji>")
                        
                        if button_found:
                            break
                
                if button_found:
                    break
            
            if not button_found:
                self.logger.warning(f"⚠️ AutoJoinGame: Кнопка присоединения не найдена под сообщением {message.id} после задержки. <emoji document_id=5881702736843511327>⚠️</emoji>")
            
        except Exception as e:
            self.logger.exception(f"❌ AutoJoinGame: Критическая ошибка в watcher для сообщения {getattr(message, 'id', 'N/A')}: {e} <emoji document_id=5879813604068298387>❗️</emoji>")