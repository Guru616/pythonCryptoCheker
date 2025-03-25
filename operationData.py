
import json
from cryptography.fernet import Fernet
import os


# Конфигурация
WALLETS_FILE = "wallets.enc"
KEY_FILE = "secret.key"


# Генерация или загрузка ключа шифрования
def get_encryption_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
        return key


# Шифрование данных
def encrypt_data(data: dict) -> bytes:
    f = Fernet(get_encryption_key())
    return f.encrypt(json.dumps(data).encode())


# Дешифровка данных
def decrypt_data(encrypted_data: bytes) -> dict:
    f = Fernet(get_encryption_key())
    try:
        return json.loads(f.decrypt(encrypted_data).decode())
    except:
        return {}


# Загрузка кошельков из файла
def load_wallets():
    if os.path.exists(WALLETS_FILE):
        with open(WALLETS_FILE, "rb") as f:
            encrypted_data = f.read()
            return decrypt_data(encrypted_data)
    return {}


# Сохранение кошельков в файл
def save_wallets(data: dict):
    with open(WALLETS_FILE, "wb") as f:
        f.write(encrypt_data(data))