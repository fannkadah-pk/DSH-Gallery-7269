package main

import (
    "database/sql"
    "encoding/json"
    "log"
    "net/http"
    "os"
    "path/filepath"

    _ "github.com/mattn/go-sqlite3"
    "github.com/gorilla/mux"
)

type FileRecord struct {
    ID           int    `json:"id"`
    Filename     string `json:"filename"`
    Originalname string `json:"originalname"`
    Filepath     string `json:"filepath"`
    FileType     string `json:"file_type"`
    Size         int64  `json:"size"`
    Mimetype     string `json:"mimetype"`
}

type Counts struct {
    Images    int `json:"images"`
    Videos    int `json:"videos"`
    Audio     int `json:"audio"`
    Documents int `json:"documents"`
}

func initDB() (*sql.DB, error) {
    os.MkdirAll("../database", os.ModePerm)
    db, err := sql.Open("sqlite3", "../database/gallery.db")
    if err != nil {
        return nil, err
    }
    schema, _ := os.ReadFile("../backend/schema.sql")
    db.Exec(string(schema))
    return db, nil
}

func getFiles(w http.ResponseWriter, r *http.Request) {
    db, _ := initDB()
    defer db.Close()

    rows, _ := db.Query("SELECT id, filename, originalname, filepath, file_type, size, mimetype FROM files WHERE deleted=0")
    defer rows.Close()

    var files []FileRecord
    for rows.Next() {
        var f FileRecord
        rows.Scan(&f.ID, &f.Filename, &f.Originalname, &f.Filepath, &f.FileType, &f.Size, &f.Mimetype)
        files = append(files, f)
    }
    json.NewEncoder(w).Encode(map[string]interface{}{"files": files})
}

func main() {
    r := mux.NewRouter()
    r.HandleFunc("/api/files", getFiles).Methods("GET")
    log.Println("Starting Go server on :9000")
    http.ListenAndServe(":9000", r)
}