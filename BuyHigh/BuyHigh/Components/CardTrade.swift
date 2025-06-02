import SwiftUI
import Combine 

struct CardTrade: View {
    @StateObject private var tradeService: TradeService 
    @ObservedObject var assetLoader: AssetLoader 

    @State private var selectedAssetID: Int? = nil // Geändert zu Int?
    @State private var quantityString: String = ""
    @State private var priceString: String = "" 

    @State private var tradeMessage: String = ""
    @State private var messageColor: Color = .primary
    @State private var isLoading: Bool = false
    @State private var showingAlert = false
    @State private var alertTitle = ""
    @State private var alertMessage = ""

    init(authManager: AuthManager, assetLoader: AssetLoader) { 
        _tradeService = StateObject(wrappedValue: TradeService(authManager: authManager))
        self.assetLoader = assetLoader
    }

    var body: some View {
        VStack(spacing: 15) {
            Text("Aktienhandel")
                .font(.title2)
                .fontWeight(.bold)
                .padding(.bottom, 5)

            // Picker für die Asset-Auswahl
            if assetLoader.assets.isEmpty {
                Text("Lade Aktien...")
                    .foregroundColor(.gray)
                if let errorMessage = assetLoader.errorMessage {
                    Text("Fehler: \(errorMessage)")
                        .foregroundColor(.red)
                        .font(.caption)
                }
            } else {
                Picker("Aktie auswählen", selection: $selectedAssetID) {
                    Text("Bitte Aktie auswählen").tag(Int?.none) // Geändert zu Int?.none für den optionalen Int-Typ
                    ForEach(assetLoader.assets) { asset in 
                        Text("\(asset.name) (\(asset.symbol))").tag(asset.id as Int?) // asset.id ist Int, tag als Int?
                    }
                }
                .padding(.horizontal)
                .onChange(of: selectedAssetID) { _ in // newValue explizit ignoriert, wenn nicht verwendet
                    updatePriceForSelectedAsset()
                }
            }
            
            // Symbol wird nun aus dem Picker abgeleitet, kein manuelles Textfeld mehr nötig
            // TextField("Aktiensymbol (z.B. AAPL)", text: $symbol)
            //     .textFieldStyle(RoundedBorderTextFieldStyle())
            //     .autocapitalization(.allCharacters)
            //     .padding(.horizontal)

            HStack {
                TextField("Menge", text: $quantityString)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .keyboardType(.decimalPad)
                
                TextField("Preis pro Aktie", text: $priceString)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .keyboardType(.decimalPad)
            }
            .padding(.horizontal)

            HStack(spacing: 20) {
                Button(action: executeBuy) {
                    Text("Kaufen")
                        .fontWeight(.semibold)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.green)
                        .foregroundColor(.white)
                        .cornerRadius(8)
                }
                .disabled(isLoading || !inputsValid())

                Button(action: executeSell) {
                    Text("Verkaufen")
                        .fontWeight(.semibold)
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.red)
                        .foregroundColor(.white)
                        .cornerRadius(8)
                }
                .disabled(isLoading || !inputsValid())
            }
            .padding(.horizontal)

            if isLoading {
                ProgressView()
                    .padding(.top, 10)
            }
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.1), radius: 5, x: 0, y: 2)
        .alert(isPresented: $showingAlert) {
            Alert(title: Text(alertTitle), message: Text(alertMessage), dismissButton: .default(Text("OK")))
        }
        .onAppear {
            if selectedAssetID == nil && !assetLoader.assets.isEmpty {
                 selectedAssetID = assetLoader.assets.first?.id
                 updatePriceForSelectedAsset()
            }
        }
    }

    private func updatePriceForSelectedAsset() {
        guard let assetId = selectedAssetID, // assetId ist jetzt Int
              let selectedAsset = assetLoader.assets.first(where: { $0.id == assetId }) else { // Vergleich Int == Int
            priceString = "" // Preis zurücksetzen, wenn keine Auswahl
            return
        }
        // Verwende defaultPrice aus dem Asset-Modell
        priceString = String(format: "%.2f", selectedAsset.defaultPrice)
    }

    private func getSelectedSymbol() -> String? {
        guard let assetId = selectedAssetID, // assetId ist jetzt Int
              let selectedAsset = assetLoader.assets.first(where: { $0.id == assetId }) else { // Vergleich Int == Int
            return nil
        }
        return selectedAsset.symbol.uppercased()
    }

    private func inputsValid() -> Bool {
        let quantity = Double(quantityString)
        let price = Double(priceString)
        return getSelectedSymbol() != nil &&
               quantity != nil && quantity! > 0 &&
               price != nil && price! > 0
    }

    private func validateAndGetData() -> (symbol: String, quantity: Double, price: Double)? {
        guard let symbol = getSelectedSymbol() else {
            showAlert(title: "Ungültige Eingabe", message: "Bitte wählen Sie eine Aktie aus.")
            return nil
        }
        guard let quantity = Double(quantityString), quantity > 0 else {
            showAlert(title: "Ungültige Eingabe", message: "Bitte geben Sie eine gültige, positive Menge ein.")
            return nil
        }
        guard let price = Double(priceString), price > 0 else {
            showAlert(title: "Ungültige Eingabe", message: "Bitte geben Sie einen gültigen, positiven Preis ein.")
            return nil
        }
        return (symbol, quantity, price)
    }
    
    private func showAlert(title: String, message: String) {
        self.alertTitle = title
        self.alertMessage = message
        self.showingAlert = true
    }

    private func executeBuy() {
        guard let tradeData = validateAndGetData() else { return }

        isLoading = true
        tradeService.buyStock(symbol: tradeData.symbol, quantity: tradeData.quantity, price: tradeData.price) { result in
            isLoading = false
            DispatchQueue.main.async {
                switch result {
                case .success(let response):
                    if response.success {
                        showAlert(title: "Erfolg", message: response.message ?? "Kauf erfolgreich!")
                    } else {
                        showAlert(title: "Fehler", message: response.message ?? "Kauf fehlgeschlagen.")
                    }
                case .failure(let error):
                    handleNetworkError(error, operation: "Kaufen")
                }
            }
        }
    }

    private func executeSell() {
        guard let tradeData = validateAndGetData() else { return }
        
        isLoading = true
        tradeService.sellStock(symbol: tradeData.symbol, quantity: tradeData.quantity, price: tradeData.price) { result in
            isLoading = false
            DispatchQueue.main.async {
                switch result {
                case .success(let response):
                    if response.success {
                        showAlert(title: "Erfolg", message: response.message ?? "Verkauf erfolgreich!")
                    } else {
                        showAlert(title: "Fehler", message: response.message ?? "Verkauf fehlgeschlagen.")
                    }
                case .failure(let error):
                    handleNetworkError(error, operation: "Verkaufen")
                }
            }
        }
    }
    
    private func handleNetworkError(_ error: NetworkError, operation: String) {
        let errorMessage: String
        switch error {
        case .serverError(let message):
            errorMessage = "Serverfehler: \(message)"
        case .decodingError:
            errorMessage = "Fehler beim Verarbeiten der Serverantwort."
        case .requestFailed:
            errorMessage = "Netzwerkanfrage fehlgeschlagen."
        case .badURL:
            errorMessage = "Ungültige API URL."
        case .noData:
            errorMessage = "Keine Daten vom Server erhalten."
        case .httpError(let statusCode, _):
            errorMessage = "HTTP Fehler: \(statusCode)."
        }
        showAlert(title: "Netzwerkfehler", message: "Fehler beim \(operation): \(errorMessage)")
    }
}

// Preview muss angepasst werden, um AssetLoader zu übergeben
// struct CardTrade_Previews: PreviewProvider {
//     static var previews: some View {
//         let authManager = AuthManager() 
//         let assetLoader = AssetLoader(authManager: authManager) 
//         // Beispiel-Asset für die Preview, das dem Asset-Modell entspricht
//         assetLoader.assets = [Asset(id: 1, symbol: "AAPL", name: "Apple Inc.", assetType: "stock", defaultPrice: 170.0, url: nil, imageUrl: nil)]
//
//         return CardTrade(authManager: authManager, assetLoader: assetLoader)
//             .environmentObject(authManager)
//             .padding()
//             .previewLayout(.sizeThatFits)
//     }
// }

