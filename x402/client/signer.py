import time
import secrets
from eth_account import Account
# from eth_account.messages import encode_structured_data
from x402.core.enums import PaymentNetwork
from x402.core.models import PaymentRequirement, PaymentPayload

KNOWN_TOKENS = {
    "84532": [
        {
            "human_name": "usdc",
            "address": "0x036CbD53842c5426634e7929541eC2318f3dCF7e",
            "name": "USDC",
            "decimals": 6,
            "version": "2",
        }
    ],
    "8453": [
        {
            "human_name": "usdc",
            "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "name": "USD Coin",  # needs to be exactly what is returned by name() on contract
            "decimals": 6,
            "version": "2",
        }
    ],
    "43113": [
        {
            "human_name": "usdc",
            "address": "0x5425890298aed601595a70AB815c96711a31Bc65",
            "name": "USD Coin",
            "decimals": 6,
            "version": "2",
        }
    ],
    "43114": [
        {
            "human_name": "usdc",
            "address": "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
            "name": "USDC",
            "decimals": 6,
            "version": "2",
        }
    ],
}


class SimpleX402Signer:
    """Simple payment signer for x402 payments."""
    
    def __init__(self, private_key: str):
        """
        Initialize with Ethereum private key.
        
        Args:
            private_key: Hex string private key (with or without 0x prefix)
        """
        if not private_key.startswith('0x'):
            private_key = '0x' + private_key
        
        self.account = Account.from_key(private_key)
        
    def create_exact_payment(self, requirement: PaymentRequirement, amount: str | None = None) -> PaymentPayload:
        """
        Create an exact payment payload.
        
        Args:
            requirement: Payment requirement from server
            amount: Amount to pay (defaults to max_amount_required)
        """
        if amount is None:
            amount = requirement.max_amount_required
        
        # Generate nonce for replay protection
        nonce = "0x" + secrets.token_hex(32)
        
        # Calculate expiry timestamps
        valid_after = int(time.time()) - requirement.max_timeout_seconds
        valid_before = int(time.time()) + requirement.max_timeout_seconds
        
        # Get chain ID based on network
        chain_id = self._get_chain_id(requirement.network)
        
        # Get token info from requirement.extra or use defaults
        token_name = self._get_token_name(str(chain_id), requirement.asset)
        token_version = self._get_token_version(str(chain_id), requirement.asset)
        
        # Create EIP-712 structured data for TransferWithAuthorization
        # This matches USDC's EIP-3009 standard
        domain = {
            "name": token_name,
            "version": token_version,
            "chainId": chain_id,
            "verifyingContract": requirement.asset
        }
        
        types = {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "chainId", "type": "uint256"},
                {"name": "verifyingContract", "type": "address"}
            ],
            "TransferWithAuthorization": [
                {"name": "from", "type": "address"},
                {"name": "to", "type": "address"},
                {"name": "value", "type": "uint256"},
                {"name": "validAfter", "type": "uint256"},
                {"name": "validBefore", "type": "uint256"},
                {"name": "nonce", "type": "bytes32"}
            ]
        }
        
        message = {
            "from": self.account.address,
            "to": requirement.pay_to,
            "value": amount,
            "validAfter": valid_after,
            "validBefore": valid_before,
            "nonce": nonce
        }
        
        # Sign using eth_account's correct method
        signature = self.account.sign_typed_data(
            domain_data=domain,
            message_types=types,
            message_data=message
        )
        
        # Create payment payload
        payload = {
            "from": self.account.address,
            "to": requirement.pay_to,
            "value": amount,
            "validAfter": str(valid_after),
            "validBefore": str(valid_before), 
            "nonce": nonce,
            "signature": {
                "r": hex(signature.r),
                "s": hex(signature.s),
                "v": signature.v
            }
        }
        
        return PaymentPayload(
            x402_version=1,
            scheme=requirement.scheme,
            network=requirement.network,
            payload=payload
        )


    
    def _get_chain_id(self, network: PaymentNetwork) -> int:
        """Get chain ID from network."""
        chain_ids = {
            PaymentNetwork.ETHEREUM_MAINNET: 1,
            PaymentNetwork.ETHEREUM_SEPOLIA: 11155111,
            PaymentNetwork.BASE_MAINNET: 8453,
            PaymentNetwork.BASE_SEPOLIA: 8453
        }
        return chain_ids.get(network, 1)

    def _get_token_name(self, chain_id: str, address: str) -> str:
        """Get the token name for a given chain and address"""
        for token in KNOWN_TOKENS[chain_id]:
            if token["address"] == address:
                return token["name"] # type: ignore
        raise ValueError(f"Token not found for chain {chain_id} and address {address}")

    def _get_token_version(self, chain_id: str, address: str) -> str:
        """Get the token version for a given chain and address"""
        for token in KNOWN_TOKENS[chain_id]:
            if token["address"] == address:
                return token["version"] # type: ignore
        raise ValueError(f"Token not found for chain {chain_id} and address {address}")