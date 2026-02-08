import logging
import base64
import json
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiohttp import web
from Crypto.Cipher import AES # Eğer bu hata verirse requirements'a ekleyeceğiz
from Crypto.Util.Padding import unpad

# --- AYARLAR ---
API_TOKEN = '8585405629:AAEKq7Kj029nfeS4k5etov7ftP2gxATtLRI'
ADMIN_ID = 7611297191

# NapsternetV Bilinen Şifre Çözme Anahtarları
# Bu anahtarlar olmadan dosya sadece "anlamsız yazı" olarak kalır
NPVT_KEY = b'5624398416543215' 
NPVT_IV = b'5624398416543215'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- GERÇEK DEŞİFRE MOTORU ---
def decrypt_aes_npvt(encoded_data):
    try:
        # Base64 ile dış kabuğu soy
        encrypted_data = base64.b64decode(encoded_data)
        
        # AES-CBC modu ile içeriği deşifre et
        cipher = AES.new(NPVT_KEY, AES.MODE_CBC, NPVT_IV)
        decrypted = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        
        return decrypted.decode('utf-8')
    except Exception as e:
        return None

def solve_config(content):
    if not content.startswith("NPVT1"):
        return "⚠️ Bu standart bir NPVT1 dosyası değil."

    payload_area = content.replace("NPVT1", "").strip()
    parts = payload_area.split(',')
    
    results = []
    for part in parts:
        # 1. Yöntem: AES Deşifre (Gerçek kırma işlemi)
        decrypted = decrypt_aes_npvt(part)
        if decrypted:
            results.append(decrypted)
        else:
            # 2. Yöntem: Eğer şifreli değilse düz Base64 dene
            try:
                padded = part + "=" * ((4 - len(part) % 4) % 4)
                db = base64.b64decode(padded).decode('utf-8', errors='ignore')
                if len(db) > 10 and any(x in db.lower() for x in ["host", "proxy", "payload", "get", "post"]):
                    results.append(db)
            except:
                continue

    if not results:
        return "❌ Dosya çok sıkı şifrelenmiş. Özel anahtar olmadan Payload okunamıyor."

    # Sonucu düzenle
    final = "🔓 **DEŞİFRE EDİLEN VPN AYARLARI**\n\n"
    for r in results:
        final += f"```text\n{r}\n```\n"
    return final

# --- RENDER/BOT AYARLARI ---
async def handle(request): return web.Response(text="Cracker Online")
async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080)))
    await site.start()

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.reply("🚀 **VPN Cracker (Deep Scan) Aktif!**\nŞimdi o dosyayı gönder, Payload'ları sökelim.")

@dp.message_handler(content_types=['document'])
async def handle_doc(message: types.Message):
    wait = await message.reply("⚙️ **AES Şifresi kırılıyor...**")
    file_info = await bot.get_file(message.document.file_id)
    downloaded = await bot.download_file(file_info.file_path)
    content = downloaded.read().decode('utf-8', errors='ignore')
    
    res = solve_config(content)
    await wait.edit_text(res, parse_mode="Markdown")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(start_web_server())
    executor.start_polling(dp, skip_updates=True)
