import json
import os
from datetime import datetime

FEEDBACK_FILE = "user_feedback.json"


def load_feedback():
    if not os.path.exists(FEEDBACK_FILE):
        return {}

    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_feedback(feedback_data):
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(feedback_data, f, ensure_ascii=False, indent=4)


def add_feedback(user_id: str, username: str, first_name: str, last_name: str, message: str):
    feedback_data = load_feedback()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if user_id not in feedback_data:
        feedback_data[user_id] = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "feedback": []
        }

    feedback_data[user_id]["feedback"].append({
        "message": message,
        "timestamp": timestamp
    })

    save_feedback(feedback_data)