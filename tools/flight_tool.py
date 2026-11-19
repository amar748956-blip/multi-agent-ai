
import os
import re
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("AVIATIONSTACK_API_KEY")
API_URL = "https://api.aviationstack.com/v1/flights"


def search_flights(query):
    """
    Fetch flights for a specified airport route.
    AviationStack requires IATA airport codes for reliable route filtering.
    """

    if not API_KEY:
        return "Flight information unavailable: AVIATIONSTACK_API_KEY is not configured."

    query_lower = query.lower()

    # Do not show flights for trips explicitly requesting land transport.
    land_keywords = [
        "train", "railway", "bus", "road trip",
        "by road", "car journey", "instead of flights"
    ]

    if any(word in query_lower for word in land_keywords):
        return "Flights not shown because the request specifies land-based transport."

    # Look for explicit IATA airport codes in the query, e.g. DEL to BOM.
    codes = re.findall(
        r"\b([A-Z]{3})\b",
        query.upper()
    )

    departure_code = codes[0] if len(codes) >= 2 else None
    arrival_code = codes[1] if len(codes) >= 2 else None

    if not departure_code or not arrival_code:
        return (
            "No flights displayed: exact departure and arrival airport codes "
            "are required to avoid showing unrelated flights. "
            "Please specify the airport codes, for example DEL to BOM."
        )

    params = {
        "access_key": API_KEY,
        "dep_iata": departure_code,
        "arr_iata": arrival_code,
        "limit": 10,
    }

    try:
        response = requests.get(API_URL, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        if data.get("error"):
            return f"Flight API error: {data['error'].get('message', 'Unknown API error')}"

        flights = []

        for flight in data.get("data", []):
            departure = flight.get("departure") or {}
            arrival = flight.get("arrival") or {}
            airline = flight.get("airline") or {}
            flight_info = flight.get("flight") or {}

            # Validate the returned route before displaying a flight.
            if (
                departure.get("iata") != departure_code
                or arrival.get("iata") != arrival_code
            ):
                continue

            flights.append(
                f"Airline: {airline.get('name', 'Unknown')}\n"
                f"Flight: {flight_info.get('iata', 'Unknown')}\n"
                f"Departure: {departure.get('airport', 'Unknown')} "
                f"({departure.get('iata', 'N/A')})\n"
                f"Arrival: {arrival.get('airport', 'Unknown')} "
                f"({arrival.get('iata', 'N/A')})\n"
                f"Status: {flight.get('flight_status', 'Unknown')}"
            )

        if not flights:
            return (
                f"No matching flights found for "
                f"{departure_code} to {arrival_code}. "
                "This does not necessarily mean no flights operate on this route."
            )

        return "\n\n".join(flights)

    except requests.RequestException as exc:
        return f"Unable to retrieve flight information: {exc}"
    except (ValueError, TypeError, KeyError) as exc:
        return f"Unable to process flight information: {exc}"
