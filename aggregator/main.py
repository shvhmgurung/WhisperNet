from fastapi import FastAPI, Request
import httpx
import os

app = FastAPI()

WORKER_URLS = os.getenv("WORKER_URLS", "").split(",")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/task")
async def distribute_task(request: Request):

    data = await request.json()
    results = []

    async with httpx.AsyncClient() as client:

        for url in WORKER_URLS:
            url = url.strip()

            if not url:
                continue

            try:
                resp = await client.post(url, json=data, timeout=30)
                results.append(resp.json())

            except Exception as e:
                
                results.append({"worker_url": url, "error": str(e)})
    return {"results": results}