# Добавляем в начало файла
import json

FEEDBACK_FILE = "feedback.json"

# Функции для работы с отзывами
def load_feedback():
    try:
        with open(FEEDBACK_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_feedback(feedback_data):
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(feedback_data, f, indent=4)
