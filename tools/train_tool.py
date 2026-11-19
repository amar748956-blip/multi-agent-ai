"""
Optional Indian train-search integration.

Set QRAIL_API_KEY after creating an account at https://www.qrail.in/developers.
Qrail documents a REST API, but route endpoint details can change; configure
QRAIL_BETWEEN_STATIONS_URL from the endpoint shown in your Qrail dashboard/docs.
Use {from_station}, {to_station}, {date}, and {api_key} placeholders in that URL.
Station values should be station codes, not city names.
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

QRAIL_API_KEY = os.getenv("QRAIL_API_KEY", "").strip()
QRAIL_BETWEEN_STATIONS_URL = os.getenv("QRAIL_BETWEEN_STATIONS_URL", "").strip()


def search_trains(query: str, from_station: str = "", to_station: str = "", journey_date: str = "") -> str:
    """Fetch trains only when station codes and a documented endpoint are configured."""
    if not QRAIL_API_KEY:
        return (
            "Train API is not configured. Add QRAIL_API_KEY to Streamlit Secrets "
            "and configure QRAIL_BETWEEN_STATIONS_URL from your Qrail dashboard."
        )
    if not QRAIL_BETWEEN_STATIONS_URL:
        return (
            "Train API key is present, but QRAIL_BETWEEN_STATIONS_URL is missing. "
            "Copy the train-between-stations endpoint template from your Qrail API docs "
            "into Streamlit Secrets. Do not use a guessed endpoint."
        )
    if not from_station.strip() or not to_station.strip():
        return (
            "Train search needs the origin and destination railway station codes. "
            "Select or verify the station codes before relying on train results."
        )

    url = QRAIL_BETWEEN_STATIONS_URL.format(
        from_station=from_station.strip().upper(),
        to_station=to_station.strip().upper(),
        date=journey_date.strip(),
        api_key=QRAIL_API_KEY,
    )
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            trains = data.get("trains") or data.get("data") or data.get("results") or []
        elif isinstance(data, list):
            trains = data
        else:
            trains = []
        if not trains:
            return f"No train results were returned for {from_station.upper()} → {to_station.upper()}."
        lines = []
        for item in trains[:15]:
            if not isinstance(item, dict):
                continue
            name = item.get("trainName") or item.get("train_name") or item.get("name") or "Train"
            number = item.get("trainNumber") or item.get("train_number") or item.get("train_no") or ""
            dep = item.get("departureTime") or item.get("departure_time") or item.get("departure") or "Not provided"
            arr = item.get("arrivalTime") or item.get("arrival_time") or item.get("arrival") or "Not provided"
            duration = item.get("duration") or item.get("travelTime") or ""
            lines.append(f"- {name} {f'({number})' if number else ''}: {dep} → {arr}{f'; duration {duration}' if duration else ''}")
        return "\n".join(lines) if lines else "The train API response format was not recognized. Check the provider docs."
    except requests.RequestException as exc:
        return f"Train API request failed: {exc}"
    except (ValueError, TypeError) as exc:
        return f"Could not read train API response: {exc}"
