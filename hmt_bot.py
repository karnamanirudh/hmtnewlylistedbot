import requests
from bs4 import BeautifulSoup
import json
import time
import datetime
import os

# 🔑 Replace with your Telegram bot token and chat ID
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_IDS = os.getenv("CHAT_IDS", "").split(",")

WATCHDATA_FILE = 'seen_watches.json'
URL = "https://hmtwatches.in/"

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for chat_id in CHAT_IDS:
        payload = {"chat_id": CHAT_ID, "text": text}
        try:
             r = requests.post(url, data=payload)
             print(f"Sent to {chat_id}: {r.status_code}")
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")

def fetch_newly_listed():
    resp = requests.get(URL)
    soup = BeautifulSoup(resp.text, 'html.parser')

    new_section = soup.find("a", string="Newly Listed")
    if not new_section:
        return []

    product_grid = new_section.find_next("div")
    items = []
    for product in product_grid.find_all("a", href=True):
        title = product.get_text(strip=True)
        link = product['href']
        if title:
            if not link.startswith("http"):
                link = "https://hmtwatches.in" + link
            items.append({'title': title, 'link': link})
    return items

def load_seen():
    try:
        return json.load(open(WATCHDATA_FILE))
    except:
        return []

def save_seen(data):
    with open(WATCHDATA_FILE, 'w') as f: 
        json.dump(data, f)

def main_loop():
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

        # ✅ Print timestamp for confirmation
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{now}] Checked for new watches. Found {len(new)} new listings.")

        time.sleep(300)  # check every 5 minutes

if __name__ == "__main__":
    main_loop()
