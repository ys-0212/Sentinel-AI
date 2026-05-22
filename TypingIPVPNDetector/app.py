# ==============================================================================
# Main Streamlit Application for Local Development (app.py)
# ==============================================================================
import streamlit as st
import numpy as np
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import time
from datetime import datetime
import supabase
import json
import warnings
from sklearn.metrics.pairwise import cosine_similarity
from streamlit_js_eval import streamlit_js_eval
import plotly.express as px
import random
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

warnings.filterwarnings("ignore")

# --- Load Secrets from Environment Variables ---
IPSTACK_KEY = os.getenv("IPSTACK_KEY")
IPQUALITYSCORE_KEY = os.getenv("IPQUALITYSCORE_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TYPINGDNA_API_KEY = os.getenv("TYPINGDNA_API_KEY")
TYPINGDNA_API_SECRET = os.getenv("TYPINGDNA_API_SECRET")
FINGERPRINTJS_API = os.getenv("FINGERPRINTJS_API")

# --- Health Check for Secrets ---
if not all([IPSTACK_KEY, IPQUALITYSCORE_KEY, SUPABASE_URL, SUPABASE_KEY, TYPINGDNA_API_KEY, TYPINGDNA_API_SECRET, FINGERPRINTJS_API]):
    st.error("One or more environment variables are missing. Please check your .env file.")
    st.stop()

# Initialize Supabase client
supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

# --- TypingDNA API Client ---
class TypingDNAClient:
    def __init__(self, api_key, api_secret):
        self.base_url = "https://api.typingdna.com"
        self.auth = HTTPBasicAuth(api_key, api_secret)

    def verify_pattern(self, user_id, typing_pattern):
        default_error_response = {'confidence': 10, 'enrollments': 0, 'message': "Typing pattern was too short for a reliable analysis."}
        if not typing_pattern or len(typing_pattern) < 80:
            return default_error_response
        try:
            check_url = f"{self.base_url}/checkuser/{user_id}"
            check_response = requests.get(check_url, auth=self.auth, timeout=5); check_response.raise_for_status()
            user_data = check_response.json()
            enrollments = user_data.get('count', 0)
            if enrollments > 0:
                verify_url = f"{self.base_url}/verify"
                payload = {'tp': typing_pattern, 'id': user_id, 'quality': '2'}
                verify_response = requests.post(verify_url, data=payload, auth=self.auth, timeout=5); verify_response.raise_for_status()
                result = verify_response.json()
                return {'confidence': result.get('confidence', 0), 'enrollments': enrollments, 'message': result.get('message', 'Success')}
            else:
                save_url = f"{self.base_url}/save"
                payload = {'tp': typing_pattern, 'id': user_id}
                save_response = requests.post(save_url, data=payload, auth=self.auth, timeout=5); save_response.raise_for_status()
                return {'confidence': 100, 'enrollments': 0, 'message': "First pattern enrolled successfully."}
        except requests.exceptions.RequestException as e:
            return {'confidence': 50, 'enrollments': -1, 'message': f"API Request Error: {e}"}

# --- Supabase Database Class ---
class SupabaseDB:
    def __init__(self, client):
        self.client = client
    def authenticate_user(self, username, password):
        try:
            response = self.client.table('users').select('user_id, password').eq('username', username).single().execute()
            user_data = response.data
            if user_data and user_data['password'] == password:
                return user_data['user_id']
            return None
        except Exception: return None
    def get_user_history(self, user_id):
        try:
            response = self.client.table('user_behavior_history').select('*').eq('user_id', user_id).order('login_time', desc=True).limit(20).execute()
            return response.data
        except Exception as e:
            st.error(f"Error fetching user history: {e}"); return []
    def save_session_data(self, data):
        try:
            self.client.table('user_behavior_history').insert([data]).execute()
            return True
        except Exception as e:
            st.error(f"Exception while saving session data: {e}"); return False

# --- Behavior Analyzer Class ---
class BehaviorAnalyzer:
    def __init__(self):
        self.threshold = 0.7
    def extract_features(self, session_data):
        features = [
            session_data.get('typing_speed', 0),
            session_data.get('mouse_movements', 0),
            int(session_data.get('vpn_detected', False)),
            session_data.get('form_completion_time', 0),
            hash(session_data.get('location', '')) % 1000,
            hash(session_data.get('device_fingerprint', '')) % 1000,
            (100 - session_data.get('typing_dna_confidence', 100)) / 100.0
        ]
        return np.array(features).reshape(1, -1)
    def calculate_anomaly_score(self, current_features, historical_features_list):
        if not historical_features_list: return 0.5
        historical_matrix = np.vstack(historical_features_list)
        similarities = cosine_similarity(current_features, historical_matrix)
        anomaly_score = 1 - np.mean(similarities)
        return max(0, min(1, anomaly_score))
    def detect_anomalies(self, current_data, historical_data):
        reasons = []
        if not historical_data:
             reasons.append("New user - establishing baseline behavior.")
             return False, 0.5, reasons
        current_features = self.extract_features(current_data)
        historical_features_list = [self.extract_features(record) for record in historical_data]
        anomaly_score = self.calculate_anomaly_score(current_features, historical_features_list)
        is_anomaly = anomaly_score > self.threshold
        if current_data['typing_dna_confidence'] < 70:
             reasons.append(f"Low typing biometrics confidence: {current_data['typing_dna_confidence']}%")
        common_locations = {r['location'] for r in historical_data}
        if current_data['location'] not in common_locations:
            reasons.append(f"New location detected: {current_data['location']}")
        if current_data['vpn_detected']:
            reasons.append("VPN or Proxy usage detected.")
        common_fingerprints = {r['device_fingerprint'] for r in historical_data}
        if current_data['device_fingerprint'] not in common_fingerprints:
            reasons.append(f"New device fingerprint detected.")
        if is_anomaly and not reasons:
            reasons.append("General behavior pattern deviates from historical norms.")
        return is_anomaly, anomaly_score, reasons

# --- API Functions ---
@st.cache_data(ttl=600)
def get_ipstack_data(ip_address):
    if not ip_address: return {"error": "No IP address provided."}
    try:
        url = f"http://api.ipstack.com/{ip_address}?access_key={IPSTACK_KEY}"
        response = requests.get(url, timeout=5); response.raise_for_status()
        return response.json()
    except Exception as e: return {"error": f"API Error: {e}"}
@st.cache_data(ttl=600)
def get_ipqualityscore_data(ip_address):
    if not ip_address: return {"error": "No IP address provided."}
    try:
        url = f"https://ipqualityscore.com/api/json/ip/{IPQUALITYSCORE_KEY}/{ip_address}"
        response = requests.get(url, timeout=5); response.raise_for_status()
        return response.json()
    except Exception as e: return {"error": f"API Error: {e}"}

# --- Streamlit App UI and Logic ---
def main():
    st.set_page_config(page_title="Live Anomaly Detection", layout="wide")
    st.title("🔒 Live User Behavior Anomaly Detection")
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.db = SupabaseDB(supabase_client)
        st.session_state.analyzer = BehaviorAnalyzer()
        st.session_state.typingdna_client = TypingDNAClient(TYPINGDNA_API_KEY, TYPINGDNA_API_SECRET)
    if not st.session_state.authenticated:
        login_page()
    else:
        dashboard_page()

def login_page():
    st.subheader("🔐 User Authentication")
    st.components.v1.html(f'''<script src="https://cdn.jsdelivr.net/gh/TypingDNA/TypingDnaRecorder-JavaScript@master/typingdna.js"></script>
    <script src="https://fpjscdn.net/v3/{FINGERPRINTJS_API}/loader_v3.9.5.js"></script>
    <script>
        window.fpPromise=import('https://fpjscdn.net/v3/{FINGERPRINTJS_API}').then(e=>e.load());
        window.getVisitorId=function(){{return window.fpPromise.then(e=>e.get()).then(e=>e.visitorId).catch(e=>"Error")}};
        function attachTypingDNA(){{
            const e=document.querySelector('input[aria-label="Username"]'),t=document.querySelector('input[aria-label="Password"]'),n=document.querySelector('input[aria-label="Type the sentence above"]');
            e&&t&&n&&!window.tdna?(window.tdna=new TypingDNA,e.id="tdna-username",t.id="tdna-password",n.id="tdna-sentence",window.tdna.addTarget("tdna-username"),window.tdna.addTarget("tdna-password"),window.tdna.addTarget("tdna-sentence"),console.log("TypingDNA recorder attached.")):window.tdna||setTimeout(attachTypingDNA,200)
        }}
        attachTypingDNA();
    </script>''',height=0)
    typing_sentences = ["The quick brown fox jumps over the lazy dog.", "Pack my box with five dozen liquor jugs."]
    if 'sentence_to_type' not in st.session_state:
        st.session_state.sentence_to_type = random.choice(typing_sentences)
    if 'login_start_time' not in st.session_state: st.session_state.login_start_time = time.time()
    with st.form("login_form"):
        username = st.text_input("Username", key="username_field", value="rohan_sharma_dev")
        password = st.text_input("Password", type="password", key="password_field", value="R#o&h@a*n@2025")
        st.markdown(f"**For typing analysis, please type the following sentence:**"); st.info(st.session_state.sentence_to_type)
        typed_sentence = st.text_input("Type the sentence above", key="sentence_field")
        login_button = st.form_submit_button("Login & Analyze")
        if login_button:
            with st.spinner("Authenticating and analyzing behavior..."):
                form_completion_time = time.time() - st.session_state.login_start_time
                js_command = "const p_user=window.tdna.getTypingPattern({type:2,targetId:'tdna-username'});const p_pass=window.tdna.getTypingPattern({type:2,targetId:'tdna-password'});const p_sent=window.tdna.getTypingPattern({type:2,targetId:'tdna-sentence'});return p_user+p_pass+p_sent;"
                typing_pattern = streamlit_js_eval(js_expressions=js_command)
                user_id = st.session_state.db.authenticate_user(username, password)
                if not user_id:
                    st.error("Invalid username or password!"); return
                fingerprint = streamlit_js_eval(js_expressions="window.getVisitorId()")
                get_ip_js = "(async () => { try { const response = await fetch('https://api.ipify.org?format=json'); const data = await response.json(); return data.ip; } catch (e) { return null; } })()"
                user_ip = streamlit_js_eval(js_expressions=get_ip_js)

                # For local testing, if IP fetch fails, use a placeholder
                if not user_ip:
                    user_ip = "8.8.8.8" # Google's DNS as a fallback
                    st.warning("Could not fetch client IP. Using a placeholder for analysis.")

                ipstack_data = get_ipstack_data(user_ip)
                ipqualityscore_data = get_ipqualityscore_data(user_ip)
                typingdna_data = st.session_state.typingdna_client.verify_pattern(str(user_id), typing_pattern)
                location = f"{ipstack_data.get('city', 'Unknown')}, {ipstack_data.get('country_name', 'Unknown')}"
                vpn_detected = ipqualityscore_data.get('vpn', False) or ipqualityscore_data.get('proxy', False)
                typing_confidence = typingdna_data.get('confidence', 50)
                words_in_sentence = len(st.session_state.sentence_to_type.split())
                typing_speed = (words_in_sentence / form_completion_time * 60) if form_completion_time > 1 else 50.0
                session_data = {
                    'user_id': user_id, 'login_time': datetime.now().isoformat(), 'typing_speed': int(typing_speed),
                    'mouse_movements': np.random.randint(150, 400), 'location': location, 'ip_address': user_ip,
                    'vpn_detected': vpn_detected, 'device_fingerprint': fingerprint,
                    'form_completion_time': int(form_completion_time), 'typing_dna_confidence': typing_confidence,
                    'ipstack_data': ipstack_data, 'ipqualityscore_data': ipqualityscore_data
                }
                historical_data = st.session_state.db.get_user_history(user_id)
                is_anomaly, risk_score, reasons = st.session_state.analyzer.detect_anomalies(session_data, historical_data)
                session_data['risk_score'] = risk_score
                st.session_state.db.save_session_data(session_data)
                st.session_state.last_analysis = {'risk_score': risk_score, 'reasons': reasons, 'session_data': session_data, 'typingdna_data': typingdna_data}
                st.session_state.authenticated = True; st.session_state.user_id = user_id; st.session_state.username = username
                if 'login_start_time' in st.session_state: del st.session_state.login_start_time
                if 'sentence_to_type' in st.session_state: del st.session_state.sentence_to_type
                st.success("Analysis complete. Welcome!"); time.sleep(1); st.rerun()

def dashboard_page():
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()
    st.subheader("📈 Login Security Assessment")
    if 'last_analysis' in st.session_state:
        res = st.session_state.last_analysis
        risk_score = res['risk_score']
        col1, col2 = st.columns([1,2])
        with col1:
            st.metric("Calculated Risk Score", f"{risk_score:.3f}")
            if risk_score >= 0.7: st.error("Assessment: 🔴 High Risk")
            elif risk_score >= 0.4: st.warning("Assessment: 🟠 Medium Risk")
            else: st.success("Assessment: 🟢 Low Risk")
        with col2:
            st.write("**Analysis Flags (Suspicious Items):**")
            if res['reasons']:
                for r in res['reasons']: st.info(f"🔹 {r}")
            else:
                st.info("🔹 No specific risk factors identified.")
    st.divider()
    st.subheader("🔬 Security Intelligence Report")
    if 'last_analysis' in st.session_state:
        session_data = res['session_data']
        typingdna_data = res['typingdna_data']
        c1, c2, c3 = st.columns(3)
        with c1:
            st.info("**Geolocation Analysis (ipstack)**")
            st.json(session_data.get('ipstack_data', {"error": "Data not found."}))
        with c2:
            st.warning("**Fraud Risk Analysis (IPQualityScore)**")
            st.json(session_data.get('ipqualityscore_data', {"error": "Data not found."}))
        with c3:
            st.success("**Typing Biometrics (TypingDNA)**")
            st.json(typingdna_data)
    st.divider()
    st.subheader("📊 Historical Behavior Dashboard")
    historical_data = st.session_state.db.get_user_history(st.session_state.user_id)
    if not historical_data: st.warning("No historical data available for this user."); return
    df = pd.DataFrame(historical_data)
    df['login_time'] = pd.to_datetime(df['login_time'], format='ISO8601', errors='coerce')
    col1, col2, col3, col4 = st.columns(4)
    avg_risk = pd.to_numeric(df['risk_score'], errors='coerce').mean()
    anomaly_count = df[pd.to_numeric(df['risk_score'], errors='coerce') > 0.7].shape[0]
    col1.metric("Total Sessions", len(df)); col2.metric("Avg Risk Score", f"{avg_risk:.3f}")
    col3.metric("Anomalies Detected", anomaly_count); col4.metric("Last Login", df['login_time'].max().strftime('%Y-%m-%d %H:%M'))
    st.subheader("📈 Behavior Trends Over Time")
    df['risk_score'] = pd.to_numeric(df['risk_score'], errors='coerce')
    df['typing_dna_confidence'] = pd.to_numeric(df['typing_dna_confidence'], errors='coerce')
    df['typing_speed'] = pd.to_numeric(df['typing_speed'], errors='coerce')
    fig = px.line(df.sort_values('login_time'), x='login_time', y=['risk_score', 'typing_dna_confidence', 'typing_speed'], title="Key Metrics Over Time", labels={'login_time': 'Session Timestamp', 'value': 'Metric Value'})
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
