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

# --- GELİŞMİŞ ŞİFRELEME ANAHTAR HAVUZU ---
# NapsternetV ve benzeri uygulamaların (NPVT, NPV, NM) kullandığı tüm bilinen anahtarlar
KEY_POOL = [
    b'5624398416543215', # Standart v3/v4
    b'6624398416543215', # Alternatif v4
    b'9b12c3d4e5f6a7b8', # Modlu APK'lar
    b'1234567890123456', # Debug
    b'8824398416543215', # Global versiyonlar
    b'1532456148934265', # Bazı v5 sürümleri
    b'0123456789abcdef'  # Genel test
]

def clean_and_pad(text):
    """Base64 verisini temizler ve eksik padding'i tamamlar."""
    text = text.strip().replace("\n", "").replace("\r", "")
    missing_padding = len(text) % 4
    if missing_padding:
        text += '=' * (4 - missing_padding)
    return text

def try_all_methods(encrypted_b64):
    """Şifreyi çözmek için her yolu dener."""
    encrypted_b64 = clean_and_pad(encrypted_b64)
    try:
        raw_data = base64.b64decode(encrypted_b64)
    except:
        return None

    # 1. Yöntem: AES-CBC (Farklı Anahtarlarla)
    for key in KEY_POOL:
        try:
            cipher = AES.new(key, AES.MODE_CBC, key)
            decrypted = unpad(cipher.decrypt(raw_data), AES.block_size)
            result = decrypted.decode('utf-8', errors='ignore')
            if any(k in result.lower() for k in ["host", "payload", "proxy", "port", "add", "id"]):
                return result
        except:
            continue

    # 2. Yöntem: Ham Base64 (Şifresiz olma ihtimali)
    try:
        decoded = raw_data.decode('utf-8', errors='ignore')
        if any(k in decoded.lower() for k in ["host", "payload", "proxy", "port", "get", "post"]):
            return decoded
    except:
        pass

    return None

def ultimate_analysis(content):
    if not content.startswith("NPVT1"):
        return "⚠️ Bu dosya geçerli bir NPVT1 formatında değil."

    data_blocks = content.replace("NPVT1", "").strip().split(',')
    
    final_output = []
    
    for i, block in enumerate(data_blocks):
        if len(block) < 8: continue
        
        decrypted_text = try_all_methods(block)
        if decrypted_text:
            final_output.append(decrypted_text)
            
    if not final_output:
        # 3. Yöntem: Dosya içindeki gizli stringleri Regex ile bulmaya çalış
        # Şifrelenmiş blok içinde bazen plaintext kısımlar kalabilir
        plain_text_finds = re.findall(r'[a-zA-Z0-9\.\-\_\/]{10,}', content)
        if plain_text_finds:
            matches = [f for f in plain_text_finds if "." in f or "/" in f]
            if matches:
                return "🔓 **Kısmi Veri Çıkarımı (Plaintext):**\n\n" + "\n".join([f"`{m}`" for m in matches[:10]])

        return "❌ **Şifreleme Kırılamadı.**\n\nBu dosya büyük ihtimalle 'Hardware Binding' (cihaza özel ID) ile şifrelenmiş. Bu tür dosyalar sadece dosyayı oluşturan kişinin telefonunda açılabilir."

    report = "🔓 **VPN YAPILANDIRMASI ÇÖZÜLDÜ**\n"
    report += "━━━━━━━━━━━━━━━\n\n"
    for idx, item in enumerate(final_output):
        # Payload temizleme ve düzenleme
        formatted = item.replace("[crlf]", "\n").replace("[split]", "\n--- SPLIT ---\n")
        report += f"📦 **Blok {idx+1}:**\n```text\n{formatted}\n```\n"
        
    return report

# --- RENDER KONTROL ---
async def handle(request): return web.Response(text="Ultimate Cracker Online")
async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080)))
    await site.start()

# --- BOT HANDLERS ---
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.reply("🧪 **Aýgül Ultimate Cracker v3.0**\n\nSistem en derin şifreleme katmanlarını analiz etmeye hazır. Dosyayı gönder, tüm bilinen yöntemleri deneyeyim.")

@dp.message_handler(content_types=['document', 'text'])
async def handle_file(message: types.Message):
    wait = await message.reply("🧬 **Heuristic analiz ve Brute-force denemeleri yapılıyor...**")
    
    try:
        content = ""
        if message.document:
            file_info = await bot.get_file(message.document.file_id)
            downloaded = await bot.download_file(file_info.file_path)
            content = downloaded.read().decode('utf-8', errors='ignore')
        else:
            content = message.text

        result = ultimate_analysis(content)
        await wait.edit_text(result, parse_mode="Markdown")
        
    except Exception as e:
        await wait.edit_text(f"❌ Kritik Sistem Hatası: {e}")

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(start_web_server())
    executor.start_polling(dp, skip_updates=True)
