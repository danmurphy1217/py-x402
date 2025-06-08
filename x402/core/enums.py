from enum import Enum

class PaymentScheme(Enum):
    EXACT = "exact"
    
    
class PaymentNetwork(Enum):
    BASE_SEPOLIA = "base-sepolia"
    BASE_MAINNET = "base-mainnet"
    ETHEREUM_SEPOLIA = "ethereum-sepolia"
    ETHEREUM_MAINNET = "ethereum-mainnet"
    
    
    