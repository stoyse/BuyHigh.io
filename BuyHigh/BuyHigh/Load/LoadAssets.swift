import Foundation
import Combine

// API_BASE_URL, ErrorDetail, und NetworkError sind jetzt in Constants.swift definiert
// und sollten global verfügbar sein, wenn Constants.swift Teil des Targets ist.

class AssetLoader: ObservableObject {
    @Published var assets: [Asset] = []
    @Published var isLoading: Bool = false
    @Published var errorMessage: String? = nil

    private var authManager: AuthManager
    private var cancellables = Set<AnyCancellable>()

    init(authManager: AuthManager) {
        self.authManager = authManager
    }

    // Die Funktion fetchAssets wird so angepasst, dass sie den neuen API-Endpunkt verwendet
    // und die direkte Array-Antwort verarbeitet.
    // Der Parameter assetType wird entfernt, da der neue Endpunkt ihn nicht verwendet.
    func fetchAssets() {
        guard let token = authManager.idToken else {
            self.errorMessage = "Authentication token not available."
            // self.assets = [] // Assets nicht leeren, wenn nur Token fehlt, alte könnten noch nützlich sein
            return
        }

        guard let url = URL(string: "https://api.stoyse.hackclub.app/assets") else {
            self.errorMessage = "Invalid URL for assets."
            // self.assets = []
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("Bearer \\(token)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        self.isLoading = true
        self.errorMessage = nil

        URLSession.shared.dataTaskPublisher(for: request)
            .tryMap { output -> Data in
                guard let httpResponse = output.response as? HTTPURLResponse else {
                    throw NetworkError.requestFailed
                }
                print("AssetLoader: HTTP Status Code: \(httpResponse.statusCode)")
                if !(200...299).contains(httpResponse.statusCode) {
                    // Versuch, eine ErrorDetail-Struktur zu dekodieren, falls der Server eine JSON-Fehlermeldung sendet
                    if let errorDetail = try? JSONDecoder().decode(ErrorDetail.self, from: output.data) {
                         throw NetworkError.serverError(message: "Server error \(httpResponse.statusCode): \(errorDetail.detail)")
                    }
                    // Fallback, wenn keine ErrorDetail dekodiert werden konnte
                    throw NetworkError.httpError(statusCode: httpResponse.statusCode, data: output.data)
                }
                return output.data
            }
            // Dekodiere jetzt zu AssetsListAPIResponse.self
            .decode(type: AssetsListAPIResponse.self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .sink(receiveCompletion: { [weak self] completion in
                guard let strongSelf = self else { return }
                strongSelf.isLoading = false
                switch completion {
                case .failure(let error):
                    var performLogout = false
                    if let decodingError = error as? DecodingError {
                        strongSelf.errorMessage = "Error decoding assets: \\(decodingError.localizedDescription). \\(decodingError)"
                         print("AssetLoader DecodingError: \\(decodingError)")
                    } else if let networkError = error as? NetworkError {
                        switch networkError {
                        case .serverError(let message):
                            strongSelf.errorMessage = message
                            // Check if the error message indicates a 401 error
                            if message.contains("401") || message.lowercased().contains("invalid auth") || message.lowercased().contains("unauthorized") {
                                performLogout = true
                            }
                        case .httpError(let statusCode, _):
                            strongSelf.errorMessage = "Error fetching assets: HTTP \\(statusCode)"
                            if statusCode == 401 {
                                performLogout = true
                            }
                        default:
                            strongSelf.errorMessage = "Error fetching assets: \\(error.localizedDescription)"
                        }
                    } else {
                        // General error handling, could also check for specific NSError codes related to authentication
                        strongSelf.errorMessage = "Error fetching assets: \\(error.localizedDescription)"
                        // Korrigiert: Verwende 'as?' für die bedingte Typumwandlung zu NSError?
                        if let nsError = error as? NSError,
                           (nsError.domain == NSURLErrorDomain && (nsError.code == NSURLErrorUserCancelledAuthentication || nsError.code == NSURLErrorUserAuthenticationRequired)) {
                            performLogout = true
                        }
                    }
                    
                    // strongSelf.assets = [] // Consider clearing assets or leaving stale data based on UX preference
                    print("AssetLoader Error: \\(String(describing: strongSelf.errorMessage))")

                    if performLogout {
                        print("AssetLoader: Detected 401 error, performing logout.")
                        // Ensure logout is called on the main thread as it updates @Published properties
                        DispatchQueue.main.async {
                            strongSelf.authManager.logout()
                        }
                    }
                case .finished:
                    print("AssetLoader: Successfully completed asset fetch operation.")
                    break
                }
            }, receiveValue: { [weak self] apiResponse in
                // Die Antwort ist jetzt das AssetsListAPIResponse-Objekt.
                // Greife auf das 'assets'-Array innerhalb dieses Objekts zu.
                if apiResponse.success {
                    self?.assets = apiResponse.assets
                    if apiResponse.assets.isEmpty {
                        print("AssetLoader: No assets found in successful response (success: true, assets: []).")
                        // self?.errorMessage = "No assets available at the moment." // Optional, je nach gewünschtem UX
                    } else {
                        print("AssetLoader: Successfully fetched and decoded \(apiResponse.assets.count) assets.")
                    }
                } else {
                    self?.errorMessage = apiResponse.message ?? "Failed to fetch assets (success: false)."
                    // self?.assets = [] // Leeren, da success false ist
                    print("AssetLoader: API reported failure: \(String(describing: self?.errorMessage))")
                }
            })
            .store(in: &cancellables)
    }
}

// Definieren Sie AssetsListAPIResponse hier oder in einer globalen Datei wie Constants.swift
// Es ist besser, sie in einer Datei zu haben, die von allen relevanten Teilen des Codes erreicht wird.
// Wenn Sie sie hier definieren, stellen Sie sicher, dass sie nicht mit einer Definition
// an anderer Stelle kollidiert. Für dieses Beispiel füge ich sie hier ein,
// aber für ein echtes Projekt wäre Constants.swift oder eine dedizierte Model-Datei besser.

struct AssetsListAPIResponse: Codable {
    let success: Bool
    let assets: [Asset] // Stellt sicher, dass 'Asset' hier sichtbar ist (sollte es sein, wenn im selben Target)
    let message: String?
}

// Stellen Sie sicher, dass die 'Asset'-Struktur (aus Asset.swift) und 'ErrorDetail' (aus Constants.swift)
// korrekt definiert sind und Teil des App-Targets sind, damit sie hier verwendet werden können.
