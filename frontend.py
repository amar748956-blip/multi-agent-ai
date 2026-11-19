import streamlit as st
import uuid
import traceback
import re
import html
import unicodedata
import random

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from country_state_city import Country, State, City
from langchain_core.messages import HumanMessage, AIMessage
from supabase import create_client
from main import app


# ============================================================
# PAGE CONFIGURATION — MUST BE CALLED ONLY ONCE
# ============================================================

st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SUPABASE AUTHENTICATION CONNECTION
# ============================================================

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )


try:
    supabase = get_supabase()
except Exception:
    st.error(
        "Unable to connect to the authentication service. "
        "Check SUPABASE_URL and SUPABASE_KEY in "
        ".streamlit/secrets.toml."
    )
    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    st.session_state.user_email = ""


# ============================================================
# GLOBAL CSS — DARK BLUE THEME
# ============================================================

st.markdown(
    """
    <style>
    :root { color-scheme: light dark; }
    .stApp { background: var(--background-color); color: var(--text-color); }
    [data-testid="stMain"] { background: transparent; }
    h1, h2, h3, h4 { color: var(--text-color); }
    .main-title { font-size: clamp(28px, 4vw, 44px); font-weight: 800; text-align:center; margin-bottom: 6px; }
    .subtitle { text-align:center; font-size:17px; opacity:.82; margin-bottom:24px; }
    .section-title { font-size:22px; font-weight:750; margin:12px 0; }
    .login-title { text-align:center; font-size:36px; font-weight:800; }
    .login-subtitle { text-align:center; opacity:.8; margin-bottom:22px; }
    .destination-card { padding: 12px; border:1px solid var(--border-color, rgba(128,128,128,.3)); border-radius:14px; }
    [data-testid="stImage"] img { height: 220px; width: 100%; object-fit: cover; border-radius: 12px; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div { border-radius:9px; }
    div.stButton > button, div.stFormSubmitButton > button {
        border-radius:10px; font-weight:700; min-height:42px;
    }
    [data-testid="stForm"], [data-testid="stExpander"] {
        border-radius:14px;
    }
    [data-testid="stSidebar"] { border-right:1px solid rgba(128,128,128,.2); }
    a { text-underline-offset:3px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOGIN AND SIGNUP PAGE
# ============================================================

if not st.session_state.logged_in:
    left, center, right = st.columns([1, 1.2, 1])

    with center:
        st.markdown(
            '<div class="login-title">🌍 Wanderverse</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="login-subtitle">'
            'Your AI-powered travel companion'
            '</div>',
            unsafe_allow_html=True,
        )

        login_tab, signup_tab = st.tabs(["🔐 Login", "✨ Sign Up"])

        with login_tab:
            st.subheader("Welcome Back!")

            with st.form("login_form"):
                login_email = st.text_input(
                    "Email address",
                    key="login_email",
                )
                login_password = st.text_input(
                    "Password",
                    type="password",
                    key="login_password",
                )
                login_submitted = st.form_submit_button(
                    "Login",
                    use_container_width=True,
                )

            if login_submitted:
                if not login_email.strip() or not login_password:
                    st.warning("Please enter your email and password.")
                else:
                    try:
                        response = supabase.auth.sign_in_with_password({
                            "email": login_email.strip(),
                            "password": login_password,
                        })

                        if response.user:
                            st.session_state.logged_in = True
                            st.session_state.user_email = (
                                response.user.email or login_email.strip()
                            )
                            st.rerun()
                        else:
                            st.error(
                                "Login was not completed. Check your "
                                "credentials and email verification."
                            )
                    except Exception:
                        st.error(
                            "Login failed. Check your email, password, "
                            "and email verification status."
                        )

        with signup_tab:
            st.subheader("Create Your Account")

            with st.form("signup_form"):
                signup_email = st.text_input(
                    "Email address",
                    key="signup_email",
                )
                signup_password = st.text_input(
                    "Create password",
                    type="password",
                    key="signup_password",
                )
                confirm_password = st.text_input(
                    "Confirm password",
                    type="password",
                    key="confirm_password",
                )
                signup_submitted = st.form_submit_button(
                    "Create Account",
                    use_container_width=True,
                )

            if signup_submitted:
                email_value = signup_email.strip()

                if not email_value or not signup_password or not confirm_password:
                    st.warning("Please fill in all fields.")
                elif len(signup_password) < 8:
                    st.warning("Password must contain at least 8 characters.")
                elif signup_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    try:
                        response = supabase.auth.sign_up({
                            "email": email_value,
                            "password": signup_password,
                        })

                        if response.user and response.session:
                            st.session_state.logged_in = True
                            st.session_state.user_email = (
                                response.user.email or email_value
                            )
                            st.success("Account created successfully!")
                            st.rerun()
                        elif response.user:
                            st.success(
                                "Account created. Check your email for "
                                "a verification link, then return here "
                                "and log in."
                            )
                        else:
                            st.error(
                                "Supabase did not return a user. Check "
                                "your project authentication settings."
                            )

                    except Exception as e:
                        # Show the error while troubleshooting.
                        # Replace this with a generic message in production.
                        st.error(f"Signup failed: {e}")

    st.stop()


# ============================================================
# AUTHENTICATED USER / LOGOUT
# ============================================================

with st.sidebar:
    st.success(f"Logged in: {st.session_state.user_email}")

    if st.button("🚪 Logout", key="logout_button"):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass

        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.pop("last_result", None)
        st.session_state.pop("thread_id", None)
        st.rerun()


# ============================================================
# LOCATION DATA HELPERS
# ============================================================

def get_attribute(item, *attribute_names):
    """Read the first available field from a model or dictionary."""
    for attribute in attribute_names:
        value = None
        if isinstance(item, dict):
            value = item.get(attribute)
        else:
            value = getattr(item, attribute, None)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


@st.cache_data(show_spinner=False)
def get_countries():
    """Return sorted (country name, country code) pairs."""
    try:
        countries = Country.get_countries() or []
        results = []
        for item in countries:
            name = get_attribute(item, "name", "country_name", "country")
            code = get_attribute(
                item, "iso2", "iso_code", "iso2_code", "iso2Code",
                "country_code", "code", "iso3", "id"
            )
            if name:
                results.append((name, code or name))
        # Remove duplicate country names while preserving a usable code.
        unique = {}
        for name, code in results:
            unique.setdefault(name, code)
        return sorted(unique.items(), key=lambda pair: pair[0].casefold())
    except Exception:
        return []


@st.cache_data(show_spinner=False)
def get_states(country_code):
    """Return sorted (state name, state identifier) pairs."""
    try:
        states = State.get_states_of_country(country_code) or []
        results = []
        for item in states:
            name = get_attribute(item, "name", "state_name", "region", "state")
            # The city database usually expects the state's short code
            # (for example, MP), not its database ID.
            code = get_attribute(
                item, "state_code", "stateCode", "iso2", "iso_code",
                "iso3166_2", "code"
            )
            if name:
                results.append((name, code or name))
        unique = {}
        for name, code in results:
            unique.setdefault(name, code)
        return sorted(unique.items(), key=lambda pair: pair[0].casefold())
    except Exception:
        return []


@st.cache_data(show_spinner=False)
def get_cities(country_code, state_identifier, state_name):
    """Return cities for the selected state only, never a country-wide list."""
    country_code = str(country_code or "").strip()
    state_identifier = str(state_identifier or "").strip()
    state_name = str(state_name or "").strip()

    # This package expects the state's short code (e.g. MP for Madhya Pradesh).
    # Try the identifier first, then the state name for compatibility.
    for identifier in dict.fromkeys(x for x in (state_identifier, state_name) if x):
        try:
            records = City.get_cities_of_state(country_code, identifier) or []
        except Exception:
            continue

        names = set()
        for item in records:
            name = get_attribute(item, "name", "city_name", "city")
            if not name:
                continue

            # Some package/data versions expose state metadata on each city.
            # When present, enforce an exact state match to avoid showing cities
            # belonging to other states.
            city_state_code = get_attribute(
                item, "state_code", "stateCode", "state_iso2", "state_iso_code"
            )
            city_state_name = get_attribute(
                item, "state_name", "state", "region", "stateName"
            )
            if city_state_code and state_identifier and city_state_code.casefold() != state_identifier.casefold():
                continue
            if city_state_name and state_name and city_state_name.casefold() != state_name.casefold():
                continue
            names.add(name)

        if names:
            return sorted(names, key=str.casefold)

    return []


# ============================================================
# LOCATION SELECTOR
# ============================================================

@st.cache_data(ttl=86400, show_spinner=False)
def get_verified_facility_types(city, state, country):
    """Return facility types only if Nominatim finds a matching place."""
    from urllib.parse import urlencode
    import requests
    candidates = [
        ("Airport", "airport"),
        ("Railway station", "railway station"),
        ("Bus station", "bus station"),
    ]
    available = []
    for label, term in candidates:
        query = ", ".join(part for part in (term, city, state, country) if part)
        try:
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "jsonv2", "limit": 1},
                headers={"User-Agent": "WanderverseTravelPlanner/1.0 (location lookup)"},
                timeout=6,
            )
            if response.ok and response.json():
                available.append(label)
        except requests.RequestException:
            continue
    return available


def location_selector(prefix, heading):
    """Display country, state, city, and location type."""
    st.markdown(f"### {heading}")
    countries = get_countries()

    if not countries:
        st.warning(
            "Location data could not be loaded. "
            "Please enter the location details manually."
        )

        country_name = st.text_input(
            "Country",
            value="India",
            key=f"{prefix}_country_text",
        )
        state_name = st.text_input(
            "State / region",
            value="Madhya Pradesh",
            key=f"{prefix}_state_text",
        )
        city_name = st.text_input(
            "City",
            key=f"{prefix}_city_text",
        )
    else:
        country_labels = [name for name, code in countries]
        country_codes = {name: code for name, code in countries}
        default_country = "India" if "India" in country_labels else country_labels[0]

        country_name = st.selectbox(
            "Country",
            options=country_labels,
            index=country_labels.index(default_country),
            key=f"{prefix}_country",
        )
        country_code = country_codes[country_name]
        states = get_states(country_code)

        if states:
            state_labels = [name for name, code in states]
            state_codes = {name: code for name, code in states}
            default_state = state_labels[0]

            state_name = st.selectbox(
                "State / region",
                options=state_labels,
                index=state_labels.index(default_state),
                key=f"{prefix}_state_{country_code}",
            )
            state_identifier = state_codes[state_name]
            cities = get_cities(
                country_code,
                state_identifier,
                state_name,
            )

            if cities:
                city_options = ["Select a city"] + cities
                preset_destination = (
                    st.session_state.get("preset_destination", "")
                    if prefix == "destination" else ""
                )
                preset_match = next(
                    (city for city in cities if city.casefold() == preset_destination.casefold()),
                    None,
                )
                default_city_index = (
                    city_options.index(preset_match) if preset_match else 0
                )
                city_name = st.selectbox(
                    "City",
                    options=city_options,
                    index=default_city_index,
                    key=f"{prefix}_city_{country_code}_{state_identifier}",
                    help="Choose a city from the selected state.",
                )
                if city_name == "Select a city":
                    city_name = ""
            else:
                st.info(
                    "Cities are unavailable in the dropdown. "
                    "Enter the city name manually."
                )
                city_name = st.text_input(
                    "Enter city",
                    key=f"{prefix}_city_manual_{country_code}_{state_name}",
                )
        else:
            st.info(
                "State data is unavailable. "
                "Enter the state and city manually."
            )
            state_name = st.text_input(
                "State / region",
                key=f"{prefix}_state_manual_{country_code}",
            )
            city_name = st.text_input(
                "City",
                key=f"{prefix}_city_manual",
            )

    # Only offer airport/station choices when a geocoder can find one nearby.
    city_for_lookup = city_name.strip() if "city_name" in locals() else ""
    facility_options = ["City centre", "Specific place"]
    if city_for_lookup and country_name:
        try:
            facility_options += get_verified_facility_types(city_for_lookup, state_name, country_name)
        except Exception:
            pass
    previous_type = st.session_state.get(f"{prefix}_location_type", "City centre")
    if previous_type not in facility_options:
        previous_type = "City centre"
    location_type = st.selectbox(
        "Location type",
        options=list(dict.fromkeys(facility_options)),
        index=list(dict.fromkeys(facility_options)).index(previous_type),
        key=f"{prefix}_location_type",
    )

    # Ask for a specific place name only when that location type is selected.
    specific_location = ""
    if location_type == "Specific place":
        specific_location = st.text_input(
            "Specific place name",
            placeholder="e.g. Dewas Railway Station or Sanwariya Seth Temple",
            key=f"{prefix}_specific_location",
        )
    else:
        # Avoid carrying an old specific-place value into a city/airport/station query.
        st.session_state.pop(f"{prefix}_specific_location", None)

    return {
        "country": country_name.strip(),
        "state": state_name.strip(),
        "city": city_name.strip(),
        "location_type": location_type,
        "specific_location": specific_location.strip(),
    }


# ============================================================
# LOCATION VALIDATION
# ============================================================

def validate_location(location):
    """Validate a city or place with Nominatim.

    Returns True when the location matches, False when it does not,
    or None if the validation service is unavailable.
    """
    city = (location.get("city") or "").strip()
    state = (location.get("state") or "").strip()
    country = (location.get("country") or "").strip()
    specific = (location.get("specific_location") or "").strip()

    place = specific or city
    if not place:
        return False

    def normalize(value):
        value = unicodedata.normalize("NFKD", str(value or ""))
        value = "".join(
            ch for ch in value if not unicodedata.combining(ch)
        )
        return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()

    parts = [place]
    if city and (not specific or normalize(city) != normalize(specific)):
        parts.append(city)
    if state:
        parts.append(state)
    if country:
        parts.append(country)

    query = ", ".join(parts)

    try:
        geolocator = Nominatim(
            user_agent="ai_travel_planning_system"
        )
        result = geolocator.geocode(
            query,
            exactly_one=True,
            timeout=10,
            addressdetails=True,
            namedetails=True,
        )

        if result is None:
            return False

        raw = result.raw or {}
        address = raw.get("address", {}) or {}
        display_name = normalize(raw.get("display_name", ""))
        result_name = normalize(raw.get("name", ""))

        if specific:
            requested = normalize(specific)
            if requested not in result_name and requested not in display_name:
                return False

        if city:
            city_fields = [
                address.get(key, "")
                for key in (
                    "city",
                    "town",
                    "village",
                    "municipality",
                    "hamlet",
                    "suburb",
                    "city_district",
                    "county",
                )
            ]
            normalized_city = normalize(city)
            if not any(
                normalize(value) == normalized_city
                for value in city_fields
            ):
                return False

        if state:
            normalized_state = normalize(state)
            returned_state = normalize(address.get("state", ""))
            if returned_state and normalized_state != returned_state:
                return False

        if country:
            normalized_country = normalize(country)
            returned_country = normalize(address.get("country", ""))
            if returned_country and normalized_country != returned_country:
                return False

        return True

    except (GeocoderServiceError, GeocoderTimedOut, OSError):
        return None
    except Exception:
        return None


def format_location(location):
    """Convert the selected location into readable text."""
    parts = [
        location.get("specific_location"),
        location.get("city"),
        location.get("state"),
        location.get("country"),
    ]

    cleaned = []
    for part in parts:
        if part and part not in cleaned:
            cleaned.append(part)

    base_location = ", ".join(cleaned)

    if location.get("location_type"):
        base_location += f" ({location['location_type']})"

    return base_location or "Location not specified"


# ============================================================
# EXTRACT FINAL RESPONSE
# ============================================================

def clean_ai_output(content):
    """Clean HTML-like tags from AI output before displaying it."""
    if not isinstance(content, str):
        content = str(content)

    # Convert escaped HTML entities such as &lt;h2&gt; into readable text.
    content = html.unescape(content)

    # Turn common HTML layout tags into Markdown-friendly spacing/lists.
    content = re.sub(r"(?i)<\s*br\s*/?\s*>", "\n", content)
    content = re.sub(r"(?i)</\s*(p|div|h[1-6]|section|article)\s*>", "\n\n", content)
    content = re.sub(r"(?i)<\s*(p|div|section|article|h[1-6])\b[^>]*>", "", content)
    content = re.sub(r"(?i)<\s*li\b[^>]*>", "- ", content)
    content = re.sub(r"(?i)</\s*li\s*>", "\n", content)
    content = re.sub(r"(?i)</?\s*(ul|ol)\b[^>]*>", "\n", content)

    # Remove any remaining HTML tags so they are not shown literally.
    content = re.sub(r"<\s*/?\s*[a-zA-Z][^>]*>", "", content)

    # Remove accidental Markdown code fences around the whole response.
    content = re.sub(r"^\s*```(?:html|markdown|md|text)?\s*\n", "", content, flags=re.IGNORECASE)
    content = re.sub(r"\n\s*```\s*$", "", content)

    return content.strip()


def extract_final_response(result):
    """Find the latest non-empty AI response and clean its formatting."""
    messages = result.get("messages", [])

    for message in reversed(messages):
        if isinstance(message, AIMessage):
            content = message.content
            if content:
                cleaned = clean_ai_output(content)
                if cleaned:
                    return cleaned

    itinerary = result.get("itinerary", "")
    if itinerary:
        return clean_ai_output(itinerary)

    return (
        "The travel planner finished, but no final response "
        "was returned."
    )


# ============================================================
# MINIMAL SIDEBAR — ACCOUNT AND CONVERSATION CONTROLS ONLY
# ============================================================

with st.sidebar:
    st.markdown("## 🌍 Wanderverse")
    st.caption(f"Signed in as {st.session_state.user_email}")

    # Logout button
    if st.button("🚪 Logout", key="sidebar_logout_unique"):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass

        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.pop("last_result", None)
        st.session_state.pop("thread_id", None)
        st.session_state.pop("preset_destination", None)
        st.rerun()

    # Initialize a new conversation ID if missing
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())

    # Start a new trip
    if st.button("🔄 Start new trip", key="new_conversation_button"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.pop("last_result", None)
        st.session_state.pop("preset_destination", None)
        st.rerun()


@st.cache_data(ttl=3600, show_spinner=False)
def get_destination_images(query, limit=8):
    """Return several relevant destination images from Wikimedia Commons."""
    try:
        response = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "generator": "search",
                "gsrsearch": f"filetype:bitmap {query}",
                "gsrnamespace": 6,
                "gsrlimit": min(max(int(limit) * 2, 8), 20),
                "prop": "imageinfo",
                "iiprop": "url",
                "iiurlwidth": 900,
            },
            headers={"User-Agent": "WanderverseTravelPlanner/1.0"},
            timeout=12,
        )
        response.raise_for_status()
        pages = list(response.json().get("query", {}).get("pages", {}).values())
        random.shuffle(pages)
        images = []
        seen = set()
        for page in pages:
            info = (page.get("imageinfo") or [{}])[0]
            url = info.get("thumburl") or info.get("url")
            if (
                url
                and url.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png", ".webp"))
                and url not in seen
            ):
                images.append(url)
                seen.add(url)
            if len(images) >= limit:
                break
        return images
    except Exception:
        return []


def get_destination_video_ids(query, limit=3):
    """Find YouTube video IDs for a destination; returns [] if YouTube blocks search."""
    try:
        response = requests.get(
            "https://www.youtube.com/results",
            params={"search_query": f"{query} travel guide tourism"},
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36"
                )
            },
            timeout=12,
        )
        response.raise_for_status()
        ids = re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"', response.text)
        unique_ids = list(dict.fromkeys(ids))
        return unique_ids[:limit]
    except Exception:
        return []


def get_destination_image(query):
    """Get a destination image from Wikimedia Commons; no API key required."""
    import requests
    response = requests.get(
        "https://commons.wikimedia.org/w/api.php",
        params={
            "action": "query", "generator": "search", "gsrsearch": query,
            "gsrnamespace": 6, "gsrlimit": 8, "prop": "imageinfo",
            "iiprop": "url", "iiurlwidth": 900, "format": "json",
        },
        headers={"User-Agent": "WanderverseTravelPlanner/1.0"},
        timeout=10,
    )
    response.raise_for_status()
    pages = list(response.json().get("query", {}).get("pages", {}).values())
    random.shuffle(pages)
    valid_urls = []
    for page in pages:
        info = (page.get("imageinfo") or [{}])[0]
        url = info.get("thumburl") or info.get("url")
        if url and url.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png", ".webp")):
            valid_urls.append(url)
    return random.choice(valid_urls) if valid_urls else None


# ============================================================
# MAIN PAGE HEADER
# ============================================================

st.markdown(
    '<div class="main-title">'
    '🌍 AI Travel Planning System'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'Plan your journey with AI-powered travel research '
    'and personalized itineraries.'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    "Choose a travel style or destination for inspiration, then select your starting point "
    "and destination below to generate a personalized plan."
)
if st.session_state.get("trip_start_from_inspiration"):
    selected_inspiration = st.session_state.get("preset_destination", "")
    st.info(
        f"You chose {selected_inspiration}. Now select your starting point under "
        "'Starting Point — From' and confirm the destination below. Then generate your plan."
    )
st.markdown("### ✨ Find your kind of getaway")

# Destinations are curated by travel style, so each category shows relevant places.
CATEGORY_DESTINATIONS = {
    "Honeymoon": [
        ("Udaipur", "Udaipur romantic lake palace Rajasthan"),
        ("Munnar", "Munnar tea gardens Kerala"),
        ("Goa", "Goa romantic beach sunset"),
        ("Andaman", "Andaman Islands tropical beach"),
    ],
    "Family trip": [
        ("Jaipur", "Jaipur Hawa Mahal family travel"),
        ("Mysuru", "Mysore Palace Karnataka"),
        ("Ooty", "Ooty Nilgiri hills toy train"),
        ("Shimla", "Shimla Ridge family holiday"),
    ],
    "Solo travel": [
        ("Rishikesh", "Rishikesh Ganges river travel"),
        ("Pondicherry", "Pondicherry French Quarter"),
        ("McLeod Ganj", "McLeod Ganj mountains"),
        ("Kochi", "Fort Kochi Kerala streets"),
    ],
    "Adventure": [
        ("Manali", "Manali mountains trekking"),
        ("Rishikesh", "Rishikesh river rafting"),
        ("Leh", "Leh Ladakh mountain landscape"),
        ("Bir Billing", "Bir Billing paragliding Himachal"),
    ],
    "Religious / pilgrimage": [
        ("Varanasi", "Varanasi ghats Ganges"),
        ("Amritsar", "Golden Temple Amritsar"),
        ("Tirupati", "Tirumala Tirupati temple"),
        ("Ujjain", "Mahakaleshwar temple Ujjain"),
    ],
    "Weekend getaway": [
        ("Pachmarhi", "Pachmarhi Madhya Pradesh waterfalls"),
        ("Agra", "Taj Mahal Agra"),
        ("Lonavala", "Lonavala hills waterfalls"),
        ("Nashik", "Nashik vineyards temples"),
    ],
    "Season-based winter trip": [
        ("Shimla", "Shimla winter snow"),
        ("Manali", "Manali snow mountains winter"),
        ("Gulmarg", "Gulmarg Kashmir snow"),
        ("Auli", "Auli Uttarakhand snow skiing"),
    ],
    "Season-based monsoon trip": [
        ("Lonavala", "Lonavala monsoon green hills waterfall"),
        ("Cherrapunji", "Cherrapunji monsoon waterfalls"),
        ("Coorg", "Coorg monsoon green coffee hills"),
        ("Mahabaleshwar", "Mahabaleshwar monsoon valley"),
    ],
}

CATEGORY_BUTTONS = [
    ("💑 Honeymoon", "Honeymoon"),
    ("👨‍👩‍👧 Family", "Family trip"),
    ("🎒 Solo travel", "Solo travel"),
    ("🥾 Adventure", "Adventure"),
    ("🛕 Pilgrimage", "Religious / pilgrimage"),
    ("🌤️ Weekend", "Weekend getaway"),
    ("❄️ Winter", "Season-based winter trip"),
    ("🌧️ Monsoon", "Season-based monsoon trip"),
]

# Use a helper to preselect country/state/city dropdown values for a clicked destination.
def set_destination_dropdowns(city_to_select):
    try:
        countries = get_countries()
        india_code = next((code for name, code in countries if name.casefold() == "india"), None)
        if not india_code:
            return
        st.session_state["destination_country"] = next(
            name for name, code in countries if code == india_code
        )
        for state_name, state_code in get_states(india_code):
            city_list = get_cities(india_code, state_code, state_name)
            matching_city = next(
                (city for city in city_list if city.casefold() == city_to_select.casefold()),
                None,
            )
            if matching_city:
                st.session_state[f"destination_state_{india_code}"] = state_name
                st.session_state[f"destination_city_{india_code}_{state_code}"] = matching_city
                return
    except Exception:
        # The preset remains available in the form if the location dataset is unavailable.
        return

preset_columns = st.columns(4)
for i, (label, style_value) in enumerate(CATEGORY_BUTTONS):
    with preset_columns[i % 4]:
        if st.button(label, key=f"preset_{i}", use_container_width=True):
            st.session_state["active_inspiration_category"] = style_value
            st.session_state["preset_style"] = style_value
            st.session_state["trip_start_from_inspiration"] = True
            st.session_state.pop("preset_destination", None)
            st.session_state["inspiration_places"] = CATEGORY_DESTINATIONS[style_value]
            st.session_state["scroll_to_journey"] = True
            st.rerun()

inspiration_heading, shuffle_column = st.columns([5, 1])
with inspiration_heading:
    active_category = st.session_state.get("active_inspiration_category")
    if active_category:
        st.markdown(f"### 🖼️ {active_category} destinations")
        st.caption(f"Showing destinations selected for {active_category.lower()}.")
    else:
        st.markdown("### 🖼️ Destination inspiration")
with shuffle_column:
    if st.button("🔄 More places", key="shuffle_inspiration"):
        if active_category:
            st.session_state["inspiration_places"] = random.sample(
                CATEGORY_DESTINATIONS[active_category],
                k=len(CATEGORY_DESTINATIONS[active_category]),
            )
        else:
            st.session_state.pop("inspiration_places", None)
        st.rerun()

if "inspiration_places" not in st.session_state:
    all_suggestions = [
        ("Jaipur", "Hawa Mahal Jaipur"),
        ("Manali", "Manali Himachal Pradesh"),
        ("Varanasi", "Varanasi ghats"),
        ("Goa", "Goa beach India"),
        ("Udaipur", "Udaipur City Palace India"),
        ("Rishikesh", "Rishikesh Ganges India"),
        ("Shimla", "Shimla Ridge India"),
        ("Mysuru", "Mysore Palace India"),
        ("Amritsar", "Golden Temple Amritsar"),
        ("Kochi", "Fort Kochi Kerala"),
        ("Pachmarhi", "Pachmarhi Madhya Pradesh"),
        ("Agra", "Taj Mahal Agra"),
    ]
    st.session_state["inspiration_places"] = random.sample(all_suggestions, 4)

image_columns = st.columns(4)
for i, (place_name, image_query) in enumerate(st.session_state["inspiration_places"]):
    with image_columns[i]:
        st.markdown(f"**{place_name}**")
        try:
            image_url = get_destination_image(image_query)
            if image_url:
                st.image(image_url, use_container_width=True)
            else:
                st.caption("Image unavailable")
        except Exception:
            st.caption("Image unavailable")

        if st.button(f"Plan a trip to {place_name}", key=f"choose_{i}", use_container_width=True):
            st.session_state["preset_destination"] = place_name
            st.session_state["trip_start_from_inspiration"] = True
            st.session_state["scroll_to_journey"] = True
            set_destination_dropdowns(place_name)
            st.rerun()


# ============================================================
# TRAVEL PLANNING FORM
# ============================================================

st.markdown('<div id="journey-details"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-title">'
    '📍 Journey Details'
    '</div>',
    unsafe_allow_html=True,
)

# IMPORTANT: Keep cascading location dropdowns OUTSIDE the form.
# Streamlit forms do not rerun when a user changes a dropdown; they only
# send updated values on submit. Outside the form, changing a state reruns
# the app immediately and refreshes the city options for that state.
origin_column, destination_column = st.columns(2)

with origin_column:
    origin = location_selector(
        "origin",
        "Starting Point — From",
    )

with destination_column:
    destination = location_selector(
        "destination",
        "Destination — To",
    )

st.divider()

with st.form("travel_planning_form"):
    st.markdown(
        '<div class="section-title">'
        '🧳 Trip Preferences'
        '</div>',
        unsafe_allow_html=True,
    )

    trip_dates_col1, trip_dates_col2 = st.columns(2)
    with trip_dates_col1:
        departure_date = st.date_input(
            "Departure / start date",
            key="departure_date",
        )
    with trip_dates_col2:
        return_date = st.date_input(
            "Return / end date",
            key="return_date",
        )

    duration = max(1, (return_date - departure_date).days + 1)
    st.caption(f"Trip duration: {duration} day(s), calculated from your dates.")

    col1, col2 = st.columns(2)

    with col1:
        budget = st.selectbox(
            "Total budget (INR)",
            options=[
                "Under ₹5,000",
                "₹5,000 – ₹10,000",
                "₹10,000 – ₹25,000",
                "₹25,000 – ₹50,000",
                "₹50,000 – ₹1,00,000",
                "₹1,00,000 – ₹2,00,000",
                "Above ₹2,00,000",
            ],
            index=2,
        )

    with col2:
        travel_style = st.selectbox(
            "Travel style",
            options=[
                "Budget-friendly",
                "Balanced",
                "Comfort / luxury",
                "Adventure",
                "Family trip",
                "Religious / pilgrimage",
                "Historical and cultural",
            ],
            index=(
                ["Budget-friendly", "Balanced", "Comfort / luxury", "Adventure", "Family trip", "Religious / pilgrimage", "Historical and cultural"].index(st.session_state["preset_style"])
                if st.session_state.get("preset_style") in ["Budget-friendly", "Balanced", "Comfort / luxury", "Adventure", "Family trip", "Religious / pilgrimage", "Historical and cultural"]
                else 1
            ),
        )

        travellers = st.number_input(
            "Number of travellers",
            min_value=1,
            max_value=50,
            value=1,
            step=1,
        )

    interests = st.multiselect(
        "What are you interested in?",
        options=[
            "Nature",
            "Mountains",
            "Beaches",
            "Food",
            "Shopping",
            "History",
            "Culture",
            "Adventure",
            "Temples / religious places",
            "Wildlife",
            "Photography",
            "Nightlife",
        ],
        default=["History", "Culture"],
    )

    additional_notes = st.text_area(
        "Additional requirements (optional)",
        placeholder=(
            "e.g. suggest trains instead of flights, "
            "include family-friendly hotels, or avoid long drives."
        ),
        height=100,
    )

    submitted = st.form_submit_button(
        "✨ Generate My Travel Plan",
        use_container_width=True,
    )


# ============================================================
# PROCESS REQUEST
# ============================================================

if submitted:
    if return_date < departure_date:
        st.error("Return date must be on or after the departure date.")
        st.stop()

    if not origin.get("city") and not origin.get("specific_location"):
        st.error("Please enter a starting city or specific location.")
        st.stop()

    elif (
        not destination.get("city")
        and not destination.get("specific_location")
    ):
        st.error("Please enter a destination city or specific location.")
        st.stop()

    else:
        with st.spinner("Checking that the entered locations exist..."):
            origin_valid = validate_location(origin)
            destination_valid = validate_location(destination)

        # Continue if the external validation service is unavailable.
        if origin_valid is None or destination_valid is None:
            st.warning(
                "Location validation is temporarily unavailable. "
                "Continuing with the locations selected in your form."
            )

            if origin_valid is None:
                origin_valid = True

            if destination_valid is None:
                destination_valid = True

        # Stop if the validation service explicitly rejects a location.
        if not origin_valid:
            st.error(
                "❌ Invalid starting location. Please check the city/place, "
                "state, and country, then try again."
            )
            st.stop()

        if not destination_valid:
            st.error(
                "❌ Invalid destination. Please check the city/place, "
                "state, and country, then try again."
            )
            st.stop()

        origin_text = format_location(origin)
        destination_text = format_location(destination)

        interests_text = (
            ", ".join(interests) if interests else "General sightseeing"
        )

        selected_travel_style = st.session_state.get("preset_style", "")
        selected_inspiration_destination = st.session_state.get("preset_destination", "")
        user_query = f"""

Plan a trip using these details.

Starting location: {origin_text}
Destination: {destination_text}
Departure date: {departure_date}
Return date: {return_date}
Duration: {duration} days
Number of travellers: {travellers}
Total budget: {budget}
Travel style: {st.session_state.get("preset_style") or travel_style}
Interests: {interests_text}
Additional requirements: {additional_notes or "None"}

Instructions:
1. Use the provided origin and destination exactly.
2. Do not replace the locations with unrelated cities.
3. Recommend suitable transport for these locations.
4. For temples, landmarks, or small towns, consider road,
   bus, or train travel where appropriate.
5. Create a day-by-day itinerary.
6. Suggest relevant accommodation using available search results.
7. Explain local transport options.
8. Estimate costs within the stated budget when possible.
9. Identify information that could not be verified.
10. Do not claim that tickets or hotels have been booked.
11. Do not invent live prices or availability.
12. Use the exact departure and return dates; make the itinerary fit those dates.
13. Suggest the best time of day and season for attractions. Clearly label general advice separately from verified opening hours.
15. Recommend only transport facilities that actually serve the selected origin/destination.
"""

        initial_state = {
            "messages": [HumanMessage(content=user_query)],
            "user_query": user_query,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0,
        }

        config = {
            "configurable": {
                "thread_id": st.session_state.thread_id,
            }
        }

        with st.spinner(
            "🤖 AI agents are researching your journey..."
        ):
            try:
                result = app.invoke(initial_state, config=config)
                st.session_state.last_result = result
                st.success("Your travel plan has been generated!")

            except Exception as error:
                st.error(
                    "Something went wrong while generating "
                    "your travel plan."
                )

                # Useful during local development. Avoid showing full
                # tracebacks to public users after deploying.
                with st.expander("View error details"):
                    st.code(str(error))
                    st.code(traceback.format_exc())


# ============================================================
# DISPLAY TRAVEL PLAN
# ============================================================

if "last_result" in st.session_state:
    result = st.session_state.last_result

    st.divider()
    st.markdown("## 🗺️ Your Travel Plan")
    final_response = extract_final_response(result)
    st.markdown(final_response)

    # Destination media is intentionally displayed after the complete itinerary.
    target_city = (
        (st.session_state.get("preset_destination") if st.session_state.get("trip_start_from_inspiration") else "")
        or destination.get("city")
        or destination.get("specific_location")
        or ""
    ).strip()
    if target_city:
        st.divider()
        st.markdown(f"## 📸 Explore {target_city}")
        st.caption("Photos and travel videos related to your destination.")

        with st.spinner(f"Finding photos of {target_city}..."):
            destination_photos = get_destination_images(
                target_city + " India travel destination",
                limit=8,
            )

        if destination_photos:
            photo_columns = st.columns(4)
            for index, photo_url in enumerate(destination_photos):
                with photo_columns[index % 4]:
                    st.image(
                        photo_url,
                        caption=f"{target_city} — photo {index + 1}",
                        use_container_width=True,
                    )
        else:
            st.info("Destination photos are temporarily unavailable.")

        st.markdown(f"### 🎬 Travel videos about {target_city}")
        with st.spinner("Finding destination videos..."):
            video_ids = get_destination_video_ids(target_city, limit=3)

        if video_ids:
            video_columns = st.columns(min(2, len(video_ids)))
            for index, video_id in enumerate(video_ids):
                with video_columns[index % len(video_columns)]:
                    st.components.v1.iframe(
                        f"https://www.youtube-nocookie.com/embed/{video_id}",
                        height=280,
                        scrolling=False,
                    )
        else:
            st.info(
                "Videos could not be embedded automatically right now. "
                "You can still browse destination videos on YouTube."
            )
            search_query = requests.utils.quote(f"{target_city} travel guide tourism")
            st.markdown(
                f"[Search YouTube for {target_city} travel videos]"
                f"(https://www.youtube.com/results?search_query={search_query})"
            )

    with st.expander("🔎 View research results"):
        flight_results = result.get("flight_results", "")
        hotel_results = result.get("hotel_results", "")
        itinerary = result.get("itinerary", "")

        st.markdown("### ✈️ Flight / Transport Results")
        st.write(
            flight_results
            if flight_results
            else "No flight or transport results were returned."
        )

        st.markdown("### 🏨 Hotel Search Results")
        st.write(
            hotel_results
            if hotel_results
            else "No hotel search results were returned."
        )

        st.markdown("### 📅 Itinerary Agent Output")
        st.write(
            itinerary
            if itinerary
            else "No separate itinerary output was returned."
        )

    st.caption(
        "Verify transport schedules, hotel details, prices, "
        "and availability with the relevant provider before travelling."
    )


# Scroll the page to Journey Details after a user clicks a category or destination card.
if st.session_state.pop("scroll_to_journey", False):
    st.components.v1.html(
        """
        <script>
        const scrollToJourney = () => {
          try {
            const doc = window.parent.document;
            const target = doc.getElementById("journey-details");
            if (target) target.scrollIntoView({behavior: "smooth", block: "start"});
          } catch (e) {}
        };
        setTimeout(scrollToJourney, 250);
        </script>
        """,
        height=0,
    )
