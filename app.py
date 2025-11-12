from flask import Flask, render_template, jsonify
import requests, json, os, time, threading, xml.etree.ElementTree as ET

app = Flask(__name__)

from datetime import datetime

@app.template_filter('datetimeformat')
def datetimeformat(value):
    return datetime.fromtimestamp(value).strftime("%H:%M")

@app.template_filter('datetimeformat_day')
def datetimeformat_day(value):
    return datetime.fromtimestamp(value).strftime("%a")


CACHE_FILE = "cache.json"
CACHE_TTL = 3 * 60 * 60   # 3 tiếng
OPENWEATHER_KEY = "554d82bd5b108ef8c58c522f3372dddf"

# ---------------- Cache utilities ----------------
def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
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
            expired_keys = [k for k, v in cache.items() if now - v.get("time", 0) > CACHE_TTL]
            if expired_keys:
                for k in expired_keys:
                    del cache[k]
                save_cache(cache)
                print(f"🧹 Cache cleared: {expired_keys}")
        except Exception as e:
            print("Cache cleanup error:", e)
        time.sleep(CACHE_TTL)

threading.Thread(target=clear_expired_cache, daemon=True).start()

# ---------------- WEATHER ----------------
@app.route('/weather')
def weather():
    def fetch_weather():
        city = "Ho Chi Minh City"
        api_key = OPENWEATHER_KEY

        # 1️⃣ Lấy thông tin thời tiết hiện tại
        url_current = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=vi"
        current = requests.get(url_current, timeout=10).json()

        lat, lon = current["coord"]["lat"], current["coord"]["lon"]

        # 2️⃣ Lấy dự báo 5 ngày (mỗi 3h)
        url_forecast = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=vi"
        forecast = requests.get(url_forecast, timeout=10).json()

        # 3️⃣ Lấy chất lượng không khí (AQI)
        url_air = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
        air = requests.get(url_air, timeout=10).json()

        return {"current": current, "forecast": forecast, "air": air}

    data = get_cached_data("weather_full", fetch_weather)
    return render_template("weather.html", data=data)

# ---------------- GOLD ----------------
@app.route('/gold')
def gold():
    def fetch_gold():
        return {"price_vnd": 7800000, "price_usd": 2400}
    data = get_cached_data("gold", fetch_gold)
    return render_template('gold.html', price_vnd=data["price_vnd"], price_usd=data["price_usd"])

# ---------------- CRYPTO ----------------
@app.route('/crypto')
def crypto():
    return render_template('crypto.html')

# ---------------- STOCK ----------------
@app.route('/stock')
def stock():
    def fetch_stock():
        api_url = "https://trading-signals-pi.vercel.app/getPotentialSymbols"
        return requests.get(api_url, timeout=10).json()
    data = get_cached_data("stock", fetch_stock)
    symbols = data.get("data", [])
    updated = data.get("latest_updated", "")
    return render_template('stock.html', symbols=symbols, updated=updated)

# ---------------- NEWS (VnExpress) ----------------
def parse_rss_items(content, limit=10):
    root = ET.fromstring(content)
    items = []
    for item in root.findall("./channel/item")[:limit]:
        title = item.findtext("title")
        link = item.findtext("link")
        pubDate = item.findtext("pubDate")
        items.append({"title": title, "link": link, "pubDate": pubDate})
    return items

@app.route('/news_json')
def news_json():
    def fetch_news():
        rss_url = "https://vnexpress.net/rss/tin-moi-nhat.rss"
        r = requests.get(rss_url, timeout=10)
        return parse_rss_items(r.content, limit=20)
    data = get_cached_data("news", fetch_news)
    return jsonify(data)

@app.route('/news')
def news():
    # page sẽ fetch /news_json client-side (để có spinner)
    return render_template('news.html')

# ---------------- FINANCE (Dow Jones RSS) ----------------
@app.route('/finance_json')
def finance_json():
    def fetch_finance():
        rss_url = "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines"
        r = requests.get(rss_url, timeout=10)
        return parse_rss_items(r.content, limit=20)
    data = get_cached_data("finance", fetch_finance)
    return jsonify(data)

@app.route('/finance')
def finance():
    # page sẽ fetch /finance_json client-side
    return render_template('finance.html')

# ---------------- ROOT ----------------
@app.route('/')
def index():
    return render_template('layout.html')

if __name__ == '__main__':
    print("🚀 Flask kiosk dashboard running — cache auto-refresh every 3h")
    app.run(host='0.0.0.0', port=5000)
