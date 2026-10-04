import os
from datetime import datetime

import streamlit as st
from langchain_core.messages import HumanMessage

from main import app


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Travel Booking System",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# SIDEBAR ALWAYS VISIBLE
# ===========================================================

st.markdown("""
<style>

/* Keep sidebar permanently visible */
section[data-testid="stSidebar"] {
    display: block !important;
    visibility: visible !important;
    transform: none !important;
    width: 280px !important;
    min-width: 280px !important;
}

/* Keep sidebar content visible */
section[data-testid="stSidebar"] > div {
    visibility: visible !important;
}

/* Hide the collapse button */
button[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

html, body, .stApp {
    font-family: Arial, sans-serif;
    background: #080d14;
    color: #e8f4ff;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}


/* ============================================================
   SIDEBAR
   ============================================================ */

section[data-testid="stSidebar"] {
    background: #080e18 !important;
    border-right: 1px solid #1c2b3d;
}

.sidebar-title {
    color: #e8f4ff;
    font-size: 16px;
    font-weight: 600;
    margin-top: 15px;
    margin-bottom: 12px;
}

.sidebar-chip {
    background: #0e1a2b;
    border: 1px solid #1c324b;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 7px;
    color: #77b9f5;
    font-size: 14px;
}


/* ============================================================
   HERO
   ============================================================ */

.hero-box {
    background:
        linear-gradient(
            rgba(5, 10, 18, 0.60),
            rgba(5, 10, 18, 0.78)
        ),
        url("https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1400&q=85");

    background-size: cover;
    background-position: center;

    height: 300px;

    border-radius: 22px;

    display: flex;
    flex-direction: column;

    align-items: center;
    justify-content: center;

    text-align: center;

    margin-bottom: 30px;

    border: 1px solid #18283a;

    box-shadow:
        0 10px 40px rgba(0,0,0,0.35);
}

.hero-badge {
    background: rgba(37, 103, 170, 0.35);

    border: 1px solid rgba(95, 160, 225, 0.55);

    color: #82c4ff;

    padding: 7px 18px;

    border-radius: 25px;

    font-size: 12px;

    font-weight: 600;

    letter-spacing: 2px;

    margin-bottom: 18px;
}

.hero-title {
    color: white;

    font-size: 42px;

    font-weight: 700;

    margin-bottom: 12px;
}

.hero-sub {
    color: #d3e5f5;

    font-size: 16px;

    max-width: 700px;

    line-height: 1.6;
}


/* ============================================================
   DESTINATION IMAGES
   ============================================================ */

.destination-image {
    border-radius: 14px;

    border: 1px solid #20354c;

    overflow: hidden;
}


/* ============================================================
   SECTION
   ============================================================ */

.section-title {
    color: #70baff;

    font-size: 14px;

    font-weight: 700;

    letter-spacing: 2px;

    margin-top: 18px;

    margin-bottom: 12px;
}


/* ============================================================
   TEXT INPUT
   ============================================================ */

.stTextArea textarea {

    background: #091521 !important;

    color: #e8f4ff !important;

    border: 1px solid #263b52 !important;

    border-radius: 12px !important;

    font-size: 15px !important;
}

.stTextArea textarea::placeholder {
    color: #4d7090 !important;
}


/* ============================================================
   BUTTONS
   ============================================================ */

.stButton > button {

    background: linear-gradient(
        135deg,
        #1d75c9,
        #0c4d8b
    ) !important;

    color: white !important;

    border: none !important;

    border-radius: 12px !important;

    min-height: 50px;

    font-weight: 600 !important;

    transition: 0.2s;
}

.stButton > button:hover {

    transform: translateY(-2px);

    box-shadow:
        0 8px 25px rgba(29,117,201,0.35);
}


/* ============================================================
   FINAL RESPONSE
   ============================================================ */

.final-box {

    background: #0b1725;

    border: 1px solid #214263;

    border-left: 4px solid #3195e8;

    border-radius: 12px;

    padding: 20px;

    margin-top: 20px;

}


/* ============================================================
   METRICS
   ============================================================ */

.metric-box {

    background: #0d1927;

    border: 1px solid #20364e;

    border-radius: 12px;

    padding: 15px;

    text-align: center;
}

.metric-number {

    color: #4da9ef;

    font-size: 28px;

    font-weight: 700;
}

.metric-label {

    color: #7ea6c6;

    font-size: 12px;

    text-transform: uppercase;
}


/* ============================================================
   INFO BOX
   ============================================================ */

.info-box {

    background: #0d1825;

    border: 1px solid #20354b;

    border-radius: 10px;

    padding: 12px;

    color: #8db4d3;

}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        '<div class="sidebar-title">🌍 AI Travel Planner</div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    thread_id = st.text_input(
        "👤 User ID",
        value="aarohi_user",
    )

    st.markdown(
        '<div class="sidebar-title">Powered by</div>',
        unsafe_allow_html=True,
    )

    technologies = [
        "🔗 LangGraph",
        "🧠 Groq · LLM",
        "🐘 PostgreSQL",
        "🔍 Tavily Search",
        "✈️ AviationStack",
    ]

    for item in technologies:

        st.markdown(
            f'<div class="sidebar-chip">{item}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="sidebar-title">Agent Pipeline</div>',
        unsafe_allow_html=True,
    )

    agents = [
        "① Flight Agent",
        "② Hotel Agent",
        "③ Itinerary Agent",
        "④ Final Agent",
    ]

    for item in agents:

        st.markdown(
            f'<div class="sidebar-chip">{item}</div>',
            unsafe_allow_html=True,
        )


# ============================================================
# HERO
# ============================================================

st.markdown(
    """
<div class="hero-box">

<div class="hero-badge">
✦ MULTI-AGENT AI SYSTEM
</div>

<div class="hero-title">
✈️ AI Travel Booking System
</div>

<div class="hero-sub">
Four specialized agents work together — searching flights,
hotels, building an itinerary, and delivering your perfect trip plan.
</div>

</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# DESTINATIONS
# ============================================================

destinations = [
    (
        "🇯🇵 Tokyo",
        "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800&q=85",
    ),

    (
        "🇫🇷 Paris",
        "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800&q=85",
    ),

    (
        "🇹🇭 Bangkok",
        "https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=800&q=85",
    ),

    (
        "🇮🇹 Rome",
        "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800&q=85",
    ),

    (
        "🇦🇪 Dubai",
        "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=800&q=85",
    ),
]


columns = st.columns(5)


for column, (name, image_url) in zip(
    columns,
    destinations,
):

    with column:

        st.image(
            image_url,
            use_container_width=True,
        )

        st.markdown(
            f"""
            <div style="
                text-align:center;
                color:#d9e9f7;
                font-weight:600;
                margin-top:-8px;
                margin-bottom:12px;
            ">
                {name}
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# DESCRIBE YOUR TRIP
# ============================================================

st.markdown(
    """
    <div class="section-title">
        🗺️ DESCRIBE YOUR TRIP
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# QUICK BUTTONS
# ============================================================

quick_columns = st.columns(4)

quick_trips = [
    "7-day Japan under ₹2L",
    "Paris trip for 5 days",
    "Dubai weekend trip",
    "Bali backpacking 10 days",
]


quick_value = ""


for column, trip in zip(
    quick_columns,
    quick_trips,
):

    with column:

        if st.button(
            trip,
            key=f"quick_{trip}",
            use_container_width=True,
        ):

            quick_value = trip


# ============================================================
# INPUT
# ============================================================

user_query = st.text_area(
    "Travel Request",

    value=quick_value,

    placeholder=(
        "e.g. Plan a complete 7-day Japan trip including "
        "flights, hotels and sightseeing under ₹2 lakhs"
    ),

    height=110,

    label_visibility="collapsed",
)


# ============================================================
# GENERATE
# ============================================================

generate = st.button(
    "🚀 Generate My Travel Plan",
    use_container_width=True,
)


# ============================================================
# GENERATE TRAVEL PLAN
# ============================================================

if generate:

    if not user_query.strip():

        st.warning(
            "⚠️ Please enter a travel request."
        )

        st.stop()


    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }


    collected = {

        "flight_results": "",

        "hotel_results": "",

        "itinerary": "",

        "final_response": "",

        "llm_calls": 0,
    }


    # ========================================================
    # PIPELINE
    # ========================================================

    st.markdown(
        """
        <div class="section-title">
            🤖 AGENT PIPELINE
        </div>
        """,
        unsafe_allow_html=True,
    )


    try:

        for chunk in app.stream(

            {
                "messages": [
                    HumanMessage(
                        content=user_query
                    )
                ],

                "user_query": user_query,

                "flight_results": "",

                "hotel_results": "",

                "itinerary": "",

                "llm_calls": 0,
            },

            config=config,

            stream_mode="updates",
        ):

            for node_name, state_update in chunk.items():


                # ====================================================
                # FLIGHT
                # ====================================================

                if node_name == "flight_agent":

                    collected[
                        "flight_results"
                    ] = state_update.get(
                        "flight_results",
                        "",
                    )

                    with st.expander(
                        "✈️ Flight Agent — Completed",
                        expanded=False,
                    ):

                        st.write(
                            collected[
                                "flight_results"
                            ]
                        )


                # ====================================================
                # HOTEL
                # ====================================================

                elif node_name == "hotel_agent":

                    collected[
                        "hotel_results"
                    ] = state_update.get(
                        "hotel_results",
                        "",
                    )

                    with st.expander(
                        "🏨 Hotel Agent — Completed",
                        expanded=False,
                    ):

                        st.write(
                            collected[
                                "hotel_results"
                            ]
                        )


                # ====================================================
                # ITINERARY
                # ====================================================

                elif node_name == "itinerary_agent":

                    collected[
                        "itinerary"
                    ] = state_update.get(
                        "itinerary",
                        "",
                    )

                    with st.expander(
                        "🗓️ Itinerary Agent — Completed",
                        expanded=False,
                    ):

                        st.markdown(
                            collected[
                                "itinerary"
                            ]
                        )


                # ====================================================
                # FINAL
                # ====================================================

                elif node_name == "final_agent":

                    messages = state_update.get(
                        "messages",
                        [],
                    )

                    if messages:

                        last_message = messages[-1]

                        if hasattr(
                            last_message,
                            "content",
                        ):

                            collected[
                                "final_response"
                            ] = last_message.content


                # ====================================================
                # LLM CALL COUNT
                # ====================================================

                collected[
                    "llm_calls"
                ] = state_update.get(
                    "llm_calls",
                    collected["llm_calls"],
                )


    except Exception as e:

        st.error(
            "❌ Error while running the travel system."
        )

        st.exception(e)

        st.stop()


    # ========================================================
    # METRICS
    # ========================================================

    st.markdown(
        """
        <div class="section-title">
            📊 TRAVEL PLAN STATUS
        </div>
        """,
        unsafe_allow_html=True,
    )


    m1, m2, m3 = st.columns(3)


    with m1:

        st.markdown(
            f"""
            <div class="metric-box">

            <div class="metric-number">
            4
            </div>

            <div class="metric-label">
            Agents
            </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    with m2:

        st.markdown(
            f"""
            <div class="metric-box">

            <div class="metric-number">
            {collected["llm_calls"]}
            </div>

            <div class="metric-label">
            LLM Calls
            </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    with m3:

        st.markdown(
            """
            <div class="metric-box">

            <div class="metric-number">
            ✅
            </div>

            <div class="metric-label">
            Completed
            </div>

            </div>
            """,
            unsafe_allow_html=True,
        )


    # ========================================================
    # FINAL RESULT
    # ========================================================

    if collected["final_response"]:

        st.markdown(
            """
            <div class="section-title">
                🧠 FINAL TRAVEL PLAN
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="final-box">',
            unsafe_allow_html=True,
        )

        st.markdown(
            collected["final_response"]
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


    # ========================================================
    # SAVE FILE
    # ========================================================

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = (
        f"travel_plan_{timestamp}.md"
    )


    file_content = f"""
# AI Travel Booking System

## User Request

{user_query}

## User ID

{thread_id}

## Generated

{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

# Flight Results

{collected["flight_results"]}

---

# Hotel Results

{collected["hotel_results"]}

---

# Itinerary

{collected["itinerary"]}

---

# Final Travel Plan

{collected["final_response"]}

---

LLM Calls: {collected["llm_calls"]}
"""


    # ========================================================
    # DOWNLOAD
    # ========================================================

    st.download_button(
        "⬇️ Download Travel Plan",

        data=file_content,

        file_name=filename,

        mime="text/markdown",

        use_container_width=True,
    )