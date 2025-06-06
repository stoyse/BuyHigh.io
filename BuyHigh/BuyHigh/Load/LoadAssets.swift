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

    func loadAssets() async {
        await loadAssetsAsync()
    }
    
    @MainActor
    private func loadAssetsAsync() async {
        // Get a fresh token
        guard let token = await authManager.getValidToken() else {
            self.errorMessage = "Authentication failed. Please log in again."
            return
        }
        
        print("AssetLoader: Using fresh token for API call")
        
        guard let url = URL(string: "https://api.stoyse.hackclub.app/assets") else {
            self.errorMessage = "Invalid URL"
            return
        }

        isLoading = true
        errorMessage = nil

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Add timeout
        request.timeoutInterval = 30.0

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                self.errorMessage = "Invalid response from server"
                self.isLoading = false
                return
            }
            
            print("AssetLoader: HTTP Status Code: \(httpResponse.statusCode)")
            
            // Handle different status codes
            switch httpResponse.statusCode {
            case 200:
                await handleSuccessResponse(data)
            case 401:
                self.errorMessage = "Authentication expired. Please log in again."
                authManager.logout()
            case 403:
                self.errorMessage = "Access denied. Please check your permissions."
            case 500...599:
                self.errorMessage = "Server error. Please try again later."
            default:
                self.errorMessage = "Unexpected error (Code: \(httpResponse.statusCode))"
            }
            
        } catch {
            print("AssetLoader: Network error: \(error.localizedDescription)")
            if error.localizedDescription.contains("timeout") {
                self.errorMessage = "Request timeout. Please check your connection."
            } else {
                self.errorMessage = "Network error: \(error.localizedDescription)"
            }
        }
        
        self.isLoading = false
    }
    
    private func handleSuccessResponse(_ data: Data) async {
        // Debug: Print raw response
        if let rawString = String(data: data, encoding: .utf8) {
            print("AssetLoader: Raw response: \(rawString)")
        }

        do {
            // Try to decode as AssetsResponse first
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
            self.errorMessage = "Failed to decode response: \(error.localizedDescription)"
        }
    }
}