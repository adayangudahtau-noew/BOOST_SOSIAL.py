#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# FORGELAB TOOL — BOOST SOSIAL (RAILWAY READY)
# Dev: @PeiterStore — fixed by Muse

import os
import sys
import re
import time
import threading
import sqlite3
import logging
from pathlib import Path
from flask import Flask

# Fix encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except: pass

# Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== CONFIG AMAN =====
BOT_TOKEN = os.getenv("8896732711:AAHgBnPNpi0fdU2WhsNxi0kcVGvZs9MbbNs") or os.getenv("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN belum di set di Railway Variables!")
    sys.exit(1)

OWNER_ID = 7092151463
OWNER_USERNAME = "@Noemia07"
BRAND_NAME = "NOE"
VERSION = "v1.0 Railway"

FORCE_CHANNELS = []
MAX_CONCURRENT_BOOSTS = 3
MAX_WORKERS_PER_BOOST = 500

# Directory
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "ForgeLabData"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = str(DATA_DIR / "forgelab.db")

logging.basicConfig(format="[%(asctime)s] %(levelname)s — %(message)s", level=logging.INFO)
log = logging.getLogger("boost")

# ===== Flask dummy biar Railway gak sleep =====
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return f"{NOE} {V 1.0} - Bot Online!"

def run_flask():
    port = int(os.getenv("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()

# ===== DATABASE (copy dari code lu, gue singkatin) =====
_db_lock = threading.Lock()
def db_conn():
    con = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL")
    return con

def init_db():
    with _db_lock, db_conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, is_free_bot INTEGER DEFAULT 0, is_premium_bot INTEGER DEFAULT 0, is_banned INTEGER DEFAULT 0, first_seen INTEGER, last_seen INTEGER);
        CREATE TABLE IF NOT EXISTS devices (id INTEGER PRIMARY KEY AUTOINCREMENT, device_id TEXT UNIQUE, source TEXT, added_by INTEGER, added_at INTEGER);
        """)
init_db()

def clean_device_id(raw):
    if not raw: return ""
    s = str(raw).strip().strip("\"' ,;\r\n\t")
    if s.startswith(("and_", "ios_")) and len(s) >= 15:
        return s.split()[0].split(",")[0]
    i = s.find("and_")
    if i != -1:
        e = i+4
        while e < len(s) and (s[e].isalnum() or s[e] in "-_"): e+=1
        return s[i:e]
    return ""

# ===== HANDLER BOT (contoh simple, logic boost lu tinggal tempel di sini) =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"✅ {BRAND_NAME} {VERSION} Online di Railway!\n\nKirim file .txt berisi device and_\nBot anti delay, jalan 24 jam.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file = await doc.get_file()
    content = (await file.download_as_bytearray()).decode('utf-8', errors='ignore')
    devices = [clean_device_id(l) for l in content.splitlines()]
    devices = [d for d in devices if d]
    
    # Simpan ke DB
    now = int(time.time())
    added = 0
    with _db_lock, db_conn() as c:
        for d in devices:
            try:
                cur = c.execute("INSERT OR IGNORE INTO devices(device_id, source, added_by, added_at) VALUES (?,?,?,?)", (d, "upload", update.effective_user.id, now))
                if cur.rowcount>0: added+=1
            except: pass
    
    await update.message.reply_text(f"Done bg! Total diterima: {len(devices)}\nBaru ke-add: {added}\nDuplikat di-skip otomatis.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    print("Bot polling started with drop_pending_updates=True")
    app.run_polling(drop_pending_updates=True)
