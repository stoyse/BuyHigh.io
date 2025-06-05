import Foundation
import Combine

// Asset Model
struct Asset: Codable, Identifiable {
    let id: Int
    let symbol: String
    let name: String
    let asset_type: String
    let default_price: Double
    let url: String?
    let image_url: String?
}

// AssetLoader Class
class AssetLoader: ObservableObject {
    @Published var assets: [Asset] = []
    @Published var isLoading: Bool = false
    @Published var errorMessage: String? = nil
    
    private var cancellables = Set<AnyCancellable>()
    
    func loadAssets() {
        guard let url = URL(string: "https://api.stoyse.hackclub.app/assets") else {
            self.errorMessage = "Invalid URL"
            return
        }
        
        self.isLoading = true
        self.errorMessage = nil
        
        URLSession.shared.dataTaskPublisher(for: url)
            .tryMap { output -> Data in
                guard let httpResponse = output.response as? HTTPURLResponse else {
                    throw URLError(.badServerResponse)
                }
                
                guard httpResponse.statusCode == 200 else {
                    throw URLError(.badServerResponse)
                }
                
                return output.data
            }
            .decode(type: [Asset].self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .sink(
                receiveCompletion: { [weak self] completion in
                    self?.isLoading = false
                    switch completion {
                    case .failure(let error):
                        self?.errorMessage = "Failed to load assets: \(error.localizedDescription)"
                        print("AssetLoader Error: \(error)")
                    case .finished:
                        self?.errorMessage = nil
                        print("Successfully loaded assets")
                    }
                },
                receiveValue: { [weak self] assets in
                    self?.assets = assets
                    print("Loaded \(assets.count) assets")
                }
            )
            .store(in: &cancellables)
    }
}