import logging
import base64
import json
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiohttp import web

# --- AYARLAR ---
API_TOKEN = '8585405629:AAEKq7Kj029nfeS4k5etov7ftP2gxATtLRI'
ADMIN_ID = 7611297191

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- ANALİZ MOTORU ---
def decrypt_npvt(raw_content):
    try:
        data = raw_content.strip()
        if not data.startswith("NPVT1"):
            return "⚠️ Bu dosya geçerli bir NPVT1 formatı değil."

        payload = data.replace("NPVT1", "").strip()
        parts = payload.split(',')
        
        # Markdown hatasını önlemek için sonuçları liste olarak tutalım
        results = []
        
        for i, part in enumerate(parts):
            try:
                # Padding düzeltme
                padded_part = part + "=" * ((4 - len(part) % 4) % 4)
                decoded_bytes = base64.b64decode(padded_part)
                decoded_text = decoded_bytes.decode('utf-8', errors='ignore').strip()
                
                if len(decoded_text) > 2:
                    # Markdown özel karakterlerini temizle veya güvenli hale getir
                    safe_text = decoded_text.replace("`", "'")
                    results.append(f"📍 Katman {i+1}:\n{safe_text}")
            except:
                continue
        
        if not results:
            return "❌ Dosya çözülemedi. Muhtemelen AES ile şifrelenmiş."

        # Mesajı oluştururken kod bloğu içine alarak Markdown hatasını engelle
        final_report = "🔓 **VPN Dosya Analizi**\n\n"
        for res in results[:5]: # Çok uzun mesaj olmaması için ilk 5 katman
            final_report += f"```\n{res}\n```\n"
        
        return final_report

    except Exception as e:
        return f"❌ Sistem Hatası: {str(e)}"

# --- RENDER CANLI TUTMA ---
async def handle(request):
    return web.Response(text="Bot Online")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080)))
    await site.start()

# --- MESAJ YÖNETİMİ ---
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("🚀 **VPN Cracker Hazır!**\nDosyayı gönder, Markdown hatası almadan içeriği görelim.")

@dp.message_handler(content_types=['document'])
async def handle_document(message: types.Message):
    wait_msg = await message.reply("🔍 **Şifreler çözülüyor...**")
    
    try:
        file_info = await bot.get_file(message.document.file_id)
        downloaded = await bot.download_file(file_info.file_path)
        content = downloaded.read().decode('utf-8', errors='ignore')
        
        result = decrypt_npvt(content)
        # MarkdownV2 veya Markdown yerine düz metin güvenliği için kod bloğu kullandık
        await wait_msg.edit_text(result, parse_mode="Markdown")
        
    except Exception as e:
        await wait_msg.edit_text(f"❌ Hata oluştu: {str(e)}")

@dp.message_handler(content_types=['text'])
async def handle_text(message: types.Message):
    if "NPVT1" in message.text:
        res = decrypt_npvt(message.text)
        await message.reply(res, parse_mode="Markdown")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(start_web_server())
    executor.start_polling(dp, skip_updates=True)
