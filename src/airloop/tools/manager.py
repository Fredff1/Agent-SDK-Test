from __future__ import annotations

from agents import RunContextWrapper, function_tool

from airloop.domain.context import AirlineAgentContext
from airloop.service.data_service import DataService


class ToolManager:
    def __init__(self, data_service: DataService):
        self.data_service = data_service
        self.flight_status_tool = self._build_flight_status_tool()
        self.cancel_flight = self._build_cancel_flight()
        self.baggage_tool = self._build_baggage_tool()
        self.update_seat = self._build_update_seat()
        self.display_seat_map = self._build_display_seat_map()
        self.order_food = self._build_order_food()
        self.faq_lookup_tool = self._build_faq_lookup_tool()

    def _build_flight_status_tool(self):
        @function_tool(
            name_override="flight_status_tool",
            description_override="Lookup status for a flight.",
        )
        async def flight_status_tool(
            context: RunContextWrapper[AirlineAgentContext],
            flight_number: str,
        ) -> str:
            flight = self.data_service.get_flight_by_number(flight_number)
            if not flight:
                return f"Flight {flight_number} was not found."
            return (
                f"Flight {flight_number} is on time. "
                f"Seat range: {flight['seat_start']}-{flight['seat_end']}."
            )

        return flight_status_tool

    def _build_cancel_flight(self):
        @function_tool(
            name_override="cancel_flight",
            description_override="Cancel a flight.",
        )
        async def cancel_flight(context: RunContextWrapper[AirlineAgentContext]) -> str:
            user_id = context.context.user_id
            order_id = context.context.order_id
            if user_id is None:
                return "User ID is required to cancel a flight."
            if order_id is None:
                return "Order ID is required to cancel a flight."
            order = self.data_service.get_order(order_id, user_id)
            if not order:
                return "Order not found."
            self.data_service.cancel_order(user_id, order_id)
            context.context.order_id = None
            return f"Flight {order['flight_number']} successfully cancelled."

        return cancel_flight

    def _build_baggage_tool(self):
        @function_tool(
            name_override="baggage_tool",
            description_override="Lookup baggage allowance and fees.",
        )
        async def baggage_tool(query: str) -> str:
            q = query.lower()
            if "fee" in q:
                return "Overweight bag fee is $75."
            if "allowance" in q:
                return "One carry-on and one checked bag (up to 50 lbs) are included."
            return "Please provide details about your baggage inquiry."

        return baggage_tool

    def _build_update_seat(self):
        @function_tool
        async def update_seat(
            context: RunContextWrapper[AirlineAgentContext],
            confirmation_number: str,
            new_seat: str,
        ) -> str:
            user_id = context.context.user_id
            order_id = context.context.order_id
            if user_id is None:
                return "User ID is required to update a seat."
            if order_id is None:
                return "Order ID is required to update a seat."
            try:
                seat_number = int(new_seat)
            except ValueError:
                return "Seat number must be a number."
            order = self.data_service.get_order(order_id, user_id)
            if not order:
                return "Order not found."
            if not (order["seat_start"] <= seat_number <= order["seat_end"]):
                return (
                    f"Seat {seat_number} is outside the allowed range "
                    f"{order['seat_start']}-{order['seat_end']}."
                )
            context.context.confirmation_number = confirmation_number
            context.context.seat_number = str(seat_number)
            self.data_service.update_order(
                order_id=order_id,
                user_id=user_id,
                seat_number=seat_number,
            )
            return f"Updated seat to {seat_number} for confirmation number {confirmation_number}"

        return update_seat

    def _build_display_seat_map(self):
        @function_tool(
            name_override="display_seat_map",
            description_override="Display an interactive seat map to the customer so they can choose a new seat.",
        )
        async def display_seat_map(context: RunContextWrapper[AirlineAgentContext]) -> str:
            user_id = context.context.user_id
            order_id = context.context.order_id
            if user_id is None:
                return "User ID is required to display seats."
            if order_id is None:
                return "Order ID is required to display seats."
            order = self.data_service.get_order(order_id, user_id)
            if not order:
                return "Order not found."
            seats = []
            for seat in range(order["seat_start"], order["seat_end"] + 1):
                seats.append(str(seat))
            rows = [" ".join(seats[i:i + 4]) for i in range(0, len(seats), 4)]
            return "\n".join(rows)

        return display_seat_map

    def _build_order_food(self):
        @function_tool(
            name_override="order_food",
            description_override="Order in-flight food for the passenger. Requires a meal name.",
        )
        async def order_food(
            context: RunContextWrapper[AirlineAgentContext],
            meal: str,
        ) -> str:
            user_id = context.context.user_id
            order_id = context.context.order_id
            if user_id is None:
                return "User ID is required to order food."
            if order_id is None:
                return "Order ID is required to order food."
            if not meal:
                return "Please specify a meal to order."
            available = [m.lower() for m in (context.context.available_meals or [])]
            if available and meal.lower() not in available:
                return f"Meal '{meal}' is not available. Available meals: {', '.join(context.context.available_meals)}"
            try:
                self.data_service.update_order(
                    order_id=order_id,
                    user_id=user_id,
                    meal_selection=meal,
                )
            except ValueError:
                return "Order not found."
            context.context.meal_selection = meal
            return f"Order placed for: {meal}"

        return order_food

    def _build_faq_lookup_tool(self):
        @function_tool(
            name_override="faq_lookup_tool",
            description_override="Lookup frequently asked questions.",
        )
        async def faq_lookup_tool(question: str) -> str:
            q = question.lower()
            if "bag" in q or "baggage" in q:
                return (
                    "You are allowed to bring one bag on the plane. "
                    "It must be under 50 pounds and 22 inches x 14 inches x 9 inches."
                )
            if "seats" in q or "plane" in q:
                return (
                    "There are 120 seats on the plane. "
                    "There are 22 business class seats and 98 economy seats. "
                    "Exit rows are rows 4 and 16. "
                    "Rows 5-8 are Economy Plus, with extra legroom."
                )
            if "wifi" in q:
                return "We have free wifi on the plane, join Airline-Wifi"
            return "I'm sorry, I don't know the answer to that question."

        return faq_lookup_tool
