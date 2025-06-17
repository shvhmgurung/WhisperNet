from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import httpx
import os

app = FastAPI()

WORKER_URLS = [u.strip() for u in os.getenv("WORKER_URLS", "").split(",") if u.strip()]

@app.get("/health")
async def health():
    """Simple health check endpoint."""
    return {"status": "ok"}

@app.post("/analyse")
async def distribute_task(request: Request):
    """
    Accepts a code review request and distributes it to all configured worker endpoints.
    Aggregates their responses.
    """
    data = await request.json()
    results = []

    async with httpx.AsyncClient() as client:
        for url in WORKER_URLS:
            try:
                resp = await client.post(url, json=data, timeout=30)
                # Try to parse JSON
                try:
                    json_resp = resp.json()
                except Exception:
                    json_resp = {"error": "Invalid JSON response", "worker_url": url, "status_code": resp.status_code, "text": resp.text}
                # Tag with worker URL if no worker_id
                if "worker_id" not in json_resp:
                    json_resp["worker_url"] = url
                results.append(json_resp)
            except Exception as e:
                results.append({"worker_url": url, "error": str(e)})
    return {"results": results}


@app.post("/gitlab_review")
async def gitlab_review(request: Request):
    """
    Simulates a GitLab webhook: Accepts a POST with {"code": "..."}.
    Triggers a federated code review by all cloud workers.
    """
    data = await request.json()
    code = data.get("code", "# No code provided from GitLab.")

    results = []
    async with httpx.AsyncClient() as client:
        for url in WORKER_URLS:
            try:
                resp = await client.post(url, json={"code": code}, timeout=30)
                json_resp = resp.json()
                results.append(json_resp)
            except Exception as e:
                results.append({"worker_url": url, "error": str(e)})

        review_summary = ""
        for w in results:
            if "review" in w:
                review_summary += f"\n\n### {w.get('worker_id') or w.get('model','Worker')}\n{w['review']}\n"
            elif "error" in w:
                review_summary += f"\n\n### {w.get('worker_url','Worker')}\nError: {w['error']}\n"
        # Post summary to GitLab (async, but you can make it sync)
        status, resp = await post_to_gitlab_review(review_summary)
        print(f"GITLAB POST: {status}: {resp}")
        return {"results": results, "gitlab_status": status}

    


@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    return """
<!DOCTYPE html>
<html>
<head>
  <title>WhisperNet Demo</title>
  <style>
    body { font-family: sans-serif; max-width: 650px; margin: 3em auto; background: #f8fafc; }
    textarea { width: 100%; height: 170px; font-family: monospace; font-size: 1em; }
    button { padding: 0.5em 1.2em; font-size: 1.07em; margin-top: 0.5em; background: #6366f1; color: #fff; border: none; border-radius: 4px; }
    #result { background: #fff; padding: 1.3em 1.2em; margin-top: 1.2em; border-radius: 7px; border: 1px solid #e4e4e7; font-size:1.03em;}
    h1 { color: #6366f1; }
  </style>
  <script>
    function whisperReview() {
      return {
        code: `def calc_total(items):\n    # TODO: handle discounts\n    total = 0\n    for price in items:\n        total += price\n    return total / len(items)  # bug: division by zero if items is empty\n\n# FIXME: handle None inputs\n\nprint(calc_total([]))`,
        result: "",
        loading: false,
        async submit() {
          this.loading = true;
          this.result = "Reviewing…";
          try {
            const res = await fetch('/gitlab_review', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ code: this.code })
            });
            const data = await res.json();
            this.result = data.results.map(worker => {
              let output = `<div style='margin-bottom:2em;'>`;
              if (worker.worker_id || worker.model)
                output += `<b style='color:#6366f1'>${worker.worker_id || worker.model}</b><br>`;
              let review = (worker.review ?? "").toString().replace(/\\n/g, '<br>').replace(/\\*\\*([^*]+)\\*\\*/g, '<b>$1</b>');
              output += `<div style='margin:0.6em 0;'>${review}</div>`;
              if (worker.issues && worker.issues.length)
                output += '<ul>' + worker.issues.map(i => `<li>${i}</li>`).join('') + '</ul>';
              if (worker.error)
                output += `<span style='color:red'>Error: ${worker.error}</span>`;
              output += `</div>`;
              return output;
            }).join('') || '<i>No output from any worker.</i>';
          } catch (err) {
            this.result = "Error connecting to server.";
          } finally {
            this.loading = false;
          }
        }
      }
    }
  </script>
  <script src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
</head>
<body>
  <h1>WhisperNet Demo</h1>
  <div x-data="whisperReview()">
    <form @submit.prevent="submit">
      <label for="code">Paste code for federated AI review:</label><br>
      <textarea id="code" name="code" x-model="code"></textarea><br>
      <button type="submit" :disabled="loading" x-text="loading ? 'Reviewing…' : 'Review Code'"></button>
    </form>
    <div id="result" x-html="result"></div>
  </div>
</body>
</html>
    """


import base64

async def post_to_gitlab_review(content: str):
    import os, httpx
    token = os.getenv("GITLAB_TOKEN")
    project = os.getenv("GITLAB_PROJECT")
    branch = os.getenv("GITLAB_BRANCH", "main")
    filename = os.getenv("GITLAB_FILE", "ai_review/last_review.md")
    api_url = f"https://gitlab.com/api/v4/projects/{project.replace('/','%2F')}/repository/files/{filename.replace('/','%2F')}"
    headers = {"PRIVATE-TOKEN": token}
    # Try to get the file first to check if it exists
    async with httpx.AsyncClient() as client:
        resp = await client.get(api_url, params={"ref": branch}, headers=headers)
        exists = resp.status_code == 200
        data = {
            "branch": branch,
            "content": content,
            "commit_message": f"Update AI review file via aggregator",
        }
        if exists:
            # Must include last commit id for updates, but GitLab API will overwrite if not
            method = client.put
        else:
            method = client.post
        resp2 = await method(api_url, headers=headers, json=data)
        return resp2.status_code, resp2.text