import logging
import base64
import json
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiohttp import web

# --- AYARLAR ---
# Yeni verdiğin Token
API_TOKEN = '8585405629:AAEKq7Kj029nfeS4k5etov7ethP2gxATtLRI'
ADMIN_ID = 7611297191

# Loglama ayarları
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# --- ANALİZ MANTIĞI ---
def analyze_vpn_config(content):
    """
    VPN yapılandırma dosyalarını (NPVT, VMESS vb.) analiz eden fonksiyon.
    """
    try:
        # NPVT (NapsternetV) Dosyası Analizi
        if content.startswith("NPVT1"):
            # NPVT1 başlığını kaldır
            raw_data = content.replace("NPVT1", "").strip()
            # NPVT dosyaları genellikle virgülle ayrılmış base64 bloklarıdır
            parts = raw_data.split(',')
            
            analysis_report = "📂 **Dosya Türü:** NapsternetV (.npvt)\n"
            analysis_report += "🔍 **Yapılandırma Analizi:**\n\n"
            
            for i, part in enumerate(parts):
                try:
                    # Base64 decode işlemi
                    decoded = base64.b64decode(part).decode('utf-8', errors='ignore')
                    if len(decoded) > 10:
                        analysis_report += f"🔹 **Blok {i+1}:** `{decoded[:200]}...` \n\n"
                except:
                    continue
            
            return analysis_report

        # VMESS Link Analizi
        elif content.startswith("vmess://"):
            v_data = content.replace("vmess://", "")
            decoded = base64.b64decode(v_data).decode('utf-8')
            js = json.loads(decoded)
            return (f"🚀 **VMESS (V2Ray) Detayları:**\n\n"
                    f"📍 **Adres:** `{js.get('add')}`\n"
                    f"🔢 **Port:** `{js.get('port')}`\n"
                    f"🆔 **UUID:** `{js.get('id')}`\n"
                    f"🌐 **Protokol:** `{js.get('net')}`\n"
                    f"📝 **İsim:** `{js.get('ps')}`")

        else:
            return "⚠️ **Bilinmeyen Format:** Bu dosya içeriği şifreli bir VPN yapılandırması gibi görünüyor ancak standart çözümleyicilerle açılamadı."

    except Exception as e:
        return f"❌ **Analiz Hatası:** Dosya okunurken bir sorun oluştu: {str(e)}"

# --- RENDER İÇİN WEB SUNUCUSU ---
async def handle(request):
    return web.Response(text="VPN Analyzer Bot Aktif!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 8080)))
    await site.start()

# --- BOT KOMUTLARI ---
@dp.message_handler(commands=['start'])
async def welcome(message: types.Message):
    await message.reply("Merhaba! Ben VPN Yapılandırma Analiz Botu. 🛠\n\nBana bir `.npvt`, `.npv` dosyası gönder veya bir `vmess://` linki at, içeriğini senin için analiz edeyim.")

@dp.message_handler(content_types=['document'])
async def handle_docs(message: types.Message):
    # Dosya bilgilerini al
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    
    # Dosyayı indir
    downloaded_file = await bot.download_file(file_path)
    # İçeriği oku (şifreli metni al)
    content = downloaded_file.read().decode('utf-8', errors='ignore').strip()
    
    msg = await message.reply("⏳ **Dosya analiz ediliyor, lütfen bekleyin...**")
    
    # Analiz et ve sonucu gönder
    result = analyze_vpn_config(content)
    await msg.edit_text(result, parse_mode="Markdown")

@dp.message_handler(content_types=['text'])
async def handle_text(message: types.Message):
    # Eğer metin olarak VPN linki atılırsa
    if "://" in message.text:
        result = analyze_vpn_config(message.text)
        await message.reply(result, parse_mode="Markdown")

if __name__ == '__main__':
    # Web sunucuyu botla birlikte çalıştır
    loop = asyncio.get_event_loop()
    loop.create_task(start_web_server())
    print("Bot ve Analiz motoru başlatıldı...")
    executor.start_polling(dp, skip_updates=True)
