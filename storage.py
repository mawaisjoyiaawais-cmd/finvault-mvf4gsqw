import os
import json
import hashlib
from datetime import datetime
from kivy.app import App

SETTINGS_FILE = "settings.json"
TRANSACTIONS_FILE = "transactions.json"
GOALS_FILE = "goals.json"

DEFAULT_SETTINGS = {
    "pin_hash": "",
    "currency": "$",
    "privacy_mode": False,
    "is_pin_set": False
}

def _get_file_path(filename):
    app = App.get_running_app()
    if app and hasattr(app, "user_data_dir") and app.user_data_dir:
        base_dir = app.user_data_dir
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(base_dir):
        try:
            os.makedirs(base_dir, exist_ok=True)
        except Exception:
            pass
    return os.path.join(base_dir, filename)

def load(name, default=None):
    filepath = _get_file_path(name)
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save(name, data):
    filepath = _get_file_path(name)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def hash_pin(pin):
    if not pin:
        return ""
    salt = "finvault_salt_2024_secure"
    return hashlib.sha256((pin + salt).encode("utf-8")).hexdigest()

def get_settings():
    stored = load(SETTINGS_FILE, DEFAULT_SETTINGS.copy())
    merged = DEFAULT_SETTINGS.copy()
    if isinstance(stored, dict):
        merged.update(stored)
    return merged

def save_settings(settings):
    return save(SETTINGS_FILE, settings)

def is_pin_configured():
    settings = get_settings()
    return bool(settings.get("is_pin_set")) and bool(settings.get("pin_hash"))

def verify_pin(pin):
    settings = get_settings()
    expected = settings.get("pin_hash", "")
    if not expected:
        return False
    return hash_pin(pin) == expected

def set_new_pin(pin):
    settings = get_settings()
    settings["pin_hash"] = hash_pin(pin)
    settings["is_pin_set"] = True
    return save_settings(settings)

def get_transactions():
    data = load(TRANSACTIONS_FILE, [])
    if isinstance(data, list):
        return data
    return []

def save_transactions(transactions):
    return save(TRANSACTIONS_FILE, transactions)

def add_transaction(item):
    txs = get_transactions()
    if "id" not in item or not item["id"]:
        item["id"] = str(int(datetime.now().timestamp() * 1000))
    if "timestamp" not in item:
        item["timestamp"] = datetime.now().isoformat()
    txs.insert(0, item)
    save_transactions(txs)
    return item

def delete_transaction(tx_id):
    txs = get_transactions()
    txs = [t for t in txs if str(t.get("id")) != str(tx_id)]
    save_transactions(txs)
    return True

def get_goals():
    data = load(GOALS_FILE, [])
    if isinstance(data, list):
        return data
    return []

def save_goals(goals):
    return save(GOALS_FILE, goals)

def add_goal(goal):
    goals = get_goals()
    if "id" not in goal or not goal["id"]:
        goal["id"] = str(int(datetime.now().timestamp() * 1000))
    goals.append(goal)
    save_goals(goals)
    return goal

def update_goal(goal_id, current_amount):
    goals = get_goals()
    for g in goals:
        if str(g.get("id")) == str(goal_id):
            g["current_amount"] = float(current_amount)
            break
    save_goals(goals)
    return True

def delete_goal(goal_id):
    goals = get_goals()
    goals = [g for g in goals if str(g.get("id")) != str(goal_id)]
    save_goals(goals)
    return True

def reset_all_data():
    default_set = DEFAULT_SETTINGS.copy()
    save_settings(default_set)
    save_transactions([])
    save_goals([])
    return True

def format_currency(amount, currency_symbol=None):
    if currency_symbol is None:
        settings = get_settings()
        currency_symbol = settings.get("currency", "$")
    try:
        num = float(amount)
    except (ValueError, TypeError):
        num = 0.0
    return f"{currency_symbol}{num:,.2f}"
