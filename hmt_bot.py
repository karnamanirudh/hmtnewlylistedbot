import requests
from bs4 import BeautifulSoup
import json
import time
import datetime
import os
import threading
from flask import Flask

app = Flask(__name__)

# ✅ Load secrets from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_IDS = os.getenv("CHAT_IDS", "").split(",")

WATCHDATA_FILE = 'seen_watches.json'
URL = "https://hmtwatches.in/"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for chat_id in CHAT_IDS:
        chat_id = chat_id.strip()
        if not chat_id:
            continue
        try:
            payload = {"chat_id": chat_id, "text": text}
            r = requests.post(url, data=payload)
            print(f"Sent to {chat_id}: {r.status_code}")
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")

def fetch_newly_listed():
    resp = requests.get(URL)
    soup = BeautifulSoup(resp.text, 'html.parser')

    # ✅ "Newly Listed" is inside <div id="menu1">
    new_section = soup.find("div", id="menu1")
    if not new_section:
        print("⚠️ Could not find 'Newly Listed' section")
        return []

    items = []
    for product in new_section.find_all("div", class_="bc_p_item"):
        title_tag = product.find("a", class_="bc_p_name")
        title = title_tag.get_text(strip=True) if title_tag else None

        link_tag = product.find("a", class_="bc_p_img", href=True)
        link = link_tag['href'] if link_tag else None

        if title and link:
            if not link.startswith("http"):
                link = "https://www.hmtwatches.in" + link
            items.append({'title': title, 'link': link})
            print(f"DEBUG Found: {title} -> {link}")  # 👀 Debug

    return items

def load_seen():
    try:
        return json.load(open(WATCHDATA_FILE))
    except:
        return []

def save_seen(data):
    with open(WATCHDATA_FILE, 'w') as f:
        json.dump(data, f)

def bot_loop():
    seen = load_seen()
    while True:
        current = fetch_newly_listed()
        new = [w for w in current if w not in seen]

        if new:
            for w in new:
                msg = f"🔥 New Watch:\n{w['title']}\n{w['link']}"
                send_telegram_message(msg)
            seen.extend(new)
            save_seen(seen)
        else:
            # Only log to console, don’t spam Telegram
            print("⏰ Checked — no new watches this hour.")

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] Checked. Found {len(new)} new listings.")

        time.sleep(3600)  # check every 1 hour

# Run bot in background thread
threading.Thread(target=bot_loop, daemon=True).start()

# Minimal Flask app to satisfy Render
@app.route("/")
def home():
    return "HMT Bot running 🚀"

if __name__ == "__main__":
    send_telegram_message("🚀 HMT Watch Bot started on Render!")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)