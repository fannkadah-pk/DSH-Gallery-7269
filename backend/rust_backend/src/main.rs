use actix_web::{web, App, HttpServer, Responder, HttpResponse};
mod db;
mod handlers;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // ensure database exists
    db::init_database().expect("failed to initialize database");

    HttpServer::new(|| {
        App::new()
            .service(handlers::upload)
            .service(handlers::get_files)
            .service(handlers::delete_file)
            .service(handlers::download_file)
            .service(handlers::get_counts)
            .service(handlers::create_backup)
            .service(handlers::restore_data)
            .service(handlers::get_trash)
            .service(handlers::restore_from_trash)
            .service(handlers::delete_permanently)
            .service(handlers::restore_all_trash)
    })
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}