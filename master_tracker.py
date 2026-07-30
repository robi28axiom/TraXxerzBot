import os
import time
import requests
import feedparser
import re
from urllib.parse import quote

TELEGRAM_BOT_TOKEN = "8725824554:AAGUsQb3t31UU9QbCbOXAIT3Uzzt5eKDKps"
TELEGRAM_CHAT_ID = "8980310038"

# Optimizirana lista ključnih profila za praćenje bez opterećenja
TOP_PROFILES = [
    "aeyakovenko", "rajgokal", "solana", "phantom", "RaydiumProtocol", "JupiterExchange",
    "lookonchain", "bubblemaps", "WhaleChart", "tier10k", "EmberCN", "SolanaFloor",
    "blknoiz06", "GCRClassic", "HsakaTrades", "MustStopMurad", "cobie", "frankdegods",
    "trader1sz", "CryptoKaleo", "AltcoinSherpa", "Ansem", "MarioNawfal", "WatcherGuru",
    "CoinDesk", "Cointelegraph", "elonmusk", "vitalikbuterin", "cz_binance", "pumpdotfun"
]

NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://poast.org",
    "https://nitter.lucabased.xyz"
]

RSS_URLS = [
    "https://news.google.com/rss/search?q=Elon+Musk+when:1h&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Trump+when:1h&hl=en-US&gl=US&ceid=US:en",
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/"
]

HIGH_PRIO_KEYWORDS = ["launched", "token", "ca:", "solana", "pump.fun", "sec", "binance", "hack", "exploit"]
STANDARD_KEYWORDS = ["trump", "musk", "doge", "meme", "crypto", "fed", "rates", "listing"]
STOP_WORDS = {"THE", "A", "AN", "TO", "IN", "FOR", "OF", "ON", "WITH", "AT", "BY", "FROM", "IS", "NEW"}
KNOWN_METAS = {"MUSK": "MUSK", "ELON": "ELON", "TRUMP": "TRUMP", "DOGE": "DOGE", "VITALIK": "VITALIK"}

SEEN_ARTICLES = set()

def calculate_score(title):
    score = 35
    title_lower = title.lower()
    for word in HIGH_PRIO_KEYWORDS:
        if word in title_lower:
            score += 20
    for word in STANDARD_KEYWORDS:
        if word in title_lower:
            score += 10
    if len(title) < 70:
        score += 10
    return min(score, 100)

def extract_smart_ticker(title):
    words = re.findall(r'\b[A-Za-z0-9]+\b', title)
    for word in words:
        if word.upper() in KNOWN_METAS:
            return KNOWN_METAS[word.upper()]
    for word in words:
        w_upper = word.upper()
        if w_upper not in STOP_WORDS and len(w_upper) > 2 and not w_upper.isdigit():
            return w_upper
    return "MEME"

def send_telegram_alert(title, link, score, source_type="TWITTER"):
    ticker = extract_smart_ticker(title)
    search_encoded = quote(ticker)
    
    header = "🐦 **[X / ALARM]**" if source_type == "TWITTER" else "📰 **[VIJEST]**"
    
    message = f"{header}\n\n📝 {title}\n🔥 Score: `{score}/100`\n🎯 Ticker: `${ticker}`\n\n"
    
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

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown", "reply_markup": {"inline_keyboard": keyboard}}
    try:
        requests.post(url, json=payload, timeout=3)
    except:
        pass

def main():
    print("🚀 Master Tracker pokrenut na Renderu (24/7)...")
    while True:
        try:
            # 1. Brza provjera RSS vijesti
            for rss_url in RSS_URLS:
                try:
                    feed = feedparser.parse(rss_url)
                    for entry in feed.entries[:3]:
                        aid = entry.get('id', entry.link)
                        if aid not in SEEN_ARTICLES:
                            SEEN_ARTICLES.add(aid)
                            score = calculate_score(entry.title)
                            if score >= 80:
                                send_telegram_alert(entry.title, entry.link, score, source_type="NEWS")
                except:
                    continue
                time.sleep(1)

            # 2. Provjera ključnih profila s pauzama
            for account in TOP_PROFILES:
                for instance in NITTER_INSTANCES:
                    try:
                        feed = feedparser.parse(f"{instance}/{account}/rss")
                        if feed.entries:
                            entry = feed.entries[0]
                            aid = entry.get('id', entry.link)
                            if aid not in SEEN_ARTICLES:
                                SEEN_ARTICLES.add(aid)
                                score = calculate_score(entry.title)
                                if score >= 80:
                                    send_telegram_alert(f"@{account}: {entry.title}", entry.link, score, source_type="TWITTER")
                            break
                    except:
                        continue
                time.sleep(2)

            # Pauza na kraju ciklusa
            time.sleep(60)
        except Exception as e:
            print(f"Greska: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
