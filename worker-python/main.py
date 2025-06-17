from fastapi import FastAPI, Request
import os

app = FastAPI()


@app.get("/health")
async def health():

    return {"status": "ok"}


@app.post("/analyse")
async def analyse(request: Request):

    data = await request.json()
    code = data.get("code", "")
    # Placeholder: Gemini integration comes later!
    insight = {
        "review": f"Received code of length {len(code)}.",
        "worker_id": os.getenv("WORKER_ID", "worker-python-01"),
        "issues": []
    }
    
    return insight