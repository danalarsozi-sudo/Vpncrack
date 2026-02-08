import logging
import base64
import json
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiohttp import web

# --- AYARLAR ---
# Senin verdiğin güncel token
API_TOKEN = '8585405629:AAEKq7Kj029nfeS4k5etov7ftP2gxATtLRI'
ADMIN_ID = 7611297191

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- DECODER MANTIĞI ---
def decrypt_vpn_config(data_str):
    try:
        if data_str.startswith("NPVT1"):
            clean_data = data_str.replace("NPVT1", "").strip()
            # NPVT dosyaları virgüllü base64 blokları içerir
            parts = clean_data.split(',')
            result_text = "📂 **NapsternetV (.npvt) Analiz Sonucu**\n\n"
            
            for i, part in enumerate(parts[:3]): # İlk 3 bloğu dene
                try:
                    decoded = base64.b64decode(part).decode('utf-8', errors='ignore')
                    if len(decoded) > 5:
                        result_text += f"🔍 **Katman {i+1}:**\n`{decoded[:300]}`\n\n"
                except:
                    continue
            return result_text
        
        elif "vmess://" in data_str:
            v_link = data_str.split("vmess://")[1]
            decoded = base64.b64decode(v_link).decode('utf-8')
            js = json.loads(decoded)
            return f"🚀 **VMESS Bulundu:**\n📍 Adres: `{js.get('add')}`\n🔢 Port: `{js.get('port')}`\n🆔 ID: `{js.get('id')}`"
            
        return "⚠️ Bu dosya formatı tanınamadı veya şifreleme çok karmaşık."
    except Exception as e:
        return f"❌ Hata: {str(e)}"

# --- RENDER CANLI TUTMA ---
async def handle(request):
    return web.Response(text="Bot Aktif!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080)))
    await site.start()

# --- BOT MESAJLARI ---
@dp.message_handler(commands=['start'])
async def welcome(message: types.Message):
    await message.reply("🛠 VPN Config Analyzer hazır!\n\nBana .npvt dosyası gönder, içini açayım.")

@dp.message_handler(content_types=['document', 'text'])
async def handle_input(message: types.Message):
    content = ""
    if message.document:
        file = await bot.get_file(message.document.file_id)
        downloaded = await bot.download_file(file.file_path)
        content = downloaded.read().decode('utf-8', errors='ignore').strip()
    else:
        content = message.text
        
    res = decrypt_vpn_config(content)
    await message.reply(res, parse_mode="Markdown")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(start_web_server())
    executor.start_polling(dp, skip_updates=True)
