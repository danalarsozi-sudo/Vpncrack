import logging
import base64
import json
import os
import asyncio
import re
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiohttp import web

# --- AYARLAR ---
API_TOKEN = '8585405629:AAEKq7Kj029nfeS4k5etov7ftP2gxATtLRI'
ADMIN_ID = 7611297191

# Logları Render panelinden takip etmek için
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
        
        report = "🔓 **VPN Dosya Analizi Başlatıldı**\n"
        report += "━━━━━━━━━━━━━━━\n"
        
        found_data = False
        for i, part in enumerate(parts):
            try:
                # Padding düzeltme
                padded_part = part + "=" * ((4 - len(part) % 4) % 4)
                decoded_bytes = base64.b64decode(padded_part)
                
                # UTF-8 denemesi
                decoded_text = decoded_bytes.decode('utf-8', errors='ignore')
                
                if len(decoded_text) > 3:
                    found_data = True
                    # Eğer içerik JSON ise güzelleştir
                    if "{" in decoded_text and "}" in decoded_text:
                        report += f"📍 **Katman {i+1} (Sistem Verisi):**\n`{decoded_text[:500]}`\n\n"
                    else:
                        report += f"🔑 **Katman {i+1} (Ham Şifre):**\n`{decoded_text[:300]}`\n\n"
            except:
                continue
        
        if not found_data:
            return "❌ **Kritik Hata:** Dosya askeri düzeyde şifrelenmiş (AES). Ham Base64 çözücü bu kilidi açamadı."
            
        report += "━━━━━━━━━━━━━━━\n⚠️ *Not: Eğer yukarıdaki veriler anlamsızsa, dosya özel bir KEY ile kilitlenmiştir.*"
        return report

    except Exception as e:
        return f"💀 **Analiz Hatası:** {str(e)}"

# --- RENDER CANLI TUTMA ---
async def handle(request):
    return web.Response(text="Aygül VPN Cracker: Aktif")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- MESAJ YÖNETİMİ ---
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("🚀 **VPN Cracker Hazır!**\n\nBana `.npvt` dosyasını gönder, şifreleme katmanlarını senin için ayırayım.")

@dp.message_handler(content_types=['document'])
async def handle_document(message: types.Message):
    # Dosya boyutu kontrolü (çok büyük dosyalar botu dondurabilir)
    if message.document.file_size > 1024 * 1024: # 1MB sınırı
        await message.reply("❌ Dosya çok büyük. Lütfen 1MB altı bir config gönder.")
        return

    wait_msg = await message.reply("🔍 **Şifreler çözülüyor, lütfen bekleyin...**")
    
    try:
        file_info = await bot.get_file(message.document.file_id)
        downloaded = await bot.download_file(file_info.file_path)
        content = downloaded.read().decode('utf-8', errors='ignore')
        
        result = decrypt_npvt(content)
        await wait_msg.edit_text(result, parse_mode="Markdown")
        
    except Exception as e:
        await wait_msg.edit_text(f"❌ **Dosya okunamadı:** {e}")

@dp.message_handler(content_types=['text'])
async def handle_text(message: types.Message):
    if message.text.startswith("vmess://") or message.text.startswith("NPVT1"):
        res = decrypt_npvt(message.text)
        await message.reply(res, parse_mode="Markdown")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(start_web_server())
    print("Bot başlatıldı...")
    executor.start_polling(dp, skip_updates=True)
