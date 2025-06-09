import Foundation

struct TradeRequestData: Codable {
    let symbol: String
    let quantity: Double
    let price: Double
}

struct TradeResponse: Codable {
    let success: Bool
    let message: String
    let transactionId: Int?
    let newBalance: Double?
    // Weitere Felder können hier bei Bedarf hinzugefügt werden
}

enum TradeError: Error {
    case invalidURL
    case requestFailed(Error)
    case noData
    case decodingError(Error)
    case apiError(String)
    case httpError(Int)
    case authenticationTokenMissing
}

class TradeService {
    
    private let baseURL = "https://api.stoyse.hackclub.app/trade" // Passe dies ggf. an deine Backend-URL an

    func buyStock(symbol: String, quantity: Double, price: Double, authManager: AuthManager) async -> Result<TradeResponse, TradeError> {
        guard let token = authManager.idToken else {
            return .failure(.authenticationTokenMissing)
        }
        
        guard let url = URL(string: "\(baseURL)/buy") else {
            return .failure(.invalidURL)
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        let tradeData = TradeRequestData(symbol: symbol, quantity: quantity, price: price)
        
        do {
            request.httpBody = try JSONEncoder().encode(tradeData)
        } catch {
            return .failure(.decodingError(error)) // Hier eher ein Encoding-Fehler, aber zur Vereinfachung
        }
        
        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                return .failure(.apiError("Invalid response from server."))
            }

            guard (200...299).contains(httpResponse.statusCode) else {
                // Versuche, eine Fehlermeldung aus dem Body zu dekodieren
                if let errorResponse = try? JSONDecoder().decode(TradeResponse.self, from: data) {
                    return .failure(.apiError(errorResponse.message))
                }
                return .failure(.httpError(httpResponse.statusCode))
            }
            
            let decodedResponse = try JSONDecoder().decode(TradeResponse.self, from: data)
            if decodedResponse.success {
                return .success(decodedResponse)
            } else {
                return .failure(.apiError(decodedResponse.message))
            }
        } catch {
            return .failure(.requestFailed(error))
        }
    }

    func sellStock(symbol: String, quantity: Double, price: Double, authManager: AuthManager) async -> Result<TradeResponse, TradeError> {
        guard let token = authManager.idToken else {
            return .failure(.authenticationTokenMissing)
        }
        
        guard let url = URL(string: "\(baseURL)/sell") else {
            return .failure(.invalidURL)
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        
        let tradeData = TradeRequestData(symbol: symbol, quantity: quantity, price: price)
        
        do {
            request.httpBody = try JSONEncoder().encode(tradeData)
        } catch {
            return .failure(.decodingError(error)) // Hier eher ein Encoding-Fehler
        }
        
        do {
            let (data, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                return .failure(.apiError("Invalid response from server."))
            }

            guard (200...299).contains(httpResponse.statusCode) else {
                if let errorResponse = try? JSONDecoder().decode(TradeResponse.self, from: data) {
                    return .failure(.apiError(errorResponse.message))
                }
                return .failure(.httpError(httpResponse.statusCode))
            }
            
            let decodedResponse = try JSONDecoder().decode(TradeResponse.self, from: data)
            if decodedResponse.success {
                return .success(decodedResponse)
            } else {
                return .failure(.apiError(decodedResponse.message))
            }
        } catch {
            return .failure(.requestFailed(error))
        }
    }
}
