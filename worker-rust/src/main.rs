use dotenvy::dotenv;
use std::env;
use axum::{routing::post, Router, Json};
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use tokio::net::TcpListener;


#[derive(Deserialize)]
struct Task {

    task_id: String, 
    code: String,
    file_path: Option<String>,
    #[serde(rename = "type")]
    task_type: Option<String>,
}


#[derive(Serialize)]
struct Insight {

    task_id: String,
    worker_id: String,
    issues: Vec<String>,
}


async fn analyse(Json(payload): Json<Task>, worker_id: String) -> Json<Insight> {
 
    let mut issues = Vec::new();

    for (i, line) in payload.code.lines().enumerate() {

        if line.contains("TODO") {
            issues.push(format!("TODO found in line {}", i + 1));
        }

        if line.contains("FIXME") {
            issues.push(format!("FIXME found in line {}", i + 1));
        }

        if line.len() > 100 {
            issues.push(format!("Line {} is too long (>{} chars)", i + 1, line.len()));
        }
    }

    Json(Insight { 
        
        task_id: payload.task_id, 
        worker_id,
        issues,
    })
}


#[tokio::main]
async fn main() {

    // Load env vars from .env if present
    dotenv().ok();

    // Get worker_id from env or default: "worker-01"
    let worker_id = env::var("WORKER_ID").unwrap_or_else(|_| "worker-01".to_string());

    // Get port from env or default: 5000
    let port = env::var("PORT").unwrap_or_else(|_| "5000".to_string());
    let port = port.parse::<u16>().unwrap_or(5000);

    // Set up Axum router: POST /analyse uses the analysis handler
    let app = Router::new()
        .route("/analyse", 
        post({
            let worker_id = worker_id.clone();
            move |payload| analyse(payload, worker_id.clone())
        })
    );

    // Set the address for the server
    let addr = SocketAddr::from(([127, 0, 0, 1], port));
    let listener = TcpListener::bind(addr).await.unwrap();
    println!("Worker {} running at http://{}", worker_id, addr);

    // Start the axum server
    axum::serve(listener, app)
        .await.unwrap();
}
