import SwiftUI
import Combine

// API_BASE_URL, ErrorDetail, und NetworkError sind jetzt in Constants.swift definiert.
// TradeRequest, TradeResponse sind spezifisch für TradeService.

class TradeService: ObservableObject {
    private var authManager: AuthManager
    private var cancellables = Set<AnyCancellable>()

    // API_BASE_URL wird jetzt aus Constants.swift verwendet.
    // Lokale Definitionen von ErrorDetail und NetworkError werden entfernt,
    // da sie jetzt in Constants.swift sind.

    init(authManager: AuthManager) {
        self.authManager = authManager
    }

    // TradeRequest und TradeResponse bleiben hier, da sie spezifisch für diesen Service sind.
    struct TradeRequest: Codable {
        let symbol: String
        let quantity: Double
        let price: Double
    }

    struct TradeResponse: Codable {
        let success: Bool
        let message: String?
        let trade_id: String?
        // Beachte: ErrorDetail ist jetzt global, falls die API es direkt in TradeResponse einbettet,
        // müsste hier `let error: ErrorDetail?` stehen, aber typischerweise ist es nicht so.
    }

    func buyStock(symbol: String, quantity: Double, price: Double, completion: @escaping (Result<TradeResponse, NetworkError>) -> Void) {
        executeTrade(endpoint: "/trades/buy", symbol: symbol, quantity: quantity, price: price, completion: completion)
    }

    func sellStock(symbol: String, quantity: Double, price: Double, completion: @escaping (Result<TradeResponse, NetworkError>) -> Void) {
        executeTrade(endpoint: "/trades/sell", symbol: symbol, quantity: quantity, price: price, completion: completion)
    }

    private func executeTrade(endpoint: String, symbol: String, quantity: Double, price: Double, completion: @escaping (Result<TradeResponse, NetworkError>) -> Void) {
        // Rufe zuerst einen frischen Token ab
        authManager.getFreshToken { [weak self] token in
            guard let self = self else { return }
            
            guard let validToken = token else {
                print("TradeService: Failed to get a fresh token or token is nil.")
                DispatchQueue.main.async {
                    completion(.failure(.requestFailed)) // Oder ein spezifischerer Auth-Fehler
                }
                return
            }

            guard let url = URL(string: "\(API_BASE_URL)\(endpoint)") else {
                DispatchQueue.main.async {
                    completion(.failure(.badURL))
                }
                return
            }

            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            request.setValue("Bearer \(validToken)", forHTTPHeaderField: "Authorization") // Verwende validToken
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")

            let tradeRequest = TradeRequest(symbol: symbol, quantity: quantity, price: price)
            guard let jsonData = try? JSONEncoder().encode(tradeRequest) else {
                DispatchQueue.main.async {
                    completion(.failure(.requestFailed)) // Fehler beim Kodieren des Requests
                }
                return
            }
            request.httpBody = jsonData

            URLSession.shared.dataTaskPublisher(for: request)
                .tryMap { output -> Data in
                    guard let httpResponse = output.response as? HTTPURLResponse else {
                        throw NetworkError.requestFailed // Kein HTTP-Response
                    }
                    print("TradeService: HTTP Status Code \(httpResponse.statusCode) for \(endpoint)")
                    if !(200...299).contains(httpResponse.statusCode) {
                        var performLogout = false
                        var errorToThrow: NetworkError
                        
                        if let errorDetail = try? JSONDecoder().decode(ErrorDetail.self, from: output.data) {
                            errorToThrow = NetworkError.serverError(message: "Serverfehler \(httpResponse.statusCode): \(errorDetail.detail)")
                        } else {
                            errorToThrow = NetworkError.httpError(statusCode: httpResponse.statusCode, data: output.data)
                        }
                        
                        if httpResponse.statusCode == 401 {
                            performLogout = true
                        }

                        if performLogout {
                            // Wichtig: Logout auf dem Main-Thread ausführen, da es @Published Properties im AuthManager aktualisiert
                            DispatchQueue.main.async {
                                self.authManager.logout()
                            }
                            // Sie könnten hier auch direkt einen Fehler werfen, der den Logout signalisiert,
                            // aber der Logout wird bereits ausgelöst. Der ursprüngliche Fehler wird trotzdem weitergegeben.
                        }
                        throw errorToThrow
                    }
                    return output.data
                }
                .decode(type: TradeResponse.self, decoder: JSONDecoder())
                .receive(on: DispatchQueue.main)
                .sink(receiveCompletion: { resultCompletion in
                    switch resultCompletion {
                    case .failure(let error):
                        if let networkError = error as? NetworkError {
                            completion(.failure(networkError))
                        } else {
                            // Fallback für andere Fehler (z.B. Dekodierungsfehler, die nicht NetworkError sind)
                            completion(.failure(NetworkError.decodingError)) 
                        }
                    case .finished:
                        break
                    }
                }, receiveValue: { response in
                    completion(.success(response))
                })
                .store(in: &self.cancellables) // self.cancellables verwenden
        }
    }
}


