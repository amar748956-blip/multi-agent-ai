import streamlit as st
import uuid
import traceback
import re
import unicodedata

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
    .stApp {
        background: linear-gradient(
            135deg,
            #0f172a 0%,
            #172554 50%,
            #1e3a5f 100%
        );
        color: #f1f5f9;
    }

    [data-testid="stMain"] {
        background: transparent;
    }

    h1, h2, h3, h4 {
        color: #bfdbfe;
    }

    .main-title {
        font-size: 42px;
        font-weight: 800;
        color: #93c5fd;
        text-align: center;
        margin-bottom: 5px;
    }

    .subtitle {
        text-align: center;
        font-size: 17px;
        color: #cbd5e1;
        margin-bottom: 30px;
    }

    .section-title {
        font-size: 22px;
        font-weight: 700;
        color: #bfdbfe;
        margin-top: 12px;
        margin-bottom: 12px;
    }

    .login-title {
        text-align: center;
        font-size: 36px;
        font-weight: bold;
        color: #93c5fd;
    }

    .login-subtitle {
        text-align: center;
        color: #cbd5e1;
        margin-bottom: 25px;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(
            180deg,
            #111827 0%,
            #1e293b 100%
        );
    }

    [data-testid="stSidebar"] * {
        color: #e2e8f0;
    }

    .stMarkdown,
    .stMarkdown p,
    label,
    [data-testid="stCaptionContainer"] {
        color: #e2e8f0;
    }

    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div {
        background-color: #f1f5f9;
        border-radius: 8px;
        border: 1px solid #64748b;
    }

    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea {
        color: #111827 !important;
        background-color: transparent;
    }

    div[data-baseweb="select"] > div {
        background: linear-gradient(
            135deg,
            #0f172a 0%,
            #172554 50%,
            #1e3a5f 100%
        ) !important;
        background-color: #172554 !important;
        color: #f1f5f9 !important;
        border: 1px solid #60a5fa !important;
        border-radius: 8px !important;
    }

    div[data-baseweb="select"] input,
    div[data-baseweb="select"] span {
        color: #f1f5f9 !important;
    }

    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    ul[data-baseweb="menu"] {
        background: linear-gradient(
            135deg,
            #0f172a 0%,
            #172554 50%,
            #1e3a5f 100%
        ) !important;
        background-color: #172554 !important;
    }

    li[role="option"],
    div[role="option"] {
        background-color: transparent !important;
        color: #f1f5f9 !important;
    }

    li[role="option"]:hover,
    div[role="option"]:hover,
    li[aria-selected="true"],
    div[aria-selected="true"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
    }

    div[data-baseweb="select"] svg {
        fill: #f1f5f9 !important;
        color: #f1f5f9 !important;
    }

    [data-baseweb="tag"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
    }

    [data-baseweb="tag"] svg {
        fill: #ffffff !important;
    }

    div.stButton > button,
    div.stFormSubmitButton > button {
        background: linear-gradient(90deg, #2563eb, #0891b2);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 700;
        width: 100%;
        transition: all 0.2s ease-in-out;
    }

    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover {
        background: #1d4ed8;
        color: white;
        border: 1px solid #93c5fd;
        transform: translateY(-1px);
    }

    [data-testid="stForm"] {
        background: rgba(30, 41, 59, 0.65);
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 20px;
    }

    [data-testid="stExpander"] {
        background: rgba(30, 41, 59, 0.75);
        border: 1px solid #475569;
        border-radius: 12px;
    }

    [data-testid="stAlert"] {
        border-radius: 10px;
    }

    hr {
        border-color: #475569;
    }

    a {
        color: #7dd3fc !important;
    }

    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #0f172a;
    }

    ::-webkit-scrollbar-thumb {
        background: #475569;
        border-radius: 8px;
    }
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
    """Return the first available non-empty attribute."""
    for attribute in attribute_names:
        value = getattr(item, attribute, None)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


@st.cache_data(show_spinner=False)
def get_countries():
    """Return country names and identifiers."""
    try:
        countries = Country.get_countries()
        results = []

        for item in countries:
            name = get_attribute(item, "name", "country_name")
            code = get_attribute(item, "iso2", "iso2_code", "code")

            if name:
                results.append((name, code or name))

        return sorted(results, key=lambda item: item[0].lower())
    except Exception:
        return []


@st.cache_data(show_spinner=False)
def get_states(country_code):
    """Return state names and usable identifiers."""
    try:
        states = State.get_states_of_country(country_code)
        results = []

        for item in states:
            name = get_attribute(item, "name", "state_name")
            code = get_attribute(
                item,
                "state_code",
                "iso2",
                "iso3166_2",
                "code",
            )

            if name:
                results.append((name, code or name))

        unique_results = {name: code for name, code in results}

        return sorted(
            list(unique_results.items()),
            key=lambda item: item[0].lower(),
        )
    except Exception:
        return []


@st.cache_data(show_spinner=False)
def get_cities(country_code, state_identifier, state_name):
    """Fetch cities using a state code or state name."""
    identifiers = []

    if state_identifier:
        identifiers.append(state_identifier)
    if state_name and state_name not in identifiers:
        identifiers.append(state_name)

    for identifier in identifiers:
        try:
            cities = City.get_cities_of_state(country_code, identifier)
            city_names = set()

            for item in cities:
                name = get_attribute(item, "name", "city_name")
                if name:
                    city_names.add(name)

            if city_names:
                return sorted(city_names, key=str.lower)
        except Exception:
            continue

    return []


# ============================================================
# LOCATION SELECTOR
# ============================================================

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
            default_state = (
                "Madhya Pradesh"
                if "Madhya Pradesh" in state_labels
                else state_labels[0]
            )

            state_name = st.selectbox(
                "State / region",
                options=state_labels,
                index=state_labels.index(default_state),
                key=f"{prefix}_state",
            )
            state_identifier = state_codes[state_name]
            cities = get_cities(
                country_code,
                state_identifier,
                state_name,
            )

            if cities:
                city_options = ["Select a city"] + cities
                city_name = st.selectbox(
                    "City",
                    options=city_options,
                    key=f"{prefix}_city",
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
                    key=f"{prefix}_city_manual",
                )
        else:
            st.info(
                "State data is unavailable. "
                "Enter the state and city manually."
            )
            state_name = st.text_input(
                "State / region",
                key=f"{prefix}_state_manual",
            )
            city_name = st.text_input(
                "City",
                key=f"{prefix}_city_manual",
            )

    location_type = st.selectbox(
        "Location type",
        options=[
            "City centre",
            "Airport",
            "Railway station",
            "Bus station",
            "Hotel / accommodation area",
            "Tourist attraction / landmark",
            "Temple / religious place",
            "Other location",
        ],
        key=f"{prefix}_location_type",
    )

    specific_location = st.text_input(
        "Specific place name (optional)",
        placeholder=(
            "e.g. Dewas Railway Station or "
            "Sanwariya Seth Temple"
        ),
        key=f"{prefix}_specific_location",
    )

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

def extract_final_response(result):
    """Find the latest non-empty AI response."""
    messages = result.get("messages", [])

    for message in reversed(messages):
        if isinstance(message, AIMessage):
            content = message.content

            if isinstance(content, str) and content.strip():
                return content
            if content:
                return str(content)

    itinerary = result.get("itinerary", "")
    if itinerary:
        return itinerary

    return (
        "The travel planner finished, but no final response "
        "was returned."
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🌍 AI Travel Planner")
    st.caption("Your AI-powered trip planning assistant")
    st.divider()

    st.markdown("### 🧩 Technology Stack")
    st.markdown(
        """
        - **LangGraph** — agent workflow
        - **Groq / LLM** — AI responses
        - **PostgreSQL** — conversation checkpoints
        - **Tavily** — web search
        - **AviationStack** — flight data
        - **Streamlit** — user interface
        """
    )

    st.divider()
    st.markdown("### ⚙️ Agent Pipeline")
    st.markdown(
        """
        1. ✈️ Flight Agent
        2. 🏨 Hotel Agent
        3. 🗺️ Itinerary Agent
        4. 📝 Final Agent
        """
    )

    st.divider()

    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())

    st.caption("Conversation ID")
    st.code(st.session_state.thread_id[:18] + "...")

    if st.button("🔄 Start New Conversation"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.pop("last_result", None)
        st.rerun()


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

st.info(
    "Enter your trip details below. The AI agents will "
    "gather available information and create a suggested plan."
)


# ============================================================
# TRAVEL PLANNING FORM
# ============================================================

with st.form("travel_planning_form"):
    st.markdown(
        '<div class="section-title">'
        '📍 Journey Details'
        '</div>',
        unsafe_allow_html=True,
    )

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
    st.markdown(
        '<div class="section-title">'
        '🧳 Trip Preferences'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        duration = st.number_input(
            "Trip duration (days)",
            min_value=1,
            max_value=60,
            value=3,
            step=1,
        )

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
    if not origin.get("city") and not origin.get("specific_location"):
        st.error("Please enter a starting city or specific location.")

    elif (
        not destination.get("city")
        and not destination.get("specific_location")
    ):
        st.error("Please enter a destination city or specific location.")

    else:
        with st.spinner("Checking that the entered locations exist..."):
            origin_valid = validate_location(origin)
            destination_valid = validate_location(destination)

        if origin_valid is None or destination_valid is None:
            st.error(
                "Location validation is temporarily unavailable. "
                "Please check your internet connection and try again. "
                "Your trip has not been generated."
            )
            st.stop()

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

        user_query = f"""
Plan a trip using these details.

Starting location: {origin_text}
Destination: {destination_text}
Duration: {duration} days
Number of travellers: {travellers}
Total budget: {budget}
Travel style: {travel_style}
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
