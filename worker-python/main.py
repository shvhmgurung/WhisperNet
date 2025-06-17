import os
import requests
import yaml
import google.auth
from google.auth.transport.requests import Request as GoogleAuthRequest
from fastapi import FastAPI, Request


def load_env_from_yaml(path="env.yaml"):
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
            for key, value in data.items():
                os.environ[key] = str(value)
    except Exception as e:
        print(f"Failed to load env.yaml: {e}")

load_env_from_yaml()

GCP_PROJECT = os.getenv("GCP_PROJECT_ID", "whispernet-final")
GCP_LOCATION = os.getenv("GCP_REGION", "us-central1")
MODEL_ID = os.getenv("MODEL_ID", "gemini-2.0-flash-001")

def get_google_access_token():
    credentials, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    credentials.refresh(GoogleAuthRequest())
    return credentials.token

def call_gemini_via_rest(prompt):
    url = f"https://{GCP_LOCATION}-aiplatform.googleapis.com/v1/projects/{GCP_PROJECT}/locations/{GCP_LOCATION}/publishers/google/models/{MODEL_ID}:generateContent"
    headers = {
        "Authorization": f"Bearer {get_google_access_token()}",
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 256,
            "temperature": 0.2
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        result = response.json()
        print("RAW GEMINI RESPONSE:", result) 
        candidates = result.get("candidates", [])
        if candidates:
            answer = candidates[0]["content"]["parts"][0].get("text", "")
        else:
            answer = "No response from model."
    except Exception as e:
        answer = f"Error from Gemini: {e}"
    return answer

app = FastAPI()

@app.get("/health")
async def health():
    """Health check endpoint for worker."""
    return {"status": "ok"}

@app.post("/analyse")
async def analyse(request: Request):
    """
    Accepts code for review and returns AI-powered analysis using Gemini.
    """
    data = await request.json()
    code = data.get("code", "")
    prompt = (
        "You are an expert software engineer. Please review the following code. "
        "List potential bugs, anti-patterns, and improvements in bullet points:\n\n"
        f"{code}"
    )
    review = call_gemini_via_rest(prompt)

    # Only extract bullet-pointed lines as issues, fallback to whole review if none found
    issues = []
    for line in review.split('\n'):
        l = line.strip()
        if l.startswith("- ") or l.startswith("* "):
            issues.append(l.lstrip("-* ").strip())
    if not issues and review:
        issues = [review.strip()]

    return {
        "review": review,
        "worker_id": f"worker-{MODEL_ID}",
        "model": MODEL_ID,
        "region": GCP_LOCATION,
        "issues": issues
    }