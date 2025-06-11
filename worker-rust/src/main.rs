use axum::{routing::post, Router, Json};
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;

#[tokio::main]
async fn main() {
    println!("Hello, world!");
}


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