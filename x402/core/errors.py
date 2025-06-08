from .models import PaymentRequirement


class X402PaymentRequiredError(Exception):
    """
    Exception raised when a payment is required to access a resource.
    """
    
    def __init__(self, message: str, requirements: list[PaymentRequirement]):
        self.message = message
        self.requirements = requirements
        
    def __str__(self):
        return f"{self.message}: {self.requirements}"