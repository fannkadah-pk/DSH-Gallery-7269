use actix_multipart::Multipart;
use actix_web::{post, get, delete, web, HttpResponse, Responder};
use futures_util::StreamExt as _;
use serde::Serialize;
use std::io::Write;
use crate::db;
use std::fs;
use chrono::Utc;

#[derive(Serialize)]
struct Message { message: String }

#[post("/api/upload")]
async fn upload(mut payload: Multipart) -> impl Responder {
    // save uploads to uploads directory and record in sqlite
    fs::create_dir_all("uploads").ok();
    let conn = db::get_connection().unwrap();
    while let Some(item) = payload.next().await {
        if let Ok(mut field) = item {
            let content_disposition = field.content_disposition();
            if let Some(filename) = content_disposition.get_filename() {
                let safe = sanitize_filename::sanitize(&filename);
                let ts = Utc::now().format("%Y%m%d_%H%M%S").to_string();
                let unique = format!("{}_{}", ts, safe);
                let filepath = format!("uploads/{}", unique);
                let mut f = fs::File::create(&filepath).unwrap();
                while let Some(chunk) = field.next().await {
                    let data = chunk.unwrap();
                    f.write_all(&data).unwrap();
                }
                // TODO: insert metadata into DB
            }
        }
    }
    HttpResponse::Ok().json(Message { message: "Upload handled".into() })
}

#[get("/api/files")]
async fn get_files() -> impl Responder {
    // query database and return JSON of lists
    HttpResponse::Ok().json(serde_json::json!({"images": [], "videos": [], "audio": [], "documents": []}))
}

// other handlers would follow similar pattern, omitted for brevity

#[delete("/api/files/{id}")]
async fn delete_file(path: web::Path<i64>) -> impl Responder {
    let _id = path.into_inner();
    HttpResponse::Ok().json(Message{message:"deleted".into()})
}

#[get("/api/counts")]
async fn get_counts() -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({"images":0,"videos":0,"audio":0,"documents":0}))
}

#[post("/api/backup")]
async fn create_backup() -> impl Responder {
    HttpResponse::Ok().json(Message{message:"backup".into()})
}

#[post("/api/restore")]
async fn restore_data() -> impl Responder {
    HttpResponse::Ok().json(Message{message:"restore".into()})
}

#[get("/api/trash")]
async fn get_trash() -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({}))
}

#[post("/api/trash/{id}/restore")]
async fn restore_from_trash(path: web::Path<i64>) -> impl Responder {
    HttpResponse::Ok().json(Message{message:"restored".into()})
}

#[delete("/api/trash/{id}")]
async fn delete_permanently(path: web::Path<i64>) -> impl Responder {
    HttpResponse::Ok().json(Message{message:"perm deleted".into()})
}

#[post("/api/trash/restore-all")]
async fn restore_all_trash() -> impl Responder {
    HttpResponse::Ok().json(Message{message:"all restored".into()})
}