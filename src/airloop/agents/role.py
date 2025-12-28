from enum import Enum, auto

class AgentRole(Enum):
    GUARD_RELEVANCE = auto()
    GUARD_JAILBREAK = auto()
    TRIAGE = auto()
    FAQ = auto()
    FLIGHT_STATUS = auto()
    FLIGHT_CANCEL = auto()
    SEAT_BOOKING = auto()
    FOOD = auto()

    
    
