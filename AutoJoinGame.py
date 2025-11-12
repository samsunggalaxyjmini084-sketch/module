# meta developer: @Androfon_AI
# meta name: AutoJoinGame
# meta version: 2.0.8
# 01000001010101000100111101001010010011100010000001000111010000010100110101000101
# 01000001010101000100111101001010010011110100100101001110001000000100011101000001
# 010011010100010100100000010011010100111101000100010101010100110001000101
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
    """Модуль для автоматического нажатия кнопки при наборе в игру в ботах мафии, а также подтверждения линчевания и повешения."""

    strings = {
        "name": "AutoJoinGame",
        "_cls_doc": "Модуль для автоматического нажатия кнопки при наборе в игру в ботах мафии, а также подтверждения линчевания и повешения.",
        "enabled": "✅ Автовход в игру и автолинчевание включены.",
        "disabled": "❌ Автовход в игру и автолинчевание выключены.",
        "status": "<emoji document_id=5875291072225087249>📊</emoji> Статус автовхода и автолинчевания:\n"
                  "Статус: {}\n"
                  "Задержка входа (секунды): {}\n"
                  "Задержка линчевания (секунды): {}\n"
                  "Боты для отслеживания: {}\n"
                  "Разрешенные чаты: {}\n"
                  "Ключевые слова кнопок: {}\n"
                  "Режим Deep-Link: {}\n"
                  "Маркер линчевания для '👎': {}\n"
                  "Фразы-триггеры входа в игру: {}\n"
                  "Фразы-триггеры линчевания: {}\n"
                  "Фразы-триггеры повешения: {}",
        "error": "❌ Ошибка при нажатии кнопки: {}",
        "no_button": "⚠️ Кнопка не найдена под сообщением",
        "help_text": """<emoji document_id=5931415565955503486>🤖</emoji> AutoJoinGame - Помощь

<emoji document_id=5935847413859225147>🏀</emoji> Команды:
<code>.ajgon</code> - Включить автовход в игру и автолинчевание
<code>.ajgoff</code> - Выключить автовход в игру и автолинчевание
<code>.ajgstatus</code> - Показать статус
<code>.ajghelp</code> - Эта справка
<code>.ajgtest</code> - Проверить последнее сообщение с набором в текущем чате
<code>.ajgid</code> - Показать список ID ботов для мафии
<code>.ajgtournaments</code> - Показать информацию о регистрации на турниры

<emoji document_id=5877260593903177342>⚙</emoji> Как работает:
Ждет сообщение о наборе в игру или о голосовании (линчевание/повешение) от указанных ботов (или от любого бота, если список пуст).
Автоматически переходит по URL кнопки и отправляет /start для входа в игру.
Если бот спрашивает "Вы точно хотите линчевать..." или "Вы точно хотите повесить...", модуль автоматически нажмет кнопку.
Если в сообщении присутствует настроенный <code>lynch_target_marker</code> (по умолчанию 𝓝𝓚), модуль нажмет кнопку с эмодзи '👎'. В противном случае, если маркера нет, нажмет '👍'.
Работает только когда включен.

<emoji document_id=5843843420468024653>⭐️</emoji> Настройки:
В конфиге модуля можно изменить задержку(и) перед нажатием. Если указано несколько значений, будет выбрано случайное.
Можно указать список ID ботов, от которых ожидать сообщения о наборе.
Можно указать список ID чатов, в которых модуль будет активен. Если список пуст, модуль будет работать во всех чатах.
<b>Настройка:</b> <code>button_keywords</code> - список ключевых слов, которые должны содержаться в тексте кнопки для ее активации. Регистр не учитывается. <b>Если среди ключевых слов есть "🌚" или "🌝", активируется специальный режим обработки Deep-Link URL, при котором боту будет отправляться команда <code>/start &lt;параметр_start&gt;</code>, извлеченный из URL кнопки.</b>
<b>Настройка:</b> <code>lynch_target_marker</code> - строка-маркер, которая, если присутствует в сообщении-триггере для голосования, заставит модуль нажать кнопку '👎'. Если этот маркер не указан в конфиге (пустая строка) или не найден в сообщении, будет нажата кнопка '👍'. По умолчанию: "" (пусто).
<b>Новая настройка:</b> <code>game_join_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях для активации автовхода в игру. По умолчанию: <code>["Ведётся набор в игру", "Регистрация началась!"]</code>.
<b>Новая настройка:</b> <code>lynch_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях для активации автолинчевания. По умолчанию: <code>["Вы точно хотите линчевать"]</code>.
<b>Новая настройка:</b> <code>lynch_hang_trigger_phrases</code> - список фраз, которые модуль будет искать в сообщениях для активации автоповешения. По умолчанию: <code>["Вы точно хотите повесить"]</code>.""",
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

.cfg AutoJoinGame button_keywords""",
        "lynch_triggered_positive": "<emoji document_id=5935968647901089910>🔫</emoji> Обнаружен запрос на линчевание/повешение. Нажимаю '👍'.",
        "lynch_button_not_found_positive": "⚠️ Запрос на линчевание/повешение обнаружен, но кнопка '👍' не найдена.",
        "lynch_triggered_negative": "<emoji document_id=5935968647901089910>🔫</emoji> Обнаружен запрос на линчевание/повешение с маркером '{marker}'. Нажимаю '👎'.",
        "lynch_button_not_found_negative": "⚠️ Запрос на линчевание/повешение с маркером '{marker}' обнаружен, но кнопка '👎' не найдена.",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "enabled",
                False,
                lambda: "Включен ли автовход в игру и автолинчевание",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "delays",
                [0.5],
                lambda: "Список задержек перед нажатием кнопки входа в игру (секунды). Если указано несколько, будет выбрано случайное.",
                validator=loader.validators.Series(loader.validators.Float(minimum=0.1, maximum=10.0))
            ),
            loader.ConfigValue(
                "lynch_delay",
                [0.5],
                lambda: "Список задержек перед нажатием кнопки '👍' или '👎' при линчевании (секунды). Если указано несколько, будет выбрано случайное.",
                validator=loader.validators.Series(loader.validators.Float(minimum=0.1, maximum=10.0))
            ),
            loader.ConfigValue(
                "bot_ids",
                [],
                lambda: "Список ID ботов, от которых ожидается сообщение о наборе в игру или линчевании. Если список пуст, сообщения будут отслеживаться от любого бота.",
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
            loader.ConfigValue(
                "lynch_target_marker",
                "", 
                lambda: "Маркер (строка), который, если присутствует в сообщении-триггере для голосования, заставит модуль нажать кнопку '👎'. Если отсутствует или маркер не указан (пустая строка), нажимается '👍'.",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "game_join_trigger_phrases",
                ["Ведётся набор в игру", "Регистрация началась!"],
                lambda: "Список фраз, которые указывают на сообщение о наборе в игру.",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                "lynch_trigger_phrases",
                ["Вы точно хотите линчевать"],
                lambda: "Список фраз, которые указывают на сообщение для голосования за линчевание (без маркера).",
                validator=loader.validators.Series(loader.validators.String())
            ),
            loader.ConfigValue(
                "lynch_hang_trigger_phrases",
                ["Вы точно хотите повесить"],
                lambda: "Список фраз, которые указывают на сообщение для голосования за повешение игрока (без маркера).",
                validator=loader.validators.Series(loader.validators.String())
            ),
        )

        self.last_processed_msg = None

    async def client_ready(self, client, _):
        self._client = client

    @loader.command(ru_doc="Включить автовход в игру и автолинчевание")
    async def ajgon(self, message: Message):
        """Включить автовход в игру и автолинчевание"""
        self.config["enabled"] = True
        await utils.answer(message, self.strings("enabled"))

    @loader.command(ru_doc="Выключить автовход в игру и автолинчевание")
    async def ajgoff(self, message: Message):
        """Выключить автовход в игру и автолинчевание"""
        self.config["enabled"] = False
        self.last_processed_msg = None 
        await utils.answer(message, self.strings("disabled"))

    @loader.command(ru_doc="Показать статус автовхода и автолинчевания")
    async def ajgstatus(self, message: Message):
        """Показать статус автовхода и автолинчевания"""
        status = "🟢 Включен" if self.config["enabled"] else "🔴 Выключен"
        
        delays = self.config["delays"]
        delay_display = f"[{', '.join(map(str, delays))}]" if len(delays) > 1 else str(delays[0])

        lynch_delays = self.config["lynch_delay"]
        lynch_delay_display = f"[{', '.join(map(str, lynch_delays))}]" if len(lynch_delays) > 1 else str(lynch_delays[0])

        bot_ids_display = ", ".join(map(str, self.config["bot_ids"])) if self.config["bot_ids"] else "Не указаны (любой бот)"

        allowed_chats_display = ", ".join(map(str, self.config["allowed_chats"])) if self.config["allowed_chats"] else "Все чаты"

        configured_button_keywords_lower = [kw.lower() for kw in self.config["button_keywords"]]
        deep_link_mode_active = '🌚' in configured_button_keywords_lower or '🌝' in configured_button_keywords_lower

        button_keywords_display = ", ".join(self.config["button_keywords"])
        if not button_keywords_display:
            button_keywords_display = "(пусто)"

        deep_link_status_display = "🟢 Активен (включен '🌚' или '🌝' в ключевых словах)" if deep_link_mode_active else "🔴 Неактивен (нет '🌚' или '🌝' в ключевых словах)"

        lynch_target_marker_display = self.config["lynch_target_marker"] if self.config["lynch_target_marker"] else "(пусто)"

        game_join_trigger_phrases_display = ", ".join(self.config["game_join_trigger_phrases"]) if self.config["game_join_trigger_phrases"] else "(пусто)"
        lynch_trigger_phrases_display = ", ".join(self.config["lynch_trigger_phrases"]) if self.config["lynch_trigger_phrases"] else "(пусто)"
        lynch_hang_trigger_phrases_display = ", ".join(self.config["lynch_hang_trigger_phrases"]) if self.config["lynch_hang_trigger_phrases"] else "(пусто)"


        await utils.answer(message, self.strings("status").format(
            status, 
            delay_display, 
            lynch_delay_display,
            bot_ids_display, 
            allowed_chats_display, 
            button_keywords_display, 
            deep_link_status_display,
            lynch_target_marker_display,
            game_join_trigger_phrases_display,
            lynch_trigger_phrases_display,
            lynch_hang_trigger_phrases_display
        ))

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

        game_join_phrases_for_test = self.config["game_join_trigger_phrases"]
        lynch_phrases_for_test = self.config["lynch_trigger_phrases"] + self.config["lynch_hang_trigger_phrases"]
        all_trigger_phrases_for_test = game_join_phrases_for_test + lynch_phrases_for_test

        trigger_phrases_str = ", ".join(all_trigger_phrases_for_test) if all_trigger_phrases_for_test else "Не указаны"

        await utils.answer(message, f"<emoji document_id=5874960879434338403>🔎</emoji> Ищу сообщения, содержащие одну из фраз: \"{trigger_phrases_str}\" (регистронезависимо) в последних 500 сообщениях в текущем чате (ID: <code>{current_chat_id}</code>) от ботов: <code>{bot_ids_str}</code>.\nРежим Deep-Link: {deep_link_status_test_display}...")

        try:
            found = False
            count = 0

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

                msg_text_lower = msg.text.lower() # Convert to lower for case-insensitive matching

                # Case-insensitive check for trigger phrases
                if any(phrase.lower() in msg_text_lower for phrase in all_trigger_phrases_for_test):
                    info = "✅ Найдено сообщение:\n\n"
                    info += f"📝 ID сообщения: <code>{msg.id}</code>\n"
                    info += f"👤 От: <code>{sender_id if sender_id is not None else 'Неизвестно'}</code>\n"

                    text_preview = msg.text[:100] + "..." if len(msg.text) > 100 else msg.text
                    info += f"💬 Текст: <code>{text_preview}</code>\n\n"

                    if getattr(msg, 'buttons', None):
                        info += "🔘 Есть кнопки: Да\n"
                        info += "Список кнопок:\n"
                        button_matched_in_test = False
                        
                        # Case-insensitive check for lynch messages
                        is_lynch_test_message = any(phrase.lower() in msg_text_lower for phrase in lynch_phrases_for_test)
                        
                        for row_idx, row in enumerate(msg.buttons):
                            for btn_idx, btn in enumerate(row):
                                try:
                                    btn_text = str(getattr(btn, 'text', f'Кнопка {btn_idx}'))
                                    btn_url = getattr(btn, 'url', None)

                                    match_indicator = ""
                                    
                                    if is_lynch_test_message:
                                        lynch_marker = self.config["lynch_target_marker"]
                                        # Check lynch_marker case-sensitively in original msg_text as it might be specific
                                        target_emoji = "👎" if lynch_marker and lynch_marker in msg.text else "👍"
                                        if target_emoji in btn_text: # Button text match is case-sensitive for emojis
                                            match_indicator = f" (✅ ПОДХОДИТ! Действие: нажать '{target_emoji}')"
                                            button_matched_in_test = True
                                    else:
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
                                        info += " (URL: Нет, это Callback кнопка)"
                                    info += "\n"
                                except Exception as btn_ex:
                                    logger.warning(f"Error processing button in ajgtest: {btn_ex}")
                                    info += f"  • Кнопка {btn_idx} (не удалось получить текст/URL: {btn_ex})\n"
                        if not button_matched_in_test and (keywords_to_check_for_test or is_lynch_test_message):
                            info += "\n⚠️ Ни одна кнопка не соответствует настроенным критериям.\n"
                        elif not keywords_to_check_for_test and not is_lynch_test_message:
                            info += "\n⚠️ Список ключевых слов для кнопок пуст и сообщение не является запросом на линчевание. Ни одна кнопка не будет активирована.\n"
                    else:
                        info += "🔘 Есть кнопки: Нет\n"

                    info += f"\n📊 Проверено сообщений: {count}"

                    await utils.answer(message, info)
                    found = True
                    break
            
            if not found:
                await utils.answer(message, f"❌ Сообщение с набором или запросом на линчевание от настроенных ботов не найдено в текущем чате ID <code>{current_chat_id}</code>\n📊 Проверено сообщений: {count}")

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
        """Обработчик всех входящих сообщений для автовхода в игру и автолинчевания."""
        try:
            if not self.config["enabled"]:
                logger.debug("AutoJoinGame: Модуль выключен. Пропускаю сообщение.")
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

            if self.last_processed_msg == message.id:
                logger.debug(f"AutoJoinGame: Сообщение {message.id} уже было обработано. Пропускаю.")
                return
            
            # Set last_processed_msg here to prevent re-processing during delays,
            # even if further filters might cause an early return for this specific message.
            self.last_processed_msg = message.id 

            allowed_chats = self.config["allowed_chats"]
            if allowed_chats and message.chat_id not in allowed_chats:
                logger.debug(f"AutoJoinGame: Чат {message.chat_id} не в списке разрешенных чатов ({allowed_chats}). Пропускаю сообщение {message.id}.")
                return

            configured_bot_ids = self.config["bot_ids"] 
            if configured_bot_ids and sender_id not in configured_bot_ids:
                logger.debug(f"AutoJoinGame: Сообщение {message.id} от бота {sender_id}, но его ID не в списке разрешенных ботов. Пропускаю.")
                return

            msg_text = message.text
            msg_text_lower = msg_text.lower() # Convert to lower for case-insensitive matching
            
            # Case-insensitive check for trigger phrases
            is_game_join = any(phrase.lower() in msg_text_lower for phrase in self.config["game_join_trigger_phrases"])
            all_lynch_trigger_phrases = self.config["lynch_trigger_phrases"] + self.config["lynch_hang_trigger_phrases"]
            is_lynch_message = any(phrase.lower() in msg_text_lower for phrase in all_lynch_trigger_phrases)

            if not (is_game_join or is_lynch_message):
                logger.debug(f"AutoJoinGame: Сообщение {message.id} не содержит ни одну из фраз для активации (вход в игру или линчевание/повешение). Пропускаю.")
                return
            
            if is_lynch_message:
                if not getattr(message, 'buttons', None):
                    logger.warning(f"⚠️ AutoJoinGame: Запрос на линчевание/повешение найден (msg_id: {message.id}), но кнопок нет. Пропускаю.")
                    return

                lynch_delays = self.config["lynch_delay"]
                chosen_lynch_delay = random.choice(lynch_delays)

                logger.info(f"⏳ AutoJoinGame: Ожидание {chosen_lynch_delay} секунд перед нажатием кнопки для линчевания/повешения сообщения {message.id}...")
                await asyncio.sleep(chosen_lynch_delay)

                lynch_marker = self.config["lynch_target_marker"]
                target_emoji = "👍" 
                success_log_message = f"🎉 AutoJoinGame: Успешно нажата кноп '{target_emoji}' для линчевания/повешения сообщения {message.id}."
                not_found_log_message = self.strings("lynch_button_not_found_positive")
                
                # Check lynch_marker case-sensitively in original msg_text as it might be specific
                if lynch_marker and lynch_marker in msg_text:
                    target_emoji = "👎"
                    success_log_message = f"🎉 AutoJoinGame: Успешно нажата кноп '{target_emoji}' для линчевания/повешения с маркером '{lynch_marker}' сообщения {message.id}."
                    not_found_log_message = self.strings("lynch_button_not_found_negative").format(marker=lynch_marker)
                    logger.info(self.strings("lynch_triggered_negative").format(marker=lynch_marker))
                else:
                    logger.info(self.strings("lynch_triggered_positive"))

                lynch_button_found = False
                for row in message.buttons:
                    for button in row:
                        try:
                            button_text = str(getattr(button, 'text', ''))
                        except Exception as e:
                            logger.warning(f"Error getting button text for lynch message {message.id}: {e}")
                            button_text = ''

                        if target_emoji in button_text: # Button text match is case-sensitive for emojis
                            logger.info(f"✅ AutoJoinGame: Найдена кноп '{target_emoji}' для линчевания/повешения: '{button_text}'")
                            try:
                                await button.click()
                                logger.info(success_log_message)
                                lynch_button_found = True
                                break 
                            except Exception as e:
                                logger.error(f"❌ AutoJoinGame: Ошибка при нажатии кнопки '{target_emoji}' для линчевания/повешения сообщения {message.id}: {e}")
                    if lynch_button_found:
                        break 
                
                if not lynch_button_found:
                    logger.warning(not_found_log_message)
                
                return 

            elif is_game_join: 
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

                                    try:
                                        await self._client.send_message(
                                            bot_username,
                                            f'/start {start_param}'
                                        )
                                        logger.info("🎉 AutoJoinGame: Успешно отправлена команда /start (уведомление в чат не отправлено).")
                                        button_found = True
                                        break 
                                    except Exception as e:
                                        logger.error(f"❌ AutoJoinGame: Ошибка при отправке Deep-Link команды /start для сообщения {message.id}: {e}")
                                else:
                                    logger.warning(f"⚠️ AutoJoinGame: Найдена кнопка '{button_text}' с URL '{button_url}', но она не является Deep-Link или режим Deep-Link неактивен. Пропускаю.")
                            else: 
                                logger.info(f"📤 AutoJoinGame: Найдена кнопка '{button_text}' (CallbackQuery). Нажимаю.")
                                try:
                                    await button.click()
                                    logger.info(f"🎉 AutoJoinGame: Успешно нажата кноп '{button_text}' для присоединения к игре.")
                                    button_found = True
                                    break 
                                except Exception as e:
                                    logger.error(f"❌ AutoJoinGame: Ошибка при нажатии кнопки '{button_text}' для присоединения к игре: {e}")
                    if button_found:
                        break 

                if not button_found:
                    logger.warning(f"⚠️ AutoJoinGame: Кнопка присоединения не найдена под сообщением {message.id} после задержки.")

        except Exception as e:
            logger.exception(f"❌ AutoJoinGame: Критическая ошибка в watcher для сообщения {getattr(message, 'id', 'N/A')}: {e}")
