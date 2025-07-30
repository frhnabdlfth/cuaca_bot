import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime
import requests
import google.generativeai as genai
from openai import OpenAI

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

TERJEMAHAN_CUACA = {
    "Sunny": "Cerah", "Clear": "Cerah", "Partly cloudy": "Sebagian berawan", "Cloudy": "Berawan",
    "Overcast": "Mendung", "Mist": "Berkabut", "Patchy rain possible": "Kemungkinan hujan ringan",
    "Light rain": "Hujan ringan", "Moderate rain": "Hujan sedang", "Heavy rain": "Hujan lebat",
    "Thunderstorm": "Hujan petir", "Fog": "Kabut", "Patchy light rain": "Gerimis",
    "Moderate or heavy rain shower": "Hujan deras", "Light snow": "Salju ringan", "Rain": "Hujan",
    "Patchy rain nearby": "Hujan ringan di sekitar", "Light rain shower": "Hujan ringan",
    "Patchy light drizzle": "Gerimis ringan tersebar",
}

EMOJI_CUACA = {
    "Cerah": "☀️", "Sebagian berawan": "🌤️", "Berawan": "☁️", "Mendung": "🌥️",
    "Berkabut": "🌫️", "Hujan ringan": "🌦️", "Hujan sedang": "🌧️", "Hujan lebat": "🌧️",
    "Hujan petir": "⛈️", "Kabut": "🌫️", "Gerimis": "🌧️", "Salju ringan": "🌨️"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Selamat datang! 🌦️\n"
        "Ketik:\n"
        "• /cuaca [lokasi] → Info cuaca\n"
        "• /tanya [pesan] → Tanya AI (ChatGPT-4)\n\n"
        "Contoh:\n"
        "• /cuaca Jakarta Selatan\n"
        "• /tanya Apa itu El Nino?\n\n"
        "Created by frhnabdlfth"
    )

async def cuaca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Ketik lokasi setelah perintah.\nContoh: `/cuaca Yogyakarta`", parse_mode="Markdown")
        return

    lokasi_input = " ".join(context.args)

    try:
        response = requests.get("https://api.weatherapi.com/v1/forecast.json", params={
            "key": WEATHER_API_KEY,
            "q": lokasi_input,
            "lang": "id",
            "days": 1,
        }, timeout=10)

        data = response.json()

        if "error" in data:
            await update.message.reply_text(f"⚠️ Maaf, data cuaca tidak ditemukan untuk: *{lokasi_input}*", parse_mode="Markdown")
            return

        lokasi = data["location"]["name"]
        wilayah = data["location"]["region"]
        negara = data["location"]["country"]
        waktu_iso = data["current"]["last_updated"]

        dt = datetime.strptime(waktu_iso, "%Y-%m-%d %H:%M")
        bulan_id = {
            1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
            5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
            9: "September", 10: "Oktober", 11: "November", 12: "Desember"
        }
        waktu = f"{dt.day} {bulan_id[dt.month]} {dt.year} Pukul {dt.strftime('%H.%M')}"

        suhu = data["current"]["temp_c"]
        kondisi_en = data["current"]["condition"]["text"]
        kondisi = TERJEMAHAN_CUACA.get(kondisi_en, kondisi_en)
        emoji = EMOJI_CUACA.get(kondisi, "🌤️")
        kelembaban = data["current"]["humidity"]
        angin = data["current"]["wind_kph"]

        pesan = (
            f"📍 **Cuaca di {lokasi}, {wilayah}, {negara}**\n"
            f"🕒 Terakhir diperbarui: {waktu}\n"
            f"{emoji} Kondisi: {kondisi}\n"
            f"🌡️ Suhu: {suhu}°C\n"
            f"💧 Kelembaban: {kelembaban}%\n"
            f"🌬️ Angin: {angin} km/jam"
        )

        perkiraan = data["forecast"]["forecastday"][0]["hour"]
        jam_sekarang = dt.hour
        perkiraan_emoji = ""

        for jam in perkiraan:
            jam_data = datetime.strptime(jam["time"], "%Y-%m-%d %H:%M")
            if jam_sekarang <= jam_data.hour <= jam_sekarang + 5 and jam_data.day == dt.day:
                jam_str = jam_data.strftime("%H:%M")
                kondisi_hour = jam["condition"]["text"]
                kondisi_id = TERJEMAHAN_CUACA.get(kondisi_hour, kondisi_hour)
                emoji_hour = EMOJI_CUACA.get(kondisi_id, "🌥️")
                perkiraan_emoji += f"\n🕓 {jam_str} — {emoji_hour} {kondisi_id}"

        if perkiraan_emoji:
            pesan += "\n\n📆 *Prakiraan Hujan 6 Jam ke Depan:*"
            pesan += perkiraan_emoji

        await update.message.reply_text(pesan, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Gagal mengambil data.\nError: `{e}`", parse_mode="Markdown")

# Konfigurasi Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("gemini-pro")

async def tanya(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Ketik pertanyaan setelah perintah.\nContoh: `/tanya Apa itu awan cumulonimbus?`",
            parse_mode="Markdown"
        )
        return

    prompt = " ".join(context.args)

    # Coba pakai GPT-3.5 dulu
    try:
        if not OPENAI_API_KEY:
            raise ValueError("API Key OpenAI tidak ditemukan.")

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Ganti dari gpt-4o ke gpt-3.5-turbo
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        jawaban = response.choices[0].message.content
        await update.message.reply_text(jawaban)
        return

    except Exception as e_openai:
        # Fallback ke Gemini
        try:
            if not GEMINI_API_KEY:
                raise ValueError("API Key Gemini tidak ditemukan.")
            response = gemini_model.generate_content(prompt)
            jawaban = response.text
            await update.message.reply_text(jawaban)
            return

        except Exception as e_gemini:
            await update.message.reply_text(
                "❌ Gagal menjawab pertanyaan.\n"
                f"Error OpenAI: `{e_openai}`\n"
                f"Error Gemini: `{e_gemini}`",
                parse_mode="Markdown"
            )

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cuaca", cuaca))
    app.add_handler(CommandHandler("tanya", tanya))

    print("Bot berjalan... tekan Ctrl+C untuk keluar.")
    app.run_polling()
