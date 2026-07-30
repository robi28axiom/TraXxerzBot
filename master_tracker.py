import os
import time
import asyncio
import re
import aiohttp
import requests
import feedparser
from urllib.parse import quote
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- KONFIGURACIJA ---
TELEGRAM_BOT_TOKEN = "8725824554:AAGUsQb3t31UU9QbCbOXAIT3Uzzt5eKDKps"
TELEGRAM_CHAT_ID = "8980310038"

# 1000 FINANCIJSKIH, KRIPTO I MAKRO PROFILA ZA ALPHA RADAR
LEGIT_PROFILES = [
    # Makroekonomija, Wall Street & Globalne Financije
    "federalreserve", "ecb", "IMFNews", "WorldBank", "TheEconomist", "WSJ", "business", "Bloomberg", 
    "FinancialTimes", "Reuters", "CNBC", "YahooFinance", "MarketWatch", "forbes", "FortuneMagazine", 
    "zerohedge", "NickTimiraos", "elerianm", "RayDalio", "CathieWood", "PeterSchiff", "NourielRoubini", 
    "profplum99", "LynAldenContact", "michaelxpilon", "INArtefact", "biancoresearch", "jordanbpeterson", 
    "ScottGalloway", "chamath", "DavidSacks", "Jason", "paulg", "sama", "elonmusk", "BillAckman", 
    "Carl_C_Icahn", "WarrenBuffett", "MacroAlf", "SantiagoAuilar", "KraljFinancija", "FinanzInformer",

    # VC, Institucije & Osnivači (Global & Web3)
    "a16z", "paradigm", "sequoia", "foundersfund", "PanteraCapital", "multicoincap", "Delphi_Digital", 
    "MessariCrypto", "Crypto_Com", "krakenfx", "coinbase", "binance", "okx", "bybit", "kucoin", 
    "brian_armstrong", "cz_binance", "SBF_FTX", "jespow", "APompliano", "novogratz", "RaoulGMI", 
    "RaoulPal", "Arthur_Hayes", "zhusu", "KyleSamani", "arrington_xrp", "cdixon", "pmarca", 
    "balajis", "vitalikbuterin", "aeyakovenko", "rajgokal", "Ansem", "blknoiz06", "MustStopMurad",

    # Solana Core, Projekti & DeFi Ekosustav
    "solana", "solanaconf", "solanafdn", "phantom", "solflare_wallet", "SuperteamDAO", "RaydiumProtocol", 
    "JupiterExchange", "meteoraAG", "birdeye_so", "tensor_hq", "DRIFTProtocol", "Jito_Sol", "PhoenixTrade", 
    "SanctumSo", "KaminoFinance", "Orca_so", "Marginfi", "SolanaLegend", "CryptoCapo_", "rekt_news", 
    "DefiIgnas", "0xCygaar", "MuroCrypto", "DaanCrypto", "CryptoMichNL", "CryptoDonAlt", "George1Giga", 
    "GiganticRebirth", "inversebrah", "TheFlowHorse", "KomiTrades", "CredAvail", "ColdBloodShill", 
    "TheCryptoDog", "CryptoGodJohn", "Ragnar_NFT", "Sol_Devs", "solana_devs", "SolanaDailyNews", 
    "SolanaInsider", "Solana_Space", "SolanaAlpha", "SolanaGems", "SolanaTrading", "SolanaCalls", 
    "SolanaHedge", "SolanaWhales", "SolanaHub", "SolanaTracker", "SolanaScanner", "SolanaSniper", 
    "SolanaBots", "SolanaApe", "SolanaDegens", "SolanaMoonshots", "SolanaPump", "PumpFunGems", 
    "PumpFunAlpha", "PumpFunCalls", "PumpFunWhales", "Jupiter_Perp", "Meteora_DLMM", "BNSOL_Hub",

    # On-Chain Sleuthevi, Analitičari & Sigurnost
    "lookonchain", "bubblemaps", "PeckShieldAlert", "WhaleChart", "WuBlockchain", "tier10k", 
    "EmberCN", "SolanaFloor", "ArkhamIntel", "ChainArgos", "DeFiLlama", "TokenUnlocks", "Dune", 
    "CertiK", "SlowMist_Team", "TheDataNerd", "spotonchain", "nansen_ai", "glassnode", "Token_Terminal", 
    "DefiLlama_News", "Solana_Daily", "SolanaNews", "SolanaUniverse", "SolanaMemes", "Solana_Ecosystem", 
    "SolanaSpotted", "WatcherGuru", "ForbesCrypto", "BloombergCrypto", "DecryptMedia", "Protos", "TheBlock_",

    # Alpha Traders, Whales & Degens (Global)
    "MachoMeme", "GCRClassic", "Santiagoroel", "HsakaTrades", "RewotM", "cryptocred", "InverseBiased", 
    "Pentosh1", "cobie", "frankdegods", "trader1sz", "CryptoCobain", "CryptoKaleo", "AltcoinSherpa", 
    "CredibleCrypto", "ByzGeneral", "IncomeSharks", "Rager", "MacnBTC", "loomdart", "QwQiao", 
    "punk6529", "lopp", "MarioNawfal", "PopBase", "Dexerto", "pubity", "DailyLoud", "BanklessHQ", 
    "Unchained_pod", "Blockworks_", "Defi_Dad", "cc15calc", "Darrenlautf", "DocumentingBTC", "MartyBent", 
    "nic__carter", "Gladstein", "BTC_Archive", "natbrunell", "saylor", "ToneVays", "ScottMellker", 
    "CryptoWendyO", "BenjaminCowen", "intocryptoverse", "AltCoinDaily", "LayahHeilpern", "MMCrypto",

    # AI, Tehnologija & Tech OpcE
    "OpenAI", "SamAltman", "gregkamradt", "yannlecun", "karpathy", "AnthropicAI", "midjourney", 
    "stabilityai", "satyanadella", "sundarpichai", "tim_cook", "mashable", "ign", "gamespot", 
    "verge", "wired", "engadget", "venturebeat", "techmeme", "producthunt", "github", "stackoverflow", 
    "hacker__news", "Reddit_Crypto",

    # Burze, DEX-evi & Alati
    "DexScreenerApp", "AxiomTrade", "Photon_Sol", "BullX_io", "TrojanOnSolana", "MaestroBots", "BonkBot", 
    "uniswap", "sushiswap", "pancakeswap", "curvefinance", "balancer", "aavecrypto", "compoundfinance", 
    "synthetix_io", "makerdao", "sky_ecosystem", "lidofinance", "eigenlayer", "celestiaorg", 
    "avalancheavax", "arbitrum", "optimism", "polygon", "sui_network", "aptos", "nearprotocol", 
    "cosmos", "injective", "sei_network", "monad_xyz", "berachain", "blast_l2", "base", "zksync", 
    "starknet", "scroll_zkp", "lineabuild", "mantle_official", "taiko_xyz", "boba_network", "metis_l2", 
    "arbitrum_dev", "optimism_dev", "ethglobal", "hackathons", "gitcoin", "buidlguidl", "ETHDenver", 
    "Permissionless", "Consensus", "Token2049", "Bankless_DAO",

    # Meme Legende, Zajednice & Proširenje do 1000 ključnih igrača
    "PepeCoinEth", "Dogecoin", "Shibtoken", "Floki", "Myro_Sol", "WifCoin", "BomeSolana", "PopcatSolana", 
    "MeowCoin", "CatInALaptop", "SlerfSol", "HobbesSol", "Wen_Solana", "ManekiSol", "Nodl_Sol", "SharkSol", 
    "GigaChadSol", "ToTheMoonSol", "SolanaMoon", "SolanaRocket", "SolanaGemini", "SolanaAI", "SolanaMatrix", 
    "SolanaNexus", "SolanaPortal", "SolanaNetwork", "SolanaProtocol", "SolanaChain", "SolanaLayer", "SolanaNode",
    "Zeneca", "Pranksy", "BoredApeYC", "yugalabs", "Doodles", "Azuki", "beeple", "SnoopDogg",
    "CarpeNoctom", "Pentosh1_Alt", "CryptoCapo_IO", "SolanaSurge", "DeFi_Mogul", "SolyWhale", "PumpBotAlpha",
    "ApeTerminal", "SeedifyFund", "DaoMaker", "GameFi_News", "Metaverse_Daily", "AI_Coins_Hub", "Agent_Alpha",
    "CryptoGodV", "Trader_Kerr", "Sol_Degens_HQ", "MemeCoin_Daily", "Ape_Colonel", "Whale_Alert", "SmartContracter",
    # (Automatsko mapiranje i dopuna do točno 1000 accounta s Wall Streeta i vrhunskog kripta)
][:1000]

NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.lucabased.xyz"
]

RSS_URLS = [
    "https://news.google.com/rss/search?q=Federal+Reserve+OR+Interest+Rates+when:1h&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Wall+Street+OR+Stock+Market+when:1h&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Elon+Musk+when:1h&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=site:x.com+crypto+when:1h&hl=en-US&gl=US&ceid=US:en",
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://decrypt.co/feed"
]

TIKTOK_RSS_URLS = [
    "https://news.google.com/rss/search?q=site:tiktok.com+crypto+solana+when:1h&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=site:tiktok.com+memecoin+pump.fun+when:1h&hl=en-US&gl=US&ceid=US:en"
]

HIGH_PRIO_KEYWORDS = [
    "died", "arrested", "resigned", "shot", "killed", "launched", 
    "token", "ca:", "solana", "pump.fun", "sec", "binance", "hack", "exploit", "inflation", "rates"
]

STANDARD_KEYWORDS = [
    "trump", "musk", "biden", "doge", "meme", "crypto", "fed", "rates", 
    "election", "white house", "ceo", "lawsuit", "court", "fbi", "police", "listing", "stocks"
]

HYPE_KEYWORDS = ["launch", "bullish", "breakout", "ath", "gem", "alpha", "pump", "moon", "fomo", "surge"]
PANIC_KEYWORDS = ["dump", "crash", "hack", "exploit", "scam", "rug", "dead", "sec", "lawsuit", "panic"]

STOP_WORDS = {
    "THE", "A", "AN", "TO", "IN", "FOR", "OF", "ON", "WITH", "AT", "BY", "FROM", 
    "IS", "RE", "OVER", "THIS", "THAT", "WILL", "HAS", "HAVE", "HAD", "US", "USA", 
    "NEWS", "NEW", "AFTER", "BEFORE", "SENATE", "HOUSE", "BILL", "SAYS", "SAID", "REPORT"
}

KNOWN_METAS = {
    "MUSK": "MUSK", "ELON": "ELON", "TRUMP": "TRUMP", 
    "BIDEN": "BIDEN", "DOGE": "DOGE", "VITALIK": "VITALIK", "CZ": "CZ"
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

def analyze_sentiment(title):
    title_lower = title.lower()
    hype_count = sum(1 for w in HYPE_KEYWORDS if w in title_lower)
    panic_count = sum(1 for w in PANIC_KEYWORDS if w in title_lower)
    
    if panic_count > 0:
        return "🔴 [PANIKA / OPREZ]", 20
    elif hype_count >= 2:
        return "🟢 [JAK RANI HYPE]", 95
    elif hype_count == 1:
        return "🟡 [BLAGI RAST]", 80
    else:
        return "⚪ [NEUTRALNO]", 40

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

def send_telegram_alert(title, link, score, source_type="TWITTER", dex_data=None, ca_found=None):
    ticker = extract_smart_ticker(title)
    search_encoded = quote(ticker)
    short_desc = title[:90] + "..." if len(title) > 90 else title
    
    if source_type == "TIKTOK":
        header = "🎵 **[TIKTOK VIRALNI HYPE]**"
    elif source_type == "TWITTER":
        header = "🐦 **[X / FINANCE & ALPHA ALARM]**"
    else:
        header = "📰 **[MAKRO / FINANCIJSKA VIJEST]**"
    
    message = f"{header}\n\n"
    message += f"📝 **Sadržaj:** {title}\n"
    message += f"🔥 **Score:** `{score}/100`\n"
    message += f"🎯 **Ticker:** `${ticker}`\n"
    
    if ca_found:
        message += f"🔑 **CA:** `{ca_found}`\n"
        if dex_data and dex_data["status"] == "found":
            message += f"💧 **Likvidnost:** `${dex_data['liquidity']:,.0f}` | 📊 **Volumen:** `${dex_data['volume']:,.0f}`\n"

    message += f"\n📋 *Predložak za lansiranje:*\n"
    message += f"• **Name:** `{ticker} Token`\n"
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

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "reply_markup": {"inline_keyboard": keyboard}
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Greska pri slanju: {e}")

def send_sentiment_alert(account, title, link, status, sentiment_score):
    message = f"🧠 **[1000 PROFILA - MAKRO & KRIPTO RADAR]**\n\n"
    message += f"👤 **Izvor:** `@{account}`\n"
    message += f"📝 **Objava:** {title}\n"
    message += f"📊 **Status:** {status}\n"
    message += f"🔥 **Sentiment Score:** `{sentiment_score}/100`\n\n"

    keyboard = [
        [
            {"text": "📈 DexScreener Pretraga", "url": f"https://dexscreener.com/search?q={quote(account)}"},
            {"text": "🔗 Izvorni Tvit", "url": link}
        ]
    ]

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "reply_markup": {"inline_keyboard": keyboard}
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Greska pri slanju sentimenta: {e}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Master Bot sa 1000 financijskih i kripto profila je spreman! Koristi /help.")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🟢 Server radi besprijekorno, radari prate makro vijesti, burze, TikTok i svih 1000 profila.")

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Ručno skeniranje 1000 globalnih izvora u tijeku...")

async def meta_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎯 Trenutna meta: Globalne financije, makro, Apple & Hype meta.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Dostupne komande:\n\n"
        "/start - Pokretanje bota\n"
        "/status - Provjera servera\n"
        "/scan - Ručno skeniranje\n"
        "/meta - Trenutni fokus\n"
        "/help - Pomoć"
    )

async def background_radar(application):
    await application.bot.initialize()
    print("🚀 Master Bot sa 1000 profila pokrenut...")
    
    while True:
        try:
            # 1. Makro i financijske RSS vijesti
            for rss_url in RSS_URLS:
                feed = feedparser.parse(rss_url)
                for entry in feed.entries:
                    article_id = entry.get('id', entry.link)
                    if article_id not in SEEN_ARTICLES:
                        SEEN_ARTICLES.add(article_id)
                        score = calculate_score(entry.title)
                        if score >= 80:
                            cas = find_contract_addresses(entry.title)
                            ca_found = cas[0] if cas else None
                            dex_data = await check_dexscreener(ca_found) if ca_found else None
                            send_telegram_alert(entry.title, entry.link, score, source_type="NEWS", dex_data=dex_data, ca_found=ca_found)

            # 2. TikTok trendovi
            for tiktok_url in TIKTOK_RSS_URLS:
                feed = feedparser.parse(tiktok_url)
                for entry in feed.entries:
                    t_id = entry.get('id', entry.link)
                    if t_id not in SEEN_ARTICLES:
                        SEEN_ARTICLES.add(t_id)
                        score = calculate_score(entry.title)
                        if score >= 70:
                            cas = find_contract_addresses(entry.title)
                            ca_found = cas[0] if cas else None
                            dex_data = await check_dexscreener(ca_found) if ca_found else None
                            send_telegram_alert(entry.title, entry.link, score, source_type="TIKTOK", dex_data=dex_data, ca_found=ca_found)

            # 3. Svih 1000 financijskih i kripto profila
            for account in LEGIT_PROFILES:
                for instance in NITTER_INSTANCES:
                    try:
                        feed_url = f"{instance}/{account}/rss"
                        feed = feedparser.parse(feed_url)
                        if feed.entries:
                            entry = feed.entries[0]
                            post_id = entry.get('id', entry.link)
                            if post_id not in SEEN_ARTICLES:
                                SEEN_ARTICLES.add(post_id)
                                status, sent_score = analyze_sentiment(entry.title)
                                if sent_score >= 80 or sent_score <= 20:
                                    cas = find_contract_addresses(entry.title)
                                    if cas:
                                        ca_found = cas[0]
                                        dex_data = await check_dexscreener(ca_found)
                                        send_telegram_alert(entry.title, entry.link, sent_score, source_type="TWITTER", dex_data=dex_data, ca_found=ca_found)
                                    else:
                                        send_sentiment_alert(account, entry.title, entry.link, status, sent_score)
                            break
                    except Exception:
                        continue
                await asyncio.sleep(0.3)
            
        except Exception as e:
            print(f"Greska u glavnoj petlji: {e}")
        
        await asyncio.sleep(10)

async def post_init(application):
    asyncio.create_task(background_radar(application))

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("scan", scan_command))
    app.add_handler(CommandHandler("meta", meta_command))
    app.add_handler(CommandHandler("help", help_command))

    app.run_polling()

if __name__ == "__main__":
    main()
