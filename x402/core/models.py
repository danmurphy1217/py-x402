import base64
import json
from typing import Any, Dict
from pydantic import BaseModel, Field

from .enums import PaymentScheme, PaymentNetwork

class PaymentRequirement(BaseModel):
    """
    The payment requirement an X402-compliant server sends along with a 402 Payment Required response.
    """
    
    # Required: Payment scheme (e.g., "exact")
    scheme: PaymentScheme 
    # Required: Blockchain network (e.g., "base-sepolia")
    network: PaymentNetwork 
    # Required: Amount in wei as string (e.g., "10000")
    max_amount_required: str = Field(..., alias="maxAmountRequired")
    # Required: URL path being paid for (e.g., "/premium")
    resource: str  
    # Required: Human-readable description
    description: str 
    # Required: Response content type (e.g., "application/json")
    mime_type: str = Field(..., alias="mimeType")
    # Required: Ethereum address to receive payment
    pay_to: str = Field(..., alias="payTo")
    # Required: Payment timeout (e.g., 300)
    max_timeout_seconds: int = Field(..., alias="maxTimeoutSeconds")
    # Required: ERC20 token contract address
    asset: str  
    # Optional: Schema of response data
    output_schema: dict | None = Field(None, alias="outputSchema")
    # Optional: Scheme-specific metadata
    extra: dict | None = None  
    

class PaymentRequiredResponse(BaseModel):
    """
    The response an X402-compliant server sends along with a 402 Payment Required response.
    
    args:
        x402_version: int - The version of the X402 protocol
        accepts: list[PaymentRequirement] - The list of payment requirements
        error: str - The error message
    """
    
    x402_version: int = Field(..., alias="x402Version")
    accepts: list[PaymentRequirement]
    error: str | None = None
    
class PaymentPayload(BaseModel):
    """
    x402 payment payload for X-PAYMENT header.
    
    This is the payload sent to the server after the server sends a 402 Payment Required response.
    
    args:
        x402_version: int - The version of the X402 protocol
        scheme: str - The payment scheme
        network: str - The blockchain network
        payload: Dict[str, Any] - The payment payload
    """
    x402_version: int
    scheme: PaymentScheme
    network: PaymentNetwork
    payload: Dict[str, Any]

    def to_header(self) -> str:
        """Convert to base64 encoded JSON for X-PAYMENT header."""
        data = {
            "x402Version": self.x402_version,
            "scheme": self.scheme,
            "network": self.network,
            "payload": self.payload
        }
        json_str = json.dumps(data, separators=(',', ':'))
        return base64.b64encode(json_str.encode()).decode()    
