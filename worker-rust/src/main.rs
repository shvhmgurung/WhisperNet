use axum::{routing::post, Router, Json};
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;


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
    println!("Hello, world!");
}
