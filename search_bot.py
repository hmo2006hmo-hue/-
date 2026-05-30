import asyncio
import io
from telethon import TelegramClient, events
from telethon.tl.functions.messages import SearchRequest
from telethon.tl.types import InputMessagesFilterEmpty
from telethon.tl.functions.bots import SetBotCommandsRequest
from telethon.tl.types import BotCommand, BotCommandScopeDefault

# البيانات الخاصة بالبوت والحساب
API_ID = 31545158
API_HASH = '68bd4a4931f41af0e8e5e034ef252cdd'
BOT_TOKEN = '8724382783:AAE-Uuy_nvKHge9wOr1ajlpTz1TuIzjm9j8'

# إنشاء الجلسات داخل Pydroid 3
user_client = TelegramClient('user_session', API_ID, API_HASH)
bot_client = TelegramClient('bot_session', API_ID, API_HASH)

@bot_client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    await event.reply(
        '👋 مرحباً! أنا بوت البحث عن الملفات والرسائل\n\n'
        '🔍 للبحث استخدم:\n'
        '/search @اسم_القناة كلمة_البحث\n\n'
        '📌 مثال:\n'
        '/search @hossammNow عذابي'
    )

@bot_client.on(events.NewMessage(pattern='/search'))
async def search_handler(event):
    parts = event.text.split(' ', 2)
    bot_chat_id = event.chat_id
    is_private = event.is_private

    if is_private:
        if len(parts) < 3 or not parts[1].startswith('@'):
            await event.reply(
                '⚠️ الصيغة الصحيحة:\n'
                '/search @اسم_القناة كلمة_البحث\n\n'
                '📌 مثال:\n'
                '/search @hossammNow عذابي'
            )
            return
        channel = parts[1]
        query = parts[2]
    else:
        if len(parts) < 2:
            await event.reply('⚠️ اكتب:\n/search كلمة_البحث')
            return
        if len(parts) >= 3 and parts[1].startswith('@'):
            channel = parts[1]
            query = parts[2]
        else:
            channel = event.chat_id
            query = parts[1]

    searching_msg = await event.reply(f'🔍 جارٍ البحث عن "{query}" وإرسال النتائج...')

    try:
        results = await user_client(SearchRequest(
            peer=channel, q=query,
            filter=InputMessagesFilterEmpty(),
            min_date=None, max_date=None,
            offset_id=0, add_offset=0,
            limit=10, max_id=0, min_id=0, hash=0
        ))

        try:
            await searching_msg.delete()
        except:
            pass

        if not results.messages:
            await event.reply('❌ لا توجد نتائج مطابقة.')
            return

        for msg in results.messages:
            try:
                # إذا كانت الرسالة تحتوي على أي نوع من الميديا (ملف، صوت، صورة، فيديو إلخ)
                if msg.media:
                    # جلب اسم الملف الأصلي إن وجد لتسميته بشكل صحيح عند الرفع
                    file_name = "file"
                    if hasattr(msg.media, 'document') and msg.media.document:
                        for attr in msg.media.document.attributes:
                            if hasattr(attr, 'file_name'):
                                file_name = attr.file_name
                                break
                    
                    try:
                        # محاولة أولى: إرسال الملف مباشرة عبر السيرفر لتوفير الوقت والإنترنت
                        await bot_client.send_message(bot_chat_id, file=msg.media, message=msg.message or "")
                    except Exception:
                        # محاولة ثانية (للملفات المحمية والمقيدة): الحساب يقوم بتحميل الملف في الرام والبوت يرفعه
                        file_buffer = io.BytesIO()
                        await user_client.download_media(msg.media, file=file_buffer)
                        file_buffer.seek(0)
                        file_buffer.name = file_name # إعطاء الملف اسمه وامتداده الأصلي (مثل .json أو .zip)
                        
                        await bot_client.send_message(bot_chat_id, file=file_buffer, message=msg.message or "")
                
                # إذا كانت الرسالة نصية فقط بدون ميديا
                elif msg.message:
                    await bot_client.send_message(bot_chat_id, msg.message)
                    
            except Exception as send_error:
                print(f"خطأ أثناء إرسال أحد الملفات: {send_error}")

    except Exception as e:
        try:
            await searching_msg.delete()
        except:
            pass
        await event.reply(f'⚠️ خطأ في البحث: {str(e)}')

async def main():
    await user_client.start()
    print('✅ حساب شخصي متصل!')

    await bot_client.start(bot_token=BOT_TOKEN)
    print('✅ البوت يعمل!')

    await bot_client(SetBotCommandsRequest(
        scope=BotCommandScopeDefault(),
        lang_code='ar',
        commands=[
            BotCommand(command='start', description='بدء استخدام البوت'),
            BotCommand(command='search', description='بحث - مثال: /search @hossammNow كلمة'),
        ]
    ))
    print('✅ تم إضافة الأوامر!')

    await asyncio.gather(
        bot_client.run_until_disconnected(),
        user_client.run_until_disconnected()
    )

if __name__ == '__main__':
    asyncio.run(main())