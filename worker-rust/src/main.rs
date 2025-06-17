use axum::{
    extract::Json,
    response::Json as RespJson,
    routing::post,
    Router,
};
use serde::{Deserialize, Serialize};
use std::env;


#[derive(Deserialize)]
struct Task {
    code: String,
}


#[derive(Serialize)]
struct Insight {
    review: String,
    worker_id: String,
    issues: Vec<String>,
}


async fn analyse(Json(task): Json<Task>) -> RespJson<Insight> {

    let mut issues = Vec::new();

    for (i, line) in task.code.lines().enumerate() {

        if line.contains("TODO") {

            issues.push(format!("TODO in line {}", i + 1));
        }

        if line.contains("FIXME") {

            issues.push(format!("FIXME in line {}", i + 1));
        }
    }

    let review = format!(
        "Rust worker checked code, found {} issue(s).",
        issues.len()
    );

    let worker_id = env::var("WORKER_ID").unwrap_or("rust-worker-01".to_string());

    RespJson(Insight {
        review,
        worker_id,
        issues,
    })
}

#[tokio::main]
async fn main() {

    let app = Router::new().route("/analyse", post(analyse));
    let port = std::env::var("PORT").unwrap_or("8080".into());
    let addr = format!("0.0.0.0:{}", port).parse().unwrap();
    
    println!("Rust worker listening on {}", addr);
    axum::Server::bind(&addr).serve(app.into_make_service()).await.unwrap();
}