
// filepath: /Users/julianstosse/Developer/BuyHigh.io/BuyHigh/BuyHigh/Constants.swift
import Foundation

// Globale API-Basis-URL
let API_BASE_URL = "http://api.stoyse.hackclub.app"

// Globale Fehlerdefinitionen

// Definiert die Struktur für Fehlerdetails, die von der API zurückgegeben werden könnten.
struct ErrorDetail: Codable {
    let detail: String
}

// Enum für verschiedene Netzwerkfehler-Typen, die während API-Aufrufen auftreten können.
enum NetworkError: Error {
    case badURL
    case requestFailed
    case decodingError
    case noData
    case serverError(message: String)
    case httpError(statusCode: Int, data: Data?)

    var localizedDescription: String {
        switch self {
        case .badURL:
            return "Ungültige URL."
        case .requestFailed:
            return "Netzwerkanfrage fehlgeschlagen."
        case .decodingError:
            return "Fehler beim Dekodieren der Daten."
        case .noData:
            return "Keine Daten empfangen."
        case .serverError(let message):
            return "Serverfehler: \(message)"
        case .httpError(let statusCode, _):
            return "HTTP-Fehler mit Statuscode: \(statusCode)."
        }
    }
}
