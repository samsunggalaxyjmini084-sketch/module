# meta developer: @Androfon_AI
# meta name: AutoJoinGame
# meta version: 1.8.4

import logging
import asyncio
import re
import random
from telethon.tl.types import Message
from telethon import events
from .. import loader, utils

logger = logging.getLogger(__name__)

# 01000001010101000100111101001010010011100010000001000111010000010100110101000101
# (ASCII Art - AUTOJOIN GAME)

@loader.tds
class AutoJoinGameMod(loader.Module):
    """Модуль для автоматического нажатия кнопки при наборе в игру"""

    strings = {
        "name": "AutoJoinGame",
        "_cls_doc": "Модуль для автоматического нажатия кнопки при наборе в игру",
        "enabled": "✅ Автовход в игру включен.",
        "disabled": "❌ Автовход в игру выключен.",
        "status": "<emoji document_id=5875291072225087249>📊</emoji> Статус автовхода:\nСтатус: {}\nЗадержка (секунды): {}\nБоты для отслеживания: {}\nРазрешенные чаты: {}\nКлючевые слова кнопок: {}",
        "error": "❌ Ошибка при нажатии кнопки: {}",
        "no_button": "⚠️ Кнопка не найдена под сообщением",
        "help_text": """<emoji document_id=5931415565955503486>🤖</emoji> AutoJoinGame - Помощь

<emoji document_id=5935847413859225147>🏀</emoji> Команды:
<code>.ajgon</code> - Включить автовход в игру
<code>.ajgoff</code> - Выключить автовход в игру
<code>.ajgstatus</code> - Показать статус
<code>.ajghelp</code> - Эта справка
<code>.ajgtest</code> - Проверить последнее сообщение с набором в текущем чате
<code>.ajgid</code> - Показать список ID ботов для мафии
<code>.ajgtournaments</code> - Показать информацию о регистрации на турниры

<emoji document_id=5877260593903177342>⚙</emoji> Как работает:
Ждет сообщение "Ведётся набор в игру" от указанных ботов (или от любого бота, если список пуст).
Автоматически переходит по URL кнопки и отправляет /start.
Работает только когда включен.

<emoji document_id=5843843420468024653>⭐️</emoji> Настройки:
В конфиге модуля можно изменить задержку(и) перед нажатием. Если указано несколько значений, будет выбрано случайное.
Можно указать список ID ботов, от которых ожидать сообщения о наборе.
Можно указать список ID чатов, в которых модуль будет активен. Если список пуст, модуль будет работать во всех чатах.
<b>Новая настройка:</b> <code>button_keywords</code> - список ключевых слов, которые должны содержаться в тексте кнопки для ее активации. Регистр не учитывается.""",
        "ajgid_bots_list": """<emoji document_id=5771887475421090729>👤</emoji> Список ID ботов для мафии:

🤵🏻 True Mafia <code>468253535</code>
True Mafia Black <code>761250017</code>
True Tales (Былины) <code>606933972</code>
Mafia Baku <code>1050428643</code>
Mafia Baku Black <code>1044037207</code>
Mafia Baku Black 2 <code>724330306</code>
Mafioso <code>5424831786</code>
Mafioso Platinum <code>7199004377</code>""",
        "ajgtournaments_text": """Регистрация для турнирных команд

<emoji document_id=5967333011652350314>🔴</emoji> или 🔵
Для Баку

🔵 или 🟠
Для Мафиосо

Примечание, в Мафиосо платиум можно менять эмодзи которые стоят на регистрации, поэтому смотрите на регистрации какие там эмодзи и потом нужные ставите в .cfg 

Настроить можно в

.cfg AutoJoinGame button_keywords"""
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
            loader.ConfigValue(
                "button_keywords",
                ["присоединиться", "играть", "🙋", "🎮", "✅"],
                lambda: "Список ключевых слов в тексте кнопки для активации автовхода (регистронезависимо).",
                validator=loader.validators.Series(loader.validators.String())
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
        
        bot_ids_display = ", ".join(map(str, self.config["bot_ids"])) if self.config["bot_ids"] else "Не указаны (любой бот)"
        
        allowed_chats_display = ", ".join(map(str, self.config["allowed_chats"])) if self.config["allowed_chats"] else "Все чаты"
        
        button_keywords_display = ", ".join(self.config["button_keywords"])
        if not self.config["button_keywords"]:
            button_keywords_display = "Не указаны (будут использованы значения по умолчанию: присоединиться, играть, 🙋, 🎮, ✅)"
        
        await utils.answer(message, self.strings("status").format(status, delay_display, bot_ids_display, allowed_chats_display, button_keywords_display))
        
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
        
        await utils.answer(message, f"<emoji document_id=5874960879434338403>🔎</emoji> Ищу сообщение с фразой \"Ведётся набор в игру\" в последних 500 сообщениях в текущем чате (ID: <code>{current_chat_id}</code>) от ботов: <code>{bot_ids_str}</code>...")
        
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
                    
                msg_text = msg.text
                    
                if "Ведётся набор в игру" in msg_text:
                    info = "✅ Найдено сообщение:\n\n"
                    info += f"📝 ID сообщения: <code>{msg.id}</code>\n"
                    info += f"👤 От: <code>{sender_id if sender_id is not None else 'Неизвестно'}</code>\n"
                    
                    text_preview = msg_text[:100] + "..." if len(msg_text) > 100 else msg_text
                    info += f"💬 Текст: <code>{text_preview}</code>\n\n"
                    
                    if getattr(msg, 'buttons', None):
                        info += "🔘 Есть кнопки: Да\n"
                        info += "Список кнопок:\n"
                        for row_idx, row in enumerate(msg.buttons):
                            for btn_idx, btn in enumerate(row):
                                try:
                                    btn_text = str(getattr(btn, 'text', f'Кнопка {btn_idx}'))
                                    btn_url = getattr(btn, 'url', None)
                                    info += f"  • <code>{btn_text}</code>"
                                    if btn_url:
                                        info += f" (URL: <code>{btn_url[:50]}...</code>)" if len(btn_url) > 50 else f" (URL: <code>{btn_url}</code>)"
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
                await utils.answer(message, f"❌ Сообщение с набором от настроенных ботов не найдено в текущем чате ID <code>{current_chat_id}</code>\n📊 Проверено сообщений: {count}")
                
        except Exception as e:
            logger.exception(f"Error in ajgtest: {e}")
            error_text = str(e) if str(e) else "Неизвестная ошибка"
            await utils.answer(message, f"❌ Ошибка: <code>{error_text}</code>")

    @loader.command(ru_doc="Показать список ID ботов для мафии")
    async def ajgid(self, message: Message):
        """Показать список ID ботов для мафии"""
        await utils.answer(message, self.strings("ajgid_bots_list"))

    @loader.command(ru_doc="Показать информацию о регистрации на турниры")
    async def ajgtournaments(self, message: Message):
        """Показать информацию о регистрации на турниры"""
        await utils.answer(message, self.strings("ajgtournaments_text"))

    @loader.watcher(incoming=True, outgoing=False)
    async def watcher(self, message: Message):
        """Обработчик всех входящих сообщений для автовхода в игру."""
        try:
            if not self.config["enabled"]:
                logger.debug("AutoJoinGame: Модуль выключен. Пропускаю сообщение.")
                return
            
            allowed_chats = self.config["allowed_chats"]
            if allowed_chats and message.chat_id not in allowed_chats:
                logger.debug(f"AutoJoinGame: Чат {message.chat_id} не в списке разрешенных чатов ({allowed_chats}). Пропускаю сообщение {message.id}.")
                return

            if not getattr(message, 'text', None):
                logger.debug(f"AutoJoinGame: Сообщение {message.id} не содержит текста. Пропускаю.")
                return
            
            if self.config["bot_ids"] and (not getattr(message, 'sender_id', None) or message.sender_id not in self.config["bot_ids"]):
                logger.debug(f"AutoJoinGame: Сообщение {message.id} не от одного из настроенных ботов (ожидаем ID из {self.config['bot_ids']}, получили {getattr(message, 'sender_id', 'N/A')}). Пропускаю.")
                return
            
            msg_text = message.text
            
            if "Ведётся набор в игру" not in msg_text:
                logger.debug(f"AutoJoinGame: Сообщение {message.id} не содержит фразу 'Ведётся набор в игру'. Пропускаю.")
                return
            
            if self.last_processed_msg == message.id:
                logger.debug(f"AutoJoinGame: Сообщение {message.id} уже было обработано. Пропускаю.")
                return
            
            self.last_processed_msg = message.id
            
            logger.info(f"🎮 AutoJoinGame: Найдено сообщение с набором! (msg_id: {message.id}, chat_id: {message.chat_id})")
            
            if not getattr(message, 'buttons', None):
                logger.warning(f"⚠️ AutoJoinGame: Сообщение с набором найдено (msg_id: {message.id}), но кнопок нет. Пропускаю.")
                return
            
            delays = self.config["delays"]
            # Config validator ensures delays is never truly empty, so random.choice is safe
            chosen_delay = random.choice(delays)
            
            logger.info(f"⏳ AutoJoinGame: Ожидание {chosen_delay} секунд перед обработкой сообщения {message.id} (выбрано из {delays})...")
            await asyncio.sleep(chosen_delay)
            
            configured_button_keywords = [kw.lower() for kw in self.config["button_keywords"]]
            # Default keywords if config is empty
            default_button_keywords = ["присоединиться", "играть", "🙋", "🎮", "✅"]
            keywords_to_check = configured_button_keywords if configured_button_keywords else default_button_keywords

            button_found = False
            for row in message.buttons:
                for button in row:
                    try:
                        button_text = str(getattr(button, 'text', ''))
                    except Exception:
                        button_text = ''
                    
                    logger.debug(f"🔍 AutoJoinGame: Проверка кнопки: '{button_text}'")
                    
                    if any(keyword in button_text.lower() for keyword in keywords_to_check): 
                        logger.info(f"✅ AutoJoinGame: Найдена кнопка присоединения: '{button_text}'")
                        
                        if getattr(button, 'url', None):
                            button_url = button.url
                            logger.info(f"🔗 AutoJoinGame: URL кнопки: {button_url}")
                            
                            match = re.search(r't\.me/([^?]+)\?start=(.+)', button_url)
                            
                            if match:
                                bot_username = match.group(1)
                                start_param = match.group(2)
                                
                                logger.info(f"📤 AutoJoinGame: Отправка /start {start_param} боту @{bot_username}")
                                
                                await self._client.send_message(
                                    bot_username, 
                                    f'/start {start_param}'
                                )
                                
                                logger.info("🎉 AutoJoinGame: Успешно отправлена команда /start (уведомление в чат не отправлено).")
                                button_found = True
                            else:
                                logger.warning(f"❌ AutoJoinGame: Не удалось распарсить URL кнопки как deep-link: {button_url}. Пропускаю.")
                        else:
                            logger.warning(f"⚠️ AutoJoinGame: Найдена кнопка '{button_text}', но у нее нет URL. Пропускаю.")
                        
                        if button_found:
                            break
                
                if button_found:
                    break
            
            if not button_found:
                logger.warning(f"⚠️ AutoJoinGame: Кнопка присоединения не найдена под сообщением {message.id} после задержки.")
            
        except Exception as e:
            logger.exception(f"❌ AutoJoinGame: Критическая ошибка в watcher для сообщения {getattr(message, 'id', 'N/A')}: {e}")
