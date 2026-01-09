import random
from typing import Optional
from pydantic import BaseModel

from airloop.domain.schema import ConversationState

NAMES = [
    "Mike", "Amy", "Fred", "Cinderella", "Alice", "Bob"
]

class AirlineAgentContext(BaseModel):
    """Context for airline customer service agents."""
    user_id: int | None = None
    order_id: int | None = None
    passenger_name: str | None = None
    confirmation_number: str | None = None
    seat_number: str | None = None
    flight_number: str | None = None
    account_number: str | None = None 
    meal_preference: str | None = None  
    meal_selection: str | None = None
    available_meals: list[str] = []
    
    conversation_state: Optional[ConversationState] = None

def create_initial_context(
    user_name: Optional[str] = None,
    account_number: Optional[str] = None,
    user_id: Optional[int] = None,
    order_id: Optional[int] = None,
    confirmation_number: Optional[str] = None,
    flight_number: Optional[str] = None,
    seat_number: Optional[str] = None,
) -> AirlineAgentContext:
    """
    Factory for a new AirlineAgentContext.
    For demo: generates a fake account number.
    In production, this should be set from real user data.
    """
    ctx = AirlineAgentContext()
    ctx.user_id = user_id
    ctx.order_id = order_id
    ctx.account_number = account_number or str(random.randint(10000000, 99999999))
    ctx.passenger_name = user_name or random.choice(NAMES)
    if confirmation_number:
        ctx.confirmation_number = confirmation_number
    if flight_number:
        ctx.flight_number = flight_number
    if seat_number:
        ctx.seat_number = seat_number
    ctx.available_meals = ["Chicken set", "Beef set", "Vegetarian set"]
    return ctx
