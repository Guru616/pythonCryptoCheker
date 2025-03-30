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

# Популярные токены (контракты могут меняться)
COMMON_TOKENS = {
    'Ethereum': {
        'USDT': '0xdac17f958d2ee523a2206206994597c13d831ec7',
        'USDC': '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',
        'DAI': '0x6b175474e89094c44da98b954eedeac495271d0f',
    },
    'BSC': {
        'BUSD': '0xe9e7cea3dedca5984780bafc599bd69add087d56',
        'USDT': '0x55d398326f99059ff775485246999027b3197955',
    },
    # Добавьте другие сети и токены по аналогии
}