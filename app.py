from flask import Flask, render_template, jsonify
import requests, json, os, time, threading, xml.etree.ElementTree as ET, yfinance as yf
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')

# =====================================================================
# =============================== FILTERS ===============================
# =====================================================================

@app.template_filter('datetimeformat')
def datetimeformat(value, fmt="%H:%M"):
    try:
        return datetime.fromtimestamp(int(value)).strftime(fmt)
    except Exception:
        return value

# =====================================================================
# =============================== CACHE ===============================
# =====================================================================

CACHE_FILE = "cache.json"
CACHE_TTL = 3 * 60 * 60  # 3 hours
OPENWEATHER_KEY = os.environ.get("OPENWEATHER_KEY", "554d82bd5b108ef8c58c522f3372dddf")

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def get_cached_data(key, fetch_func):
    cache = load_cache()
    now = time.time()

    if key in cache and (now - cache[key]["time"] < CACHE_TTL):
        return cache[key]["data"]

    data = fetch_func()
    cache[key] = {"data": data, "time": now}
    save_cache(cache)
    return data

def clear_expired_cache():
    while True:
        try:
            cache = load_cache()
            now = time.time()
            expired = [k for k, v in cache.items() if now - v.get("time", 0) > CACHE_TTL]

            if expired:
                for k in expired:
                    del cache[k]
                save_cache(cache)
                print(f"🧹 Cache cleared: {expired}")

        except Exception as e:
            print("Cache cleanup error:", e)

        time.sleep(CACHE_TTL)

threading.Thread(target=clear_expired_cache, daemon=True).start()

# =====================================================================
# =============================== WEATHER =============================
# =====================================================================

def fetch_weather_data():
    city = "Ho Chi Minh City"
    api_key = OPENWEATHER_KEY

    # ===== 1) Current Weather =====
    url_current = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={api_key}&units=metric&lang=vi"
    )
    current = requests.get(url_current, timeout=10).json()

    lat, lon = current["coord"]["lat"], current["coord"]["lon"]

    # ===== 2) Forecast 3h x 5 days =====
    url_forecast = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=vi"
    )
    forecast_raw = requests.get(url_forecast, timeout=10).json()

    # ===== Group forecast into daily results =====
    timezone_shift = forecast_raw["city"]["timezone"]
    daily = {}

    for item in forecast_raw.get("list", []):
        ts = item["dt"]
        date = datetime.utcfromtimestamp(ts + timezone_shift).strftime("%d/%m")

        temp = item["main"]["temp"]
        icon = item["weather"][0]["icon"]
        desc = item["weather"][0]["description"]

        if date not in daily:
            daily[date] = {"temps": [], "descs": [], "icons": []}

        daily[date]["temps"].append(temp)
        daily[date]["descs"].append(desc)
        daily[date]["icons"].append(icon)

    # Convert grouped data to list
    daily_list = []
    for date, info in daily.items():
        daily_list.append({
            "date": date,
            "temp_min": round(min(info["temps"]), 1),
            "temp_max": round(max(info["temps"]), 1),
            "description": max(set(info["descs"]), key=info["descs"].count),
            "icon": max(set(info["icons"]), key=info["icons"].count),
        })

    daily_list = daily_list[:6]  # Limit to 6 days

    # ===== 3) Air Quality =====
    url_air = (
        f"http://api.openweathermap.org/data/2.5/air_pollution"
        f"?lat={lat}&lon={lon}&appid={api_key}"
    )
    air = requests.get(url_air, timeout=10).json()

    return {
        "current": current,
        "forecast_daily": daily_list,
        "air": air
    }

@app.route('/weather')
def weather():
    data = get_cached_data("weather_full", fetch_weather_data)
    return render_template("weather.html", data=data)

# =====================================================================
# ============================ NEWS (VNEXPRESS) ========================
# =====================================================================

def parse_rss_items(content, limit=20):
    root = ET.fromstring(content)
    items = []

    for item in root.findall("./channel/item")[:limit]:
        items.append({
            "title": item.findtext("title"),
            "link": item.findtext("link"),
            "pubDate": item.findtext("pubDate")
        })

    return items

@app.route('/news_json')
def news_json():
    def fetch_news():
        url = "https://vnexpress.net/rss/tin-moi-nhat.rss"
        r = requests.get(url, timeout=10)
        return parse_rss_items(r.content, limit=20)

    data = get_cached_data("news", fetch_news)
    return jsonify(data)

@app.route('/news')
def news():
    return render_template('news.html')

# =====================================================================
# =============================== MARKET ===============================
# =====================================================================

@app.route('/market')
def market():
    def fetch_market():
        tickers = {
            "DXY": "DX-Y.NYB","EURUSD":"EURUSD=X","USDJPY":"JPY=X","USDCHF":"CHF=X",
            "GBPUSD":"GBPUSD=X","AUDUSD":"AUDUSD=X","USDVND":"USDVND=X",
            "VNINDEX":"^VNINDEX.VN","DJIA":"^DJI","NASDAQ":"^IXIC",
            "S&P500":"^GSPC","KOSPI":"^KS11","NIKKEI":"^N225","SHANGHAI":"000001.SS",
            "Gold":"GC=F","Silver":"SI=F","Brent":"BZ=F","Crude":"CL=F",
            "BTCUSDT":"BTC-USD","ETHUSDT":"ETH-USD","XRPUSDT":"XRP-USD","BNBUSDT":"BNB-USD"
        }

        try:
            data = yf.download(list(tickers.values()), period="2d", interval="1h",
                               progress=False, group_by="ticker")
        except:
            data = {}

        forex, stock, commodity, crypto = {}, {}, {}, {}

        for name, symbol in tickers.items():
            try:
                if isinstance(data, dict) or data is None:
                    continue

                if symbol in data.columns.get_level_values(0):
                    closes = data[symbol]["Close"].dropna()
                else:
                    closes = None

                if closes is None or len(closes) < 2:
                    continue

                current = closes.iloc[-1]
                prev = closes.iloc[-2]

                row = {
                    "price": round(float(current), 2),
                    "change": "▲" if current > prev else "▼",
                    "percent": round(((current - prev) / prev) * 100, 2)
                }

                if name in ["DXY","EURUSD","USDJPY","USDCHF","GBPUSD","AUDUSD","USDVND"]:
                    forex[name] = row
                elif name in ["VNINDEX","DJIA","NASDAQ","S&P500","KOSPI","NIKKEI","SHANGHAI"]:
                    stock[name] = row
                elif name in ["Gold","Silver","Brent","Crude"]:
                    commodity[name] = row
                else:
                    crypto[name] = row

            except:
                pass

        # fallback VNINDEX
        if "VNINDEX" not in stock:
            try:
                vn = yf.Ticker("^VNINDEX.VN").history(period="2d")
                if not vn.empty:
                    current = vn["Close"].iloc[-1]
                    prev = vn["Close"].iloc[-2]
                    stock["VNINDEX"] = {
                        "price": round(float(current), 2),
                        "change": "▲" if current > prev else "▼",
                        "percent": round(((current-prev)/prev)*100, 2)
                    }
            except:
                pass

        # potential symbols API
        def fetch_symbols():
            try:
                url = "https://trading-signals-pi.vercel.app/getPotentialSymbols"
                return requests.get(url, timeout=10).json()
            except:
                return {"data": [], "latest_updated": ""}

        stock_api = get_cached_data("stock_potential", fetch_symbols)

        return {
            "forex": forex,
            "stock": stock,
            "crypto": crypto,
            "commodity": commodity,
            "symbols": stock_api.get("data", []),
            "updated": stock_api.get("latest_updated", "")
        }

    data = get_cached_data("market_data", fetch_market)
    return render_template("market.html", data=data)

# =====================================================================
# =============================== FINANCE ===============================
# =====================================================================

@app.route('/finance_json')
def finance_json():
    def fetch_finance():
        url = "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines"
        r = requests.get(url, timeout=10)
        return parse_rss_items(r.content, limit=20)

    data = get_cached_data("finance", fetch_finance)
    return jsonify(data)

@app.route('/finance')
def finance():
    return render_template("finance.html")

# =====================================================================
# =============================== ROOT ===============================
# =====================================================================

@app.route('/')
def index():
    return render_template("layout.html")

if __name__ == "__main__":
    print("Starting Flask kiosk dashboard...")
    app.run(host="0.0.0.0", port=5000)
