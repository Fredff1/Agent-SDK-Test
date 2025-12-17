import random

from pydantic import BaseModel

class AirlineAgentContext(BaseModel):
    """Context for airline customer service agents."""
    passenger_name: str | None = None
    confirmation_number: str | None = None
    seat_number: str | None = None
    flight_number: str | None = None
    account_number: str | None = None  # Account number associated with the customer

def create_initial_context() -> AirlineAgentContext:
    """
    Factory for a new AirlineAgentContext.
    For demo: generates a fake account number.
    In production, this should be set from real user data.
    """
    ctx = AirlineAgentContext()
    ctx.account_number = str(random.randint(10000000, 99999999))
    return ctx