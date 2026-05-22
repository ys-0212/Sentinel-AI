# ==============================================================================
# LOCAL MODE – User Behavior Anomaly Detection (SQLite)
# Mirrors original app.py (no external APIs)
# ==============================================================================

import streamlit as st
import sqlite3
import time
import random
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
import plotly.express as px

DB_PATH = "local.db"

# ------------------------------------------------------------------------------
# DATABASE UTILITIES
# ------------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_behavior_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            login_time TEXT,
            typing_speed INTEGER,
            mouse_movements INTEGER,
            location TEXT,
            ip_address TEXT,
            vpn_detected INTEGER,
            device_fingerprint TEXT,
            form_completion_time INTEGER,
            typing_dna_confidence INTEGER,
            risk_score REAL
        )
    """)

    cur.execute("SELECT 1 FROM users WHERE username='test'")
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users VALUES (?, ?, ?)",
            ("local-user-001", "test", "test123")
        )

    conn.commit()
    conn.close()

# ------------------------------------------------------------------------------
# DATABASE ACCESS LAYER
# ------------------------------------------------------------------------------
class LocalDB:
    def __init__(self):
        self.conn = get_db()

    def authenticate_user(self, username, password):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT user_id, password FROM users WHERE username=?",
            (username,)
        )
        row = cur.fetchone()
        if not row:
            return None
        return row["user_id"] if row["password"] == password else None

    def get_user_history(self, user_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM user_behavior_history
            WHERE user_id=?
            ORDER BY login_time DESC
            LIMIT 20
        """, (user_id,))
        return [dict(r) for r in cur.fetchall()]

    def save_session(self, d):
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO user_behavior_history (
                user_id, login_time, typing_speed, mouse_movements,
                location, ip_address, vpn_detected, device_fingerprint,
                form_completion_time, typing_dna_confidence, risk_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            d["user_id"], d["login_time"], d["typing_speed"],
            d["mouse_movements"], d["location"], d["ip_address"],
            int(d["vpn_detected"]), d["device_fingerprint"],
            d["form_completion_time"], d["typing_dna_confidence"],
            d["risk_score"]
        ))
        self.conn.commit()

# ------------------------------------------------------------------------------
# BEHAVIOR ANALYZER (MATCHES app.py LOGIC)
# ------------------------------------------------------------------------------
class BehaviorAnalyzer:
    def __init__(self):
        self.threshold = 0.7

    def extract_features(self, s):
        return np.array([
            s["typing_speed"],
            s["mouse_movements"],
            int(s["vpn_detected"]),
            s["form_completion_time"],
            hash(s["location"]) % 1000,
            hash(s["device_fingerprint"]) % 1000,
            (100 - s["typing_dna_confidence"]) / 100.0
        ]).reshape(1, -1)

    def analyze(self, current, history):
        reasons = []

        if not history:
            return False, 0.5, ["New user – baseline established"]

        hist_matrix = np.vstack([
            self.extract_features(h) for h in history
        ])

        similarity = cosine_similarity(
            self.extract_features(current),
            hist_matrix
        )
        risk = 1 - np.mean(similarity)

        # Explainable rules (same philosophy as app.py)
        if current["typing_dna_confidence"] < 70:
            reasons.append(
                f"Low typing confidence: {current['typing_dna_confidence']}%"
            )

        if risk > self.threshold and not reasons:
            reasons.append("Behavior deviates from historical pattern")

        return risk > self.threshold, risk, reasons

# ------------------------------------------------------------------------------
# STREAMLIT APP
# ------------------------------------------------------------------------------
def main():
    st.set_page_config("Local Anomaly Detection", layout="wide")
    st.title("🔒 Local User Behavior Anomaly Detection")

    if "initialized" not in st.session_state:
        init_db()
        st.session_state.db = LocalDB()
        st.session_state.analyzer = BehaviorAnalyzer()
        st.session_state.authenticated = False
        st.session_state.initialized = True

    if not st.session_state.authenticated:
        login_page()
    else:
        dashboard_page()

# ------------------------------------------------------------------------------
def login_page():
    st.subheader("🔐 User Authentication (Local)")

    sentence = random.choice([
        "The quick brown fox jumps over the lazy dog.",
        "Pack my box with five dozen liquor jugs."
    ])

    if "start_time" not in st.session_state:
        st.session_state.start_time = time.time()

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        st.markdown("**Type the following sentence:**")
        st.info(sentence)
        st.text_input("Typing input (for timing only)")

        submit = st.form_submit_button("Login & Analyze")

    if not submit:
        return

    user_id = st.session_state.db.authenticate_user(username, password)
    if not user_id:
        st.error("Invalid username or password")
        return

    duration = max(1, time.time() - st.session_state.start_time)
    typing_speed = int(len(sentence.split()) / duration * 60)

    session = {
        "user_id": user_id,
        "login_time": datetime.now().isoformat(),
        "typing_speed": typing_speed,
        "mouse_movements": random.randint(150, 400),
        "location": "Localhost, Offline",
        "ip_address": "127.0.0.1",
        "vpn_detected": False,
        "device_fingerprint": "local-browser",
        "form_completion_time": int(duration),
        "typing_dna_confidence": random.randint(80, 98),
        "risk_score": 0.0
    }

    history = st.session_state.db.get_user_history(user_id)
    _, risk, reasons = st.session_state.analyzer.analyze(session, history)
    session["risk_score"] = risk

    st.session_state.db.save_session(session)
    st.session_state.last_analysis = {
        "risk": risk,
        "reasons": reasons,
        "session": session
    }

    st.session_state.authenticated = True
    st.session_state.username = username
    st.success("Login successful")
    st.rerun()

# ------------------------------------------------------------------------------
def dashboard_page():
    st.sidebar.success(f"Logged in as {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    analysis = st.session_state.last_analysis
    s = analysis["session"]

    st.subheader("📈 Login Security Assessment")

    col1, col2, col3 = st.columns(3)
    col1.metric("Risk Score", f"{analysis['risk']:.3f}")
    col2.metric("Typing Confidence", f"{s['typing_dna_confidence']}%")
    col3.metric("Typing Speed", f"{s['typing_speed']} WPM")

    if analysis["risk"] >= 0.7:
        st.error("🔴 High Risk")
    elif analysis["risk"] >= 0.4:
        st.warning("🟠 Medium Risk")
    else:
        st.success("🟢 Low Risk")

    st.subheader("🚩 Analysis Flags")
    if analysis["reasons"]:
        for r in analysis["reasons"]:
            st.info(r)
    else:
        st.info("No specific anomalies detected")

    st.subheader("🔬 Session Details (Matches app.py)")
    st.json({
        "typing_dna_confidence": s["typing_dna_confidence"],
        "typing_speed": s["typing_speed"],
        "mouse_movements": s["mouse_movements"],
        "form_completion_time": s["form_completion_time"],
        "device_fingerprint": s["device_fingerprint"],
        "location": s["location"]
    })

    st.subheader("📊 Historical Risk Trend")
    history = st.session_state.db.get_user_history(s["user_id"])
    if history:
        df = pd.DataFrame(history)
        df["login_time"] = pd.to_datetime(df["login_time"])
        fig = px.line(
            df.sort_values("login_time"),
            x="login_time",
            y="risk_score",
            title="Risk Score Over Time"
        )
        st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------------------
if __name__ == "__main__":
    main()
