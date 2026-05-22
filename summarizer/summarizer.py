# summarizer.py
import requests
import os
import json

# --- API KEY FROM ENVIRONMENT ---
# Get API key from environment variable
API_KEY = os.environ.get("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

if API_KEY == "gsk_...":
    print("⚠️ WARNING: API key is not set in summarizer.py. Please replace 'gsk_...' with your actual key.")

# --- API Configuration ---
URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def get_incident_details_from_text(complaint_text, image_evidence_text, pdf_evidence_text, audio_evidence_text, text_from_video_audio, text_from_video_frames):
    """
    Uses the Groq API to extract key details into a structured JSON object.
    """
    departments = """
    Department for Promotion of Industry and Internal Trade (DPIIT), Department of Commerce (DoC), Department of Consumer Affairs (DoCA), Department of Economic Affairs (DEA), Department of Financial Services (DoFS), Department of Revenue (DoR), Department of Telecommunications (DoT), Ministry of Home Affairs (MHA)
    """
    prompt = f"""
    You are an expert cybercrime analyst. Analyze the following information and extract key details into a clean JSON object.
    Complaint: "{complaint_text}"
    Image Evidence: "{image_evidence_text}"
    PDF Evidence: "{pdf_evidence_text}"
    Audio Evidence: "{audio_evidence_text}"
    Video Audio: "{text_from_video_audio}"
    Video Frames: "{text_from_video_frames}"
    ---
    List of potential government departments: {departments}
    Instructions for JSON:
    1. "crime_type": Choose from: 'spam', 'phishing', 'smishing', 'malware', 'ransomware', 'data_breach', 'financial_fraud', 'identity_theft', 'cyber_stalking', 'other'.
    2. "financial_loss_inr": Estimate financial loss in INR. Use 0 if none. Must be a number.
    3. "is_ongoing": boolean, true if the attack is current, else false.
    4. "victims_affected": integer, number of people affected.
    5. "data_sensitivity": Choose from: 'none', 'personal', 'financial', 'medical', 'classified'.
    6. "target_type": Choose from: 'individual', 'organization', 'government'.
    7. "evidence_match": Does evidence support complaint? Choose from: true, false, "partial".
    8. "relevant_department": From the list provided, identify up to two most relevant departments as a JSON list of strings.
    Output only the raw JSON object.
    """
    payload = {
        "model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1, "max_tokens": 1024, "response_format": {"type": "json_object"},
    }
    try:
        response = requests.post(URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        response_data = response.json()
        json_string = response_data["choices"][0]["message"]["content"]
        return json.loads(json_string)
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error in get_incident_details_from_text: {e}")
        try:
             # Try to print more details from the response if available
             print(f"Response: {response.text}")
        except:
             pass
        return None

def get_narrative_summary(complaint_text, image_evidence_text, pdf_evidence_text, audio_evidence_text, text_from_video_audio, text_from_video_frames):
    """
    Uses the Groq API to generate a human-readable summary of the incident.
    """
    prompt = f"""
    You are a cybercrime analyst. Based on the complaint and evidence below, write a concise, human-readable narrative summary of the incident in 2-4 clear sentences.
    Focus on the main events and impact. Also provide a one-line summary.
    Complaint: "{complaint_text}"
    Image Evidence: "{image_evidence_text}"
    PDF Evidence: "{pdf_evidence_text}"
    Audio Evidence: "{audio_evidence_text}"
    Video Audio: "{text_from_video_audio}"
    Video Frames: "{text_from_video_frames}"
    ---
    Provide the summary in plain text.
    """
    payload = {
        "model": "llama-3.1-8b-instant", "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3, "max_tokens": 512,
    }
    try:
        response = requests.post(URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        response_data = response.json()
        return response_data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        error_message = f"Error: Could not generate summary. Details: {e}"
        print(f"❌ {error_message}")
        try:
             # Try to print more details from the response if available
             print(f"Response: {response.text}")
        except:
             pass
        return error_message