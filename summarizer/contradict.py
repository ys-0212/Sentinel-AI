import requests
import json
import os

# --- API KEY FROM ENVIRONMENT ---
# Get API key from environment variable
API_KEY = os.environ.get("GROQ_API_KEY")
if not API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")

if API_KEY == "gsk_...":
    print("⚠️ WARNING: API key in contradict.py is a placeholder. Please replace 'gsk_...' with your actual key.")

# --- API Configuration ---
URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

def contradiction_in_complain_and_evidences(complaint_text, image_evidence_text, pdf_evidence_text, audio_evidence_text, text_from_video_audio, text_from_video_frames):
    """
    Analyzes a cybercrime complaint against evidence to find contradictions.

    Returns:
        A tuple containing the detailed JSON analysis and a boolean indicating
        if a significant contradiction was found. Returns (None, False) on error.
    """
    prompt = f"""
    You are a meticulous cybercrime evidence analyst. Your task is to compare the user's complaint against the text extracted from various evidence sources.

    **Objective**: Identify and compare key cybercrime-related entities (financial amounts, recipient names, UPI IDs, transaction IDs, dates) between the complaint and the evidence. Ignore any information not relevant to the core claim.

    **Complaint**:
    "{complaint_text}"

    **Evidence Text (from all sources)**:
    - Image: "{image_evidence_text}"
    - PDF: "{pdf_evidence_text}"
    - Audio: "{audio_evidence_text}"
    - Video Audio: "{text_from_video_audio}"
    - Video Frames: "{text_from_video_frames}"

    ---
    **Instructions**:
    1.  Extract key cybercrime entities from the complaint (e.g., amount, recipient name/ID, date, transaction ID).
    2.  Search for the same entities in the provided evidence texts. If an entity is not found in the evidence, explicitly state that.
    3.  Produce a JSON object with a root key "contradiction_analysis".
    4.  For each entity analyzed (e.g., "financial_amount", "recipient_upi_id"), provide:
        - "complaint_value": The value from the complaint. Use "Not Mentioned" if absent.
        - "evidence_value": The value from the evidence. Use "Not Found" if absent.
        - "match_status": Must be "match", "contradiction", or "partial_match".
        - "summary": A brief, one-sentence explanation.
    5.  **Crucially, if the "match_status" is "contradiction", you MUST prefix the summary with "🚨 CONTRADICTION:" to highlight the issue.**

    Your response must be only a valid JSON object.
    """

    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1024,
        "response_format": {"type": "json_object"},
    }
    
    try:
        response = requests.post(URL, headers=HEADERS, json=payload)
        response.raise_for_status()
        response_data = response.json()
        json_string = response_data["choices"][0]["message"]["content"]
        
        # Parse the JSON response
        json_result = json.loads(json_string)
        
        # Check for contradictions
        has_contradiction = False
        analysis = json_result.get("contradiction_analysis", {})
        for entity_details in analysis.values():
            if entity_details.get("match_status") == "contradiction":
                has_contradiction = True
                break
        
        return json_result, has_contradiction

    except requests.exceptions.RequestException as e:
        print(f"❌ API Error in contradiction check: {e}")
        return None, False
    except json.JSONDecodeError:
        print("❌ Error: Failed to decode JSON response from the API.")
        return None, False
    except Exception as e:
        print(f"❌ An unexpected error occurred in contradiction check: {e}")
        return None, False