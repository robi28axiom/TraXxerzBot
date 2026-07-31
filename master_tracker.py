import asyncio
import re
import aiohttp
import feedparser
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- KONFIGURACIJA ---
TELEGRAM_BOT_TOKEN = "8725824554:AAGUsQb3t31UU9QbCbOXAIT3Uzzt5eKDKps"
TELEGRAM_CHAT_ID = "8980310038"

# GLOBALNE POSTAVKE
CURRENT_THRESHOLD = 40
ACTIVE_PROFILES = [
    # --- 1. ELON MUSK, TRUMP & AMERIČKA ADMINISTRACIJA ---
    "elonmusk", "realDonaldTrump", "WhiteHouse", "POTUS", "SecTreasury", "StateDept", "US_FDA", "PentagonPresSec",
    # --- 2. REGULATORI I EKONOMSKA POLITIKA ---
    "SECGov", "federalreserve", "USTreasury", "CommodityFutures",
    # --- 3. KLJUČNI AMERIČKI NOVINARI & INSAJDERI ---
    "AccountantForYou", "MarioNawfal", "WatcherGuru", "zerohedge", "NickTimiraos", "WSJ", "business",
    # --- 4. SOLANA MEME, DEGEN & ALPHA TRADERS ---
    "Ansem", "MustStopMurad", "blknoiz06", "SolanaLegend", "CryptoCapo_", "TheFlowHorse", "AltcoinSherpa", "GCRClassic", "HsakaTrades",
    # --- 5. ON-CHAIN SLEUTHEVI & WHALES ---
    "lookonchain", "bubblemaps", "PeckShieldAlert", "ArkhamIntel", "spotonchain",
    # --- 6. SOLANA CORE & INFRASTRUKTURA ---
    "solana", "phantom", "RaydiumProtocol", "JupiterExchange", "meteoraAG", "birdeye_so",
    # --- 7. TRADING ALATI & BURZE ---
    "DexScreenerApp", "AxiomTrade", "Photon_Sol", "BullX_io", "binance", "coinbase", "a16z", "paradigm"
]

STOP_WORDS = {
    "THE", "A", "AN", "TO", "IN", "FOR", "OF", "ON", "WITH", "AT", "BY", "FROM", 
    "IS", "RE", "OVER", "THIS", "THAT", "WILL", "HAS", "HAVE", "HAD", "US", "USA", 
    "NEWS", "NEW", "AFTER", "BEFORE", "SENATE", "HOUSE", "BILL", "SAYS", "SAID", "REPORT"
}

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

SEEN_ARTICLES = set()
bot = Bot(token=TELEGRAM_BOT_TOKEN)

def find_contract_addresses(text: str):
    solana_pattern = r'\b[1-9A-HJ-NP-Za-km-z]{32,44}pump\b'
    matches = re.findall(solana_pattern, text)
    return list(set(matches))

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

def extract_smart_ticker(title):
    words = re.findall(r'\b[A-Za-z0-9]+\b', title)
    for word in words:
        if word.upper() in KNOWN_METAS:
            return KNOWN_METAS[word.upper()]
    for word in words:
        w_up = word.upper()
        if w_up not in STOP_WORDS and len(w_up) > 2 and not w_up.isdigit():
            return w_up
    return "MEME"

def generate_dynamic_token_idea(title: str):
    t_low = title.lower()
    if any(w in t_low for w in ["war", "conflict", "attack", "military"]):
        return "WW3 Survivor", "WW3"
    elif any(w in t_low for w in ["fed", "inflation", "rates", "powell", "cpi"]):
        return "Fed Rate Panic", "PRINTER"
    elif any(w in t_low for w in ["sec", "lawsuit", "court", "suing"]):
        return "SEC Target", "SEC"
    elif any(w in t_low for w in ["trump", "biden", "election", "white house"]):
        return "White House Drama", "BALLOT"
    elif any(w in t_low for w in ["cat", "kitty", "kitten"]):
        return "Depressed Cat", "FATCAT"
    elif any(w in t_low for w in ["dog", "puppy", "shiba"]):
        return "Alpha Doge", "DOGE"
    elif any(w in t_low for w in ["frog", "pepe"]):
        return "Brainrot Frog", "FROG"
    elif any(w in t_low for w in ["apple", "iphone", "tim cook"]):
        return "Apple Event Leak", "APPLE"
    elif any(w in t_low for w in ["ai", "openai", "gpt", "robot"]):
        return "Rogue AI Agent", "ROBOT"
    else:
        ticker = extract_smart_ticker(title)
        return f"{ticker} Meta Token", ticker

async def send_telegram_alert(title, link, score, account=None, dex_data=None, ca_found=None, media_url=None):
    token_name, ticker = generate_dynamic_token_idea(title)
    search_encoded = quote(ticker)
    short_desc = title[:90] + "..." if len(title) > 90 else title
    
    header = f"🐦 **[X / TOP RADAR - {CURRENT_THRESHOLD}/100]**"
    message = f"{header}\n\n"
    if account:
        message += f"👤 **Izvor:** `@{account}`\n"
    message += f"📝 **Sadržaj:** {title}\n"
    message += f"🔥 **Score:** `{score}/100`\n"
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
            {"text": "🔗 Izvor", "url": link}
        ]
    ]

    try:
        if media_url:
            try:
                await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=media_url, caption=message, parse_mode="Markdown", reply_markup={"inline_keyboard": keyboard})
                return
            except Exception:
                pass
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="Markdown", reply_markup={"inline_keyboard": keyboard})
    except Exception as e:
        print(f"Greska pri slanju: {e}")

async def run_single_scan():
    count = 0
    for account in ACTIVE_PROFILES:
        try:
            feed_url = f"https://rsshub.app/twitter/user/{account}"
            feed = feedparser.parse(feed_url)
            if feed.entries:
                entry = feed.entries[0]
                post_id = entry.get('id', entry.link)
                if post_id not in SEEN_ARTICLES:
                    SEEN_ARTICLES.add(post_id)
                    cas = find_contract_addresses(entry.title)
                    ca_found = cas[0] if cas else None
                    
                    media_url = None
                    if hasattr(entry, 'media_content') and entry.media_content:
                        for media in entry.media_content:
                            m_url = media.get('url')
                            if m_url and any(ext in m_url.lower() for ext in ['.jpg', '.png', '.webp', '.gif']):
                                media_url = m_url
                                break
                    
                    dex_data = await check_dexscreener(ca_found) if ca_found else None
                    await send_telegram_alert(entry.title, entry.link, CURRENT_THRESHOLD, account=account, dex_data=dex_data, ca_found=ca_found, media_url=media_url)
                    count += 1
        except Exception:
            pass
        await asyncio.sleep(1.0)
    return count

async def twitter_radar_loop():
    print(f"🚀 Automatski radar pokrenut: {len(ACTIVE_PROFILES)} profila, prag {CURRENT_THRESHOLD}...")
    while True:
        try:
            await run_single_scan()
        except Exception as e:
            print(f"Greska u petlji: {e}")
        await asyncio.sleep(60)

# --- TELEGRAM KOMANDE ---
async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
        return
    await update.message.reply_text("🔄 Ručno skeniranje svih profila u tijeku...")
    found = await run_single_scan()
    await update.message.reply_text(f"✅ Skeniranje završeno! Pronađeno novih objava: {found}")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
        return
    msg = (
        f"📊 **STATUS RADARA**\n\n"
        f"• Aktivnih profila: `{len(ACTIVE_PROFILES)}`\n"
        f"• Prag score-a: `{CURRENT_THRESHOLD}/100`\n"
        f"• Spremljenih objava u memoriji: `{len(SEEN_ARTICLES)}`\n"
        f"• Status: `Online / Vrti u pozadini`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CURRENT_THRESHOLD
    if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
        return
    if context.args:
        try:
            val = int(context.args[0])
            CURRENT_THRESHOLD = val
            await update.message.reply_text(f"✅ Prag uspješno promijenjen na: `{CURRENT_THRESHOLD}`", parse_mode="Markdown")
        except ValueError:
            await update.message.reply_text("❌ Molimo unesi valjani broj, npr: `/threshold 50`")
    else:
        await update.message.reply_text(f"Trenutni prag je: `{CURRENT_THRESHOLD}`. Promijeni ga s: `/threshold <broj>`", parse_mode="Markdown")

async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
        return
    profiles_str = ", ".join([f"`@{p}`" for p in ACTIVE_PROFILES])
    await update.message.reply_text(f"📋 **Pratim sljedeće profile ({len(ACTIVE_PROFILES)}):**\n\n{profiles_str}", parse_mode="Markdown")

async def main():
    # Pokretanje Telegram aplikacije za komande
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("scan", cmd_scan))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("threshold", cmd_threshold))
    app.add_handler(CommandHandler("list", cmd_list))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # Istovremeno pokretanje pozadinske petlje za automatsko skeniranje
    asyncio.create_task(twitter_radar_loop())

    # Drži bot upaljenim
    stop_event = asyncio.Event()
    await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(main())
