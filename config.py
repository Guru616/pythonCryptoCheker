BOT_TOKEN = ""
ADMIN_TG_ID = ""

ETHERSCAN_KEY = ""
BSCSCAN_KEY = ""
BASESCAN_KEY = ""
# Подключение к узлам сетей
NETWORKS = {
    "Ethereum": "https://ethereum-rpc.publicnode.com",
    "Arbitrum": "https://arb1.arbitrum.io/rpc",
    "Base": "https://mainnet.base.org",
    "Polygon": "https://polygon-rpc.com",
    "BNB": "https://bsc-pokt.nodies.app",
    "OP": "https://optimism-rpc.publicnode.com",
    "Abstract":"https://api.mainnet.abs.xyz",
    #"Monad Testnet":"https://testnet-rpc.monad.xyz"
}

# Добавляем в config.py
SCAN_APIS = {
    'Ethereum': {'url': 'https://api.etherscan.io/api', 'key': ETHERSCAN_KEY},
    'BSC': {'url': 'https://api.bscscan.com/api', 'key': BSCSCAN_KEY},
    'Polygon': {'url': 'https://api.polygonscan.com/api', 'key': 'YOUR_POLYGONSCAN_KEY'},
    'Base': {'url': 'https://api.basescan.org/api', 'key': BASESCAN_KEY},
    # Добавьте другие сети по аналогии
}

TOKENS = {
    'arbitrum': {
        'USDT': '0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9'.lower(),
        'USDC': '0xaf88d065e77c8cC2239327C5EDb3A432268e5831'.lower(),
        'DAI': '0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1'.lower()
    },
    'ethereum': {
        'USDT': '0xdac17f958d2ee523a2206206994597c13d831ec7'.lower(),
        'USDC': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'.lower(),
        'DAI': '0x6b175474e89094c44da98b954eedeac495271d0f'.lower()
    },
    # Добавьте другие сети по аналогии
}
# Добавим словарь с символами нативных токенов для каждой сети
NATIVE_TOKENS = {
    'ethereum': 'ETH',
    'arbitrum': 'ETH',
    'base': 'ETH',
    'polygon': 'MATIC',
    'bsc': 'BNB',
    'optimism': 'ETH',
    'abstract': 'ETH'  # Уточните правильный символ для Abstract
}