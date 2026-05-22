# core.py - Call Scam Detector
# Provides audio and text analysis for scam detection

import os
import json
from typing import Optional

# Try to import vosk for audio transcription
try:
    from vosk import Model, KaldiRecognizer, SetLogLevel
    SetLogLevel(-1)  # Suppress vosk logs
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

try:
    import groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Get the directory where this file is located
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Model paths for vosk
_MODEL_PATHS = {
    "en": os.path.join(_CURRENT_DIR, "model-en"),
    "hi": os.path.join(_CURRENT_DIR, "model-hi")
}

# Groq API configuration
_GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not _GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set")
_LLM_MODELS = [
    "openai/gpt-oss-120b",
    "llama-3.1-70b-versatile",
    "mixtral-8x7b-32768"
]


def _get_groq_client():
    """Get Groq client instance."""
    if not GROQ_AVAILABLE:
        raise ImportError("groq package not installed")
    return groq.Groq(api_key=_GROQ_API_KEY)


def transcribe_audio(audio_path: str, language: str = "en") -> str:
    """
    Transcribe audio file to text using Vosk.
    
    Args:
        audio_path: Path to audio file
        language: Language code ('en' for English, 'hi' for Hindi)
        
    Returns:
        Transcribed text
    """
    if not VOSK_AVAILABLE:
        return "[Vosk not available - please install vosk package]"
    
    if not PYDUB_AVAILABLE:
        return "[pydub not available - please install pydub package]"
    
    model_path = _MODEL_PATHS.get(language, _MODEL_PATHS["en"])
    
    if not os.path.exists(model_path):
        return f"[Model not found at {model_path}]"
    
    try:
        # Convert audio to WAV format with correct sample rate
        audio = AudioSegment.from_file(audio_path)
        audio = audio.set_channels(1)  # Mono
        audio = audio.set_frame_rate(16000)  # 16kHz
        
        # Export to temporary WAV file
        temp_wav = audio_path + ".temp.wav"
        audio.export(temp_wav, format="wav")
        
        # Load model and transcribe
        model = Model(model_path)
        rec = KaldiRecognizer(model, 16000)
        rec.SetWords(True)
        
        transcript_parts = []
        
        with open(temp_wav, "rb") as wf:
            # Skip WAV header
            wf.read(44)
            
            while True:
                data = wf.read(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if result.get("text"):
                        transcript_parts.append(result["text"])
            
            # Get final result
            final_result = json.loads(rec.FinalResult())
            if final_result.get("text"):
                transcript_parts.append(final_result["text"])
        
        # Cleanup temp file
        if os.path.exists(temp_wav):
            os.remove(temp_wav)
        
        return " ".join(transcript_parts)
        
    except Exception as e:
        return f"[Transcription error: {str(e)}]"


def analyze_text_for_scam(text: str) -> dict:
    """
    Analyze text for scam indicators using LLM.
    
    Args:
        text: Text to analyze (call transcript or message)
        
    Returns:
        dict with:
            - classification: str (Scam, Likely Scam, Suspicious, Likely Safe, Safe)
            - reason: str (explanation)
            - error: str (only if error occurred)
    """
    if not text or not text.strip():
        return {
            "classification": "Unknown",
            "reason": "No text provided for analysis"
        }
    
    if not GROQ_AVAILABLE:
        return {
            "classification": "Unknown",
            "reason": "Groq package not available - cannot perform AI analysis",
            "error": "groq package not installed"
        }
    
    system_prompt = """You are an expert fraud analyst specializing in phone scam detection. 
Analyze the provided call transcript or message and classify it as one of:
- "Scam" - Clear indicators of fraud (urgent money requests, impersonation, threats)
- "Likely Scam" - Multiple suspicious elements, probably fraudulent
- "Suspicious" - Some concerning patterns, needs caution
- "Likely Safe" - Minor concerns but probably legitimate  
- "Safe" - Normal conversation with no fraud indicators

Look for common scam patterns:
1. Urgency/pressure tactics ("act now", "limited time")
2. Impersonation (bank, government, tech support)
3. Requests for personal info, OTPs, passwords
4. Money transfer requests
5. Threats (legal action, account suspension)
6. Too-good-to-be-true offers
7. Emotional manipulation

Respond ONLY with a JSON object:
{
    "classification": "<one of the above classifications>",
    "reason": "<brief explanation of your analysis>"
}"""

    try:
        client = _get_groq_client()
        
        for model in _LLM_MODELS:
            try:
                response = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Analyze this transcript:\n\n{text}"}
                    ],
                    model=model,
                    temperature=0.1,
                    max_tokens=256,
                    response_format={"type": "json_object"}
                )
                
                result = json.loads(response.choices[0].message.content)
                return {
                    "classification": result.get("classification", "Unknown"),
                    "reason": result.get("reason", "No explanation provided")
                }
                
            except Exception as model_error:
                continue
        
        return {
            "classification": "Unknown",
            "reason": "All AI models failed",
            "error": "Could not get response from any model"
        }
        
    except Exception as e:
        return {
            "classification": "Unknown",
            "reason": f"Analysis failed: {str(e)}",
            "error": str(e)
        }


def analyze_audio_for_scam(audio_path: str, language: str = "en") -> dict:
    """
    Analyze audio file for scam indicators.
    
    First transcribes the audio, then analyzes the transcript.
    
    Args:
        audio_path: Path to audio file
        language: Language code ('en' or 'hi')
        
    Returns:
        dict with:
            - transcript: str (transcribed text)
            - language: str (detected/specified language)
            - classification: str (Scam, Likely Scam, etc.)
            - reason: str (explanation)
            - error: str (only if error occurred)
    """
    if not os.path.exists(audio_path):
        return {
            "transcript": "",
            "language": language,
            "classification": "Unknown",
            "reason": f"Audio file not found: {audio_path}",
            "error": "File not found"
        }
    
    # Transcribe audio
    transcript = transcribe_audio(audio_path, language)
    
    # Check if transcription failed
    if transcript.startswith("[") and transcript.endswith("]"):
        return {
            "transcript": transcript,
            "language": language,
            "classification": "Unknown",
            "reason": "Could not transcribe audio",
            "error": transcript
        }
    
    # Analyze transcript
    analysis = analyze_text_for_scam(transcript)
    
    return {
        "transcript": transcript,
        "language": language,
        "classification": analysis.get("classification", "Unknown"),
        "reason": analysis.get("reason", ""),
        "error": analysis.get("error")
    }


# Test function
if __name__ == "__main__":
    # Test text analysis
    test_text = """
    Hello, this is urgent! Your bank account has been compromised. 
    We need you to transfer your money to this safe account immediately 
    or you will lose everything. Please share your OTP to verify your identity.
    """
    
    print("Testing text analysis...")
    result = analyze_text_for_scam(test_text)
    print(f"Classification: {result['classification']}")
    print(f"Reason: {result['reason']}")
