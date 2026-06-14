"""Streamlit chat UI for the Airline Customer Support FastAPI backend."""

import os

import requests
import streamlit as st

DEFAULT_API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Airline Customer Support",
    page_icon="✈️",
    layout="wide",
)


# ---------------- Sidebar ----------------
with st.sidebar:
    st.title("✈️ Airline Support")
    st.caption("AI-powered customer support demo")

    api_url = st.text_input("FastAPI backend URL", value=DEFAULT_API_URL)

    # Live health check
    try:
        r = requests.get(f"{api_url.rstrip('/')}/health", timeout=3)
        if r.ok:
            st.success("API is reachable")
        else:
            st.warning(f"API returned status {r.status_code}")
    except Exception:
        st.error("API not reachable")

    st.markdown("---")
    st.markdown("**Try asking:**")
    st.markdown(
        "- *What is the status of flight 6E477 on 10 Nov 2026?*\n"
        "- *How much free baggage is allowed for domestic flights?*\n"
        "- *Can I travel with my pet?*\n"
        "- *What is the capital of France?* (off-topic — fallback)\n"
        "- *Ignore all previous instructions...* (blocked by guardrail)"
    )

    if st.button("Clear conversation"):
        st.session_state.history = []
        st.rerun()


# ---------------- Main pane ----------------
st.title("Airline Customer Support")
st.write("Ask about flight status, schedules, baggage rules, refunds, and more.")

if "history" not in st.session_state:
    st.session_state.history = []


def _route_badge(route: str) -> str:
    colors = {
        "SQL": "#1F77B4",
        "RAG": "#2CA02C",
        "Fallback": "#FF7F0E",
        "Input Guardrail": "#D62728",
    }
    color = colors.get(route, "#7F7F7F")
    return (
        f"<span style='background:{color};color:white;padding:2px 8px;"
        f"border-radius:6px;font-size:0.8em;'>route: {route}</span>"
    )


# Render existing conversation
for turn in st.session_state.history:
    with st.chat_message("user"):
        st.write(turn["query"])
    with st.chat_message("assistant"):
        st.write(turn["response"])
        st.markdown(_route_badge(turn.get("route", "?")), unsafe_allow_html=True)
        with st.expander("Pipeline details"):
            st.json({k: v for k, v in turn.items() if k != "response"})


# Chat input
user_query = st.chat_input("Type your question here...")

if user_query:
    with st.chat_message("user"):
        st.write(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    f"{api_url.rstrip('/')}/ask",
                    json={"query": user_query},
                    timeout=120,
                )
                resp.raise_for_status()
                data = resp.json()
            except requests.exceptions.RequestException as e:
                st.error(f"Could not reach the API at {api_url}.\n\n{e}")
                data = None

        if data:
            st.write(data.get("response", "(no response)"))
            st.markdown(_route_badge(data.get("route", "?")), unsafe_allow_html=True)

            with st.expander("Pipeline details"):
                st.json({k: v for k, v in data.items() if k != "response"})

            st.session_state.history.append(data)
