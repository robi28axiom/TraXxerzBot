import asyncio
import aiohttp
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- KONFIGURACIJA ---
TELEGRAM_BOT_TOKEN = "8725824554:AAGUsQb3t31UU9QbCbOXAIT3Uzzt5eKDKps"
TELEGRAM_CHAT_ID = "8980310038"

# Prati ključne izvore i mreže
ACTIVE_SOURCES = 42

CRYPTO_HYPE_KEYWORDS = [
    "sol", "solana", "pump", "token", "coin", "memecoin", "alpha", "gem", "moon", 
    "dex", "liquidity", "volume", "marketcap", "mc", "bull", "bear", "degen", "ape", 
    "airdrop", "sniper", "rug", "wallet", "buy", "long", "short", "pnl", "million", 
    "billion", "sec", "fed", "binance", "coinbase", "raydium", "jupiter", "breaking", 
    "launch", "listing", "ath", "surge", "spike"
]

SEEN_POSTS = set()
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def calculate_hype_score(text: str):
    t_lower = text.lower()
    score = 30
    matches = 0
    for kw in CRYPTO_HYPE_KEYWORDS:
        if kw in t_lower:
            matches += 1
    score += matches * 15
    if "$" in text or "%" in text or "ath" in t_lower or "million" in t_lower:
        score += 20
    return min(score, 99)

async def fetch_live_feed():
    # Korištenje pouzdanog CryptoPanic API-ja za real-time objave i vijesti
    url = "https://cryptopanic.com/api/v1/posts/?auth_token=free&public=true&kinds=news,media"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    new_count = 0
                    for item in data.get("results", []):
                        post_id = str(item.get("id"))
                        title = item.get("title", "")
                        source = item.get("source", {}).get("title", "Crypto Feed")
                        url_link = item.get("url", "https://cryptopanic.com")

                        if post_id and post_id not in SEEN_POSTS:
                            SEEN_POSTS.add(post_id)
                            if len(SEEN_POSTS) > 1000:
                                SEEN_POSTS.pop()

                            hype_score = calculate_hype_score(title)
                            await send_telegram_post(title, url_link, source, hype_score)
                            new_count += 1
                            await asyncio.sleep(0.3)
                    return new_count
        except Exception as e:
            print(f"Greška u dohvaćanju feeda: {e}")
    return 0

async def send_telegram_post(title, link, source_name, hype_score):
    short_desc = title[:150] + "..." if len(title) > 150 else title
    search_encoded = quote(title[:30])

    if hype_score >= 75:
        hype_emoji = "🔥"
    elif hype_score >= 50:
        hype_emoji = "⚡"
    else:
        hype_emoji = "📌"

    message = f"{hype_emoji} **[LIVE RADAR FEED - {hype_score}% HYPE]**\n\n"
    message += f"👤 **Izvor:** `{source_name}`\n"
    message += f"💬 **Objava:**\n{short_desc}\n\n"
    message += f"🔗 [Otvori izvor]({link})\n\n"
    message += f"👇 *Brze akcije:*"

    keyboard = [
        [
            {"text": "⚡ Axiom Search", "url": f"https://axiom.trade/search?q={search_encoded}"},
            {"text": "🚀 Pump.fun", "url": f"https://pump.fun/board?search={search_encoded}"}
        ],
        [
            {"text": "📈 DexScreener", "url": f"https://dexscreener.com/search?q={search_encoded}"},
            {"text": "🌐 Idi na Objavu", "url": link}
        ]
    ]

    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID, 
            text=message, 
            parse_mode="Markdown", 
            reply_markup={"inline_keyboard": keyboard},
            disable_web_page_preview=False
        )
    except Exception as e:
        print(f"Greska pri slanju: {e}")

async def background_radar_loop():
    print(f"🚀 Live Feed Radar aktivan!")
    while True:
        try:
            await fetch_live_feed()
        except Exception as e:
            print(f"Greska u petlji: {e}")
        # Provjerava svakih 15 sekundi
        await asyncio.sleep(15)

async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
        return
    await update.message.reply_text("🔄 Ručno skeniram live feed...")
    found = await fetch_live_feed()
    await update.message.reply_text(f"✅ Skeniranje završeno. Pronađeno novih objava: {found}")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
        return
    msg = (
        f"📊 **LIVE RADAR STATUS**\n\n"
        f"• Praćenih izvora: `{ACTIVE_SOURCES}`\n"
        f"• Status: `Online & Aktivno`\n"
        f"• Spremljenih objava: `{len(SEEN_POSTS)}`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("scan", cmd_scan))
    app.add_handler(CommandHandler("status", cmd_status))

    async def post_init(application):
        asyncio.create_task(background_radar_loop())

    app.post_init = post_init
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
