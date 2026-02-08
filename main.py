import logging
import base64
import json
import os
import asyncio
import re
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiohttp import web
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# --- AYARLAR ---
API_TOKEN = '8585405629:AAEKq7Kj029nfeS4k5etov7ftP2gxATtLRI'
ADMIN_ID = 7611297191

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- GENİŞLETİLMİŞ ANAHTAR LİSTESİ ---
# NapsternetV sürümlerinde kullanılan farklı anahtarlar
KEYS_TO_TRY = [
    b'5624398416543215', # Standart v3/v4 anahtarı
    b'9b12c3d4e5f6a7b8', # Bazı modlu sürümler
    b'1234567890123456', # Test anahtarı
    b'6624398416543215'  # Alternatif anahtar
]

def attempt_decrypt(encrypted_base64):
    """Farklı anahtarlarla deşifre denemesi yapar."""
    try:
        # Padding düzeltme
        missing_padding = len(encrypted_base64) % 4
        if missing_padding:
            encrypted_base64 += '=' * (4 - missing_padding)
            
        encrypted_data = base64.b64decode(encrypted_base64)
        
        for key in KEYS_TO_TRY:
            try:
                # Genellikle IV ve Key aynıdır
                cipher = AES.new(key, AES.MODE_CBC, key)
                decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)
                text = decrypted.decode('utf-8', errors='ignore')
                
                # Eğer içinde VPN anahtar kelimeleri varsa doğru anahtarı bulduk demektir
                keywords = ["host", "payload", "proxy", "port", "id", "add", "net", "tls"]
                if any(k in text.lower() for k in keywords):
                    return text
            except:
                continue
    except:
        pass
    return None

def analyze_npvt(content):
    if not content.startswith("NPVT1"):
        return "⚠️ Geçersiz NPVT1 formatı."

    payload_area = content.replace("NPVT1", "").strip()
    # Bazı dosyalar virgül yerine direkt şifreli blok içerir
    parts = payload_area.split(',')
    
    decrypted_results = []
    
    for part in parts:
        if len(part) < 10: continue
        
        # Önce şifre kırmayı dene
        decrypted = attempt_decrypt(part)
        if decrypted:
            decrypted_results.append(decrypted)
        else:
            # Şifreli değilse düz base64 dene
            try:
                padded = part + "=" * ((4 - len(part) % 4) % 4)
                plain = base64.b64decode(padded).decode('utf-8', errors='ignore')
                if any(k in plain.lower() for k in ["host", "payload", "proxy", "port"]):
                    decrypted_results.append(plain)
            except:
                continue

    if not decrypted_results:
        return "❌ Maalesef bu dosyanın şifreleme anahtarı kütüphanemizde yok.\n\n💡 Bu dosya çok yeni bir yöntemle korunuyor olabilir."

    # Sonucu düzenle ve Payload kısımlarını belirginleştir
    final_text = "🔓 **VPN CONFIG DEŞİFRE EDİLDİ**\n"
    final_text += "━━━━━━━━━━━━━━━\n\n"
    
    for i, res in enumerate(decrypted_results):
        # Gereksiz boşlukları ve karakterleri temizle
        clean_res = res.strip()
        final_text += f"📦 **Blok {i+1}:**\n```text\n{clean_res}\n```\n"
        
    return final_text

# --- RENDER CANLI TUTMA ---
async def handle(request): return web.Response(text="Deep Cracker Online")
async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080)))
    await site.start()

# --- BOT İŞLEMLERİ ---
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("🕵️ **Aýgül Deep Cracker v2.0**\n\nBana en zorlu .npvt dosyalarını gönder, tüm anahtarları deneyerek Payload'ı sökmeye çalışayım.")

@dp.message_handler(content_types=['document'])
async def handle_doc(message: types.Message):
    status_msg = await message.reply("🔍 **Kaba kuvvet (Brute-force) anahtar denemesi yapılıyor...**")
    
    try:
        file_info = await bot.get_file(message.document.file_id)
        downloaded = await bot.download_file(file_info.file_path)
        content = downloaded.read().decode('utf-8', errors='ignore')
        
        result = analyze_npvt(content)
        await status_msg.edit_text(result, parse_mode="Markdown")
    except Exception as e:
        await status_msg.edit_text(f"❌ Hata: {e}")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(start_web_server())
    executor.start_polling(dp, skip_updates=True)
