use axum::{
    extract::Json,
    response::IntoResponse,
    routing::{post, get},
    Router,
    Json as RespJson,
};
use serde::{Deserialize, Serialize};
use std::env;
use tokio::net::TcpListener;
use std::net::SocketAddr;

// Input structure for code analysis tasks
#[derive(Deserialize)]
struct Task {
    code: String,
}

// Output structure returned by this worker
#[derive(Serialize)]
struct Insight {
    review: String,
    worker_id: String,
    model: String,
    issues: Vec<String>,
}

// /analyse POST endpoint
async fn analyse(Json(task): Json<Task>) -> RespJson<Insight> {
    let mut issues = Vec::new();

    for (i, line) in task.code.lines().enumerate() {
        if line.contains("TODO") {
            issues.push(format!("TODO in line {}", i + 1));
        }
        if line.contains("FIXME") {
            issues.push(format!("FIXME in line {}", i + 1));
        }
        if line.len() > 100 {
            issues.push(format!("Line {} is too long (>{} chars)", i + 1, line.len()));
        }
    }

    let review = if issues.is_empty() {
        "Rust worker checked code, no issues found.".to_string()
    } else {
        format!("Rust worker checked code, found {} issue(s).", issues.len())
    };

    let worker_id = env::var("WORKER_ID").unwrap_or_else(|_| "rust-worker-01".to_string());
    let model = "static-checker-rust-1.0".to_string();

    RespJson(Insight {
        review,
        worker_id,
        model,
        issues,
    })
}

// /health GET endpoint (returns JSON)
async fn health() -> impl IntoResponse {
    RespJson(serde_json::json!({"status": "ok"}))
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        .route("/analyse", post(analyse))
        .route("/health", get(health));
    let addr: SocketAddr = "0.0.0.0:8080".parse().unwrap();
    let listener = TcpListener::bind(addr).await.unwrap();
    println!("Rust worker listening on {}", addr);
    axum::serve(listener, app.into_make_service()).await.unwrap();
}