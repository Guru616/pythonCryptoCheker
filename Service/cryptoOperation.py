# Функции для работы с блокчейном
import logging

from pybit.unified_trading import HTTP
from web3 import Web3


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


async def get_token_balance(web3, wallet_address, token_address):
    try:
        # Преобразуем адреса в checksum-формат
        wallet_address = Web3.to_checksum_address(wallet_address)
        token_address = Web3.to_checksum_address(token_address)

        # Стандартный ABI для ERC20 токенов (только функция balanceOf)
        abi = '[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]'

        contract = web3.eth.contract(address=token_address, abi=abi)
        balance = contract.functions.balanceOf(wallet_address).call()
        decimals = 18  # По умолчанию

        # Попробуем получить decimals из контракта
        try:
            decimals_abi = '[{"constant":true,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]'
            decimals_contract = web3.eth.contract(address=token_address, abi=decimals_abi)
            decimals = decimals_contract.functions.decimals().call()
        except Exception as e:
            logging.warning(f"Couldn't get decimals for token {token_address}, using 18: {e}")

        return balance / (10 ** decimals)
    except Exception as e:
        logging.error(f"Error getting token balance: {e}")
        return 0

# Функция для получения цены токена (можно реализовать через CoinGecko API или другой источник)
async def get_token_price(token_symbol):
    prices = {
        'ETH': get_eth_to_usdt(),
        'MATIC': 0.55,  # Примерное значение, замените на актуальное
        'BNB': 300.00,  # Примерное значение
        'USDT': 1.0,
        'USDC': 1.0,
        'DAI': 1.0
    }
    return prices.get(token_symbol.upper(), 0)