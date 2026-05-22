import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from groq import Groq
from groq_analyzer import analyze_chat_with_groq

# --- The Streamlit App UI ---
def main():
    st.set_page_config(page_title="AI Agent Threat Detector", layout="wide", initial_sidebar_state="expanded")

    # Load environment variables from .env file
    load_dotenv()
    groq_api_key = os.getenv("GROQ_API_KEY")

    # Load the dataset for few-shot examples
    try:
        dataset = pd.read_csv('malicious_text_dataset.csv')
    except FileNotFoundError:
        st.error("Dataset file 'malicious_text_dataset.csv' not found. Please make sure it's in the same directory.")
        st.stop()

    st.sidebar.title("Configuration")
    st.sidebar.info(
        "This app uses the Groq API to analyze chat conversations for malicious intent. "
        "It will use the API key from your `.env` file."
    )
    if not groq_api_key or groq_api_key == "YOUR_GROQ_API_KEY_HERE":
        st.sidebar.warning("API key not found. Please create a `.env` file and add your `GROQ_API_KEY`.")
    else:
        st.sidebar.success("Groq API key loaded successfully!")

    st.title("🤖 AI Agent Threat Detector")
    st.markdown(
        "Paste the full conversation with an AI bot below. This tool will analyze it for signs of manipulation, "
        "phishing, scams, and other malicious behaviors using the provided dataset."
    )

    chat_input = st.text_area("Enter Chat Conversation Here:", height=250, placeholder="User: My computer is slow.\nBot: I've detected a virus. Download this file to fix it...")

    if st.button("Analyze Chat", use_container_width=True):
        if not groq_api_key or groq_api_key == "YOUR_GROQ_API_KEY_HERE":
            st.error("Please set your Groq API key in the `.env` file before analyzing.")
            st.stop()

        if not chat_input.strip():
            st.warning("Please enter a chat conversation to analyze.")
            st.stop()

        try:
            client = Groq(api_key=groq_api_key)
        except Exception as e:
            st.error(f"Failed to initialize Groq client: {e}")
            st.stop()

        with st.spinner("Analyzing... The AI analyst is on the case!"):
            analysis_result = analyze_chat_with_groq(client, chat_input, dataset)

        if analysis_result:
            st.success("Analysis Complete!")

            score = analysis_result.get("threat_score", 0)
            intent = analysis_result.get("intent_classification", "N/A")
            summary = analysis_result.get("summary", "No summary provided.")

            if score >= 7: color, icon = "red", "🚨"
            elif score >= 4: color, icon = "orange", "⚠️"
            else: color, icon = "green", "✅"

            st.header(f"{icon} Threat Assessment")
            st.markdown(f"### <span style='color:{color};'>{intent}</span>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            col1.metric(label="Threat Score (0-10)", value=score)
            col2.info(f"**Recommendation:** {summary}")

            st.subheader("Detailed Breakdown")
            col1_details, col2_details = st.columns(2)
            with col1_details:
                st.markdown("**Detected Social Engineering Tactics:**")
                tactics = analysis_result.get("social_tactics_detected", [])
                if tactics:
                    for tactic in tactics: st.markdown(f"- `{tactic}`")
                else: st.markdown("None detected.")

            with col2_details:
                st.markdown("**Detected Indicators of Compromise (IOCs):**")
                iocs = analysis_result.get("ioc_detected", [])
                if iocs:
                    for ioc in iocs: st.markdown(f"- `{ioc}`")
                else: st.markdown("None detected.")
        else:
            st.error("Failed to get analysis from the API. Please check for errors and try again.")

if __name__ == "__main__":
    main()
