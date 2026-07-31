import asyncio
import re
import aiohttp
import requests
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import quote

# --- KONFIGURACIJA ---
TELEGRAM_BOT_TOKEN = "8725824554:AAGUsQb3t31UU9QbCbOXAIT3Uzzt5eKDKps"
TELEGRAM_CHAT_ID = "8980310038"

# TOP 50 KLJUČNIH PROFILA (Elon Musk, Trump, Bijela kuća, Regulative, Sol Alpha & Alati)
TOP_50_TWITTER = [
    # --- 1. ELON MUSK, TRUMP & AMERIČKA ADMINISTRACIJA ---
    "elonmusk",         
    "realDonaldTrump",  
    "WhiteHouse",       
    "POTUS",            
    "SecTreasury",      
    "StateDept",        
    "US_FDA",           
    "PentagonPresSec",  

    # --- 2. REGULATORI I EKONOMSKA POLITIKA ---
    "SECGov",           
    "federalreserve",   
    "USTreasury",       
    "CommodityFutures", 

    # --- 3. KLJUČNI AMERIČKI NOVINARI & INSAJDERI ---
    "AccountantForYou", 
    "MarioNawfal",      
    "WatcherGuru",      
    "zerohedge",        
    "NickTimiraos",     
    "WSJ",              
    "business",         

    # --- 4. SOLANA MEME, DEGEN & ALPHA TRADERS ---
    "Ansem",            
    "MustStopMurad",    
    "blknoiz06",        
    "SolanaLegend",     
    "CryptoCapo_",      
    "TheFlowHorse",     
    "AltcoinSherpa",    
    "GCRClassic",       
    "HsakaTrades",      

    # --- 5. ON-CHAIN SLEUTHEVI & WHALES ---
    "lookonchain",      
    "bubblemaps",       
    "PeckShieldAlert",  
    "ArkhamIntel",      
    "spotonchain",      

    # --- 6. SOLANA CORE & INFRASTRUKTURA ---
    "solana",           
    "phantom",          
    "RaydiumProtocol",  
    "JupiterExchange",  
    "meteoraAG",        
    "birdeye_so",       

    # --- 7. TRADING ALATI & BURZE ---
    "DexScreenerApp",   
    "AxiomTrade",       
    "Photon_Sol",       
    "BullX_io",         
    "binance",          
    "coinbase",         
    "a16z",             
    "paradigm"          
]

TIKTOK_RSS_URLS = [
    "https://news.google.com/rss/search?q=site:tiktok.com+viral+trend+when:1h&hl=en-US&gl=US&ceid=US:en"
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
        upper_word = word.upper()
        if upper_word in KNOWN_METAS:
            return KNOWN_METAS[upper_word]
    for word in words:
        upper_word = word.upper()
        if upper_word not in STOP_WORDS and len(upper_word) > 2 and not upper_word.isdigit():
            return upper_word
    return "MEME"

def generate_dynamic_token_idea(title: str):
    title_lower = title.lower()
    if any(w in title_lower for w in ["war", "conflict", "attack", "military", "army"]):
        return "WW3 Survivor", "WW3"
    elif any(w in title_lower for w in ["fed", "inflation", "rates", "interest", "powell", "cpi"]):
        return "Fed Rate Panic", "PRINTER"
    elif any(w in title_lower for w in ["sec", "lawsuit", "court", "suing", "charge", "arrest"]):
        return "SEC Target", "SEC"
    elif any(w in title_lower for w in ["trump", "biden", "election", "white house", "vote"]):
        return "White House Drama", "BALLOT"
    elif any(w in title_lower for w in ["cat", "kitty", "kitten", "meow"]):
        return "Depressed Cat", "FATCAT"
    elif any(w in title_lower for w in ["dog", "puppy", "shiba", "bark"]):
        return "Alpha Doge", "DOGE"
    elif any(w in title_lower for w in ["frog", "pepe"]):
        return "Brainrot Frog", "FROG"
    elif any(w in title_lower for w in ["musk", "tesla", "spacex", "x"]):
        return "Musk Tweet Glitch", "X"
    elif any(w in title_lower for w in ["apple", "iphone", "tim cook", "mac"]):
        return "Apple Event Leak", "APPLE"
    elif any(w in title_lower for w in ["ai", "openai", "gpt", "robot", "agent"]):
        return "Rogue AI Agent", "ROBOT"
    else:
        ticker = extract_smart_ticker(title)
        return f"{ticker} Meta Token", ticker

def extract_media_from_entry(entry):
    if hasattr(entry, 'media_content') and entry.media_content:
        for media in entry.media_content:
            url = media.get('url')
            if url and any(ext in url.lower() for ext in ['.jpg', '.png', '.webp', '.gif', '.mp4']):
                return url
    summary = entry.get('summary', '')
    if summary:
        soup = BeautifulSoup(summary, 'html.parser')
        img_tag = soup.find('img')
        if img_tag and img_tag.get('src'):
            return img_tag['src']
    return None

def send_telegram_alert(title, link, score, source_type="TWITTER", account=None, dex_data=None, ca_found=None, media_url=None):
    token_name, ticker = generate_dynamic_token_idea(title)
    search_encoded = quote(ticker)
    short_desc = title[:90] + "..." if len(title) > 90 else title
    
    if source_type == "TIKTOK":
        header = "🎵 **[TIKTOK ULTRA-SPORI RADAR]**"
    else:
        header = "🐦 **[X / TOP 50 - GLAVNI RADAR]**"
    
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

    url_send = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "reply_markup": {"inline_keyboard": keyboard}
    }
    
    try:
        if media_url:
            photo_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            photo_payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "photo": media_url,
                "caption": message,
                "parse_mode": "Markdown",
                "reply_markup": {"inline_keyboard": keyboard}
            }
            res = requests.post(photo_url, json=photo_payload, timeout=5)
            if res.status_code != 200:
                requests.post(url_send, json=payload, timeout=5)
        else:
            requests.post(url_send, json=payload, timeout=5)
    except Exception as e:
        print(f"Greska pri slanju: {e}")

async def background_radar(application):
    await application.bot.initialize()
    print("🚀 Optimizirani Top 50 radar (Musk, Trump, WhiteHouse & Sol) uspješno pokrenut...")
    
    tiktok_counter = 0

    while True:
        try:
            # 1. TikTok provjera (svaki 15. krug)
            tiktok_counter += 1
            if tiktok_counter >= 15:
                tiktok_counter = 0
                for tiktok_url in TIKTOK_RSS_URLS:
                    feed = feedparser.parse(tiktok_url)
                    for entry in feed.entries:
                        t_id = entry.get('id', entry.link)
                        if t_id not in SEEN_ARTICLES:
                            SEEN_ARTICLES.add(t_id)
                            cas = find_contract_addresses(entry.title)
                            ca_found = cas[0] if cas else None
                            dex_data = await check_dexscreener(ca_found) if ca_found else None
                            media_url = extract_media_from_entry(entry)
                            send_telegram_alert(entry.title, entry.link, 100, source_type="TIKTOK", dex_data=dex_data, ca_found=ca_found, media_url=media_url)

            # 2. Glavni fokus: Top 50 Twitter profila preko RSSHub-a
            for account in TOP_50_TWITTER:
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
                            dex_data = await check_dexscreener(ca_found) if ca_found else None
                            media_url = extract_media_from_entry(entry)
                            send_telegram_alert(entry.title, entry.link, 70, source_type="TWITTER", account=account, dex_data=dex_data, ca_found=ca_found, media_url=media_url)
                except Exception:
                    pass
                
                await asyncio.sleep(3.0)  # Pauza od 3 sekunde između profila
            
        except Exception as e:
            print(f"Greska u glavnoj petlji: {e}")
        
        await asyncio.sleep(20)

def main():
    from telegram.ext import ApplicationBuilder
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(background_radar).build()
    app.run_polling()

if __name__ == "__main__":
    main()
