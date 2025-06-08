import requests

from x402.client.signer import SimpleX402Signer
from x402.core.models import PaymentRequirement
from x402.core.errors import X402PaymentRequiredError

class X402Client:
    """
    Minimal x402 HTTP client with a few different request options:
    
    - request: Make HTTP request with x402 payment handling.
    - pay_and_request: Make request with payment for specific requirements.
    - auto_pay_request: Make request with automatic payment handling.
    
    args:
        signer: Payment signer for creating payment payloads
    """
    
    def __init__(self, signer: SimpleX402Signer):
        """
        Initialize x402 client.
        
        Args:
            signer: Payment signer for creating payment payloads
        """
        self.signer = signer
        self.session = requests.Session()
        
    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with x402 payment handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            X402PaymentRequiredError: When payment is required
        """
        response = self.session.request(method, url, **kwargs)
        
        if response.status_code == 402:
            # Parse payment requirements
            try:
                data = response.json()
                requirements = [PaymentRequirement.model_validate(req) for req in data["accepts"]]
                raise X402PaymentRequiredError(f"Payment required: {data}", requirements)
            except (ValueError, KeyError) as e:
                raise X402PaymentRequiredError(f"Invalid 402 response: {e}", [])
        
        return response
  
    def pay_and_request(self, method: str, url: str, requirement: PaymentRequirement, 
                       amount: str | None = None, **kwargs) -> requests.Response:
        """
        Make request with payment for specific requirements.
        
        Args:
            method: HTTP method
            url: URL to request
            requirements: Payment requirements to fulfill
            amount: Amount to pay (defaults to max_amount_required)
            **kwargs: Additional request arguments
            
        Returns:
            Response object with content
        """
        # Create payment
        payment = self.signer.create_exact_payment(requirement, amount)
        
        # Add X-PAYMENT header
        headers = kwargs.get('headers', {})
        headers['X-PAYMENT'] = payment.to_header()
        kwargs['headers'] = headers
        
        # Make request with payment
        response = self.session.request(method, url, **kwargs)
        return response
        
    def auto_pay_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make request with automatic payment handling.
        
        This method automatically handles 402 responses by creating and sending payments.
        
        Args:
            method: HTTP method
            url: URL to request
            **kwargs: Additional request arguments
            
        Returns:
            Response object with content
        """
        try:
            return self.request(method, url, **kwargs)
        except X402PaymentRequiredError as e:
            if not e.requirements:
                raise ValueError("No payment options available")
            
            # IMPORTANT: default to first payment requirement
            # TODO: improve this logic -- give client more flexibility
            requirement = e.requirements[0]
            print(f"💳 Auto-paying {requirement.max_amount_required} for: {requirement.description}")
            
            return self.pay_and_request(method, url, requirement, **kwargs)
