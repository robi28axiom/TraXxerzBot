import os
import time
import requests
import feedparser
import re
from urllib.parse import quote

TELEGRAM_BOT_TOKEN = "8725824554:AAGUsQb3t31UU9QbCbOXAIT3Uzzt5eKDKps"
TELEGRAM_CHAT_ID = "8980310038"

# 300 LEGIT PROFILA ZA SENTIMENT
LEGIT_PROFILES = [
    "aeyakovenko", "rajgokal", "solana", "solanaconf", "solanafdn", "phantom", "solflare_wallet", 
    "SuperteamDAO", "RaydiumProtocol", "JupiterExchange", "meteoraAG", "birdeye_so", "tensor_hq",
    "DRIFTProtocol", "Jito_Sol", "PhoenixTrade", "SanctumSo", "KaminoFinance", "Orca_so", "Marginfi",
    "lookonchain", "bubblemaps", "PeckShieldAlert", "WhaleChart", "WuBlockchain", "tier10k", 
    "EmberCN", "SolanaFloor", "ArkhamIntel", "ChainArgos", "DeFiLlama", "TokenUnlocks", "Dune",
    "CertiK", "SlowMist_Team", "TheDataNerd", "spotonchain", "nansen_ai", "glassnode", "Token_Terminal",
    "blknoiz06", "MachoMeme", "GCRClassic", "Santiagoroel", "HsakaTrades", "RewotM", "cryptocred", 
    "InverseBiased", "Pentosh1", "MustStopMurad", "cobie", "frankdegods", "trader1sz", "CryptoCobain", 
    "CryptoKaleo", "AltcoinSherpa", "CredibleCrypto", "ByzGeneral", "IncomeSharks", "Ansem", 
    "Rager", "MacnBTC", "loomdart", "QwQiao", "zhusu", "KyleSamani", "multicoincap", "arrington_xrp", 
    "paradigm", "punk6529", "lopp", "brian_armstrong", "MarioNawfal", "PopBase", "Dexerto", "pubity", 
    "DailyLoud", "CoinDesk", "Cointelegraph", "DecryptMedia", "Protos", "TheBlock_", "BanklessHQ", 
    "Unchained_pod", "Blockworks_", "Delphi_Digital", "MessariCrypto", "WatcherGuru", "ForbesCrypto", 
    "BloombergCrypto", "Reuters", "FinancialTimes", "WSJ", "TechCrunch", "TheVerge", "OpenAI", 
    "SamAltman", "gregkamradt", "yannlecun", "karpathy", "AnthropicAI", "midjourney", "stabilityai", 
    "elonmusk", "satyanadella", "sundarpichai", "tim_cook", "vitalikbuterin", "cz_binance",
    "SolanaLegend", "CryptoCapo_", "rekt_news", "DefiIgnas", "0xCygaar", "MuroCrypto", "DaanCrypto", 
    "CryptoMichNL", "CryptoDonAlt", "George1Giga", "GiganticRebirth", "inversebrah", "TheFlowHorse", 
    "KomiTrades", "CredAvail", "ColdBloodShill", "TheCryptoDog", "CryptoGodJohn", "Ragnar_NFT", 
    "Zeneca", "Pranksy", "BoredApeYC", "yugalabs", "Doodles", "Azuki", "beeple", "SnoopDogg", 
    "mashable", "ign", "gamespot", "verge", "wired", "engadget", "venturebeat", "techmeme", 
    "producthunt", "github", "stackoverflow", "hacker__news", "Reddit_Crypto", "Crypto_Com", 
    "krakenfx", "coinbase", "binance", "okx", "bybit", "kucoin", "gate_io", "bitgetglobal", 
    "htx_global", "mexc_global", "uniswap", "sushiswap", "pancakeswap", "curvefinance", "balancer", 
    "aavecrypto", "compoundfinance", "synthetix_io", "makerdao", "sky_ecosystem", "lidofinance", 
    "eigenlayer", "celestiaorg", "avalancheavax", "arbitrum", "optimism", "polygon", "sui_network", 
    "aptos", "nearprotocol", "cosmos", "injective", "sei_network", "monad_xyz", "berachain", "blast_l2", 
    "base", "zksync", "starknet", "scroll_zkp", "lineabuild", "mantle_official", "taiko_xyz", 
    "boba_network", "metis_l2", "arbitrum_dev", "optimism_dev", "solana_devs", "ethglobal", "hackathons", 
    "gitcoin", "buidlguidl", "ETHDenver", "Permissionless", "Consensus", "Token2049", "Bankless_DAO", 
    "Defi_Dad", "cc15calc", "Darrenlautf", "DefiLlama_News", "Solana_Daily", "SolanaNews", "SolanaUniverse", 
    "SolanaMemes", "Solana_Ecosystem", "SolanaSpotted", "SolanaDailyNews", "SolanaInsider", "Solana_Space", 
    "SolanaAlpha", "SolanaGems", "SolanaTrading", "SolanaCalls", "SolanaHedge", "SolanaWhales", "SolanaHub", 
    "SolanaTracker", "SolanaScanner", "SolanaSniper", "SolanaBots", "SolanaApe", "SolanaDegens", 
    "SolanaMoonshots", "SolanaPump", "PumpFunGems", "PumpFunAlpha", "PumpFunCalls", "PumpFunWhales", 
    "DexScreenerApp", "AxiomTrade", "Photon_Sol", "BullX_io", "TrojanOnSolana", "MaestroBots", "BonkBot", 
    "PepeCoinEth", "Dogecoin", "Shibtoken", "Floki", "Myro_Sol", "WifCoin", "BomeSolana", "PopcatSolana", 
    "MeowCoin", "CatInALaptop", "SlerfSol", "HobbesSol", "Wen_Solana", "ManekiSol", "Nodl_Sol", "SharkSol", 
    "GigaChadSol", "ToTheMoonSol", "SolanaMoon", "SolanaRocket", "SolanaGemini", "SolanaAI", "SolanaMatrix", 
    "SolanaNexus", "SolanaPortal", "SolanaNetwork", "SolanaProtocol", "SolanaChain", "SolanaLayer", "SolanaNode"
]

NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.lucabased.xyz"
]

RSS_URLS = [
    "https://news.google.com/rss/search?q=Elon+Musk+when:1h&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Trump+when:1h&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=site:x.com+crypto+when:1h&hl=en-US&gl=US&ceid=US:en",
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://decrypt.co/feed"
]

HIGH_PRIO_KEYWORDS = [
    "died", "arrested", "resigned", "shot", "killed", "launched", 
    "token", "ca:", "solana", "pump.fun", "sec", "binance", "hack", "exploit"
]

STANDARD_KEYWORDS = [
    "trump", "musk", "biden", "doge", "meme", "crypto", "fed", "rates", 
    "election", "white house", "ceo", "lawsuit", "court", "fbi", "police", "listing"
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

def send_telegram_alert(title, link, score, source_type="TWITTER"):
    ticker = extract_smart_ticker(title)
    search_encoded = quote(ticker)
    short_desc = title[:90] + "..." if len(title) > 90 else title
    
    if source_type == "TWITTER":
        header = "🐦 **[X / TWITTER ALARM]**"
    else:
        header = "📰 **[TOP VIJEST / RSS]**"
    
    message = f"{header}\n\n"
    message += f"📝 **Sadržaj:** {title}\n"
    message += f"🔥 **Score:** `{score}/100`\n"
    message += f"🎯 **Ticker:** `${ticker}`\n\n"
    message += f"📋 *Predložak za lansiranje:*\n"
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
    message = f"🧠 **[300 LEGIT PROFILA - SENTIMENT]**\n\n"
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

def main():
    print("🚀 Master Tracker & Sentiment Bot pokrenut u jednoj skripti...")
    while True:
        try:
            # 1. Provjera glavnih vijesti i trackera
            for rss_url in RSS_URLS:
                feed = feedparser.parse(rss_url)
                for entry in feed.entries:
                    article_id = entry.get('id', entry.link)
                    if article_id not in SEEN_ARTICLES:
                        SEEN_ARTICLES.add(article_id)
                        score = calculate_score(entry.title)
                        if score >= 80:
                            send_telegram_alert(entry.title, entry.link, score, source_type="NEWS")

            # 2. Provjera 300 legit profila (s pragom spuštenim na 80)
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
                                # Šalje ako je sentiment 80+ ili opasna panika (20)
                                if sent_score >= 80 or sent_score <= 20:
                                    send_sentiment_alert(account, entry.title, entry.link, status, sent_score)
                            break
                    except Exception:
                        continue
                time.sleep(1)
            
            time.sleep(15)
        except Exception as e:
            print(f"Greska u glavnoj petlji: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
