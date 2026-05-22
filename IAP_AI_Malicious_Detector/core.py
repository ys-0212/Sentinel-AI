# core.py - Raw wrapper for IAP_AI_Malicious_Detector
# Provides raw input/output functions without Streamlit dependency

import os
import json
import pandas as pd
import time
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Get the directory where this file is located
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_DATASET_PATH = os.path.join(_CURRENT_DIR, "malicious_text_dataset.csv")

# Model configuration with fallbacks
_MODELS = [
    os.getenv("GROQ_PRIMARY_MODEL", "llama-3.3-70b-versatile"),
    os.getenv("GROQ_FALLBACK_MODEL", "llama-3.1-70b-versatile"),
    os.getenv("GROQ_SECONDARY_FALLBACK", "mixtral-8x7b-32768")
]


def _get_groq_client() -> Groq:
    """Initialize and return Groq client."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set. Please set it in .env file.")
    return Groq(api_key=api_key)


def _load_dataset() -> pd.DataFrame:
    """Load the few-shot examples dataset."""
    if not os.path.exists(_DATASET_PATH):
        raise FileNotFoundError(f"Dataset file not found at {_DATASET_PATH}")
    return pd.read_csv(_DATASET_PATH)


def _build_few_shot_prompt(dataset: pd.DataFrame) -> str:
    """Build few-shot examples string from dataset."""
    examples_str = ""
    for _, row in dataset.iterrows():
        formatted_text = row['text'].replace('\n', '\\n')
        examples_str += f"--- CHAT START ---\n{formatted_text}\n--- CHAT END ---\nANALYSIS:\nIntent: {row['label']}\n\n"
    return examples_str


def analyze_text(text: str, max_retries: int = 3) -> dict:
    """
    Analyze text (chat/email/message/SMS) for malicious intent.
    
    Args:
        text: The text content to analyze (chat conversation, email, SMS, etc.)
        max_retries: Maximum number of retry attempts
        
    Returns:
        dict with keys:
            - threat_score: int (0-10, 0=benign, 10=highly malicious)
            - intent_classification: str (Benign, Phishing, Scareware, etc.)
            - social_tactics_detected: list of detected tactics
            - ioc_detected: list of indicators of compromise
            - summary: str (brief analysis and recommendation)
            - error: str (only present if an error occurred)
    """
    try:
        client = _get_groq_client()
        dataset = _load_dataset()
        examples_str = _build_few_shot_prompt(dataset)
        
        system_prompt = f"""
        You are an expert AI Cybersecurity Analyst. Your task is to analyze a given chat conversation and detect any malicious intent.
        You must identify social engineering tactics, potential indicators of compromise (IOCs), and classify the bot's intent.

        Respond ONLY with a JSON object with the following structure:
        {{
          "threat_score": <An integer from 0 (benign) to 10 (highly malicious)>,
          "intent_classification": "<One of: Benign, Phishing, Scareware, Ransomware, Business Email Compromise, Social Engineering Scam, Unknown Malicious>",
          "social_tactics_detected": ["<List of detected tactics, e.g., Urgency, Impersonation, Scarcity, Authority, Flattery, Inducing Anxiety>"],
          "ioc_detected": ["<List of detected IOCs, e.g., Malicious URL, File Download (.exe), Request for Credentials, Request for Remote Access, Request for Payment>"],
          "summary": "<A brief, one-sentence summary of your analysis and a recommendation for the user.>"
        }}

        Here are some examples of how to analyze chats:
        {examples_str}
        Now, analyze the following chat. Provide ONLY the JSON output.
        """
        
        # Try each model with exponential backoff
        for attempt in range(max_retries):
            for model_idx, model in enumerate(_MODELS):
                try:
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"--- CHAT START ---\n{text}\n--- CHAT END ---\nANALYSIS:\n"}
                        ],
                        model=model,
                        temperature=0.1,
                        max_tokens=512,
                        response_format={"type": "json_object"},
                    )
                    
                    response_content = chat_completion.choices[0].message.content
                    result = json.loads(response_content)
                    
                    # Add metadata about which model was used
                    result['_model_used'] = model
                    result['_attempt'] = attempt + 1
                    
                    return result
                    
                except Exception as model_error:
                    # If this is the last model and last attempt, raise the error
                    if model_idx == len(_MODELS) - 1 and attempt == max_retries - 1:
                        raise model_error
                    
                    # Otherwise, try next model or wait and retry
                    if model_idx < len(_MODELS) - 1:
                        print(f"Model {model} failed, trying next model...")
                        continue
                    else:
                        # Wait before retrying with exponential backoff
                        wait_time = (2 ** attempt) * 0.5  # 0.5s, 1s, 2s
                        print(f"All models failed on attempt {attempt + 1}, waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
        
    except FileNotFoundError as e:
        return {
            "error": f"Dataset file not found: {str(e)}",
            "threat_score": 0,
            "intent_classification": "Error",
            "social_tactics_detected": [],
            "ioc_detected": [],
            "summary": "Analysis failed: Dataset file not found. Please ensure malicious_text_dataset.csv exists."
        }
    except ValueError as e:
        return {
            "error": str(e),
            "threat_score": 0,
            "intent_classification": "Error",
            "social_tactics_detected": [],
            "ioc_detected": [],
            "summary": f"Analysis failed: {str(e)}"
        }
    except Exception as e:
        return {
            "error": str(e),
            "threat_score": 0,
            "intent_classification": "Error",
            "social_tactics_detected": [],
            "ioc_detected": [],
            "summary": f"Analysis failed: {str(e)}. Please check your API key and internet connection."
        }


# Test function
if __name__ == "__main__":
    test_text = """
    User: My computer is running slow.
    Bot: I've detected a critical virus on your system! Download this antivirus tool immediately: http://malware-site.com/fix.exe
    You must act now or your files will be deleted!
    """
    result = analyze_text(test_text)
    print(json.dumps(result, indent=2))
