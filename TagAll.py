# meta developer: @Androfon_AI
# meta name: TagAll
# meta version: 2.0.6
#
# 01101110 01100101 01110110 01100101 01110010 00100000 01100111 01101001 01110110 01100101 00100000 01110101 01110000
# 01101110 01100101 01110110 01100101 01110010 00100000 01101100 01100101 01110100 00100000 01111001 01101111 01110101 00100000 01100100 01101111 01110111 01101110
# 01101110 01100101 01110110 01100101 01110010 00100000 01110010 01110101 01101110 00100000 01100001 01110010 01101111 01110101 01101110 01100100 00100000 01100001 01101110 01100100 00100000 01100100 01100101 01110011 01100101 01110010 01110100 00100000 01111001 01101111 01110101
# 01101110 01100101 01110110 01100101 01110010 00100000 01101101 01100001 01101011 01100101 00100000 01111001 01101111 01110101 00100000 01100011 01110010 01111001 00100000 01101110 01100101 01110110 01100101 01110010 00100000 01110011 01100001 01111001 00100000 01100111 01101111 01101111 01100100 01100010 01111001 01100101
# 01101110 01100101 01110110 01100101 01110010 00100000 01110100 01100101 01101100 01101100 00100000 01100001 01101100 01101100 00100000 01100001 00100000 01101100 01101001 01100101 00100000 01100001 01110010 01101111 01110101 01101110 01100100 00100000 01100001 01101110 01100100 00100000 01101000 01110101 01110010 01110100 00100000 01111001 01101111 01110101
# (Rick Astley - Never Gonna Give You Up)

import asyncio
import contextlib
import logging
import random
import time

from hikkatl.tl.types import Message
from hikkatl.tl.functions.channels import InviteToChannelRequest

from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


class StopEvent:
    def __init__(self):
        self.state = True

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
        "_cfg_doc_timeout": "Время между сообщениями с тегами",
        "_cfg_doc_silent": "Не отправлять сообщение с кнопкой отмены",
        "_cfg_doc_cycle_tagging": (
            "Тегать всех участников снова и снова, пока вы не остановите скрипт,"
            " используя кнопку в сообщении"
        ),
        "_cfg_doc_cycle_delay": "Задержка между циклами тегов в секундах",
        "_cfg_doc_chunk_size": "Сколько пользователей тегать в одном сообщении",
        "_cfg_doc_delete_gathering_message": "Удалять сообщение о сборе участников сразу после отправки",
        "_cfg_doc_duration": "Как долго (в секундах) должен работать процесс TagAll. Установите 0 для неограниченного времени.",
        "gathering": "🧚‍♀️ <b>Отмечаю участников чата...</b>",
        "cancel": "🚫 Отмена",
        "cancelled": "🧚‍♀️ <b>Сбор участников отменен!</b>",
        "tagall_stopped": "🧚‍♀️ <b>TagAll остановлен!</b>",
        "tagall_not_running": "🚫 <b>TagAll сейчас не запущен.</b>",
    }

    strings_de = {
        "bot_error": "🚫 <b>Einladung des Inline-Bots in den Chat fehlgeschlagen oder der Chat-Typ wird für Bot-Einladungen nicht unterstützt.</b>",
        "_cfg_doc_delete": "Nachrichten nach Erwähnung löschen",
        "_cfg_doc_use_bot": "Inline-Bot verwenden, um Leute zu erwähnen",
        "_cfg_doc_timeout": (
            "Zeitintervall, in dem zwischen den Erwähnungen gewartet wird"
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
        "_cfg_doc_delete_gathering_message": "Die Sammelnachricht sofort nach dem Senden löschen",
        "_cfg_doc_duration": "Wie lange (in Sekunden) soll der TagAll-Prozess laufen. Setzen Sie 0 für unbegrenzte Zeit.",
        "gathering": "🧚‍♀️ <b>Erwähne Teilnehmer dieses Chats...</b>",
        "cancel": "🚫 Abbrechen",
        "cancelled": "🧚‍♀️ <b>TagAll abgebrochen!</b>",
        "tagall_stopped": "🧚‍♀️ <b>TagAll gestoppt!</b>",
        "tagall_not_running": "🚫 <b>TagAll läuft derzeit nicht.</b>",
    }

    strings_tr = {
        "bot_error": "🚫 <b>Inline botunu sohbete davet edilemedi veya sohbet türü bot davetleri için desteklenmiyor.</b>",
        "_cfg_doc_delete": "Etiketledikten sonra mesajları sil",
        "_cfg_doc_use_bot": "İnsanları etiketlemek için inline botu kullan",
        "_cfg_doc_timeout": "Her etiket mesajı arasında ne kadar bekleneceği",
        "_cfg_doc_silent": "İptal düğmesi olmadan mesaj gönderme",
        "_cfg_doc_cycle_tagging": (
            "Mesajdaki düğmeyi kullanarak betiği durdurana kadar tüm katılımcıları"
            " tekrar tekrar etiketle"
        ),
        "_cfg_doc_cycle_delay": "Etiketleme döngüsü arasındaki gecikme süresi (saniye)",
        "_cfg_doc_chunk_size": "Bir mesajda kaç kullanıcı etiketlenecek",
        "_cfg_doc_delete_gathering_message": "Toplama mesajını gönderdikten hemen sonra sil",
        "_cfg_doc_duration": "TagAll süreci ne kadar (saniye olarak) çalışmalı. Sınırsız süre için 0 olarak ayarlayın.",
        "gathering": "🧚‍♀️ <b>Bu sohbetteki katılımcıları çağırıyorum...</b>",
        "cancel": "🚫 İptal",
        "cancelled": "🧚‍♀️ <b>TagAll iptal edildi!</b>",
        "tagall_stopped": "🧚‍♀️ <b>TagAll durduruldu!</b>",
        "tagall_not_running": "🚫 <b>TagAll şu anda çalışmıyor.</b>",
    }

    strings_uz = {
        "bot_error": (
            "🚫 <b>Inline botni chatga taklif qilish muvaffaqiyatsiz bo‘ldi yoki chat turi bot takliflari uchun qo‘llab-quvvatlanmaydi.</b>"
        ),
        "_cfg_doc_delete": "Etiketdan so‘ng xabarlarni o‘chirish",
        "_cfg_doc_use_bot": "Odamlarni etiketlash uchun inline botdan foydalanish",
        "_cfg_doc_timeout": "Har bir etiket xabari orasida nechta kutish kerak",
        "_cfg_doc_silent": "Bekor tugmasi olmadan xabar jo‘natish",
        "_cfg_doc_cycle_tagging": (
            "Xabar bo‘yicha tugmani ishlatib, skriptni to‘xtatguncha barcha"
            " qatnashuvchilarni qayta-qayta etiketlash"
        ),
        "_cfg_doc_cycle_delay": "Har bir etiketlash tsikli orasida gecikma (soniya)",
        "_cfg_doc_chunk_size": "Bir xabarda nechta foydalanuvchi etiketlanadi",
        "_cfg_doc_delete_gathering_message": "Yig'in xabarini yuborilgandan so'ng darhol o'chirish",
        "_cfg_doc_duration": "TagAll jarayoni qancha vaqt (soniya) ishlashi kerak. Cheksiz vaqt uchun 0 ga o'rnating.",
        "gathering": "🧚‍♀️ <b>Ushbu chatta qatnashganlarni chaqiraman...</b>",
        "cancel": "🚫 Bekor qilish",
        "cancelled": "🧚‍♀️ <b>TagAll bekor qilindi!</b>",
        "tagall_stopped": "🧚‍♀️ <b>TagAll to'xtatildi!</b>",
        "tagall_not_running": "🚫 <b>TagAll hozirda ishlamayapti.</b>",
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
                0.1,
                lambda: self.strings("_cfg_doc_timeout"),
                validator=loader.validators.Float(minimum=0),
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
                "delete_gathering_message",
                False,
                lambda: self.strings("_cfg_doc_delete_gathering_message"),
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "duration",
                0,
                lambda: self.strings("_cfg_doc_duration"),
                validator=loader.validators.Integer(minimum=0),
            ),
        )
        self._tagall_event = None

    async def cancel(self, call: InlineCall, event: StopEvent):
        event.stop()
        await call.answer(self.strings("cancelled"))

    @loader.command(
        groups=True,
        ru_doc="[текст] - Отметить всех участников чата. [текст] будет отправлен вместе с тегами. Если текст не указан, будут отправлены только теги.",
        de_doc="[Text] - Alle Chatteilnehmer erwähnen. [Text] wird zusammen mit den Erwähnungen gesendet. Wenn kein Text angegeben ist, werden nur die Erwähnungen gesendet.",
        tr_doc="[metin] - Sohbet katılımcılarını etiketle. [metin] etiketlerle birlikte gönderilecektir. Metin belirtilmezse, sadece etiketler gönderilecektir.",
        uz_doc="[matn] - Chat qatnashuvchilarini tegish. [matn] teglar bilan birga yuboriladi. Agar matn ko'rsatilmagan bo'lsa, faqat teglar yuboriladi.",
    )
    async def tagall(self, message: Message):
        """[text] - Отметить всех участников чата. [text] будет отправлен вместе с тегами. Если текст не указан, будут отправлены только теги."""
        args = utils.get_args_raw(message)

        deleted_message_ids_hikkatl = []
        deleted_message_ids_aiogram = []
        cancel_msg = None

        is_bot_sender = self.config["use_bot"]

        if message.out:
            await message.delete()

        chat_entity = await self._client.get_input_entity(message.peer_id)
        chat_id_for_aiogram = message.chat_id

        if is_bot_sender:
            try:
                bot_entity = await self._client.get_input_entity(self.inline.bot_username)
                await self._client(InviteToChannelRequest(chat_entity, [bot_entity]))
            except Exception as e:
                logger.error(f"Failed to invite bot: {e}")
                await utils.answer(message, self.strings("bot_error"))
                return

        event = StopEvent()
        self._tagall_event = event

        if not (self.config["silent"] or self.config["delete_gathering_message"]):
            cancel_msg = await self.inline.form(
                message=message,
                text=self.strings("gathering"),
                reply_markup={
                    "text": self.strings("cancel"),
                    "callback": self.cancel,
                    "args": (event,),
                },
            )

        participants = []
        async for user in self._client.iter_participants(message.peer_id):
            if not user.bot and not user.deleted:
                participants.append(user)
        
        random.shuffle(participants)

        message_prefix = utils.escape_html(args) if args else ""
        
        start_time = time.time()

        try:
            first, br = True, False
            while True if self.config["cycle_tagging"] else first:
                if self.config["duration"] > 0 and (time.time() - start_time) > self.config["duration"]:
                    event.stop()
                    br = True
                    break

                for chunk in utils.chunks(participants, self.config["chunk_size"]):
                    if not event.state:
                        br = True
                        break
                    
                    if self.config["duration"] > 0 and (time.time() - start_time) > self.config["duration"]:
                        event.stop()
                        br = True
                        break

                    tags = []
                    for user in chunk:
                        if user.username:
                            user_display_name = f"@{user.username}"
                        else:
                            # Улучшенная логика для отображения имени пользователя
                            names = []
                            if user.first_name:
                                names.append(user.first_name)
                            if user.last_name:
                                names.append(user.last_name)
                            
                            user_display_name = " ".join(names).strip()
                            if not user_display_name:
                                user_display_name = "Пользователь" # Запасной вариант, если нет имени и фамилии
                            
                            user_display_name = utils.escape_html(user_display_name)
                    
                        tags.append(f'<a href="tg://user?id={user.id}">{user_display_name}</a>')

                    if message_prefix:
                        full_message_text = f"{message_prefix}\n{' '.join(tags)}"
                    else:
                        full_message_text = ' '.join(tags)

                    if is_bot_sender:
                        m = await self.inline.bot_client.send_message(
                            chat_id_for_aiogram,
                            full_message_text,
                            parse_mode="HTML",
                        )
                        if self.config["delete"]:
                            deleted_message_ids_aiogram.append(m.message_id)
                    else:
                        m = await self._client.send_message(
                            chat_entity,
                            full_message_text,
                            parse_mode="HTML",
                        )
                        if self.config["delete"]:
                            deleted_message_ids_hikkatl.append(m.id)

                    await asyncio.sleep(self.config["timeout"])

                if br:
                    break

                first = False
                if self.config["cycle_tagging"]:
                    await asyncio.sleep(self.config["cycle_delay"])
        finally:
            self._tagall_event = None

            if cancel_msg:
                if not event.state:
                    await cancel_msg.edit(self.strings("cancelled"))
                else:
                    await cancel_msg.delete()

            if self.config["delete"]:
                with contextlib.suppress(Exception):
                    if deleted_message_ids_hikkatl:
                        for chunk_ids in utils.chunks(deleted_message_ids_hikkatl, 100):
                            await self._client.delete_messages(chat_entity, chunk_ids)

                    if deleted_message_ids_aiogram:
                        for msg_id in deleted_message_ids_aiogram:
                            await self.inline.bot_client.delete_message(chat_id_for_aiogram, msg_id)

    @loader.command(
        ru_doc="Остановить запущенный процесс TagAll.",
        de_doc="Den laufenden TagAll-Prozess stoppen.",
        tr_doc="Çalışan TagAll sürecini durdur.",
        uz_doc="Ishlayotgan TagAll jarayonini to'xtatish.",
    )
    async def stoptagall(self, message: Message):
        """Остановить запущенный процесс TagAll."""
        if self._tagall_event and self._tagall_event.state:
            self._tagall_event.stop()
            await utils.answer(message, self.strings("tagall_stopped"))
        else:
            await utils.answer(message, self.strings("tagall_not_running"))
        Tag
        if message.out:
            await message.delete()
