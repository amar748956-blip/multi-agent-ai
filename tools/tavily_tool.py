
import os
import time
import logging
import requests

from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Tavily configuration
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

client = None

if TAVILY_API_KEY:
    client = TavilyClient(api_key=TAVILY_API_KEY)
else:
    logger.warning(
        "TAVILY_API_KEY is missing. "
        "Please configure it in your environment or Streamlit Secrets."
    )


def tavily_search(query, max_results=5, max_attempts=3):
    """
    Search the web using Tavily with retry handling.

    Args:
        query (str): Search query.
        max_results (int): Maximum number of results.
        max_attempts (int): Number of attempts for temporary failures.

    Returns:
        str: Formatted search results or a safe error message.
    """

    # Validate query
    if not query or not str(query).strip():
        return "No search query provided."

    # Validate API configuration
    if client is None:
        logger.error("Tavily API key is not configured.")
        return (
            "Hotel search is temporarily unavailable because "
            "the search API is not configured. Please try again later."
        )

    query = str(query).strip()

    for attempt in range(max_attempts):
        try:
            response = client.search(
                query=query,
                max_results=max_results,
                timeout=30,
            )

            search_results = response.get("results", [])

            if not search_results:
                return "No relevant hotel or travel information was found."

            results = []

            for i, result in enumerate(search_results, 1):
                title = result.get("title") or "Unknown"
                url = result.get("url") or ""
                snippet = (result.get("content") or "").strip()

                # Limit snippet length
                if len(snippet) > 300:
                    snippet = snippet[:300].rsplit(" ", 1)[0] + "..."

                results.append(
                    f"{i}. **{title}**\n"
                    f"   {url}\n"
                    f"   {snippet}"
                )

            return "\n\n".join(results)

        except (requests.exceptions.RequestException, TimeoutError) as exc:
            logger.warning(
                "Tavily connection failed (attempt %s/%s): %s",
                attempt + 1,
                max_attempts,
                type(exc).__name__,
            )

            if attempt < max_attempts - 1:
                time.sleep(2 ** attempt)
                continue

            logger.error(
                "Tavily search failed after %s attempts.",
                max_attempts,
            )

            return (
                "Hotel search is temporarily unavailable because "
                "the web search service could not be reached. "
                "Please try generating your travel plan again later."
            )

        except Exception:
            logger.exception("Unexpected error during Tavily search.")

            return (
                "An unexpected error occurred during hotel search. "
                "Please try again later."
            )

    return "Hotel search is temporarily unavailable."
