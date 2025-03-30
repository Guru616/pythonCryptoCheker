# Функции для работы с блокчейном
import logging

from pybit.unified_trading import HTTP


def get_balance(web3, wallet_address):
    balance_wei = web3.eth.get_balance(wallet_address)
    balance_eth = web3.from_wei(balance_wei, "ether")
    return float(balance_eth)
def get_eth_to_usdt():
    session = None
    try:
        # Инициализация клиента Bybit
        session = HTTP()

        # Получаем текущую цену ETH/USDT
        ticker = session.get_tickers(category="spot", symbol="ETHUSDT")

        if ticker['retCode'] == 0 and len(ticker['result']['list']) > 0:
            return float(ticker['result']['list'][0]['lastPrice'])
        else:
            logging.error("Не удалось получить курс ETH/USDT от Bybit")
            return None
    except Exception as e:
        logging.error(f"Ошибка при получении курса через pybit: {e}")
        return None
    finally:
        # Правильное завершение сессии
        if session:
            try:
                # Для pybit нет метода close, используем del для очистки
                del session
            except Exception as e:
                logging.error(f"Ошибка при закрытии сессии: {e}")
def get_btc_to_usdt():
    session = None
    try:
        # Инициализация клиента Bybit
        session = HTTP()

        # Получаем текущую цену BTC/USDT
        ticker = session.get_tickers(category="spot", symbol="BTCUSDT")

        if ticker['retCode'] == 0 and len(ticker['result']['list']) > 0:
            return float(ticker['result']['list'][0]['lastPrice'])
        else:
            logging.error("Не удалось получить курс BTC/USDT от Bybit")
            return None
    except Exception as e:
        logging.error(f"Ошибка при получении курса BTC через pybit: {e}")
        return None
    finally:
        # Правильное завершение сессии
        if session:
            try:
                del session
            except Exception as e:
                logging.error(f"Ошибка при закрытии сессии: {e}")
