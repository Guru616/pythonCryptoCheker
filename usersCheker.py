import json
from datetime import datetime
from typing import Dict



# Файл для хранения данных пользователей
USERS_FILE = "users.json"

def load_users() -> Dict:
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_users(users_data: Dict):
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f, indent=4)


def update_user(user_id: str, username: str, first_name: str, last_name: str):
    users = load_users()

    if user_id not in users:
        users[user_id] = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        users[user_id]["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if username: users[user_id]["username"] = username
        if first_name: users[user_id]["first_name"] = first_name
        if last_name: users[user_id]["last_name"] = last_name

    save_users(users)


def get_user_wallets_count(user_id: str, wallets_data: Dict) -> int:
    return len(wallets_data.get(user_id, []))