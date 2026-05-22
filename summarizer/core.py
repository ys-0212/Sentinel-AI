# core.py - Raw wrapper for summarizer
# Provides raw input/output functions for complaint summarization

import os
import sys
import json

# Add the summarizer directory to path for imports
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)

# Import existing modules with graceful fallback for missing dependencies
try:
    from pdf_to_text import extract_text_from_pdf
except ImportError:
    def extract_text_from_pdf(path): return ""

try:
    from image_to_text import extract_text_from_image
except ImportError:
    def extract_text_from_image(path): return ""

try:
    from summarizer import get_incident_details_from_text, get_narrative_summary
except ImportError:
    def get_incident_details_from_text(*args): return {}
    def get_narrative_summary(*args): return "Summarizer not available"

try:
    from classifier import classify_cybercrime
except ImportError:
    def classify_cybercrime(details): return ("Unknown", 0)

try:
    from contradict import contradiction_in_complain_and_evidences
except ImportError:
    def contradiction_in_complain_and_evidences(*args): return (None, False)

try:
    from audio_to_text import extract_text_from_audio
except ImportError:
    def extract_text_from_audio(path): return ""

try:
    from video_to_text import extract_details_from_video
except ImportError:
    def extract_details_from_video(path): return {"transcribed_audio": "", "text_from_frames": []}


def extract_evidence_text(
    pdf_path: str = None,
    image_path: str = None,
    audio_path: str = None,
    video_path: str = None
) -> dict:
    """
    Extract text from various evidence files.
    
    Args:
        pdf_path: Path to PDF evidence file
        image_path: Path to image evidence file
        audio_path: Path to audio evidence file
        video_path: Path to video evidence file
        
    Returns:
        dict with extracted text from each source
    """
    result = {
        "pdf_text": "",
        "image_text": "",
        "audio_text": "",
        "video_audio_text": "",
        "video_frame_text": ""
    }
    
    # Extract PDF text
    if pdf_path and os.path.exists(pdf_path):
        try:
            result["pdf_text"] = extract_text_from_pdf(pdf_path)
        except Exception as e:
            result["pdf_text"] = f"Error extracting PDF: {e}"
    
    # Extract image text (OCR)
    if image_path and os.path.exists(image_path):
        try:
            result["image_text"] = extract_text_from_image(image_path)
        except Exception as e:
            result["image_text"] = f"Error extracting image text: {e}"
    
    # Extract audio text (transcription)
    if audio_path and os.path.exists(audio_path):
        try:
            result["audio_text"] = extract_text_from_audio(audio_path)
        except Exception as e:
            result["audio_text"] = f"Error transcribing audio: {e}"
    
    # Extract video content
    if video_path and os.path.exists(video_path):
        try:
            video_details = extract_details_from_video(video_path)
            result["video_audio_text"] = video_details.get("transcribed_audio", "")
            result["video_frame_text"] = " ".join(video_details.get("text_from_frames", []))
        except Exception as e:
            result["video_audio_text"] = f"Error processing video: {e}"
    
    return result


def check_contradictions(
    complaint: str,
    evidence: dict
) -> dict:
    """
    Check for contradictions between complaint and evidence.
    
    Args:
        complaint: The complaint text
        evidence: dict from extract_evidence_text()
        
    Returns:
        dict with contradiction analysis
    """
    # Check if there's any evidence to analyze
    has_evidence = any([
        evidence.get("pdf_text"),
        evidence.get("image_text"),
        evidence.get("audio_text"),
        evidence.get("video_audio_text"),
        evidence.get("video_frame_text")
    ])
    
    if not has_evidence:
        return {
            "has_contradiction": False,
            "analysis": None,
            "message": "No evidence provided for contradiction analysis"
        }
    
    try:
        analysis, has_contradiction = contradiction_in_complain_and_evidences(
            complaint,
            evidence.get("image_text", ""),
            evidence.get("pdf_text", ""),
            evidence.get("audio_text", ""),
            evidence.get("video_audio_text", ""),
            evidence.get("video_frame_text", "")
        )
        
        return {
            "has_contradiction": has_contradiction,
            "analysis": analysis
        }
    except Exception as e:
        return {
            "has_contradiction": False,
            "analysis": None,
            "error": str(e)
        }


def summarize_complaint(
    complaint: str,
    pdf_path: str = None,
    image_path: str = None,
    audio_path: str = None,
    video_path: str = None
) -> dict:
    """
    Summarize a cybercrime complaint with evidence analysis.
    
    Args:
        complaint: The complaint text (required)
        pdf_path: Optional path to PDF evidence
        image_path: Optional path to image evidence
        audio_path: Optional path to audio evidence
        video_path: Optional path to video evidence
        
    Returns:
        dict with:
            - narrative_summary: str (human-readable summary)
            - incident_details: dict (structured incident info)
            - classification: str (priority level)
            - severity_score: float (1-5)
            - contradiction: dict (contradiction analysis if evidence provided)
            - evidence_extracted: dict (text extracted from evidence)
            - error: str (only if error occurred)
    """
    if not complaint or not complaint.strip():
        return {
            "error": "No complaint text provided",
            "narrative_summary": "",
            "incident_details": {},
            "classification": "",
            "severity_score": 0
        }
    
    # Extract evidence text
    evidence = extract_evidence_text(pdf_path, image_path, audio_path, video_path)
    
    # Check contradictions
    contradiction_result = check_contradictions(complaint, evidence)
    
    # Get narrative summary
    try:
        narrative_summary = get_narrative_summary(
            complaint,
            evidence.get("image_text", ""),
            evidence.get("pdf_text", ""),
            evidence.get("audio_text", ""),
            evidence.get("video_audio_text", ""),
            evidence.get("video_frame_text", "")
        )
    except Exception as e:
        narrative_summary = f"Error generating summary: {e}"
    
    # Get incident details
    try:
        incident_details = get_incident_details_from_text(
            complaint,
            evidence.get("image_text", ""),
            evidence.get("pdf_text", ""),
            evidence.get("audio_text", ""),
            evidence.get("video_audio_text", ""),
            evidence.get("video_frame_text", "")
        )
    except Exception as e:
        incident_details = {"error": str(e)}
    
    # Classify priority
    classification = ""
    severity_score = 0
    if incident_details and "error" not in incident_details:
        try:
            classification, severity_score = classify_cybercrime(incident_details)
        except Exception as e:
            classification = f"Error: {e}"
    
    return {
        "narrative_summary": narrative_summary,
        "incident_details": incident_details,
        "classification": classification,
        "severity_score": severity_score,
        "contradiction": contradiction_result,
        "evidence_extracted": evidence
    }


def get_severity_color(severity_score: float) -> str:
    """
    Get color code based on severity score.
    
    Args:
        severity_score: Score from 1-5
        
    Returns:
        Color name (green, yellow, orange, red)
    """
    if severity_score <= 0:
        return "gray"  # Unknown/Error
    elif severity_score <= 2:
        return "yellow"  # Low
    elif severity_score <= 3:
        return "orange"  # Medium
    elif severity_score <= 4:
        return "orangered"  # High
    else:
        return "red"  # Very High/Critical


# Test function
if __name__ == "__main__":
    # Test with a sample complaint
    test_complaint = """
    I received a call from someone claiming to be from my bank. They said my account 
    was compromised and asked me to transfer Rs. 50,000 to a safe account. I followed 
    their instructions and transferred the money through UPI. Now I realize it was a scam.
    """
    
    result = summarize_complaint(test_complaint)
    print("Summarization Result:")
    print(json.dumps(result, indent=2, default=str))
