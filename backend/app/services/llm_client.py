import requests
from flask import current_app

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

NULLABLE_TEXT = {"type": "STRING", "nullable": True}

GEMINI_BILL_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "patient_name": NULLABLE_TEXT,
        "hospital_name": NULLABLE_TEXT,
        "admission_date": NULLABLE_TEXT,
        "discharge_date": NULLABLE_TEXT,
        "diagnosis": NULLABLE_TEXT,
        "line_items": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {"description": {"type": "STRING"}, "amount": {"type": "NUMBER"}},
                "required": ["description", "amount"],
            },
        },
        "total_amount": {"type": "NUMBER", "nullable": True},
    },
    "required": ["patient_name", "hospital_name", "admission_date", "discharge_date", "line_items", "total_amount"],
}


class LLMError(Exception):
    pass


def ask_groq(system_prompt, user_text):
    config = current_app.config
    response = requests.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {config['GROQ_API_KEY']}"},
        json={
            "model": config["GROQ_MODEL"],
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
        },
        timeout=config["LLM_TIMEOUT_SECONDS"],
    )
    if response.status_code != 200:
        raise LLMError(f"Groq returned {response.status_code}")
    return response.json()["choices"][0]["message"]["content"]


def ask_gemini(system_prompt, user_text):
    config = current_app.config
    response = requests.post(
        GEMINI_URL.format(model=config["GEMINI_MODEL"]),
        headers={"x-goog-api-key": config["GEMINI_API_KEY"]},
        json={
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_text}]}],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
                "responseSchema": GEMINI_BILL_SCHEMA,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        },
        timeout=config["LLM_TIMEOUT_SECONDS"],
    )
    if response.status_code != 200:
        raise LLMError(f"Gemini returned {response.status_code}")
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]


def available_providers():
    config = current_app.config
    providers = []
    if config["GROQ_API_KEY"]:
        providers.append(("groq", ask_groq))
    if config["GEMINI_API_KEY"]:
        providers.append(("gemini", ask_gemini))
    return providers
