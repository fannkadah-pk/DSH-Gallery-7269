import io.ktor.server.engine.*
import io.ktor.server.netty.*
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.request.*
import io.ktor.server.routing.*
import io.ktor.server.plugins.contentnegotiation.*
import io.ktor.serialization.kotlinx.json.*
import kotlinx.serialization.Serializable
import java.io.File
import java.sql.DriverManager

@Serializable
data class FileRecord(val id: Int, val filename: String, val originalname: String)

fun main() {
    embeddedServer(Netty, port = 8081) {
        install(ContentNegotiation) {
            json()
        }
        routing {
            get("/api/files") {
                val files = getFilesFromDb()
                call.respond(mapOf("files" to files))
            }
            post("/api/upload") {
                // handle multipart upload
                call.respond(mapOf("message" to "upload ok"))
            }
        }
    }.start(wait = true)
}

fun getFilesFromDb(): List<FileRecord> {
    val conn = DriverManager.getConnection("jdbc:sqlite:../database/gallery.db")
    val stmt = conn.createStatement()
    val rs = stmt.executeQuery("SELECT id, filename, originalname FROM files WHERE deleted=0")
    val list = mutableListOf<FileRecord>()
    while (rs.next()) {
        list += FileRecord(rs.getInt("id"), rs.getString("filename"), rs.getString("originalname"))
    }
    rs.close(); stmt.close(); conn.close()
    return list
}
