# WhisperNet

**Federated AI Code Review that respects your privacy.**

WhisperNet is a privacy-first, federated AI code review system that integrates directly with GitLab. Your code never leaves your infrastructure—AI workers run independently in secure environments and whisper insights back to an aggregator for judgment-free review.

---

## Demo

Try the live demo:

[WhisperNet Online Review UI](https://whispernet-aggregator-442496336144.us-central1.run.app/demo)

## Architecture

- **Aggregator:** FastAPI service that receives code, sends to workers, aggregates and returns results.
- **Workers:**
  - `whispernet-worker-python`: Python-based worker using Gemini 2.0 API via Vertex AI
  - `whispernet-worker-rust`: Rust-based static analysis
- **GitLab Integration:** Git webhook triggers federated review and updates `last_review.md` directly in the repo.
- **Frontend:** Alpine.js + HTML for live UI interaction

All workers and aggregator are deployed on Google Cloud Run.

---

## Features

- Federated multi-model AI reviews
- GitLab webhook integration
- Auto-posts reviews into Git repositories
- Privacy-respecting: code never leaves your server
- Real-time web interface with syntax-aware feedback
- Built with Rust, Python, FastAPI, Google Cloud, and Gemini via Vertex AI

---

## Quickstart

### Clone

```bash
git clone https://gitlab.com/your-org/whispernet
cd whispernet
```

### Setup Environment

Create `env.yaml` for the aggregator:

```yaml
WORKER_URLS: "https://worker-1-url,https://worker-2-url"
GITLAB_TOKEN: "your_private_token"
GITLAB_REPO: "https://gitlab.com/your-org/whispernet-demo"
GITLAB_FILE_PATH: "last_review.md"
```

Each worker requires their own `env.yaml` with:

```yaml
PROJECT_ID: "your-google-project-id"
REGION: "us-central1"
MODEL: "gemini-2.0-flash-001"
```

### Deploy to Cloud Run (or locally with Docker)

```bash
docker build -t whispernet-aggregator ./aggregator
docker run -p 8080:8080 whispernet-aggregator
```

Repeat for each worker directory.

---

## Webhook (GitLab)

To auto-trigger review on every commit:

- Add a GitLab webhook pointing to:

  ```
  https://whispernet-aggregator-xxx.run.app/gitlab_review
  ```

- Trigger: `Push events`
- Secret Token: Same as `GITLAB_TOKEN` in `env.yaml`

---

## Example Output

Reviews are aggregated like this:

```markdown
## worker-gemini-2.0-flash-001

- Division by zero detected
- Incorrect calculation: average instead of sum
- Missing input validation for `None`
- TypeError risks from non-numeric inputs

## rust-worker-01

- TODO in line 2
- FIXME in line 8
```

---

## Built With

- **FastAPI** – aggregator backend
- **Rust** – static analysis worker
- **Python** – Gemini API integration
- **Vertex AI** – Gemini 2.0 via Google Cloud
- **Docker** – containerized deploys
- **Alpine.js** – frontend interactivity
- **Cloud Run** – fully serverless deployment
- **GitLab** – source control + webhook integration

---

## Try It Out

- [Live Aggregator UI](https://whispernet-aggregator-442496336144.us-central1.run.app/demo)
- [Python Worker Cloud Endpoint](https://whispernet-worker-python-442496336144.us-central1.run.app/analyse)
- [Rust Worker Cloud Endpoint](https://whispernet-worker-rust-442496336144.us-central1.run.app/analyse)
- [GitLab Repo with Auto-Updated Review](https://gitlab.com/lx0xvn-group/whispernet-demo/-/blob/main/ai_review.md)

---
