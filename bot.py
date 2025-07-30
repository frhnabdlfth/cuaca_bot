from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime
import requests

BOT_TOKEN = '7802750048:AAEfaXzEYeVuipRG1iGaSfBwsirXqRNSb1I'
WEATHER_API_KEY = 'e12909bee6cf4f3f8e2102800253007'

# Kamus terjemahan kondisi cuaca
TERJEMAHAN_CUACA = {
    "Sunny": "Cerah", "Clear": "Cerah", "Partly cloudy": "Sebagian berawan", "Cloudy": "Berawan",
    "Overcast": "Mendung", "Mist": "Berkabut", "Patchy rain possible": "Kemungkinan hujan ringan",
    "Light rain": "Hujan ringan", "Moderate rain": "Hujan sedang", "Heavy rain": "Hujan lebat",
    "Thunderstorm": "Hujan petir", "Fog": "Kabut", "Patchy light rain": "Gerimis",
    "Moderate or heavy rain shower": "Hujan deras", "Light snow": "Salju ringan", "Rain": "Hujan",
    "Patchy rain nearby": "Hujan ringan di sekitar",
    "Light rain shower": "Hujan ringan",
    "Patchy light drizzle": "Gerimis ringan tersebar",
}

# Emoji sesuai kondisi
EMOJI_CUACA = {
    "Cerah": "☀️", "Sebagian berawan": "🌤️", "Berawan": "☁️", "Mendung": "🌥️",
    "Berkabut": "🌫️", "Hujan ringan": "🌦️", "Hujan sedang": "🌧️", "Hujan lebat": "🌧️",
    "Hujan petir": "⛈️", "Kabut": "🌫️", "Gerimis": "🌧️", "Salju ringan": "🌨️"
}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Selamat datang! 🌦️\n"
        "Ketik /cuaca [nama kota atau wilayah] untuk melihat informasi cuaca.\n\n"
        "Contoh:\n"
        "• /cuaca Jakarta Selatan\n"
        "• /cuaca Bandung, Jawa Barat\n"
        "• /cuaca New York\n\n"

        "Jika tidak ada lokasi yang diberikan, bot akan meminta Anda untuk memasukkan lokasi.\n"
        "Created by frhnabdlfth\n"
    )

# /cuaca
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

        # Tambahkan prakiraan hujan 6 jam ke depan
        prakiraan = data["forecast"]["forecastday"][0]["hour"]
        jam_sekarang = dt.hour
        prakiraan_emoji = ""

        for jam in prakiraan:
            jam_data = datetime.strptime(jam["time"], "%Y-%m-%d %H:%M")
            if jam_data.hour >= jam_sekarang and jam_data.hour <= jam_sekarang + 5:
                jam_str = jam_data.strftime("%H:%M")
                kondisi_hour = jam["condition"]["text"]
                kondisi_id = TERJEMAHAN_CUACA.get(kondisi_hour, kondisi_hour)
                emoji_hour = EMOJI_CUACA.get(kondisi_id, "🌥️")

                prakiraan_emoji += f"\n🕓 {jam_str} — {emoji_hour} {kondisi_id}"

        if prakiraan_emoji:
            pesan += "\n\n📆 *Prakiraan Hujan 6 Jam ke Depan:*"
            pesan += prakiraan_emoji

        await update.message.reply_text(pesan, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Gagal mengambil data.\nError: `{e}`", parse_mode="Markdown")

# Jalankan bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cuaca", cuaca))
    print("Bot berjalan... tekan Ctrl+C untuk keluar.")
    app.run_polling()
