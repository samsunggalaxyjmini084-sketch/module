# meta developer: @Androfon_AI
# meta name: TagAll
# meta version: 2.0.35 # Increased version for new features and command rename
#
# 01101110 01100101 01110110 01100101 01110010 00100000 01100111 01101001 01110110 01100101 00100000 01101001 01110101 01110000
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
        logger.debug(f"StopEvent created for chat {chat_id}")

    def stop(self):
        if self.state:
            self.state = False
            logger.debug(f"StopEvent for chat {self.chat_id} set to stopped.")


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
        "_cfg_doc_duration": "Как долго (в секундах) должен работать процесс TagAll. Установите 0 для неограниченного времени.",
        "_cfg_doc_trigger_message": "Сообщение(я)-триггер(ы) для остановки TagAll. Разделяйте запятыми. Если кто-то напишет одно из них в чате, TagAll остановится.",
        "_cfg_doc_trigger_user_id": "ID пользователя(ей) или бота(ов), который(ые) может(могут) остановить TagAll сообщением-триггером. Разделяйте запятыми. Установите пустым, чтобы любой мог остановить.",
        "_cfg_doc_activation_trigger_message": "Сообщение(я)-триггер(ы) для запуска TagAll. Разделяйте запятыми. Если кто-то напишет одно из них в чате, TagAll запустится.",
        "_cfg_doc_activation_trigger_user_id": "ID пользователя(ей) или бота(ов), который(ые) может(могут) запустить TagAll сообщением-триггером. Разделяйте запятыми. Установите пустым, чтобы любой мог запустить.",
        "_cfg_doc_autostart_delay": "Задержка (в секундах) перед автозапуском TagAll после завершения предыдущего цикла или при включении autotagall. Установите 0 для отключения.",
        "_cfg_doc_autostart_message": "Сообщение для автозапуска TagAll (используется, если нет кастомного для чата).",
        "_cmd_autotagall_doc": "[on|off|<chat_id>] - Включить или выключить триггеры для запуска/остановки TagAll <b>в этом чате</b>. Используйте `on` для включения, `off` для выключения. Без аргументов или только с <chat_id> покажет статус триггеров.",
        "_cmd_tagauto_doc": "[on|off|<chat_id>] [текст] - Включить или выключить автозапуск TagAll <b>в этом чате</b>. Используйте `on` для включения, `off` для выключения. Если указан [текст] после `on`, он будет использоваться как сообщение для автозапуска TagAll в этом чате, переопределяя глобальную настройку. Без аргументов или только с <chat_id> покажет статус автозапуска.", # Renamed
        "_cmd_tagall_doc": "[<chat_id>] [текст] - Отметить всех участников чата. [текст] будет отправлен вместе с тегами. Если текст не указан, будут отправлены только теги. Если указан <chat_id>, команда будет выполнена в этом чате.",
        "_cmd_stoptagall_doc": "[<chat_id>] - Остановить запущенный процесс TagAll. Если указан <chat_id>, процесс будет остановлен в этом чате.",
        "triggers_state_enabled": "✅ <b>Триггеры TagAll (остановка, активация) включены в чате {chat_id}!</b>",
        "triggers_state_disabled": "❌ <b>Триггеры TagAll (остановка, активация) выключены в чате {chat_id}!</b>",
        "triggers_status_enabled": "✅ <b>Триггеры TagAll (остановка, активация) в чате {chat_id} включены.</b>\n"
                                  "  Остановка по триггеру: {stop_enabled}\n"
                                  "  Запуск по триггеру: {activation_enabled}",
        "triggers_status_disabled": "❌ <b>Триггеры TagAll (остановка, активация) в чате {chat_id} выключены.</b>\n"
                                   "  Остановка по триггеру: {stop_enabled}\n"
                                   "  Запуск по триггеру: {activation_enabled}",
        "autostart_state_enabled": "✅ <b>Автозапуск TagAll включен в чате {chat_id}!</b>",
        "autostart_state_disabled": "❌ <b>Автозапуск TagAll выключен в чате {chat_id}!</b>",
        "autostart_status_enabled_with_message": "✅ <b>Автозапуск TagAll в чате {chat_id} включен.</b>\n  Сообщение: <code>{message}</code>",
        "autostart_status_enabled_no_message": "✅ <b>Автозапуск TagAll в чате {chat_id} включен.</b>\n  Используется глобальное сообщение: <code>{message}</code>",
        "autostart_status_disabled": "❌ <b>Автозапуск TagAll в чате {chat_id} выключен.</b>",
        "invalid_trigger_arg": "🚫 <b>Неверный аргумент. Используйте 'on', 'off' или оставьте пустым для просмотра статуса.</b>",
        "tagall_stopped": "🧚‍♀️ <b>TagAll остановлен в чате {chat_id}!</b>",
        "tagall_not_running": "🚫 <b>TagAll в данный момент не запущен в чате {chat_id}.</b>",
        "tagall_already_running": "🚫 <b>TagAll уже запущен в чате {chat_id}. Используйте <code>.stoptagall {chat_id}</code>, чтобы остановить его.</b>",
        "tagall_autostart_cancelled": "✅ <b>Запланированный автозапуск TagAll в чате {chat_id} отменен.</b>",
        "chat_not_found": "🚫 <b>Не удалось найти чат с ID:</b> <code>{chat_id}</code>",
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
        "_cfg_doc_duration": "Wie lange (in Sekunden) der TagAll-Prozess laufen soll. Auf 0 für unbegrenzte Zeit einstellen.",
        "tagall_stopped": "🧚‍♀️ <b>TagAll gestoppt in Chat {chat_id}!</b>",
        "tagall_not_running": "🚫 <b>TagAll läuft derzeit nicht in Chat {chat_id}.</b>",
        "tagall_already_running": "🚫 <b>TagAll läuft bereits in Chat {chat_id}. Verwenden Sie <code>.stoptagall {chat_id}</code>, um es zu stoppen.</b>",
        "_cfg_doc_trigger_message": "Trigger-Nachricht(en), um TagAll zu stoppen. Kommagetrennt eingeben. Wenn jemand dies im Chat schreibt, stoppt TagAll.",
        "_cfg_doc_trigger_user_id": "ID(s) des Benutzers oder Bots, der TagAll mit einer Trigger-Nachricht stoppen kann. Kommagetrennt eingeben. Leer lassen, damit jeder stoppen kann.",
        "_cfg_doc_activation_trigger_message": "Trigger-Nachricht(en) zum Starten von TagAll. Kommagetrennt eingeben. Wenn jemand dies im Chat schreibt, startet TagAll.",
        "_cfg_doc_activation_trigger_user_id": "ID(s) des Benutzers oder Bots, der TagAll mit einer Trigger-Nachricht starten kann. Kommagetrennt eingeben. Leer lassen, damit jeder starten kann.",
        "_cfg_doc_autostart_delay": "Verzögerung (in Sekunden) vor dem Autostart von TagAll nach Abschluss eines vorherigen Zyklus oder beim Aktivieren von autotagall. Auf 0 für Deaktivierung einstellen.",
        "_cfg_doc_autostart_message": "Nachricht für den Autostart von TagAll (wird verwendet, wenn kein benutzerdefinierter für den Chat vorhanden ist).",
        "_cmd_autotagall_doc": "[on|off|<chat_id>] - Trigger zum Starten/Stoppen von TagAll <b>in diesem Chat</b> aktivieren oder deaktivieren. Verwenden Sie `on` zum Aktivieren, `off` zum Deaktivieren. Ohne Argumente oder nur mit <chat_id> wird der Trigger-Status angezeigt.",
        "_cmd_tagauto_doc": "[on|off|<chat_id>] [Text] - Autostart von TagAll <b>in diesem Chat</b> aktivieren oder deaktivieren. Verwenden Sie `on` zum Aktivieren, `off` zum Deaktivieren. Wenn [Text] nach `on` angegeben ist, wird er als Nachricht für den TagAll-Autostart in diesem Chat verwendet und überschreibt die globale Einstellung. Ohne Argumente oder nur mit <chat_id> wird der Autostart-Status angezeigt.", # Renamed
        "_cmd_tagall_doc": "[<chat_id>] [Text] - Alle Chatteilnehmer erwähnen. [Text] wird zusammen mit den Erwähnungen gesendet. Wenn kein Text angegeben ist, werden nur die Erwähnungen gesendet. Wenn <chat_id> angegeben ist, wird der Befehl in diesem Chat ausgeführt.",
        "_cmd_stoptagall_doc": "[<chat_id>] - Den laufenden TagAll-Prozess stoppen. Wenn <chat_id> angegeben ist, wird der Prozess in diesem Chat gestoppt.",
        "triggers_state_enabled": "✅ <b>TagAll Trigger (Stopp, Aktivierung) in Chat {chat_id} aktiviert!</b>",
        "triggers_state_disabled": "❌ <b>TagAll Trigger (Stopp, Aktivierung) in Chat {chat_id} deaktiviert!</b>",
        "triggers_status_enabled": "✅ <b>TagAll Trigger (Stopp, Aktivierung) in Chat {chat_id} aktiviert.</b>\n"
                                  "  Trigger stoppen: {stop_enabled}\n"
                                  "  Trigger aktivieren: {activation_enabled}",
        "triggers_status_disabled": "❌ <b>TagAll Trigger (Stopp, Aktivierung) in Chat {chat_id} deaktiviert.</b>\n"
                                   "  Trigger stoppen: {stop_enabled}\n"
                                   "  Trigger aktivieren: {activation_enabled}",
        "autostart_state_enabled": "✅ <b>TagAll Autostart in Chat {chat_id} aktiviert!</b>",
        "autostart_state_disabled": "❌ <b>TagAll Autostart in Chat {chat_id} deaktiviert!</b>",
        "autostart_status_enabled_with_message": "✅ <b>TagAll Autostart in Chat {chat_id} aktiviert.</b>\n  Nachricht: <code>{message}</code>",
        "autostart_status_enabled_no_message": "✅ <b>TagAll Autostart in Chat {chat_id} aktiviert.</b>\n  Verwendet globale Nachricht: <code>{message}</code>",
        "autostart_status_disabled": "❌ <b>TagAll Autostart in Chat {chat_id} deaktiviert.</b>",
        "invalid_trigger_arg": "🚫 <b>Ungültiges Argument. Verwenden Sie 'on', 'off' oder lassen Sie es leer, um den Status anzuzeigen.</b>",
        "tagall_autostart_cancelled": "✅ <b>Geplanter TagAll Autostart in Chat {chat_id} abgebrochen.</b>",
        "chat_not_found": "🚫 <b>Chat mit ID:</b> <code>{chat_id}</code> <b>nicht gefunden.</b>",
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
        "_cfg_doc_duration": "TagAll sürecinin ne kadar süre (saniye) çalışması gerektiği. Sınırsız süre için 0 olarak ayarlayın.",
        "tagall_stopped": "🧚‍♀️ <b>TagAll durduruldu {chat_id} sohbetinde!</b>",
        "tagall_not_running": "🚫 <b>TagAll şu anda {chat_id} sohbetinde çalışmıyor.</b>",
        "tagall_already_running": "🚫 <b>TagAll zaten {chat_id} sohbetinde çalışıyor. Durdurmak için <code>.stoptagall {chat_id}</code> kullanın.</b>",
        "_cfg_doc_trigger_message": "TagAll'u durdurmak için tetikleyici mesaj(lar). Virgülle ayırın. Biri bunu sohbete yazarsa, TagAll durur.",
        "_cfg_doc_trigger_user_id": "TagAll'u tetikleyici mesajla durdurabilecek kullanıcı veya bot kimliği(leri). Virgülle ayırın. Herkesin durdurabilmesi için boş bırakın.",
        "_cfg_doc_activation_trigger_message": "TagAll'u başlatmak için tetikleyici mesaj(lar). Virgülle ayırın. Biri bunu sohbete yazarsa, TagAll başlar.",
        "_cfg_doc_activation_trigger_user_id": "TagAll'u tetikleyici mesajla başlatabilecek kullanıcı veya bot kimliği(leri). Virgülle ayırın. Herkesin başlatabilmesi için boş bırakın.",
        "_cfg_doc_autostart_delay": "Önceki döngü tamamlandıktan veya autotagall etkinleştirildikten sonra TagAll'un otomatik başlatılması için gecikme (saniye). Devre dışı bırakmak için 0 olarak ayarlayın.",
        "_cfg_doc_autostart_message": "TagAll otomatik başlatma mesajı (sohbet için özel bir tane yoksa kullanılır).",
        "_cmd_autotagall_doc": "[on|off|<chat_id>] - TagAll'u başlatmak/durdurmak için tetikleyicileri <b>bu sohbette</b> etkinleştir veya devre dışı bırak. Hepsini etkinleştirmek için `on`, hepsini devre dışı bırakmak için `off` kullanın. Argüman olmadan veya sadece <chat_id> ile tetikleyici durumunu gösterir.",
        "_cmd_tagauto_doc": "[on|off|<chat_id>] [metin] - TagAll otomatik başlatmayı <b>bu sohbette</b> etkinleştir veya devre dışı bırak. Etkinleştirmek için `on`, devre dışı bırakmak için `off` kullanın. `on` komutundan sonra [metin] belirtilirse, bu sohbette TagAll otomatik başlatma için bir mesaj olarak kullanılacak ve global ayarı geçersiz kılacaktır. Argüman olmadan veya sadece <chat_id> ile otomatik başlatma durumunu gösterir.", # Renamed
        "_cmd_tagall_doc": "[<chat_id>] [metin] - Sohbet katılımcılarını etiketle. [metin] etiketlerle birlikte gönderilecektir. Metin belirtilmezse, sadece etiketler gönderilecektir. <chat_id> belirtilirse, komut bu sohbette yürütülür.",
        "_cmd_stoptagall_doc": "[<chat_id>] - Çalışan TagAll sürecini durdur. <chat_id> belirtilirse, süreç bu sohbette durdurulur.",
        "triggers_state_enabled": "✅ <b>TagAll Tetikleyiciler (durdurma, etkinleştirme) {chat_id} sohbetinde etkinleştirildi!</b>",
        "triggers_state_disabled": "❌ <b>TagAll Tetikleyiciler (durdurma, etkinleştirme) {chat_id} sohbetinde devre dışı bırakıldı!</b>",
        "triggers_status_enabled": "✅ <b>TagAll Tetikleyiciler (durdurma, etkinleştirme) {chat_id} sohbetinde etkin.</b>\n"
                                  "  Durdurma tetikleyicisi: {stop_enabled}\n"
                                  "  Etkinleştirme tetikleyicisi: {activation_enabled}",
        "triggers_status_disabled": "❌ <b>TagAll Tetikleyiciler (durdurma, etkinleştirme) {chat_id} sohbetinde devre dışı.</b>\n"
                                   "  Durdurma tetikleyicisi: {stop_enabled}\n"
                                   "  Etkinleştirme tetikleyicisi: {activation_enabled}",
        "autostart_state_enabled": "✅ <b>TagAll Otomatik Başlatma {chat_id} sohbetinde etkinleştirildi!</b>",
        "autostart_state_disabled": "❌ <b>TagAll Otomatik Başlatma {chat_id} sohbetinde devre dışı bırakıldı!</b>",
        "autostart_status_enabled_with_message": "✅ <b>TagAll Otomatik Başlatma {chat_id} sohbetinde etkin.</b>\n  Mesaj: <code>{message}</code>",
        "autostart_status_enabled_no_message": "✅ <b>TagAll Otomatik Başlatma {chat_id} sohbetinde etkin.</b>\n  Global mesaj kullanılıyor: <code>{message}</code>",
        "autostart_status_disabled": "❌ <b>TagAll Otomatik Başlatma {chat_id} sohbetinde devre dışı.</b>",
        "invalid_trigger_arg": "🚫 <b>Geçersiz argüman. 'on', 'off' kullanın veya durumu görmek için boş bırakın.</b>",
        "tagall_autostart_cancelled": "✅ <b>Planlanmış TagAll otomatik başlatma {chat_id} sohbetinde iptal edildi.</b>",
        "chat_not_found": "🚫 <b>Sohbet ID'si:</b> <code>{chat_id}</code> <b>bulunamadı.</b>",
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
        "_cfg_doc_duration": "TagAll jarayoni qancha vaqt (soniya) ishlashi kerak. Cheksiz vaqt uchun 0 ga o'rnating.",
        "_cfg_doc_trigger_message": "TagAllni to'xtatish uchun trigger xabari(lari). Vergul bilan ajrating. Agar kimdir uni chatda yozsa, TagAll to'xtaydi.",
        "_cfg_doc_trigger_user_id": "TagAllni trigger xabari bilan to'xtata oladigan foydalanuvchi(lar) yoki bot(lar) ID'si(lari). Vergul bilan ajrating. Har kim to'xtatishi uchun bo'sh qoldiring.",
        "_cfg_doc_activation_trigger_message": "TagAllni ishga tushirish uchun trigger xabari(lari). Vergul bilan ajrating. Agar kimdir uni chatda yozsa, TagAll ishga tushadi.",
        "_cfg_doc_activation_trigger_user_id": "TagAllni trigger xabari bilan ishga tushira oladigan foydalanuvchi(lar) yoki bot(lar) ID'si(lari). Vergul bilan ajrating. Har kim ishga tushirishi uchun bo'sh qoldiring.",
        "_cfg_doc_autostart_delay": "Oldingi tsikl tugaganidan yoki autotagall yoqilganidan keyin TagAllni avtomatik ishga tushirishdan oldin kechikish (soniya). O'chirish uchun 0 ga o'rnating.",
        "_cfg_doc_autostart_message": "TagAll avtomatik ishga tushirish xabari (chat uchun maxsus birorta bo'lmasa ishlatiladi).",
        "_cmd_autotagall_doc": "[on|off|<chat_id>] - TagAllni ishga tushirish/to'xtatish uchun triggerlarni <b>bu chatda</b> yoqish yoki o'chirish. Yoqish uchun `on`, o'chirish uchun `off` dan foydalaning. Argumentlarsiz yoki faqat <chat_id> bilan triggerlar holatini ko'rsatadi.",
        "_cmd_tagauto_doc": "[on|off|<chat_id>] [matn] - TagAll avtomatik ishga tushirishni <b>bu chatda</b> yoqish yoki o'chirish. Yoqish uchun `on`, o'chirish uchun `off` dan foydalaning. Agar `on` dan keyin [matn] ko'rsatilgan bo'lsa, u shu chatda TagAll avtomatik ishga tushirish uchun xabar sifatida ishlatiladi va global sozlamani bekor qiladi. Argumentlarsiz yoki faqat <chat_id> bilan avtomatik ishga tushirish holatini ko'rsatadi.", # Renamed
        "_cmd_tagall_doc": "[<chat_id>] [matn] - Chat qatnashuvchilarini tegish. [matn] teglar bilan birga yuboriladi. Agar matn ko'rsatilgan bo'lsa, teglar bilan birga yuboriladi. Matn ko'rsatilmagan bo'lsa, faqat teglar yuboriladi. Agar <chat_id> ko'rsatilgan bo'lsa, buyruq shu chatda bajariladi.",
        "_cmd_stoptagall_doc": "[<chat_id>] - Ishlayotgan TagAll jarayonini to'xtatish. Agar <chat_id> ko'rsatilgan bo'lsa, jarayon shu chatda to'xtatiladi.",
        "triggers_state_enabled": "✅ <b>TagAll triggerlari (to'xtatish, faollashtirish) {chat_id} chatida yoqildi!</b>",
        "triggers_state_disabled": "❌ <b>TagAll triggerlari (to'xtatish, faollashtirish) {chat_id} chatida o'chirildi!</b>",
        "triggers_status_enabled": "✅ <b>TagAll triggerlari (to'xtatish, faollashtirish) {chat_id} chatida yoqilgan.</b>\n"
                                  "  To'xtatish triggeri: {stop_enabled}\n"
                                  "  Faollashtirish triggeri: {activation_enabled}",
        "triggers_status_disabled": "❌ <b>TagAll triggerlari (to'xtatish, faollashtirish) {chat_id} chatida o'chirilgan.</b>\n"
                                   "  To'xtatish triggeri: {stop_enabled}\n"
                                   "  Faollashtirish triggeri: {activation_enabled}",
        "autostart_state_enabled": "✅ <b>TagAll Avtomatik Ishga Tushirish {chat_id} chatida yoqildi!</b>",
        "autostart_state_disabled": "❌ <b>TagAll Avtomatik Ishga Tushirish {chat_id} chatida o'chirildi!</b>",
        "autostart_status_enabled_with_message": "✅ <b>TagAll Avtomatik Ishga Tushirish {chat_id} chatida yoqilgan.</b>\n  Xabar: <code>{message}</code>",
        "autostart_status_enabled_no_message": "✅ <b>TagAll Avtomatik Ishga Tushirish {chat_id} chatida yoqilgan.</b>\n  Global xabar ishlatilmoqda: <code>{message}</code>",
        "autostart_status_disabled": "❌ <b>TagAll Avtomatik Ishga Tushirish {chat_id} chatida o'chirildi.</b>",
        "invalid_trigger_arg": "🚫 <b>Noto'g'ri argument. 'on', 'off' dan foydalaning yoki holatini ko'rish uchun bo'sh qoldiring.</b>",
        "tagall_autostart_cancelled": "✅ <b>Rejalashtirilgan TagAll avtomatik ishga tushirilishi {chat_id} chatida bekor qilindi.</b>",
        "chat_not_found": "🚫 <b>ID'si:</b> <code>{chat_id}</code> <b>topilmadi.</b>",
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
                "autostart_delay",
                0,
                lambda: self.strings("_cfg_doc_autostart_delay"),
                validator=loader.validators.Integer(minimum=0),
            ),
            loader.ConfigValue(
                "autostart_message",
                "",
                lambda: self.strings("_cfg_doc_autostart_message"),
                validator=loader.validators.String(),
            ),
        )
        self._tagall_events: dict[int, StopEvent] = {}
        self._scheduled_autostarts: dict[int, tuple[asyncio.Task, StopEvent]] = {}

    async def client_ready(self, client, db):
        self._client = client
        self._db = db
        # Ensure event handler is added only once
        if self._message_watcher not in self._client.list_event_handlers():
            self._client.add_event_handler(self._message_watcher, events.NewMessage(incoming=True))
        
        # Schedule autostart for chats that had it enabled before restart
        autostart_enabled_chats = self._db.get(self.name, "autostart_enabled_chats", [])
        for chat_id in autostart_enabled_chats: # `chat_id` is already int now due to fix in tagautostart
            try:
                # Check if autostart is specifically enabled for this chat
                if self._db.get(self.name, f"autostart_enabled_{chat_id}", False):
                    logger.info(f"Scheduling autostart for chat {chat_id} from persistent state during client_ready.")
                    # _schedule_autostart will handle adding it to _scheduled_autostarts and _tagall_events
                    self._client.loop.create_task(self._schedule_autostart(chat_id))
            except Exception as e:
                logger.warning(f"Error processing autostart for chat ID '{chat_id}' from DB: {e}")


    async def on_unload(self):
        # Remove the event handler to prevent it from being called after unload
        if self._client and self._message_watcher in self._client.list_event_handlers():
            self._client.remove_event_handler(self._message_watcher, events.NewMessage(incoming=True))

        # Stop all running TagAll processes
        for chat_id, event in list(self._tagall_events.items()):
            if event.state:
                event.stop()
                logger.info(f"Stopped active TagAll process in chat {chat_id} due to module unload.")
        self._tagall_events.clear()

        # Cancel all scheduled autostart tasks
        for chat_id, (task, event) in list(self._scheduled_autostarts.items()):
            if not task.done():
                task.cancel()
                event.stop() # Ensure the associated StopEvent is also marked as stopped
                logger.info(f"Cancelled scheduled autostart for chat {chat_id} due to module unload.")
            # Clean up _tagall_events for cancelled scheduled tasks that might still be there
            if chat_id in self._tagall_events and self._tagall_events[chat_id] is event:
                del self._tagall_events[chat_id]
                logger.debug(f"Removed StopEvent for chat {chat_id} from _tagall_events after scheduled autostart cancellation during unload.")
        self._scheduled_autostarts.clear()

        logger.info("All TagAll processes and scheduled autostarts stopped due to module unload.")

    def _parse_chat_and_args(self, message: Message):
        """
        Parses the message arguments to extract a potential chat_id and the remaining arguments.
        Returns (target_chat_id: int, command_args: str).
        """
        args_raw = utils.get_args_raw(message)
        parts = args_raw.split(None, 1)  # Split into at most 2 parts: first word, rest

        target_chat_id = message.chat_id
        command_args = args_raw

        if parts:
            try:
                potential_chat_id = int(parts[0])
                target_chat_id = potential_chat_id
                command_args = parts[1] if len(parts) > 1 else ""
            except ValueError:
                pass # The first part is not an integer, so it's part of the command arguments.
            except Exception as e:
                logger.warning(f"Error parsing potential chat ID for command: {e}")
                pass

        return target_chat_id, command_args

    def _parse_user_ids(self, user_ids_raw: str) -> list[int]:
        """Parses a comma-separated string of user IDs into a list of integers."""
        parsed_ids = []
        for uid_str in user_ids_raw.split(','):
            uid_str = uid_str.strip()
            if uid_str:
                try:
                    uid = int(uid_str)
                    if uid > 0: # Ensure ID is positive
                        parsed_ids.append(uid)
                except ValueError:
                    logger.warning(f"Invalid user ID configured: '{uid_str}'. Must be a positive integer.")
        return parsed_ids

    async def _cancel_scheduled_autostart(self, chat_id: int) -> bool:
        """Cancels a pending autostart for a given chat_id if it exists."""
        if chat_id in self._scheduled_autostarts and not self._scheduled_autostarts[chat_id][0].done():
            task, event = self._scheduled_autostarts[chat_id]
            task.cancel()
            event.stop() # Mark the associated StopEvent as stopped
            del self._scheduled_autostarts[chat_id]
            
            # If this StopEvent was also in _tagall_events (as a scheduled but not yet active process), remove it.
            if chat_id in self._tagall_events and self._tagall_events[chat_id] is event:
                del self._tagall_events[chat_id]
                logger.debug(f"Removed StopEvent for chat {chat_id} from _tagall_events after scheduled autostart cancellation.")

            logger.info(f"Cancelled pending autostart for chat {chat_id}.")
            return True
        return False

    async def _schedule_autostart(self, chat_id: int):
        """Schedules an autostart for TagAll in the given chat."""
        # If TagAll is already running or scheduled, do nothing
        if chat_id in self._tagall_events and self._tagall_events[chat_id].state:
            logger.debug(f"TagAll already running or scheduled in chat {chat_id}, skipping autostart schedule.")
            return
        
        # If an autostart is already pending (and its task is not done), do nothing
        if chat_id in self._scheduled_autostarts and not self._scheduled_autostarts[chat_id][0].done():
            logger.debug(f"Autostart already scheduled for chat {chat_id}, skipping new schedule.")
            return

        is_autostart_enabled = self._db.get(self.name, f"autostart_enabled_{chat_id}", False)
        autostart_delay = self.config["autostart_delay"]
        
        # Determine the message for this specific autostart
        custom_message = self._db.get(self.name, f"autostart_message_{chat_id}", None) # Using per-chat DB key
        actual_message = custom_message if custom_message is not None else self.config["autostart_message"]

        if is_autostart_enabled and autostart_delay > 0:
            logger.info(f"Scheduling TagAll autostart in chat {chat_id} in {autostart_delay} seconds with message: '{actual_message}'.")
            
            event = StopEvent(chat_id)
            self._tagall_events[chat_id] = event # Mark as running/scheduled from now on in _tagall_events

            async def delayed_start():
                try:
                    await asyncio.sleep(autostart_delay)
                    if event.state: # Check if it wasn't stopped during the delay
                        logger.info(f"Executing scheduled TagAll autostart for chat {chat_id} with message: '{actual_message}'.")
                        # Pass the actual message. _run_tagall_process will manage _tagall_events.
                        await self._run_tagall_process(chat_id, actual_message, event, True) 
                    else:
                        logger.info(f"Scheduled TagAll for chat {chat_id} was stopped during delay (event.state is False).")
                except asyncio.CancelledError:
                    logger.info(f"Scheduled autostart for chat {chat_id} was cancelled.")
                except Exception as e:
                    logger.error(f"Error during delayed autostart for chat {chat_id}: {e}")
                finally:
                    # Clean up the scheduled autostart entry regardless of outcome
                    if chat_id in self._scheduled_autostarts:
                        del self._scheduled_autostarts[chat_id]
                        logger.debug(f"Cleaned up _scheduled_autostarts for chat {chat_id}.")
                    
                    # If _run_tagall_process was NOT called (e.g., cancelled or stopped during delay),
                    # we need to ensure the event is removed from _tagall_events.
                    # If _run_tagall_process WAS called, its finally block handles removing from _tagall_events.
                    if not event.state and chat_id in self._tagall_events and self._tagall_events[chat_id] is event:
                        del self._tagall_events[chat_id]
                        logger.debug(f"Cleaned up _tagall_events for chat {chat_id} after delayed start was stopped/cancelled without _run_tagall_process being called.")


            task = self._client.loop.create_task(delayed_start())
            self._scheduled_autostarts[chat_id] = (task, event)
        else:
            logger.debug(f"Autostart not enabled or delay is 0 for chat {chat_id}.")

    async def _message_watcher(self, message: Message):
        """Monitors incoming messages for configured trigger messages (stop and start) and optional users."""
        if not message.text or not message.chat_id or message.out: # Ignore outgoing messages
            return

        chat_id = message.chat_id
        message_text_lower = message.text.strip().lower()

        stop_triggers_enabled = self._db.get(self.name, f"stop_triggers_enabled_{chat_id}", False)
        activation_triggers_enabled = self._db.get(self.name, f"activation_triggers_enabled_{chat_id}", False)

        # --- Handle STOP trigger ---
        if stop_triggers_enabled:
            trigger_stop_messages = [t.strip().lower() for t in self.config["trigger_message"].split(',') if t.strip()]
            trigger_stop_user_ids = self._parse_user_ids(self.config["trigger_user_id"])

            has_stop_trigger_message = any(trigger in message_text_lower for trigger in trigger_stop_messages)
            is_authorized_stop_user = not trigger_stop_user_ids or (message.sender and message.sender.id in trigger_stop_user_ids)

            current_tagall_event = self._tagall_events.get(chat_id)
            
            if has_stop_trigger_message and is_authorized_stop_user:
                stopped_something = False
                if current_tagall_event and current_tagall_event.state:
                    current_tagall_event.stop()
                    logger.info(f"TagAll stopped by trigger message '{message.text}' from sender {message.sender.id if message.sender else 'unknown'} in chat {chat_id}")
                    stopped_something = True
                
                # Also cancel any scheduled autostart
                if await self._cancel_scheduled_autostart(chat_id):
                    stopped_something = True
                
                if stopped_something:
                    await self._client.send_message(chat_id, self.strings("tagall_stopped").format(chat_id=chat_id))
                    return # Stop processing further triggers for this message

        # --- Handle ACTIVATION trigger ---
        if activation_triggers_enabled:
            activation_trigger_messages = [t.strip().lower() for t in self.config["activation_trigger_message"].split(',') if t.strip()]
            activation_trigger_user_ids = self._parse_user_ids(self.config["activation_trigger_user_id"])

            has_activation_trigger_message = any(trigger in message_text_lower for trigger in activation_trigger_messages)
            is_authorized_activation_user = not activation_trigger_user_ids or (message.sender and message.sender.id in activation_trigger_user_ids)

            if has_activation_trigger_message and is_authorized_activation_user:
                # Check if TagAll is already running or scheduled
                if (chat_id in self._tagall_events and self._tagall_events[chat_id].state) or \
                   (chat_id in self._scheduled_autostarts and not self._scheduled_autostarts[chat_id][0].done()):
                    logger.info(f"TagAll already running or scheduled in chat {chat_id}, ignoring activation trigger.")
                    return

                logger.info(f"TagAll activated by trigger message '{message.text}' from sender {message.sender.id if message.sender else 'unknown'} in chat {chat_id}")

                event = StopEvent(chat_id)
                self._tagall_events[chat_id] = event # Mark as running immediately

                # Activation triggers currently don't support custom messages, use empty string
                self._client.loop.create_task(self._run_tagall_process(chat_id, "", event, True))

    async def _run_tagall_process(self, chat_id: int, message_text: str, event: StopEvent, silent_start: bool = False):
        """Internal function to handle the core TagAll logic."""
        deleted_message_ids_hikkatl = []
        deleted_message_ids_bot_client = []

        is_bot_sender = self.config["use_bot"]

        try:
            chat_entity = await self._client.get_input_entity(chat_id)
        except Exception as e:
            logger.error(f"Failed to get chat entity for ID {chat_id}: {e}")
            # Always inform if chat not found, even if silent_start, as it's a critical error
            await self._client.send_message(chat_id, self.strings("chat_not_found").format(chat_id=chat_id))
            event.stop() # Mark the event as stopped
            # Ensure cleanup if chat_entity failed and process didn't even start properly
            if chat_id in self._tagall_events and self._tagall_events[chat_id] is event:
                del self._tagall_events[chat_id]
            return

        if is_bot_sender:
            # Robust check for self.inline module and its bot_username
            if not hasattr(self, 'inline') or not hasattr(self.inline, 'bot_username') or not self.inline.bot_username:
                logger.error("Inline bot is not configured or available. Falling back to userbot if possible.")
                is_bot_sender = False # Fallback to userbot
            else:
                try:
                    bot_entity = await self._client.get_input_entity(self.inline.bot_username)
                    with contextlib.suppress(Exception): # Suppress if bot is already in channel
                        await self._client(InviteToChannelRequest(chat_entity, [bot_entity]))
                except Exception as e:
                    logger.error(f"Failed to get bot entity or invite bot: {e}. Falling back to userbot.")
                    if not silent_start: # Only send error message if not a silent start
                        await self._client.send_message(chat_id, self.strings("bot_error"))
                    is_bot_sender = False # Fallback to userbot

        participants = []
        owner_id = self._client.tg_id
        async for user in self._client.iter_participants(chat_id):
            if not user.bot and not user.deleted and user.id != owner_id:
                participants.append(user)

        random.shuffle(participants)

        start_time = time.time()

        try:
            first_pass = True
            while self.config["cycle_tagging"] or first_pass:
                if not event.state:
                    logger.info(f"TagAll process in chat {chat_id} stopped (event.state is False).")
                    break

                if self.config["duration"] > 0 and (time.time() - start_time) > self.config["duration"]:
                    event.stop()
                    logger.info(f"TagAll process in chat {chat_id} stopped due to duration limit.")
                    break

                current_participants_for_cycle = []
                if self.config["cycle_tagging"] and not first_pass:
                    logger.debug(f"Re-fetching participants for cycling in chat {chat_id}.")
                    async for user in self._client.iter_participants(chat_id):
                        if not user.bot and not user.deleted and user.id != owner_id:
                            current_participants_for_cycle.append(user)
                    random.shuffle(current_participants_for_cycle)
                    participants = current_participants_for_cycle
                
                if not participants:
                    logger.warning(f"No participants found in chat {chat_id} for TagAll, stopping.")
                    event.stop()
                    break

                for chunk in utils.chunks(participants, self.config["chunk_size"]):
                    if not event.state:
                        logger.info(f"TagAll process in chat {chat_id} stopped within chunk (event.state is False).")
                        break

                    if self.config["duration"] > 0 and (time.time() - start_time) > self.config["duration"]:
                        event.stop()
                        logger.info(f"TagAll process in chat {chat_id} stopped due to duration limit within chunk.")
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

                    if message_text:
                        full_message_text = f"{message_text}\n{' '.join(tags)}"
                    else:
                        full_message_text = " ".join(tags)

                    if is_bot_sender and hasattr(self, 'inline') and hasattr(self.inline, 'bot_client') and self.inline.bot_client:
                        m = await self.inline.bot_client.send_message(
                            chat_id,
                            full_message_text,
                            parse_mode="HTML",
                        )
                        if self.config["delete"]:
                            deleted_message_ids_bot_client.append(m.id)
                    else:
                        # Fallback or default to userbot
                        m = await self._client.send_message(
                            chat_entity,
                            full_message_text,
                            parse_mode="HTML",
                        )
                        if self.config["delete"]:
                            deleted_message_ids_hikkatl.append(m.id)

                    await asyncio.sleep(self.config["timeout"])

                first_pass = False
                if self.config["cycle_tagging"] and event.state:
                    logger.debug(f"TagAll in chat {chat_id} sleeping for cycle_delay: {self.config['cycle_delay']}s")
                    await asyncio.sleep(self.config["cycle_delay"])
                elif not self.config["cycle_tagging"]:
                    break

        finally:
            if self.config["delete"]:
                with contextlib.suppress(Exception):
                    if deleted_message_ids_hikkatl:
                        for chunk_ids in utils.chunks(deleted_message_ids_hikkatl, 100):
                            await self._client.delete_messages(chat_entity, chunk_ids)
                            logger.debug(f"Deleted userbot messages in chat {chat_id}: {chunk_ids}")

                    if deleted_message_ids_bot_client:
                        if hasattr(self, 'inline') and hasattr(self.inline, 'bot_client') and self.inline.bot_client:
                            for chunk_ids in utils.chunks(deleted_message_ids_bot_client, 100):
                                # Use chat_id (int) for bot_client.delete_messages
                                await self.inline.bot_client.delete_messages(chat_id, chunk_ids) 
                                logger.debug(f"Deleted bot messages in chat {chat_id}: {chunk_ids}")
                        else:
                            logger.warning("Inline bot client not available for deleting its messages.")

            if event.state: # If the process completed without being explicitly stopped
                logger.info(f"TagAll process completed naturally in chat {chat_id}.")
                # If not cycling, and autostart is enabled, schedule next run
                if not self.config["cycle_tagging"]:
                    self._client.loop.create_task(self._schedule_autostart(chat_id))
            else:
                logger.info(f"TagAll process stopped manually or by trigger in chat {chat_id}.")

            # Ensure the event is removed from active processes
            if chat_id in self._tagall_events and self._tagall_events[chat_id] is event:
                del self._tagall_events[chat_id]
                logger.debug(f"Removed StopEvent for chat {chat_id} from _tagall_events.")


    @loader.command(
        groups=True,
        ru_doc=lambda self: self.strings("_cmd_tagall_doc"),
        de_doc=lambda self: self.strings("_cmd_tagall_doc"),
        tr_doc=lambda self: self.strings("_cmd_tagall_doc"),
        uz_doc=lambda self: self.strings("_cmd_tagall_doc"),
    )
    async def tagall(self, message: Message):
        """[<chat_id>] [текст] - Отметить всех участников чата. [текст] будет отправлен вместе с тегами. Если текст не указан, будут отправлены только теги. Если указан <chat_id>, команда будет выполнена в этом чате."""
        target_chat_id, message_text = self._parse_chat_and_args(message)

        if target_chat_id in self._tagall_events and self._tagall_events[target_chat_id].state:
            await utils.answer(message, self.strings("tagall_already_running").format(chat_id=target_chat_id))
            if message.out:
                await message.delete()
            return
        
        # Cancel any pending autostart for this chat if a manual tagall is initiated
        if await self._cancel_scheduled_autostart(target_chat_id):
            await utils.answer(message, self.strings("tagall_autostart_cancelled").format(chat_id=target_chat_id))

        if message.out:
            await message.delete()

        event = StopEvent(target_chat_id)
        self._tagall_events[target_chat_id] = event # Mark as running immediately

        self._client.loop.create_task(self._run_tagall_process(target_chat_id, message_text, event, False))


    @loader.command(
        ru_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
        de_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
        tr_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
        uz_doc=lambda self: self.strings("_cmd_stoptagall_doc"),
    )
    async def stoptagall(self, message: Message):
        """[<chat_id>] - Остановить запущенный процесс TagAll. Если указан <chat_id>, процесс будет остановлен в этом чате."""
        target_chat_id, _ = self._parse_chat_and_args(message)
        
        stopped_something = False

        # Cancel any pending autostart for this chat
        if await self._cancel_scheduled_autostart(target_chat_id):
            stopped_something = True

        # Stop actively running TagAll process
        event = self._tagall_events.get(target_chat_id)
        if event and event.state:
            event.stop()
            stopped_something = True
            # The _run_tagall_process's finally block will remove it from _tagall_events
            # Or if it was just a scheduled but not yet running event, _cancel_scheduled_autostart would have removed it.

        if stopped_something:
            await utils.answer(message, self.strings("tagall_stopped").format(chat_id=target_chat_id))
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
            stop_enabled = self._db.get(self.name, f"stop_triggers_enabled_{target_chat_id}", False)
            activation_enabled = self._db.get(self.name, f"activation_triggers_enabled_{target_chat_id}", False)

            if stop_enabled or activation_enabled:
                await utils.answer(message, self.strings("triggers_status_enabled").format(
                    chat_id=target_chat_id,
                    stop_enabled="✅" if stop_enabled else "❌",
                    activation_enabled="✅" if activation_enabled else "❌",
                ))
            else:
                await utils.answer(message, self.strings("triggers_status_disabled").format(
                    chat_id=target_chat_id,
                    stop_enabled="✅" if stop_enabled else "❌",
                    activation_enabled="✅" if activation_enabled else "❌",
                ))
        else:
            await utils.answer(message, self.strings("invalid_trigger_arg"))

        if message.out:
            await message.delete()

    @loader.command( # Renamed command from tagautostart to tagauto
        ru_doc=lambda self: self.strings("_cmd_tagauto_doc"),
        de_doc=lambda self: self.strings("_cmd_tagauto_doc"),
        tr_doc=lambda self: self.strings("_cmd_tagauto_doc"),
        uz_doc=lambda self: self.strings("_cmd_tagauto_doc"),
    )
    async def tagauto(self, message: Message): # Renamed function
        """[on|off|<chat_id>] [текст] - Включить или выключить автозапуск TagAll в указанном или текущем чате. Используйте `on` для включения, `off` для выключения. Если указан [текст] после `on`, он будет использоваться как сообщение для автозапуска TagAll в этом чате, переопределяя глобальную настройку. Без аргументов или только с <chat_id> покажет статус автозапуска."""
        target_chat_id, raw_args = self._parse_chat_and_args(message)
        
        parts = raw_args.split(None, 1) # Split into action and potential custom text
        action = parts[0].lower().strip() if parts else ""
        custom_message_arg = parts[1].strip() if len(parts) > 1 else None

        # Retrieve the list of chats with autostart enabled for persistence
        autostart_enabled_chats = self._db.get(self.name, "autostart_enabled_chats", [])

        if action == "on":
            self._db.set(self.name, f"autostart_enabled_{target_chat_id}", True)

            # Store the custom message or clear it if not provided
            if custom_message_arg is not None:
                self._db.set(self.name, f"autostart_message_{target_chat_id}", custom_message_arg) # Use per-chat DB key
            else:
                self._db.set(self.name, f"autostart_message_{target_chat_id}", None) # Clear any custom message to use global

            # Add chat_id to the persistent list if not already present (store as int)
            if target_chat_id not in autostart_enabled_chats:
                autostart_enabled_chats.append(target_chat_id)
                self._db.set(self.name, "autostart_enabled_chats", autostart_enabled_chats)

            await utils.answer(message, self.strings("autostart_state_enabled").format(chat_id=target_chat_id))
            # Schedule the first run immediately (after delay)
            self._client.loop.create_task(self._schedule_autostart(target_chat_id))

        elif action == "off":
            self._db.set(self.name, f"autostart_enabled_{target_chat_id}", False)
            self._db.set(self.name, f"autostart_message_{target_chat_id}", None) # Clear custom message on disable using per-chat DB key
            
            # Remove chat_id from the persistent list if present
            if target_chat_id in autostart_enabled_chats:
                autostart_enabled_chats.remove(target_chat_id)
                self._db.set(self.name, "autostart_enabled_chats", autostart_enabled_chats)

            # Cancel any pending autostart for this chat
            if await self._cancel_scheduled_autostart(target_chat_id):
                await utils.answer(message, self.strings("tagall_autostart_cancelled").format(chat_id=target_chat_id))
            else:
                await utils.answer(message, self.strings("autostart_state_disabled").format(chat_id=target_chat_id))
        elif not action: # Status check
            autostart_enabled = self._db.get(self.name, f"autostart_enabled_{target_chat_id}", False)
            custom_message = self._db.get(self.name, f"autostart_message_{target_chat_id}", None) # Get per-chat custom message
            global_message = self.config["autostart_message"]

            if autostart_enabled:
                if custom_message is not None:
                    await utils.answer(message, self.strings("autostart_status_enabled_with_message").format(
                        chat_id=target_chat_id, message=custom_message
                    ))
                else:
                    await utils.answer(message, self.strings("autostart_status_enabled_no_message").format(
                        chat_id=target_chat_id, message=global_message
                    ))
            else:
                await utils.answer(message, self.strings("autostart_status_disabled").format(chat_id=target_chat_id))
        else:
            await utils.answer(message, self.strings("invalid_trigger_arg"))

        if message.out:
            await message.delete()