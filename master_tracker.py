import asyncio
import re
import aiohttp
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- KONFIGURACIJA ---
TELEGRAM_BOT_TOKEN = "8725824554:AAGUsQb3t31UU9QbCbOXAIT3Uzzt5eKDKps"
TELEGRAM_CHAT_ID = "8980310038"

# GLOBALNE POSTAVKE
CURRENT_THRESHOLD = 40

# Ključni X profili koje pratimo kroz alternativne izvore trendova
ACTIVE_PROFILES = [
    "elonmusk", "realDonaldTrump", "WhiteHouse", "POTUS", "SECGov", 
    "federalreserve", "MarioNawfal", "WatcherGuru", "Ansem", "MustStopMurad", 
    "blknoiz06", "SolanaLegend", "lookonchain", "bubblemaps", "solana", "phantom"
]

KNOWN_METAS = {
    "MEME": "MEME", "SOL": "SOL", "COIN": "COIN", "TOKEN": "TOKEN", "PUMP": "PUMP", 
    "ALPHA": "ALPHA", "GEM": "GEM", "MOON": "MOON", "DEX": "DEX", "BULL": "BULL", 
    "BEAR": "BEAR", "WHALE": "WHALE", "DEGEN": "DEGEN", "APE": "APE", "AIRDROP": "AIRDROP",
    "CAT": "CAT", "DOG": "DOG", "PEPE": "PEPE", "WIF": "WIF", "BOME": "BOME", 
    "POPCAT": "POPCAT", "SHIB": "SHIB", "FLOKI": "FLOKI", "FROG": "FROG", "DUCK": "DUCK", 
    "MONKEY": "MONKEY", "CHICKEN": "CHICKEN", "PIG": "PIG",
    "WAR": "WAR", "PEACE": "PEACE", "TRUMP": "TRUMP", "BIDEN": "BIDEN", "PUTIN": "PUTIN", 
    "ZELENSKY": "ZELENSKY", "NATO": "NATO", "FED": "FED", "SEC": "SEC", "CORP": "CORP", 
    "TAX": "TAX", "DOLLAR": "DOLLAR", "GOLD": "GOLD", "OIL": "OIL", "MONEY": "MONEY",
    "AI": "AI", "GPT": "GPT", "BOT": "BOT", "CHIP": "CHIP", "APPLE": "APPLE", 
    "TESLA": "TESLA", "MUSK": "MUSK", "ELON": "ELON", "VITALIK": "VITALIK", "CZ": "CZ"
}

SEEN_PUMP_TOKENS = set()
VIRAL_KEYWORDS_CACHE = set(["TRUMP", "ELON", "AI", "FED", "SEC", "CAT", "DOG", "APPLE", "SOL", "ANSEM"])

bot = Bot(token=TELEGRAM_BOT_TOKEN)

async def check_dexscreener(token_ca: str):
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_ca}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get("pairs", [])
                    if pairs:
                        pair = pairs[0]
                        return {
                            "status": "found",
                            "dex": pair.get("dexId", "Nepoznato"),
                            "liquidity": pair.get("liquidity", {}).get("usd", 0),
                            "volume": pair.get("volume", {}).get("h24", 0)
                        }
        except Exception:
            pass
    return {"status": "not_found"}

def generate_dynamic_token_idea(title: str):
    t_low = title.lower()
    if any(w in t_low for w in ["trump", "biden", "election", "white house"]):
        return "White House Drama", "BALLOT"
    elif any(w in t_low for w in ["cat", "kitty", "kitten"]):
        return "Depressed Cat", "FATCAT"
    elif any(w in t_low for w in ["dog", "puppy", "shiba"]):
        return "Alpha Doge", "DOGE"
    elif any(w in t_low for w in ["apple", "iphone", "tim cook"]):
        return "Apple Event Leak", "APPLE"
    elif any(w in t_low for w in ["ai", "openai", "gpt", "robot"]):
        return "Rogue AI Agent", "ROBOT"
    else:
        words = re.findall(r'\b[A-Za-z0-9]+\b', title)
        for word in words:
            if word.upper() in KNOWN_METAS:
                return f"{KNOWN_METAS[word.upper()]} Meta", KNOWN_METAS[word.upper()]
        for word in words:
            w_up = word.upper()
            if len(w_up) > 2 and not w_up.isdigit():
                return f"{w_up} Token", w_up
        return "MEME Token", "MEME"

async def fetch_x_trends_or_news():
    # Povlačimo kripto i političke trendove s otvorenih izvora (CryptoPanic / GNews alternative) da bot "zna" o čemu se priča
    url = "https://cryptopanic.com/api/v1/posts/?auth_token=free&public=true&kinds=news"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("results", [])
                    for item in results[:10]:
                        title = item.get("title", "")
                        words = re.findall(r'\b[A-Za-z]{4,}\b', title)
                        for w in words:
                            if w.upper() not in {"THIS", "THAT", "WITH", "FROM"}:
                                VIRAL_KEYWORDS_CACHE.add(w.upper())
        except Exception:
            pass

async def send_telegram_alert(title, link, dex_data=None, ca_found=None, matched_meta=None):
    token_name, ticker = generate_dynamic_token_idea(title)
    search_encoded = quote(ticker)
    short_desc = title[:90] + "..." if len(title) > 90 else title
    
    header = "🚀 **[ALPHA RADAR & PUMP.FUN SNIPER]**"
    if matched_meta:
        header = f"🔥 **[VIRAL META MATCH: {matched_meta}]**"

    message = f"{header}\n\n"
    message += f"📝 **Naziv Tokena:** {title}\n"
    message += f"🎯 **Ticker:** `${ticker}`\n"
    
    if ca_found:
        message += f"🔑 **CA:** `{ca_found}`\n"
        if dex_data and dex_data["status"] == "found":
            message += f"💧 **Likvidnost:** `${dex_data['liquidity']:,.0f}` | 📊 **Volumen:** `${dex_data['volume']:,.0f}`\n"

    message += f"\n📋 *Predložak za lansiranje:*\n"
    message += f"• **Name:** `{token_name}`\n"
    message += f"• **Ticker:** `${ticker}`\n"
    message += f"• **Description:** `{short_desc}`\n\n"
    message += f"👇 *Brzi linkovi:*"

    keyboard = [
        [
            {"text": f"⚡ Axiom ({ticker})", "url": f"https://axiom.trade/search?q={search_encoded}"},
            {"text": f"🚀 Pump.fun", "url": f"https://pump.fun/board?search={search_encoded}"}
        ],
        [
            {"text": "📈 DexScreener", "url": f"https://dexscreener.com/search?q={search_encoded}"},
            {"text": "🔗 Pump Token", "url": link}
        ]
    ]

    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown", reply_markup={"inline_keyboard": keyboard})
    except Exception as e:
        print(f"Greska pri slanju: {e}")

async def scan_pump_fun_trending():
    # Osvježavamo viralne ključne riječi prije skeniranja lanca
    await fetch_x_trends_or_news()

    url = "https://frontend-api.pump.fun/coins?offset=0&limit=30&sort=created_timestamp&order=DESC"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    coins = await response.json()
                    new_count = 0
                    for coin in coins:
                        mint = coin.get("mint")
                        name = coin.get("name", "")
                        symbol = coin.get("symbol", "")
                        
                        if mint and mint not in SEEN_PUMP_TOKENS:
                            SEEN_PUMP_TOKENS.add(mint)
                            
                            # Provjeravamo poklapa li se naziv tokena s nekom od viralnih meta riječi s X-a/vijesti
                            combined_text = f"{name} {symbol}".upper()
                            matched_meta = next((kw for kw in VIRAL_KEYWORDS_CACHE if kw in combined_text), None)

                            dex_data = await check_dexscreener(mint)
                            
                            # Šaljemo obavijest za sve ili posebno naglašavamo ako je viralni match
                            await send_telegram_alert(
                                title=f"{name} (${symbol})", 
                                link=f"https://pump.fun/coin/{mint}", 
                                dex_data=dex_data, 
                                ca_found=mint,
                                matched_meta=matched_meta
                            )
                            new_count += 1
                            await asyncio.sleep(0.3)
                    return new_count
        except Exception as e:
            print(f"API greska: {e}")
    return 0

async def background_radar_loop():
    print(f"🚀 Hibridni Alpha & On-Chain radar pokrenut!")
    while True:
        try:
            await scan_pump_fun_trending()
        except Exception as e:
            print(f"Greska u petlji: {e}")
        await asyncio.sleep(35)

# --- TELEGRAM KOMANDE ---
async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
        return
    await update.message.reply_text("🔄 Skeniram X trendove i Pump.fun tokene...")
    found = await scan_pump_fun_trending()
    await update.message.reply_text(f"✅ Skeniranje završeno! Obrađeno novih tokena/meta: {found}")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
        return
    msg = (
        f"📊 **STATUS HIBRIDnog RADARA**\n\n"
        f"• Aktivnih ključnih riječi (X/News cache): `{len(VIRAL_KEYWORDS_CACHE)}`\n"
        f"• Praćenje lanca: `Pump.fun & DexScreener Live`\n"
        f"• Status: `Online i lovi tokene`"
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
