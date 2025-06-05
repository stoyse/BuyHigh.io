import Foundation
import SwiftUI

// Defines the structure for a single asset
struct Asset: Codable, Identifiable {
    let id: Int
    let symbol: String
    let name: String
    let asset_type: String
    let default_price: Double
    let url: String?
    let image_url: String?
}

// Defines the structure for the API response
struct AssetsResponse: Codable {
    let success: Bool
    let assets: [Asset]?
    let message: String?
}

class AssetLoader: ObservableObject {
    @Published var assets: [Asset] = []
    @Published var isLoading = false
    @Published var errorMessage: String? = nil
    
    private var authManager: AuthManager

    init(authManager: AuthManager) {
        self.authManager = authManager
    }

    func loadAssets() {
        guard let token = authManager.idToken else {
            self.errorMessage = "Token not available. Please log in."
            return
        }
        
        // Debug: Print token info
        print("AssetLoader: Attempting to fetch assets")
        print("AssetLoader: Token available: \(token.prefix(20))...") // Only show first 20 chars for security
        
        guard let url = URL(string: "https://api.stoyse.hackclub.app/assets") else {
            self.errorMessage = "Invalid URL"
            return
        }
        
        // Debug: Print the constructed URL
        print("AssetLoader: Constructed URL: \(url.absoluteString)")

        isLoading = true
        errorMessage = nil

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        URLSession.shared.dataTask(with: request) { data, response, error in
            DispatchQueue.main.async {
                self.isLoading = false
                
                // Debug: Print response info
                if let httpResponse = response as? HTTPURLResponse {
                    print("AssetLoader: HTTP Status Code: \(httpResponse.statusCode)")
                }
                
                if let error = error {
                    print("AssetLoader: Network error: \(error.localizedDescription)")
                    self.errorMessage = "Failed to load data: \(error.localizedDescription)"
                    return
                }

                guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
                    print("AssetLoader: Invalid HTTP response or status code")
                    self.errorMessage = "Invalid response from server"
                    return
                }

                guard let data = data else {
                    print("AssetLoader: No data received")
                    self.errorMessage = "No data received"
                    return
                }
                
                // Debug: Print raw response
                if let rawString = String(data: data, encoding: .utf8) {
                    print("AssetLoader: Raw response: \(rawString)")
                }

                do {
                    // Try to decode as AssetsResponse first (if API returns wrapped response)
                    if let decodedResponse = try? JSONDecoder().decode(AssetsResponse.self, from: data) {
                        print("AssetLoader: Decoded response - success: \(decodedResponse.success)")
                        print("AssetLoader: Number of assets: \(decodedResponse.assets?.count ?? 0)")
                        
                        if decodedResponse.success {
                            self.assets = decodedResponse.assets ?? []
                        } else {
                            print("AssetLoader: Server returned failure: \(decodedResponse.message ?? "No message")")
                            self.errorMessage = decodedResponse.message ?? "Failed to load assets."
                        }
                    } else {
                        // Fallback: Try to decode as direct array of assets
                        let decodedAssets = try JSONDecoder().decode([Asset].self, from: data)
                        print("AssetLoader: Decoded direct array - Number of assets: \(decodedAssets.count)")
                        self.assets = decodedAssets
                    }
                } catch {
                    print("AssetLoader: JSON decode error: \(error.localizedDescription)")
                    self.errorMessage = "Failed to decode JSON: \(error.localizedDescription)"
                }
            }
        }.resume()
    }
}