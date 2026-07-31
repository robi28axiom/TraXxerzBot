import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from urllib.parse import quote

# --- KONFIGURACIJA ---
TELEGRAM_BOT_TOKEN = "8725824554:AAGUsQb3t31UU9QbCbOXAIT3Uzzt5eKDKps"
TELEGRAM_CHAT_ID = "8980310038"

FEEDS = [
    "https://nitter.poast.org/WhaleAlert/rss",
    "https://nitter.poast.org/WatcherGuru/rss",
    "https://nitter.poast.org/solana/rss",
    "https://nitter.poast.org/DexScreenerApp/rss"
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

def is_fresh_post(pub_date_str):
    if not pub_date_str:
        return True # Ako nema datuma, propusti ga da ne blokira
    try:
        post_time = parsedate_to_datetime(pub_date_str)
        now = datetime.now(timezone.utc)
        diff_minutes = (now - post_time).total_seconds() / 60
        # Vraća True samo ako je objava mlađa od 10 minuta (uz malo tolerancije za UTC pomake)
        return diff_minutes <= 12
    except Exception:
        return True

async def fetch_feed(session, feed_url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with session.get(feed_url, headers=headers, timeout=10) as response:
            if response.status == 200:
                content = await response.text()
                root = ET.fromstring(content)
                items = []
                for item in root.findall(".//item"):
                    title = item.find("title")
                    link = item.find("link")
                    pub_date = item.find("pubDate")
                    
                    title_text = title.text if title is not None else ""
                    link_text = link.text if link is not None else ""
                    pub_text = pub_date.text if pub_date is not None else ""
                    
                    link_text = link_text.replace("nitter.poast.org", "twitter.com").replace("nitter.net", "twitter.com")
                    
                    if title_text and link_text:
                        items.append({
                            "id": link_text,
                            "title": title_text,
                            "link": link_text,
                            "pubDate": pub_text
                        })
                return items
    except Exception:
        pass
    return []

async def scan_all_feeds():
    async with aiohttp.ClientSession() as session:
        new_count = 0
        for feed_url in FEEDS:
            posts = await fetch_feed(session, feed_url)
            for post in posts:
                post_id = post["id"]
                if post_id and post_id not in SEEN_POSTS:
                    SEEN_POSTS.add(post_id)
                    if len(SEEN_POSTS) > 1000:
                        SEEN_POSTS.pop()

                    title = post["title"]
                    link = post["link"]
                    pub_date = post["pubDate"]
                    source = feed_url.split("/")[3]
                    
                    hype_score = calculate_hype_score(title)
                    
                    # UVJET: Hype > 80% I da je mlađe od 10 minuta
                    if hype_score > 80 and is_fresh_post(pub_date):
                        await send_telegram_post(title, link, f"@{source}", hype_score)
                        new_count += 1
                    
                    await asyncio.sleep(0.2)
        return new_count

async def send_telegram_post(title, link, source_name, hype_score):
    short_desc = title[:150] + "..." if len(title) > 150 else title
    search_encoded = quote(title[:30])

    message = f"🔥 **[ULTRA-FRESH ELITE ALERT - {hype_score}% HYPE]**\n\n"
    message += f"👤 **Izvor:** `{source_name}`\n"
    message += f"💬 **Objava:**\n{short_desc}\n\n"
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
    print(f"🚀 Ultra-Fresh Radar aktivan (>80% Hype & <10 min)!")
    while True:
        try:
            await scan_all_feeds()
        except Exception as e:
            print(f"Greska u petlji: {e}")
        await asyncio.sleep(15)

async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
        return
    await update.message.reply_text("🔄 Tražim samo svježe elite objave (<10 min, >80% hype)...")
    found = await scan_all_feeds()
    await update.message.reply_text(f"✅ Skeniranje završeno. Pronađeno svježih objava: {found}")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
        return
    msg = (
        f"📊 **ULTRA-FRESH RADAR STATUS**\n\n"
        f"• Praćenih kanala: `{len(FEEDS)}`\n"
        f"• Hype prag: `> 80%`\n"
        f"• Vremenski limit: `< 10 minuta`\n"
        f"• Status: `Online & Aktivno`"
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
