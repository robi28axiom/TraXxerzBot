import asyncio
import re
import aiohttp
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- KONFIGURACIJA ---
TELEGRAM_BOT_TOKEN = "8725824554:AAGUsQb3t31UU9QbCbOXAIT3Uzzt5eKDKps"
TELEGRAM_CHAT_ID = "8980310038"

ACTIVE_PROFILES = [
    "elonmusk", "realDonaldTrump", "WhiteHouse", "POTUS", "SECGov",
    "federalreserve", "USTreasury", "AccountantForYou", "MarioNawfal",
    "WatcherGuru", "zerohedge", "NickTimiraos", "WSJ", "business",
    "Ansem", "MustStopMurad", "blknoiz06", "SolanaLegend", "CryptoCapo_",
    "TheFlowHorse", "AltcoinSherpa", "GCRClassic", "HsakaTrades", "lookonchain",
    "bubblemaps", "PeckShieldAlert", "ArkhamIntel", "spotonchain", "solana",
    "phantom", "RaydiumProtocol", "JupiterExchange", "meteoraAG", "birdeye_so",
    "DexScreenerApp", "AxiomTrade", "Photon_Sol", "BullX_io", "binance",
    "coinbase", "a16z", "paradigm"
]

CRYPTO_HYPE_KEYWORDS = [
    "sol", "solana", "pump", "token", "coin", "memecoin", "alpha", "gem", "moon", 
    "dex", "liquidity", "volume", "marketcap", "mc", "bull", "bear", "degen", "ape", 
    "airdrop", "sniper", "rug", "wallet", "buy", "long", "short", "pnl", "million", 
    "billion", "sec", "fed", "binance", "coinbase", "raydium", "jupiter", "breaking", 
    "launch", "listing", "ath", "surge", "spike"
]

SEEN_POSTS = set()
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def calculate_hype_score(title: str):
    t_lower = title.lower()
    score = 30  # Početna baza za svaku objavu
    
    matches = 0
    for kw in CRYPTO_HYPE_KEYWORDS:
        if kw in t_lower:
            matches += 1
            
    score += matches * 15
    
    if "$" in title or "%" in title or "ath" in t_lower or "million" in t_lower:
        score += 20
        
    return min(score, 99)

async def send_hype_alert(title, link, source_name, hype_score):
    short_desc = title[:120] + "..." if len(title) > 120 else title
    search_encoded = quote(title[:30])

    if hype_score >= 75:
        hype_emoji = "🔥"
    elif hype_score >= 50:
        hype_emoji = "⚡"
    else:
        hype_emoji = "💤"

    message = f"{hype_emoji} **[X / HYPE RADAR - {hype_score}% HYPE]**\n\n"
    message += f"👤 **Izvor:** `{source_name}`\n"
    message += f"💬 **Objava:** {short_desc}\n"
    message += f"📈 **Crypto/Hype Procjena:** `{hype_score}%`\n\n"
    message += f"🔗 [Otvori izvor]({link})\n\n"
    message += f"👇 *Brze akcije za Token/Ape:*"

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
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"Greska pri slanju: {e}")

async def fetch_live_feed():
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
                        source = item.get("source", {}).get("title", "X Alpha Source")
                        url_link = item.get("url", "https://twitter.com")

                        if post_id and post_id not in SEEN_POSTS:
                            SEEN_POSTS.add(post_id)
                            if len(SEEN_POSTS) > 500:
                                SEEN_POSTS.pop()

                            # Izračunaj hype postotak za svaku objavu bez obzira na sve
                            hype_score = calculate_hype_score(title)

                            # ŠALJE SVE - nema preskakanja, čak i ako je 30% ili 40% hype-a
                            await send_hype_alert(title, url_link, source, hype_score)
                            new_count += 1
                            await asyncio.sleep(0.5)
                    return new_count
        except Exception as e:
            print(f"Greška: {e}")
    return 0

async def background_radar_loop():
    print(f"🚀 All-In Hype Radar pokrenut (Prikazuje apsolutno sve s postocima)!")
    while True:
        try:
            await fetch_live_feed()
        except Exception as e:
            print(f"Greska u petlji: {e}")
        await asyncio.sleep(15)

# --- TELEGRAM KOMANDE ---
async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
        return
    await update.message.reply_text("🔄 Skeniram apsolutno sve objave i računam postotke...")
    found = await fetch_live_feed()
    await update.message.reply_text(f"✅ Skeniranje završeno. Poslano objava: {found}")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
        return
    msg = (
        f"📊 **ALL-IN HYPE STATUS**\n\n"
        f"• Praćenih profila: `{len(ACTIVE_PROFILES)}`\n"
        f"• Filteri: `Isključeni (Šalje se 100% objava s postocima)`\n"
        f"• Spremljenih objava: `{len(SEEN_POSTS)}`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("scan", cmd_scan))
    app.add_handler(CommandHandler("status", cmd_status))

    await app.initialize()
    await app.bot.delete_webhook(drop_pending_updates=True)
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    asyncio.create_task(background_radar_loop())

    stop_event = asyncio.Event()
    await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(main())
