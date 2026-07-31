import asyncio
import aiohttp
import xml.etree.ElementTree as ET
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

async def fetch_profile_rss(session, username):
    url = f"https://nitter.poast.org/{username}/rss"
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                content = await response.text()
                root = ET.fromstring(content)
                items = []
                for item in root.findall(".//item"):
                    title = item.find("title")
                    link = item.find("link")
                    
                    title_text = title.text if title is not None else ""
                    link_text = link.text if link is not None else f"https://twitter.com/{username}"
                    link_text = link_text.replace("nitter.poast.org", "twitter.com").replace("nitter.net", "twitter.com")
                    
                    items.append({
                        "id": link_text,
                        "title": title_text,
                        "link": link_text,
                        "source": f"@{username}"
                    })
                return items
    except Exception:
        pass
    return []

async def scan_all_profiles():
    async with aiohttp.ClientSession() as session:
        new_count = 0
        for username in ACTIVE_PROFILES:
            posts = await fetch_profile_rss(session, username)
            for post in posts:
                post_id = post["id"]
                if post_id and post_id not in SEEN_POSTS:
                    SEEN_POSTS.add(post_id)
                    if len(SEEN_POSTS) > 1000:
                        SEEN_POSTS.pop()

                    title = post["title"]
                    source = post["source"]
                    link = post["link"]
                    hype_score = calculate_hype_score(title)
                    
                    await send_telegram_post(title, link, source, hype_score)
                    new_count += 1
                    await asyncio.sleep(0.2)
            await asyncio.sleep(0.5)
        return new_count

async def send_telegram_post(title, link, source_name, hype_score):
    short_desc = title[:150] + "..." if len(title) > 150 else title
    search_encoded = quote(title[:30])

    if hype_score >= 75:
        hype_emoji = "🔥"
    elif hype_score >= 50:
        hype_emoji = "⚡"
    else:
        hype_emoji = "📌"

    message = f"{hype_emoji} **[X / 50 PROFILES FEED - {hype_score}% HYPE]**\n\n"
    message += f"👤 **Profil:** `{source_name}`\n"
    message += f"💬 **Objava / RT:**\n{short_desc}\n\n"
    message += f"🔗 [Otvori na X-u]({link})\n\n"
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
    print(f"🚀 Full-Profile RSS Radar aktivan (Prati sve twitove, RT-ove i slike)!")
    while True:
        try:
            await scan_all_profiles()
        except Exception as e:
            print(f"Greska u petlji: {e}")
        await asyncio.sleep(30)

async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
        return
    await update.message.reply_text("🔄 Ručno skeniram svih 50 profila...")
    found = await scan_all_profiles()
    await update.message.reply_text(f"✅ Skeniranje završeno. Pronađeno novih objava: {found}")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
        return
    msg = (
        f"📊 **FULL FEED RADAR STATUS**\n\n"
        f"• Praćenih X profila: `{len(ACTIVE_PROFILES)}`\n"
        f"• Vrsta sadržaja: `Sve (Twitovi, Retwitovi, Mediji/Slike)`\n"
        f"• Spremljenih objava: `{len(SEEN_POSTS)}`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("scan", cmd_scan))
    app.add_handler(CommandHandler("status", cmd_status))

    # Pokrećemo pozadinski zadatak unutar application post-init hooka da event loop bude ispravan
    async def post_init(application):
        asyncio.create_task(background_radar_loop())

    app.post_init = post_init

    # Pokrećemo polling bez ručnog asyncio.run()
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
