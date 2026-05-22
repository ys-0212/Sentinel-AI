import json
import os
from pdf_to_text import extract_text_from_pdf
from image_to_text import extract_text_from_image
from summarizer import get_incident_details_from_text, get_narrative_summary
from classifier import classify_cybercrime
from contradict import contradiction_in_complain_and_evidences
from audio_to_text import extract_text_from_audio
from video_to_text import extract_details_from_video

# --- User Input ---
complaint = input("Enter the complaint: ")
pdf_path = input("Enter the path to the PDF file (if any): ")
image_path = input("Enter the path to the image file (if any): ")
audio_file_path = input("Enter the path to the audio file (if any): ")
video_file_path = input("Enter the path to the video file (if any): ")

# --- Text and Data Extraction ---
image_text = extract_text_from_image(image_path) if image_path and os.path.exists(image_path) else ""
pdf_text = extract_text_from_pdf(pdf_path) if pdf_path and os.path.exists(pdf_path) else ""
audio_text = extract_text_from_audio(audio_file_path) if audio_file_path and os.path.exists(audio_file_path) else ""
video_details = extract_details_from_video(video_file_path) if video_file_path and os.path.exists(video_file_path) else {"transcribed_audio": "", "text_from_frames": []}
text_from_video_audio = video_details.get("transcribed_audio", "")
text_from_video_frames = " ".join(video_details.get("text_from_frames", []))

# --- Contradiction Analysis ---
if any([image_text, pdf_text, audio_text, text_from_video_audio, text_from_video_frames]):
    contradiction_text, contradiction = contradiction_in_complain_and_evidences(complaint, image_text, pdf_text, audio_text, text_from_video_audio, text_from_video_frames)
    if contradiction:
        print("\n--- Contradiction Analysis ---")
        print("🚨 Contradiction found between the complaint and evidence.")
        print(json.dumps(contradiction_text, indent=2))

# --- Summarization and Classification ---
print("\n--- Generating Summary and Details ---")
narrative_summary = get_narrative_summary(complaint, image_text, pdf_text, audio_text, text_from_video_audio, text_from_video_frames)
incident_details = get_incident_details_from_text(complaint, image_text, pdf_text, audio_text, text_from_video_audio, text_from_video_frames)

if narrative_summary:
    print("\n--- Summary ---")
    print(narrative_summary)

if incident_details:
    print("\n--- Incident Details (JSON) ---")
    print(json.dumps(incident_details, indent=2))

    print("\n--- Relevant Departments ---")
    print(json.dumps(incident_details.get('relevant_department', 'Not found'), indent=2))

    classification, score = classify_cybercrime(incident_details)
    print("\n--- Priority Classification ---")
    print(f"Priority: {classification}")
else:
    print("\n--- Could not generate incident details. Skipping classification. ---")