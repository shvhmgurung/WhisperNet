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


async fn analyse(Json(payload): Json<Task>) -> Json<Insight> {
    
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
        worker_id: "worker-01".to_string(),
        issues,
    })
}

#[tokio::main]
async fn main() {

    // Set up Axum router: POST /analyse uses the analysis handler
    let app = Router::new()
        .route("/analyse", post(analyse));

    // Set the address for the server
    let addr = SocketAddr::from(([127, 0, 0, 1], 5000));
    let listener = TcpListener::bind(addr).await.unwrap();
    println!("Worker running at http://{}", addr);

    // Start the axum server
    axum::serve(listener, app)
        .await.unwrap();
}
