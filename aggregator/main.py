from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx

WORKER_URLS = ["http://127.0.0.1:5000/analyse",]

app = FastAPI()


@app.post("/task")
async def handle_task(request: Request):
    
    # Parse the incoming JSON as a dict
    task = await request.json

    result = []

    # Send the same task to all workers, collect responses
    async with httpx.AsyncClient() as client:

        for url in WORKER_URLS:

            try:
                resp = await client.post(url, json=task, timeout=5)
                resp.raise_for_status()
                data = resp.json()
                result.append(data)

            except Exception as e:
                result.append({
                    "worker_id": url,
                    "error": str(e),
                    "issues": [],
                })
    
    # Aggeregrate: collect all issues from all workers
    all_issues = []

    for r in result:
        all_issues.extend(r.get("issues", []))

    response = {
        "task_id": task.get("task_id"),
        "total_workers": len(result),
        "all_issues": all_issues,
        "raw_worker_response": result,
    }

    return JSONResponse(content=response)




