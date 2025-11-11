# meta developer: @Androfon_AI
# meta name: AutoJoinGame
# meta version: 1.9.6
# 0100000101010100010011110100101001001001010011100010000001000111010000010100110101000101
# (ASCII Art - ATOJIN GAME)

import logging
import asyncio
import random
import urllib.parse
from telethon.tl.types import Message
from telethon import events
from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class AutoJoinGameMod(loader.Module):
    """Модуль для автоматического нажатия кнопки при наборе в игру в ботах мафии"""

    strings = {
        "name": "AutoJoinGame",
        "_cls_doc": "Модуль для автоматического нажатия кнопки при наборе в игру в ботах мафии",
        "enabled": "✅ Автовход в игру включен.",
        "disabled": "❌ Автовход в игру выключен.",
        "status": "<emoji document_id=5875291072225087249>📊</emoji> Статус автовхода:\nСтатус: {}\nЗадержка (секунды): {}\nБоты для отслеживания: {}\nРазрешенные чаты: {}\nКлючевые слова кнопок: {}\nРежим Deep-Link: {}",
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
<b>Новая настройка:</b> <code>button_keywords</code> - список ключевых слов, которые должны содержаться в тексте кнопки для ее активации. Регистр не учитывается. <b>Если среди ключевых слов есть "🌚" или "🌝", активируется специальный режим обработки Deep-Link URL, при котором боту будет отправляться команда <code>/start &lt;параметр_start&gt;</code>, извлеченный из URL кнопки.</b>""",
        "ajgid_bots_list": """<emoji document_id=5771887475421090729>👤</emoji> Список ID ботов для мафии:

🤵🏻 True Mafia <code>468253535</code>
True Mafia Black <code>761250017</code>
True Tales (Былины) <code>606933972</code>
Mafia Baku <code>1050428643</code>
Mafia Baku Black <code>1044037207</code>
Mafia Baku Black 2 <code>724330306</code>
Mafioso <code>5424831786</code>
Mafioso Platinum <code>7199004377</code>
Mafia Combat Premium <code>1634167847</code>""",
        "ajgtournaments_text": """Регистрация для турнирных команд

🔴 или 🔵
Для Баку

🔵 или 🟠
Для Мафиосо

🌚 или 🌝

Для Комбата
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
                ["присоединиться", "играть", "🙋", "🎮", "✅", "🌚"],
                lambda: "Список ключевых слов в тексте кнопки для активации автовхода (регистронезависимо). Если среди ключевых слов есть '🌚' или '🌝', активируется специальный режим обработки Deep-Link URL.",
                validator=loader.validators.Series(loader.validators.String())
            ),
        )

        self.last_processed_msg = None

    async def client_ready(self, client, _):
        self._client = client
        self.last_processed_msg = None

    @loader.command(ru_doc="Включить автовход в игру")
    async def ajgon(self, message: Message):
        """Включить автовход в игру"""
        self.config["enabled"] = True
        await utils.answer(message, self.strings("enabled"))

    @loader.command(ru_doc="Выключить автовход в игру")
    async def ajgoff(self, message: Message):
        """Выключить автовход в игру"""
        self.config["enabled"] = False
        self.last_processed_msg = None
        await utils.answer(message, self.strings("disabled"))

    @loader.command(ru_doc="Показать статус автовхода")
    async def ajgstatus(self, message: Message):
        """Показать статус автовхода"""
        status = "🟢 Включен" if self.config["enabled"] else "🔴 Выключен"
        delays = self.config["delays"]
        delay_display = f"[{', '.join(map(str, delays))}]" if len(delays) > 1 else str(delays[0])

        bot_ids_display = ", ".join(map(str, self.config["bot_ids"])) if self.config["bot_ids"] else "Не указаны (любой бот)"

        allowed_chats_display = ", ".join(map(str, self.config["allowed_chats"])) if self.config["allowed_chats"] else "Все чаты"

        configured_button_keywords_lower = [kw.lower() for kw in self.config["button_keywords"]]
        deep_link_mode_active = '🌚' in configured_button_keywords_lower or '🌝' in configured_button_keywords_lower

        button_keywords_display = ", ".join(self.config["button_keywords"])
        if not button_keywords_display:
            button_keywords_display = "(пусто)"

        deep_link_status_display = "🟢 Активен (включен '🌚' или '🌝' в ключевых словах)" if deep_link_mode_active else "🔴 Неактивен (нет '🌚' или '🌝' в ключевых словах)"

        await utils.answer(message, self.strings("status").format(status, delay_display, bot_ids_display, allowed_chats_display, button_keywords_display, deep_link_status_display))

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

        configured_button_keywords_lower = [kw.lower() for kw in self.config["button_keywords"]]
        deep_link_mode_active = '🌚' in configured_button_keywords_lower or '🌝' in configured_button_keywords_lower
        deep_link_status_test_display = "🟢 Активен" if deep_link_mode_active else "🔴 Неактивен"

        await utils.answer(message, f"<emoji document_id=5874960879434338403>🔎</emoji> Ищу сообщение с фразой \"Ведётся набор в игру\" или \"Регистрация началась!\" в последних 500 сообщениях в текущем чате (ID: <code>{current_chat_id}</code>) от ботов: <code>{bot_ids_str}</code>.\nРежим Deep-Link: {deep_link_status_test_display}...")

        try:
            found = False
            count = 0

            trigger_phrases = ["Ведётся набор в игру", "Регистрация началась!"]

            keywords_to_check_for_test = configured_button_keywords_lower

            async for msg in self._client.iter_messages(current_chat_id, limit=500):
                count += 1

                if not getattr(msg, 'text', None):
                    continue

                sender = await msg.get_sender()
                sender_id = getattr(sender, 'id', None)

                if not getattr(sender, 'bot', False):
                    continue

                if configured_bot_ids and sender_id not in configured_bot_ids:
                    continue

                msg_text = msg.text

                if any(phrase in msg_text for phrase in trigger_phrases):
                    info = "✅ Найдено сообщение:\n\n"
                    info += f"📝 ID сообщения: <code>{msg.id}</code>\n"
                    info += f"👤 От: <code>{sender_id if sender_id is not None else 'Неизвестно'}</code>\n"

                    text_preview = msg_text[:100] + "..." if len(msg_text) > 100 else msg_text
                    info += f"💬 Текст: <code>{text_preview}</code>\n\n"

                    if getattr(msg, 'buttons', None):
                        info += "🔘 Есть кнопки: Да\n"
                        info += "Список кнопок:\n"
                        button_matched_in_test = False
                        for row_idx, row in enumerate(msg.buttons):
                            for btn_idx, btn in enumerate(row):
                                try:
                                    btn_text = str(getattr(btn, 'text', f'Кнопка {btn_idx}'))
                                    btn_url = getattr(btn, 'url', None)

                                    match_indicator = ""
                                    if any(keyword in btn_text.lower() for keyword in keywords_to_check_for_test):
                                        match_indicator = " (✅ ПОДХОДИТ!)"
                                        button_matched_in_test = True

                                    info += f"  • <code>{btn_text}</code>{match_indicator}"
                                    if btn_url:
                                        parsed_url = urllib.parse.urlparse(btn_url)
                                        query_params = urllib.parse.parse_qs(parsed_url.query)
                                        start_param = query_params.get('start', [None])[0]

                                        bot_username = None
                                        if parsed_url.hostname in ['t.me', 'telegram.me'] and parsed_url.path:
                                            path_parts = parsed_url.path.lstrip('/').split('/')
                                            if path_parts and path_parts[0]:
                                                bot_username = path_parts[0]
                                        elif parsed_url.scheme == 'tg' and parsed_url.netloc == 'resolve':
                                            query_params_tg = urllib.parse.parse_qs(parsed_url.query)
                                            bot_username = query_params_tg.get('domain', [None])[0]

                                        url_display = f" (URL: <code>{btn_url[:50]}...</code>)" if len(btn_url) > 50 else f" (URL: <code>{btn_url}</code>)"

                                        if start_param and deep_link_mode_active and bot_username:
                                            info += f"{url_display} (Действие Deep-Link: будет отправлено <code>/start {start_param}</code> боту @{bot_username})"
                                        elif start_param and not deep_link_mode_active and bot_username:
                                            info += f"{url_display} (Действие Deep-Link: <b>не</b> будет отправлено, режим Deep-Link неактивен)"
                                        else:
                                            info += url_display
                                    else:
                                        info += " (URL: Нет)"
                                    info += "\n"
                                except Exception as btn_ex:
                                    logger.warning(f"Error processing button in ajgtest: {btn_ex}")
                                    info += f"  • Кнопка {btn_idx} (не удалось получить текст/URL: {btn_ex})\n"
                        if not button_matched_in_test and keywords_to_check_for_test:
                            info += "\n⚠️ Ни одна кнопка не соответствует настроенным ключевым словам.\n"
                        elif not keywords_to_check_for_test:
                            info += "\n⚠️ Список ключевых слов для кнопок пуст. Ни одна кнопка не будет активирована по тексту.\n"
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

            sender = await message.get_sender()
            if not getattr(sender, 'bot', False):
                logger.debug(f"AutoJoinGame: Сообщение {message.id} не от бота. Пропускаю.")
                return

            sender_id = getattr(sender, 'id', None)
            if sender_id is None:
                logger.warning(f"AutoJoinGame: Не удалось получить ID отправителя для сообщения {message.id}. Пропускаю.")
                return

            if self.config["bot_ids"] and sender_id not in self.config["bot_ids"]:
                logger.debug(f"AutoJoinGame: Сообщение {message.id} от бота {sender_id}, но его ID не в списке разрешенных ботов. Пропускаю.")
                return

            msg_text = message.text

            trigger_phrases = ["Ведётся набор в игру", "Регистрация началась!"]
            if not any(phrase in msg_text for phrase in trigger_phrases):
                logger.debug(f"AutoJoinGame: Сообщение {message.id} не содержит ни одну из фраз для активации ({trigger_phrases}). Пропускаю.")
                return

            if self.last_processed_msg == message.id:
                logger.debug(f"AutoJoinGame: Сообщение {message.id} уже было обработано. Пропускаю.")
                return

            self.last_processed_msg = message.id

            logger.info(f"🎮 AutoJoinGame: Найдено сообщение с набором/регистрацией! (msg_id: {message.id}, chat_id: {message.chat_id})")

            if not getattr(message, 'buttons', None):
                logger.warning(f"⚠️ AutoJoinGame: Сообщение с набором/регистрацией найдено (msg_id: {message.id}), но кнопок нет. Пропускаю.")
                return

            delays = self.config["delays"]
            chosen_delay = random.choice(delays)

            logger.info(f"⏳ AutoJoinGame: Ожидание {chosen_delay} секунд перед обработкой сообщения {message.id} (выбрано из {delays})...")
            await asyncio.sleep(chosen_delay)

            configured_button_keywords_lower = [kw.lower() for kw in self.config["button_keywords"]]
            keywords_to_check = configured_button_keywords_lower

            deep_link_mode_active = '🌚' in configured_button_keywords_lower or '🌝' in configured_button_keywords_lower

            button_found = False
            for row in message.buttons:
                for button in row:
                    try:
                        button_text = str(getattr(button, 'text', ''))
                    except Exception as e:
                        logger.warning(f"Error getting button text for message {message.id}: {e}")
                        button_text = ''

                    logger.debug(f"🔍 AutoJoinGame: Проверка кнопки: '{button_text}'")

                    if any(keyword in button_text.lower() for keyword in keywords_to_check):
                        logger.info(f"✅ AutoJoinGame: Найдена кнопка присоединения: '{button_text}'")

                        if getattr(button, 'url', None):
                            button_url = button.url
                            logger.info(f"🔗 AutoJoinGame: URL кнопки: {button_url}")

                            parsed_url = urllib.parse.urlparse(button_url)

                            bot_username = None
                            if parsed_url.hostname in ['t.me', 'telegram.me'] and parsed_url.path:
                                path_parts = parsed_url.path.lstrip('/').split('/')
                                if path_parts and path_parts[0]:
                                    bot_username = path_parts[0]
                            elif parsed_url.scheme == 'tg' and parsed_url.netloc == 'resolve':
                                query_params_tg = urllib.parse.parse_qs(parsed_url.query)
                                bot_username = query_params_tg.get('domain', [None])[0]

                            query_params = urllib.parse.parse_qs(parsed_url.query)
                            start_param = query_params.get('start', [None])[0]

                            if deep_link_mode_active and bot_username and start_param:
                                logger.info(f"📤 AutoJoinGame: Режим Deep-Link активен. Отправка /start {start_param} боту @{bot_username}")

                                await self._client.send_message(
                                    bot_username,
                                    f'/start {start_param}'
                                )

                                logger.info("🎉 AutoJoinGame: Успешно отправлена команда /start (уведомление в чат не отправлено).")
                                button_found = True
                                break
                            elif bot_username and start_param and not deep_link_mode_active:
                                logger.warning(f"⚠️ AutoJoinGame: Найдена кнопка с Deep-Link URL '{button_url}', но режим Deep-Link не активирован ('🌚' или '🌝' отсутствуют в button_keywords). Команда /start не будет отправлена.")
                            else:
                                logger.warning(f"❌ AutoJoinGame: Не удалось распарсить URL кнопки как Deep-Link (не Telegram URL или не найден параметр 'start') в URL: {button_url}. Пропускаю.")
                        else:
                            logger.warning(f"⚠️ AutoJoinGame: Найдена кнопка '{button_text}', но у нее нет URL. Пропускаю.")

                if button_found:
                    break

            if not button_found:
                logger.warning(f"⚠️ AutoJoinGame: Кнопка присоединения не найдена под сообщением {message.id} после задержки.")

        except Exception as e:
            logger.exception(f"❌ AutoJoinGame: Критическая ошибка в watcher для сообщения {getattr(message, 'id', 'N/A')}: {e}")
