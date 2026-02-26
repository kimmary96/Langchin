import json
import os
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_medical_history():
    _ensure_data_dir()
    path = os.path.join(DATA_DIR, "medical_history.json")
    if not os.path.exists(path):
        save_medical_history([])
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_medical_history(history):
    _ensure_data_dir()
    path = os.path.join(DATA_DIR, "medical_history.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def load_health_diary():
    _ensure_data_dir()
    path = os.path.join(DATA_DIR, "health_diary.json")
    if not os.path.exists(path):
        save_health_diary({})
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_health_diary(diary):
    _ensure_data_dir()
    path = os.path.join(DATA_DIR, "health_diary.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(diary, f, ensure_ascii=False, indent=2)


def get_diary_entry(date_str):
    diary = load_health_diary()
    return diary.get(date_str, None)


def save_diary_entry(date_str, entry):
    diary = load_health_diary()
    diary[date_str] = entry
    save_health_diary(diary)


def save_chat_history(date_str, messages):
    _ensure_data_dir()
    path = os.path.join(DATA_DIR, f"chat_{date_str}.json")
    serializable = []
    for msg in messages:
        serializable.append({
            "role": msg.get("role", ""),
            "content": msg.get("content", ""),
        })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)


def get_chat_history(date_str):
    _ensure_data_dir()
    path = os.path.join(DATA_DIR, f"chat_{date_str}.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_dates_with_records():
    _ensure_data_dir()
    diary = load_health_diary()
    dates = set(diary.keys())
    for filename in os.listdir(DATA_DIR):
        if filename.startswith("chat_") and filename.endswith(".json"):
            date_str = filename[5:-5]
            dates.add(date_str)
    return sorted(dates)
