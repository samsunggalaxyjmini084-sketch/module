# meta developer: @Androfon_AI
# meta name: TagAll
# meta version: 2.0.33
#
# 01101110 01100101 01110110 01100101 01110010 00100000 01100111 01101001 01110110 01100101 00100000 01110101 01110000
# 01101110 01100101 01110110 01100101 01110010 00100000 01101100 01100101 01110100 00100000 01111001 01101111 01110101 00100000 01100100 01101111 01110111 01101110
# 01101110 01100101 01110110 01100101 01110010 00100000 01110010 01110101 01101110 00100000 01100001 01110010 01101111 01110101 01101110 01100100 00100000 01100001 01101110 01100100 00100000 01100100 01100101 01110011 01100101 01110010 01110100 00100000 01111001 01101111 01110101
# 01101110 01100101 01110110 01100101 01110010 00100000 01101101 01100001 01101011 01100101 00100000 01111001 01101111 01110101 00100000 01100011 01110010 01111001 00100000 01101110 01100101 01110110 01100101 01110010 00100000 01110011 01100001 01111001 00100000 01100111 01101111 01101111 01100100 01100010 01111001 01100101
# 01101110 01100101 01110110 01100101 01110010 00100000 01110100 01100101 01101100 00100000 01100001 01101100 01101100 00100000 01100001 00100000 01101100 01101001 01100101 00100000 01100001 01110010 01101111 01110101 01101110 01100100 00100000 01100001 01101110 00100000 01101000 01110101 01110010 01110100 00100000 01111001 01101111 01110101
# (Rick Astley - Never Gonna Give You Up)

import asyncio
import contextlib
import logging
import random
import time
import re

from hikkatl.tl.functions.channels import InviteToChannelRequest
from hikkatl.tl.types import Message
from hikkatl import events

from .. import loader, utils

logger = logging.getLogger(__name__)


class StopEvent:
    """
    Event class to signal stopping the TagAll process.
    Stores the chat_id to ensure the trigger message comes from the correct chat.
    """

    def __init__(self, chat_id: int):
        self.state = True
        self.chat_id = chat_id
        self.last_timeout: float | None = None

    def stop(self):
        self.state = False


@loader.tds
class TagAllMod(loader.Module):
    """Отмечает всех участников чата, используя инлайн бот или классическим методом"""

    strings = {
        "name": "TagAll",
        "bot_error": "🚫 <b>Не получилось пригласить бота в чат или тип чата не поддерживается для приглашения бота.</b>",
        "_cfg_doc_delete": "Удалять сообщения после тега",
        "_cfg_doc_use_bot": "Использовать бота для тегов",
        "_cfg_doc_timeout": (
            "Время между сообщениями с тегами. Можно указать одно значение (например, '0.1'),"
            " несколько значений через запятую (например, '0.1, 0.5, 1.0') или диапазон"
            " (например, '0.1-1.0')."
        ),
        "_cfg_doc_silent": "Не отправлять сообщение с кнопкой отмены",
        "_cfg_doc_cycle_tagging": (
            "Тегать всех участников снова и снова, пока вы не остановите скрипт,"
            " используя кнопку в сообщении"
        ),
        "_cfg_doc_cycle_delay": "Задержка между циклами тегов в секундах",
        "_cfg_doc_chunk_size": "Сколько пользователей тегать в одном сообщении",
        "_cfg_doc_duration": "Как долго (в секундах) должен работать процесс TagAll. Установите 0 для неограниченного времени.",
        "_cfg_doc_trigger_message": "Сообщение(я)-триггер(ы) для остановки TagAll. Разделяйте запятыми. Если кто-то напишет одно из них в чате, TagAll остановится.",
        "_cfg_doc_trigger_user_id": "ID пользователя(ей) или бота(ов), который(ые) может(могут) остановить TagAll сообщением-триггером. Разделяйте запятыми. Установите пустым, чтобы любой мог остановить.",
        "_cfg_doc_activation_trigger_message": "Сообщение(я)-триггер(ы) для запуска TagAll. Разделяйте запятыми. Если кто-то напишет одно из них в чате, TagAll запустится.",
        "_cfg_doc_activation_trigger_user_id": "ID пользователя(ей) или бота(ов), который(ые) может(могут) запустить TagAll сообщением-триггером. Разделяйте запятыми. Установите пустым, чтобы любой мог запустить.",
        "_cfg_doc_exclude_user_ids": "ID пользователя(ей), которых не нужно тегать. Разделяйте запятыми. Например: <code>123456789, 987654321</code>",
        "_cmd_autotagall_doc": "[on|off|<chat_id>] - Включить или выключить триггеры для запуска/остановки TagAll в <b>указанном или текущем чате</b>. Используйте `on` для включения, `off` для выключения. Без аргументов или только с <chat_id> покажет статус триггеров.",
        "_cmd_tagall_doc": "[<chat_id>] [текст] - Отметить всех участников чата. [текст] будет отправлен вместе с тегами. Если текст не указан, будут отправлены только теги. Если указан <chat_id>, команда будет выполнена в этом чате.",
        "_cmd_stoptagall_doc": "[<chat_id>] - Остановить запущенный процесс TagAll. Если указан <chat_id>, процесс будет остановлен в этом чате.",
        "triggers_state_enabled": "✅ <b>Триггеры TagAll включены в чате {chat_id}!</b>",
        "triggers_state_disabled": "❌ <b>Триггеры TagAll выключены в чате {chat_id}!</b>",
        "triggers_status_enabled": "✅ <b>Триггеры TagAll в чате {chat_id} включены.</b>",
        "triggers_status_disabled": "❌ <b>Триггеры TagAll в чате {chat_id} выключены.</b>",
        "invalid_trigger_arg": "🚫 <b>Неверный аргумент. Используйте 'on', 'off' или оставьте пустым для просмотра статуса.</b>",
        "tagall_not_running": "🚫 <b>TagAll в данный момент не запущен в чате {chat_id}.</b>",
        "tagall_already_running": "🚫 <b>TagAll уже запущен в чате {chat_id}. Используйте <code>.stoptagall {chat_id}</code>, чтобы остановить его.</b>",
        "no_eligible_participants": "🚫 <b>В этом чате нет подходящих участников для тега.</b>",
    }

    strings_de = {
        "bot_error": "🚫 <b>Einladung des Inline-bots in den Chat fehlgeschlagen oder der Chat-Typ wird für Bot-Einladungen nicht unterstützt.</b>",
        "_cfg_doc_delete": "Nachrichten nach Erwähnung löschen",
        "_cfg_doc_use_bot": "Inline-Bot verwenden, um Leute zu erwähnen",
        "_cfg_doc_timeout": (
            "Zeitintervall, in dem zwischen den Erwähnungen gewartet wird. Kann ein"
            " einzelner Wert (z. B. '0.1'), mehrere durch Komma getrennte Werte (z. B."
            " '0.1, 0.5, 1.0') oder ein Bereich (z. B. '0.1-1.0') sein."
        ),
        "_cfg_doc_silent": "Nachricht ohne Abbrechen-Button senden",
        "_cfg_doc_cycle_tagging": (
            "Alle Teilnehmer immer wieder erwähnen, bis du das Skript mit der"
            " Schaltfläche in der Nachricht stoppst"
        ),
        "_cfg_doc_cycle_delay": (
            "Verzögerung zwischen jedem Zyklus der Erwähnung in Sekunden"
        ),
        "_cfg_doc_chunk_size": "Wie viele Benutzer in einer Nachricht erwähnt werden sollen",
        "_cfg_doc_duration": "Wie lange (in Sekunden) der TagAll-Prozess laufen soll. Auf 0 für unbegrenzte Zeit einstellen.",
        "tagall_not_running": "🚫 <b>TagAll läuft derzeit nicht in Chat {chat_id}.</b>",
        "tagall_already_running": "🚫 <b>TagAll läuft bereits in Chat {chat_id}. Verwenden Sie <code>.stoptagall {chat_id}</code>, um es zu stoppen.</b>",
        "_cfg_doc_trigger_message": "Trigger-Nachricht(en), um TagAll zu stoppen. Kommagetrennt eingeben. Wenn jemand dies im Chat schreibt, stoppt TagAll.",
        "_cfg_doc_trigger_user_id": "ID(s) des Benutzers oder Bots, der TagAll mit einer Trigger-Nachricht stoppen kann. Kommagetrennt eingeben. Leer lassen, damit jeder stoppen kann.",
        "_cfg_doc_activation_trigger_message": "Trigger-Nachricht(en) zum Starten von TagAll. Kommagetrennt eingeben. Wenn jemand dies im Chat schreibt, startet TagAll.",
        "_cfg_doc_activation_trigger_user_id": "ID(s) des Benutzers oder Bots, der TagAll mit einer Trigger-Nachricht starten kann. Kommagetrennt eingeben. Leer lassen, damit jeder starten kann.",
        "_cfg_doc_exclude_user_ids": "Benutzer-ID(s), die nicht erwähnt werden sollen. Kommagetrennt eingeben. Zum Beispiel: <code>123456789, 987654321</code>",
        "_cmd_autotagall_doc": "[on|off|<chat_id>] - Trigger zum Starten/Stoppen von TagAll in <b>angegebenem oder aktuellem Chat</b> aktivieren oder deaktivieren. Verwenden Sie `on` zum Aktivieren, `off` zum Deaktivieren. Ohne Argumente oder nur mit <chat_id> wird der Trigger-Status angezeigt.",
        "_cmd_tagall_doc": "[<chat_id>] [Text] - Alle Chatteilnehmer erwähnen. [Text] wird zusammen mit den Erwähnungen gesendet. Wenn kein Text angegeben ist, werden nur die Erwähnungen gesendet. Wenn <chat_id> angegeben ist, wird der Befehl in diesem Chat ausgeführt.",
        "_cmd_stoptagall_doc": "[<chat_id>] - Den laufenden TagAll-Prozess stoppen. Wenn <chat_id> angegeben ist, wird der Prozess in diesem Chat gestoppt.",
        "triggers_state_enabled": "✅ <b>TagAll Trigger in Chat {chat_id} aktiviert!</b>",
        "triggers_state_disabled": "❌ <b>TagAll Trigger in Chat {chat_id} deaktiviert!</b>",
        "triggers_status_enabled": "✅ <b>TagAll Trigger in Chat {chat_id} aktiviert.</b>",
        "triggers_status_disabled": "❌ <b>TagAll Trigger in Chat {chat_id} deaktiviert.</b>",
        "invalid_trigger_arg": "🚫 <b>Ungültiges Argument. Verwenden Sie 'on', 'off' oder lassen Sie es leer, um den Status anzuzeigen.</b>",
        "no_eligible_participants": "🚫 <b>In diesem Chat gibt es keine geeigneten Teilnehmer zum Taggen.</b>",
    }

    strings_tr = {
        "bot_error": "🚫 <b>Inline botunu sohbete davet edilemedi veya sohbet türü bot davetleri için desteklenmiyor.</b>",
        "_cfg_doc_delete": "Etiketledikten sonra mesajları sil",
        "_cfg_doc_use_bot": "İnsanları etiketlemek için inline botu kullan",
        "_cfg_doc_timeout": (
            "Her etiket mesajı arasında ne kadar bekleneceği. Tek bir değer (örneğin,"
            " '0.1'), virgülle ayrılmış birden çok değer (örneğin, '0.1, 0.5, 1.0')"
            " veya bir aralık (örneğin, '0.1-1.0') belirtebilirsiniz."
        ),
        "_cfg_doc_silent": "İptal düğmesi olmadan mesaj gönderme",
        "_cfg_doc_cycle_tagging": (
            "Mesajdaki düğmeyi kullanarak betiği durdurana kadar tüm katılımcıları"
            " tekrar tekrar etiketle"
        ),
        "_cfg_doc_cycle_delay": "Etiketleme döngüsü arasındaki gecikme süresi (saniye)",
        "_cfg_doc_chunk_size": "Bir mesajda kaç kullanıcı etiketlenecek",
        "_cfg_doc_duration": "TagAll sürecinin ne kadar süre (saniye) çalışması gerektiği. Sınırsız süre için 0 olarak ayarlayın.",
        "tagall_not_running": "🚫 <b>TagAll şu anda {chat_id} sohbetinde çalışmıyor.</b>",
        "tagall_already_running": "🚫 <b>TagAll zaten {chat_id} sohbetinde çalışıyor. Durdurmak için <code>.stoptagall {chat_id}</code> kullanın.</b>",
        "_cfg_doc_trigger_message": "TagAll'u durdurmak için tetikleyici mesaj(lar). Virgülle ayırın. Biri bunu sohbete yazarsa, TagAll durur.",
        "_cfg_doc_trigger_user_id": "TagAll'u tetikleyici mesajla durdurabilecek kullanıcı veya bot kimliği(leri). Virgülle ayırın. Herkesin durdurabilmesi için boş bırakın.",
        "_cfg_doc_activation_trigger_message": "TagAll'u başlatmak için tetikleyici mesaj(lar). Virgülle ayırın. Biri bunu sohbete yazarsa, TagAll başlar.",
        "_cfg_doc_activation_trigger_user_id": "TagAll'u tetikleyici mesajla başlatabilecek kullanıcı veya bot kimliği(leri). Virgülle ayırın. Herkesin başlatabilmesi için boş bırakın.",
        "_cfg_doc_exclude_user_ids": "Etiketlenmeyecek kullanıcı kimliği(leri). Virgülle ayırın. Örneğin: <code>123456789, 987654321</code>",
        "_cmd_autotagall_doc": "[on|off|<chat_id>] - TagAll'u başlatmak/durdurmak için tetikleyicileri <b>belirtilen veya mevcut sohbette</b> etkinleştir veya devre dışı bırak. Etkinleştirmek için `on`, devre dışı bırakmak için `off` kullanın. Argüman olmadan veya sadece <chat_id> ile tetikleyici durumunu gösterir.",
        "_cmd_tagall_doc": "[<chat_id>] [metin] - Sohbet katılımcılarını etiketle. [metin] etiketlerle birlikte gönderilecektir. Metin belirtilmezse, sadece etiketler gönderilecektir. <chat_id> belirtilirse, komut bu sohbette yürütülür.",
        "_cmd_stoptagall_doc": "[<chat_id>] - Çalışan TagAll sürecini durdur. <chat_id> belirtilirse, süreç bu sohbette durdurulur.",
        "triggers_state_enabled": "✅ <b>TagAll Tetikleyiciler {chat_id} sohbetinde etkinleştirildi!</b>",
        "triggers_state_disabled": "❌ <b>TagAll Tetikleyiciler {chat_id} sohbetinde devre dışı bırakıldı!</b>",
        "triggers_status_enabled": "✅ <b>TagAll Tetikleyiciler {chat_id} sohbetinde etkin.</b>",
        "triggers_status_disabled": "❌ <b>TagAll Tetikleyiciler {chat_id} sohbetinde devre dışı.</b>",
        "invalid_trigger_arg": "🚫 <b>Geçersiz argüman. 'on', 'off' kullanın veya durumu görmek için boş bırakın.</b>",
        "no_eligible_participants": "🚫 <b>Bu sohbette etiketlenecek uygun katılımcı yok.</b>",
    }

    strings_uz = {
        "bot_error": (
            "🚫 <b>Inline botni chatga taklif qilish muvaffaqiyatsiz bo‘ldi yoki chat turi bot takliflari uchun qo‘llab-quvvatlanmaydi.</b>"
        ),
        "_cfg_doc_delete": "Etiketdan so‘ng xabarlarni o‘chirish",
        "_cfg_doc_use_bot": "Odamlarni etiketlash uchun inline botdan foydalanish",
        "_cfg_doc_timeout": (
            "Har bir etiket xabari orasida nechta kutish kerak. Bitta qiymat (masalan,"
            " '0.1'), vergul bilan ajratilgan bir nechta qiymatlar (masalan,"
            " '0.1, 0.5, 1.0') yoki diapazon (masalan, '0.1-1.0') ko'rsatishingiz mumkin."
        ),
        "_cfg_doc_silent": "Bekor tugmasi olmadan xabar jo‘natish",
        "_cfg_doc_cycle_tagging": (
            "Xabar bo‘yicha tugmani ishlatib, skriptni to‘xtatguncha barcha"
            " qatnashuvchilarni qayta-qayta etiketlash"
        ),
        "_cfg_doc_cycle_delay": "Har bir etiketlash tsikli orasida gecikma (soniya)",
        "_cfg_doc_chunk_size": "Bir xabarda nechta foydalanuvchi etiketlanadi",
        "_cfg_doc_duration": "TagAll jarayoni qancha vaqt (soniya) ishlashi kerak. Cheksiz vaqt uchun 0 ga o'rnating.",
        "_cfg_doc_trigger_message": "TagAllni to'xtatish uchun trigger xabari(lari). Vergul bilan ajrating. Agar kimdir uni chatda yozsa, TagAll to'xtaydi.",
        "_cfg_doc_trigger_user_id": "TagAllni trigger xabari bilan to'xtata oladigan foydalanuvchi(lar) yoki bot(lar) ID'si(lari). Vergul bilan ajrating. Har kim to'xtatishi uchun bo'sh qoldiring.",
        "_cfg_doc_activation_trigger_message": "TagAllni ishga tushirish uchun trigger xabari(lari). Vergul bilan ajrating. Agar kimdir uni chatda yozsa, TagAll ishga tushadi.",
        "_cfg_doc_activation_trigger_user_id": "TagAllni trigger xabari bilan ishga tushira oladigan foydalanuvchi(lar) yoki bot(lar) ID'si(lari). Vergul bilan ajrating. Har kim ishga tushirishi uchun bo'sh qoldiring.",
        "_cfg_doc_exclude_user_ids": "Etiketlanmaydigan foydalanuvchi ID(lar)i. Vergul bilan ajrating. Misol uchun: <code>123456789, 987654321</code>",
        "_cmd_autotagall_doc": "[on|off|<chat_id>] - TagAllni ishga tushirish/to'xtatish uchun triggerlarni <b>belgilangan yoki joriy chatda</b> yoqish yoki o'chirish. Yoqish uchun `on`, o'chirish uchun `off` dan foydalaning. Argumentlarsiz yoki faqat <chat_id> bilan triggerlar holatini ko'rsatadi.",
        "_cmd_tagall_doc": "[<chat_id>] [matn] - Chat qatnashuvchilarini tegish. [matn] teglar bilan birga yuboriladi. Agar matn ko'rsatilgan bo'lsa, teglar bilan birga yuboriladi. Matn ko'rsatilmagan bo'lsa, faqat teglar yuboriladi. Agar <chat_id> ko'rsatilgan bo'lsa, buyruq shu chatda bajariladi.",
        "_cmd_stoptagall_doc": "[<chat_id>] - Ishlayotgan TagAll jarayonini to'xtatish. Agar <chat_id> ko'rsatilgan bo'lsa, jarayon shu chatda to'xtatiladi.",
        "triggers_state_enabled": "✅ <b>TagAll triggerlari {chat_id} chatida yoqildi!</b>",
        "triggers_state_disabled": "❌ <b>TagAll triggerlari {chat_id} chatida o'chirildi!</b>",
        "triggers_status_enabled": "✅ <b>TagAll triggerlari {chat_id} chatida yoqilgan.</b>",
        "triggers_status_disabled": "❌ <b>TagAll triggerlari {chat_id} chatida o'chirilgan.</b>",
        "invalid_trigger_arg": "🚫 <b>Noto'g'ri argument. 'on', 'off' dan foydalaning yoki holatini ko'rish uchun bo'sh qoldiring.</b>",
        "no_eligible_participants": "🚫 <b>Bu chatda tegish uchun mos ishtirokchilar topilmadi.</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "delete",
                False,
                lambda: self.strings("_cfg_doc_delete"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "use_bot",
                False,
                lambda: self.strings("_cfg_doc_use_bot"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "timeout",
                "0.1",
                lambda: self.strings("_cfg_doc_timeout"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "silent",
                False,
                lambda: self.strings("_cfg_doc_silent"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "cycle_tagging",
                False,
                lambda: self.strings("_cfg_doc_cycle_tagging"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "cycle_delay",
                0,
                lambda: self.strings("_cfg_doc_cycle_delay"),
                validator=loader.validators.Integer(minimum=0),
            ),
            loader.ConfigValue(
                "chunk_size",
                3,
                lambda: self.strings("_cfg_doc_chunk_size"),
                validator=loader.validators.Integer(minimum=1),
            ),
            loader.ConfigValue(
                "duration",
                0,
                lambda: self.strings("_cfg_doc_duration"),
                validator=loader.validators.Integer(minimum=0),
            ),
            loader.ConfigValue(
                "trigger_message",
                "",
                lambda: self.strings("_cfg_doc_trigger_message"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "trigger_user_id",
                "",
                lambda: self.strings("_cfg_doc_trigger_user_id"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "activation_trigger_message",
                "",
                lambda: self.strings("_cfg_doc_activation_trigger_message"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "activation_trigger_user_id",
                "",
                lambda: self.strings("_cfg_doc_activation_trigger_user_id"),
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "exclude_user_ids",
                "",
                lambda: self.strings("_cfg_doc_exclude_user_ids"),
                validator=loader.validators.String(),
            ),
        )
        self._tagall_events: dict[int, StopEvent] = {}

    async def client_ready(self, client, db):
        self._client = client
        self._db = db
        # Убедитесь, что обработчик событий добавлен только один раз
        if self._message_watcher not in self._client.list_event_handlers():
            self._client.add_event_handler(self._message_watcher, events.NewMessage(incoming=True))

    async def on_unload(self):
        # Удаляем обработчик событий, чтобы он не вызывался после выгрузки
        if self._client and self._message_watcher in self._client.list_event_handlers():
            self._client.remove_event_handler(self._message_watcher, events.NewMessage(incoming=True))

        # Останавливаем все запущенные процессы TagAll
        # Итерируем по копии значений словаря, чтобы избежать RuntimeError, если словарь изменяется во время итерации
        for event in list(self._tagall_events.values()):
            if event.state:
                event.stop()
        self._tagall_events.clear()
        logger.info("Все процессы TagAll остановлены из-за выгрузки модуля.")

    def _parse_chat_and_args(self, message: Message):
        """
        Разбирает аргументы сообщения для извлечения потенциального chat_id и оставшихся аргументов.
        Возвращает (target_chat_id: int, command_args: str).
        """
        args_raw = utils.get_args_raw(message)
        parts = args_raw.split(None, 1)

        target_chat_id = message.chat_id
        command_args = args_raw

        if parts:
            try:
                potential_chat_id = int(parts[0])
                target_chat_id = potential_chat_id
                command_args = parts[1] if len(parts) > 1 else ""
            except ValueError:
                # Первая часть не является целым числом, значит, это часть аргументов команды.
                # Используем chat ID сообщения как целевой. command_args остается args_raw.
                pass
            except Exception as e:
                # В случае других неожиданных ошибок, логируем и продолжаем с chat ID сообщения.
                logger.warning(f"Неожиданная ошибка при разборе потенциального chat ID в _parse_chat_and_args: {e}")
                pass

        return target_chat_id, command_args

    def _get_random_timeout(self, event: StopEvent) -> float:
        """
        Разбирает конфигурацию таймаута и возвращает случайное значение таймаута.
        Поддерживает одно число с плавающей точкой, несколько чисел через запятую или диапазон чисел (например, "0.1-1.0").
        Гарантирует, что один и тот же таймаут не повторяется в двух последовательных вызовах,
        если указано несколько различных значений.
        """
        timeout_str = self.config["timeout"]
        default_timeout = 0.1
        current_timeout = default_timeout

        try:
            # Удаляем все символы, кроме цифр, точек, запятых и дефисов
            cleaned_timeout_str = re.sub(r"[^0-9.,-]", "", timeout_str)

            if "," in cleaned_timeout_str:
                values = []
                for part in cleaned_timeout_str.split(','):
                    part = part.strip()
                    if part:
                        try:
                            val = float(part)
                            if val >= 0.0: # Убедимся, что таймаут не отрицательный
                                values.append(val)
                        except ValueError:
                            pass
                
                if values:
                    if len(values) > 1 and event.last_timeout is not None and event.last_timeout in values:
                        available_values = [v for v in values if v != event.last_timeout]
                        if not available_values: # Если все значения совпадают с last_timeout или только одно уникальное значение
                            available_values = values # Сбрасываем до всех значений, чтобы разрешить выбор
                        current_timeout = random.choice(available_values)
                    else:
                        current_timeout = random.choice(values)
                else:
                    logger.warning(f"Не удалось разобрать значения таймаута из '{timeout_str}'. Используется значение по умолчанию {default_timeout}.")
            
            elif "-" in cleaned_timeout_str:
                parts = cleaned_timeout_str.split('-', 1)
                if len(parts) == 2:
                    try:
                        min_val = float(parts[0].strip())
                        max_val = float(parts[1].strip())
                        
                        min_val = max(0.0, min_val) # Убедимся, что таймаут не отрицательный
                        max_val = max(0.0, max_val) # Убедимся, что таймаут не отрицательный

                        if min_val > max_val:
                            min_val, max_val = max_val, min_val
                        
                        current_timeout = random.uniform(min_val, max_val)
                    except ValueError:
                        logger.warning(f"Не удалось разобрать диапазон таймаута из '{timeout_str}'. Используется значение по умолчанию {default_timeout}.")
                elif len(parts) == 1 and parts[0].strip(): # Обработка случаев типа "0.5-" или "-0.5" или просто "0.5"
                    try:
                        single_val = float(parts[0].strip())
                        current_timeout = max(0.0, single_val)
                    except ValueError:
                        logger.warning(f"Не удалось разобрать одиночное значение таймаута из '{timeout_str}'. Используется значение по умолчанию {default_timeout}.")
                else:
                    logger.warning(f"Не удалось разобрать диапазон таймаута из '{timeout_str}'. Используется значение по умолчанию {default_timeout}.")
            
            else: # Одно значение с плавающей точкой
                single_val_str = cleaned_timeout_str.strip()
                if single_val_str:
                    try:
                        current_timeout = max(0.0, float(single_val_str))
                    except ValueError:
                        logger.warning(f"Не удалось разобрать одиночное значение таймаута из '{timeout_str}'. Используется значение по умолчанию {default_timeout}.")
                else:
                    logger.warning(f"Пустая строка таймаута. Используется значение по умолчанию {default_timeout}.")

        except Exception as e:
            logger.error(f"Неожиданная ошибка при разборе таймаута '{timeout_str}': {e}. Используется значение по умолчанию {default_timeout}.")
        
        event.last_timeout = current_timeout
        return current_timeout


    async def _message_watcher(self, message: Message):
        """Отслеживает входящие сообщения на предмет настроенных триггерных сообщений (остановка и запуск) и опциональных пользователей."""
        if not message.text or not message.chat_id or message.out:
            return

        chat_id = message.chat_id
        current_tagall_event = self._tagall_events.get(chat_id)
        message_text_lower = message.text.strip().lower()

        # Получаем настройки триггеров для каждого чата
        stop_triggers_enabled = self._db.get(self.name, f"stop_triggers_enabled_{chat_id}", False)
        activation_triggers_enabled = self._db.get(self.name, f"activation_triggers_enabled_{chat_id}", False)

        # --- Обработка триггера ОСТАНОВКИ ---
        if stop_triggers_enabled:
            trigger_stop_messages_raw = self.config["trigger_message"]
            trigger_stop_messages = [t.strip().lower() for t in trigger_stop_messages_raw.split(',') if t.strip()]
            trigger_stop_user_ids_raw = self.config["trigger_user_id"]
            trigger_stop_user_ids = set()
            for uid_str in trigger_stop_user_ids_raw.split(','):
                uid_str = uid_str.strip()
                if uid_str:
                    try:
                        uid = int(uid_str)
                        if uid > 0:
                            trigger_stop_user_ids.add(uid)
                    except ValueError:
                        logger.warning(f"Неверный trigger_user_id в конфигурации: '{uid_str}'. Должен быть целым числом.")

            has_stop_trigger_message = False
            if trigger_stop_messages:
                for trigger in trigger_stop_messages:
                    if trigger in message_text_lower:
                        has_stop_trigger_message = True
                        break

            is_authorized_stop_user = not trigger_stop_user_ids or (message.sender and message.sender.id in trigger_stop_user_ids)

            if current_tagall_event and current_tagall_event.state and has_stop_trigger_message and is_authorized_stop_user:
                current_tagall_event.stop()
                # Удалено упоминание об остановке по запросу пользователя.
                return

        # --- Обработка триггера АКТИВАЦИИ ---
        if activation_triggers_enabled:
            activation_trigger_messages_raw = self.config["activation_trigger_message"]
            activation_trigger_messages = [t.strip().lower() for t in activation_trigger_messages_raw.split(',') if t.strip()]
            activation_trigger_user_ids_raw = self.config["activation_trigger_user_id"]
            activation_trigger_user_ids = set()
            for uid_str in activation_trigger_user_ids_raw.split(','):
                uid_str = uid_str.strip()
                if uid_str:
                    try:
                        uid = int(uid_str)
                        if uid > 0:
                            activation_trigger_user_ids.add(uid)
                    except ValueError:
                        logger.warning(f"Неверный activation_trigger_user_id в конфигурации: '{uid_str}'. Должен быть целым числом.")

            has_activation_trigger_message = False
            if activation_trigger_messages:
                for trigger in activation_trigger_messages:
                    if trigger in message_text_lower:
                        has_activation_trigger_message = True
                        break

            is_authorized_activation_user = not activation_trigger_user_ids or (message.sender and message.sender.id in activation_trigger_user_ids)

            if has_activation_trigger_message and is_authorized_activation_user:
                if current_tagall_event and current_tagall_event.state:
                    logger.info(f"TagAll уже запущен в чате {chat_id}, игнорируем триггер активации.")
                    return

                logger.info(f"TagAll активирован триггерным сообщением '{message.text}' от отправителя {message.sender.id if message.sender else 'unknown'} в чате {chat_id}")

                event = StopEvent(chat_id)
                self._tagall_events[chat_id] = event

                self._client.loop.create_task(self._run_tagall_process(chat_id, "", event, True))

    async def _run_tagall_process(self, chat_id: int, message_prefix: str, event: StopEvent, silent_start: bool = False):
        """Внутренняя функция для обработки основной логики TagAll."""
        deleted_message_ids_hikkatl = []
        deleted_message_ids_bot_client = []

        is_bot_sender = self.config["use_bot"]

        try:
            chat_entity = await self._client.get_input_entity(chat_id)
        except Exception as e:
            logger.error(f"Не удалось получить сущность чата для ID {chat_id}: {e}")
            if not silent_start:
                await self._client.send_message(chat_id, f"🚫 <b>Не удалось найти чат с ID:</b> <code>{chat_id}</code>")
            event.stop()
            if chat_id in self._tagall_events:
                del self._tagall_events[chat_id]
            return

        excluded_user_ids = set()
        exclude_ids_raw = self.config["exclude_user_ids"]
        for uid_str in exclude_ids_raw.split(','):
            uid_str = uid_str.strip()
            if uid_str:
                try:
                    excluded_user_ids.add(int(uid_str))
                except ValueError:
                    logger.warning(f"Неверный ID пользователя в конфигурации 'exclude_user_ids': '{uid_str}'. Должен быть целым числом.")

        if is_bot_sender:
            try:
                if not hasattr(self, 'inline') or not hasattr(self.inline, 'bot_username'):
                    raise RuntimeError("Инлайн-бот не настроен или недоступен.")

                bot_entity = await self._client.get_input_entity(self.inline.bot_username)
                with contextlib.suppress(Exception):
                    await self._client(InviteToChannelRequest(chat_entity, [bot_entity]))
            except Exception as e:
                logger.error(f"Не удалось получить сущность бота или пригласить бота: {e}")
                if not silent_start:
                    await self._client.send_message(chat_id, self.strings("bot_error"))
                event.stop()
                if chat_id in self._tagall_events:
                    del self._tagall_events[chat_id]
                return

        participants = []
        owner_id = self._client.tg_id
        async for user in self._client.iter_participants(chat_id):
            if not user.bot and not user.deleted and user.id != owner_id and user.id not in excluded_user_ids:
                participants.append(user)
        
        if not participants:
            logger.warning(f"В чате {chat_id} не найдено подходящих участников для TagAll, останавливаем.")
            if not silent_start:
                await self._client.send_message(chat_id, self.strings("no_eligible_participants"))
            event.stop()
            if chat_id in self._tagall_events:
                del self._tagall_events[chat_id]
            return

        random.shuffle(participants)

        start_time = time.time()

        try:
            first_pass = True
            while self.config["cycle_tagging"] or first_pass:
                if not event.state:
                    break

                if self.config["duration"] > 0 and (time.time() - start_time) > self.config["duration"]:
                    event.stop()
                    break

                current_participants_for_cycle = []
                if self.config["cycle_tagging"] and not first_pass:
                    logger.debug(f"Повторный запрос участников для цикла в чате {chat_id}.")
                    async for user in self._client.iter_participants(chat_id):
                        if not user.bot and not user.deleted and user.id != owner_id and user.id not in excluded_user_ids:
                            current_participants_for_cycle.append(user)
                    random.shuffle(current_participants_for_cycle)
                    participants = current_participants_for_cycle
                
                if not participants:
                    logger.warning(f"В чате {chat_id} не найдено участников для TagAll, останавливаем цикл.")
                    break

                for chunk in utils.chunks(participants, self.config["chunk_size"]):
                    if not event.state:
                        break

                    if self.config["duration"] > 0 and (time.time() - start_time) > self.config["duration"]:
                        event.stop()
                        break

                    tags = []
                    for user in chunk:
                        if user.username:
                            user_display_name = f"@{user.username}"
                        else:
                            display_name_parts = []
                            if user.first_name:
                                display_name_parts.append(user.first_name)
                            if user.last_name:
                                display_name_parts.append(user.last_name)

                            display_name = " ".join(display_name_parts)
                            user_display_name = utils.escape_html(display_name or "Пользователь")

                        tags.append(f'<a href="tg://user?id={user.id}">{user_display_name}</a>')

                    if message_prefix:
                        full_message_text = f"{message_prefix}\n{' '.join(tags)}"
                    else:
                        full_message_text = " ".join(tags)

                    if is_bot_sender:
                        if hasattr(self, 'inline') and hasattr(self.inline, 'bot_client') and self.inline.bot_client:
                            m = await self.inline.bot_client.send_message(
                                chat_id,
                                full_message_text,
                                parse_mode="HTML",
                            )
                            if self.config["delete"]:
                                deleted_message_ids_bot_client.append(m.id)
                        else:
                            logger.error("Клиент инлайн-бота недоступен или не настроен, переключаемся на юзербота для отправки сообщений.")
                            m = await self._client.send_message(
                                chat_entity,
                                full_message_text,
                                parse_mode="HTML",
                            )
                            if self.config["delete"]:
                                deleted_message_ids_hikkatl.append(m.id)
                    else:
                        m = await self._client.send_message(
                            chat_entity,
                            full_message_text,
                            parse_mode="HTML",
                        )
                        if self.config["delete"]:
                            deleted_message_ids_hikkatl.append(m.id)

                    await asyncio.sleep(self._get_random_timeout(event))

                first_pass = False
                if self.config["cycle_tagging"] and event.state:
                    await asyncio.sleep(self.config["cycle_delay"])
                elif not self.config["cycle_tagging"]:
                    break

        finally:
            if self.config["delete"]:
                with contextlib.suppress(Exception):
                    if deleted_message_ids_hikkatl:
                        for chunk_ids in utils.chunks(deleted_message_ids_hikkatl, 100):
                            await self._client.delete_messages(chat_entity, chunk_ids)

                    if deleted_message_ids_bot_client:
                        if hasattr(self, 'inline') and hasattr(self.inline, 'bot_client') and self.inline.bot_client:
                            for chunk_ids in utils.chunks(deleted_message_ids_bot_client, 100):
                                await self.inline.bot_client.delete_messages(chat_entity, chunk_ids)
                        else:
                            logger.warning("Клиент инлайн-бота недоступен для удаления своих сообщений.")

            if event.state:
                logger.info(f"Процесс TagAll завершен естественным образом в чате {chat_id}.")
            # Удалено упоминание об остановке по запросу пользователя.

            if chat_id in self._tagall_events:
                del self._tagall_events[chat_id]

    @loader.command(
        groups=True,
        ru_doc=lambda self: self.strings("_cmd_tagall_doc"),
        de_doc=lambda self: self.strings("_cmd_tagall_doc"),
        tr_doc=lambda self: self.strings("_cmd_tagall_doc"),
        uz_doc=lambda self: self.strings("_cmd_tagall_doc"),
    )
    async def tagall(self, message: Message):
        """[<chat_id>] [текст] - Отметить всех участников чата. [текст] будет отправлен вместе с тегами. Если текст не указан, будут отправлены только теги. Если указан <chat_id>, команда будет выполнена в этом чате."""
        target_chat_id, message_prefix = self._parse_chat_and_args(message)

        if target_chat_id in self._tagall_events and self._tagall_events[target_chat_id].state:
            await utils.answer(message, self.strings("tagall_already_running").format(chat_id=target_chat_id))
            if message.out:
                await message.delete()
            return

        if message.out:
            await message.delete()

        event = StopEvent(target_chat_id)
        self._tagall_events[target_chat_id] = event

        self._client.loop.create_task(self._run_tagall_process(target_chat_id, message_prefix, event, False))


    @loader.command(
        ru_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
        de_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
        tr_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
        uz_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
    )
    async def stoptagall(self, message: Message):
        """[<chat_id>] - Остановить запущенный процесс TagAll. Если указан <chat_id>, процесс будет остановлен в этом чате."""
        target_chat_id, _ = self._parse_chat_and_args(message)
        event = self._tagall_events.get(target_chat_id)

        if event and event.state:
            event.stop()
            # Удалено упоминание об остановке по запросу пользователя.
        else:
            await utils.answer(message, self.strings("tagall_not_running").format(chat_id=target_chat_id))

        if message.out:
            await message.delete()

    @loader.command(
        ru_doc=lambda self: self.strings("_cmd_autotagall_doc"),
        de_doc=lambda self: self.strings("_cmd_autotagall_doc"),
        tr_doc=lambda self: self.strings("_cmd_autotagall_doc"),
        uz_doc=lambda self: self.strings("_cmd_autotagall_doc"),
    )
    async def autotagall(self, message: Message):
        """[on|off|<chat_id>] - Включить или выключить триггеры для запуска/остановки TagAll в указанном или текущем чате. Без аргументов или только с <chat_id> покажет статус триггеров."""
        target_chat_id, args = self._parse_chat_and_args(message)
        args = args.lower().strip()

        if args == "on":
            self._db.set(self.name, f"stop_triggers_enabled_{target_chat_id}", True)
            self._db.set(self.name, f"activation_triggers_enabled_{target_chat_id}", True)
            await utils.answer(message, self.strings("triggers_state_enabled").format(chat_id=target_chat_id))
        elif args == "off":
            self._db.set(self.name, f"stop_triggers_enabled_{target_chat_id}", False)
            self._db.set(self.name, f"activation_triggers_enabled_{target_chat_id}", False)
            await utils.answer(message, self.strings("triggers_state_disabled").format(chat_id=target_chat_id))
        elif not args:
            is_enabled = self._db.get(self.name, f"stop_triggers_enabled_{target_chat_id}", False)
            if is_enabled:
                await utils.answer(message, self.strings("triggers_status_enabled").format(chat_id=target_chat_id))
            else:
                await utils.answer(message, self.strings("triggers_status_disabled").format(chat_id=target_chat_id))
        else:
            await utils.answer(message, self.strings("invalid_trigger_arg"))

        if message.out:
            await message.delete()
