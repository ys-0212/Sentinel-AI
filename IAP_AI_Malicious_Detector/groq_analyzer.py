# groq_analyzer.py
import json
import pandas as pd
from groq import Groq

def analyze_chat_with_groq(client, user_input, few_shot_examples):
    """
    Analyzes the user's input chat using a few-shot prompt with Groq API.

    Args:
        client (Groq): The initialized Groq API client.
        user_input (str): The chat conversation to analyze.
        few_shot_examples (pd.DataFrame): A DataFrame with 'text' and 'label' columns for examples.

    Returns:
        dict: A dictionary containing the analysis results, or None on error.
    """
    # Construct the few-shot examples part of the prompt from the DataFrame
    examples_str = ""
    for _, row in few_shot_examples.iterrows():
        # Ensure multi-line text is formatted correctly within the prompt
        formatted_text = row['text'].replace('\n', '\\n')
        examples_str += f"--- CHAT START ---\n{formatted_text}\n--- CHAT END ---\nANALYSIS:\nIntent: {row['label']}\n\n"

    # The main system prompt - this is the "Threat-Aware Prompting" (TAP)
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

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": f"--- CHAT START ---\n{user_input}\n--- CHAT END ---\nANALYSIS:\n",
                }
            ],
            model="openai/gpt-oss-120b",
            temperature=0.1,
            max_tokens=512,
            top_p=1,
            stop=None,
            response_format={"type": "json_object"},
            stream=False,
        )
        response_content = chat_completion.choices[0].message.content
        return json.loads(response_content)
    except Exception as e:
        # In a real app, you'd want to log this error more robustly
        print(f"Error communicating with Groq API: {e}")
        return None
