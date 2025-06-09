import SwiftUI
import Foundation
import Combine

struct CardSelectStock: View {
    @StateObject private var assetLoader: AssetLoader
    @Binding var selectedSymbol: String?
    @State private var selectedAsset: Asset?
    @State private var searchText: String = ""
    @ObservedObject var stockLoader: StockDataLoader
    private let authManager: AuthManager
    
    init(selectedSymbol: Binding<String?>, authManager: AuthManager, stockLoader: StockDataLoader) {
        self._selectedSymbol = selectedSymbol
        self._assetLoader = StateObject(wrappedValue: AssetLoader(authManager: authManager))
        self.authManager = authManager
        self.stockLoader = stockLoader
    }
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            headerView
            searchBar
            contentView
            selectedAssetView
        }
        .frame(maxWidth: .infinity)
        .onAppear {
            Task {
                await assetLoader.loadAssets()
            }
        }
    }
    
    private var headerView: some View {
        Text("Select an Asset")
            .font(.title2)
            .fontWeight(.bold)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal)
    }
    
    private var searchBar: some View {
        HStack {
            Image(systemName: "magnifyingglass")
                .foregroundColor(.secondary)
            
            TextField("Search assets...", text: $searchText)
                .textFieldStyle(PlainTextFieldStyle())
                .frame(maxWidth: .infinity)
            
            if !searchText.isEmpty {
                Button(action: {
                    searchText = ""
                }) {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundColor(.secondary)
                }
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(Color(.systemGray6))
        .cornerRadius(10)
        .padding(.horizontal)
    }
    
    @ViewBuilder
    private var contentView: some View {
        if assetLoader.isLoading {
            loadingView
        } else if let errorMessage = assetLoader.errorMessage {
            errorView(errorMessage)
        } else if assetLoader.assets.isEmpty {
            emptyView
        } else {
            assetsGridView
        }
    }
    
    private var loadingView: some View {
        HStack {
            Spacer()
            ProgressView("Loading assets...")
                .foregroundColor(.secondary)
            Spacer()
        }
        .frame(maxWidth: .infinity)
        .padding()
    }
    
    private func errorView(_ message: String) -> some View {
        VStack {
            Image(systemName: "exclamationmark.triangle")
                .foregroundColor(.orange)
                .font(.title2)
            Text(message)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            Button("Retry") {
                Task {
                    await assetLoader.loadAssets()
                }
            }
            .buttonStyle(.bordered)
        }
        .frame(maxWidth: .infinity)
        .padding()
    }
    
    private var emptyView: some View {
        VStack {
            Image(systemName: "tray")
                .foregroundColor(.secondary)
                .font(.title2)
            Text("No assets available")
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
    }
    
    private var assetsGridView: some View {
        ScrollView {
            LazyVGrid(columns: [
                GridItem(.flexible(), spacing: 12),
                GridItem(.flexible(), spacing: 12)
            ], spacing: 12) {
                ForEach(filteredAssets) { asset in
                    AssetCard(
                        asset: asset,
                        isSelected: selectedAsset?.id == asset.id,
                        stockLoader: stockLoader,
                        onTap: {
                            selectAsset(asset)
                        }
                    )
                    .frame(maxWidth: .infinity)
                }
            }
            .padding(.horizontal)
        }
        .frame(maxWidth: .infinity)
    }
    
    private var filteredAssets: [Asset] {
        if searchText.isEmpty {
            return assetLoader.assets
        } else {
            return assetLoader.assets.filter { asset in
                asset.name.localizedCaseInsensitiveContains(searchText) ||
                asset.symbol.localizedCaseInsensitiveContains(searchText)
            }
        }
    }
    
    @ViewBuilder
    private var selectedAssetView: some View {
        if let selectedAsset = selectedAsset {
            VStack(alignment: .leading, spacing: 8) {
                Divider()
                
                HStack {
                    selectedAssetInfoView(selectedAsset)
                    Spacer()
                    selectedAssetPriceView(selectedAsset)
                }
                .frame(maxWidth: .infinity)
            }
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(12)
            .padding(.horizontal)
        }
    }
    
    private func selectedAssetInfoView(_ asset: Asset) -> some View {
        VStack(alignment: .leading) {
            Text("Selected Asset")
                .font(.caption)
                .foregroundColor(.secondary)
            Text(asset.name)
                .font(.headline)
            Text(asset.symbol)
                .font(.subheadline)
                .foregroundColor(.blue)
        }
    }
    
    private func selectedAssetPriceView(_ asset: Asset) -> some View {
        VStack(alignment: .trailing) {
            Text("Price")
                .font(.caption)
                .foregroundColor(.secondary)
            
            // Display currentPrice from stockLoader if it matches the selected asset
            // The actual loading is triggered in .onAppear of this view or when an asset is selected
            if selectedAsset?.symbol == asset.symbol, let price = stockLoader.currentPrice {
                Text("$\(price, specifier: "%.2f")")
                    .font(.headline)
                    .foregroundColor(.primary)
            } else {
                Text("Loading...")
                    .font(.headline)
                    .foregroundColor(.secondary)
                    .onAppear {
                        // Trigger loading when this view appears for the specific asset,
                        // but only if it's the currently selected one.
                        if selectedAsset?.symbol == asset.symbol {
                            stockLoader.loadCurrentPrice(symbol: asset.symbol)
                        }
                    }
            }
        }
    }
    
    private func selectAsset(_ asset: Asset) {
        selectedAsset = asset
        selectedSymbol = asset.symbol
        // Load stock data (current price) for the newly selected asset
        stockLoader.loadCurrentPrice(symbol: asset.symbol)
    }
}

struct AssetCard: View {
    let asset: Asset
    let isSelected: Bool
    @ObservedObject var stockLoader: StockDataLoader
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            cardContent
                .padding()
                .frame(maxWidth: .infinity)
                .frame(height: 120)
                .background(cardBackground)
                .overlay(cardBorder)
                .cornerRadius(12)
                .shadow(color: Color.primary.opacity(0.1), radius: isSelected ? 4 : 2, x: 0, y: isSelected ? 2 : 1)
                .scaleEffect(isSelected ? 1.02 : 1.0)
                .animation(.easeInOut(duration: 0.2), value: isSelected)
        }
        .buttonStyle(PlainButtonStyle())
    }
    
    private var cardContent: some View {
        VStack(alignment: .leading, spacing: 8) {
            headerView
            assetNameView
            Spacer()
            bottomView
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
    
    private var headerView: some View {
        HStack {
            symbolView
            Spacer()
            assetTypeTag
        }
        .frame(maxWidth: .infinity)
    }
    
    private var symbolView: some View {
        Text(asset.symbol)
            .font(.headline)
            .fontWeight(.bold)
            .foregroundColor(isSelected ? .white : .primary)
    }
    
    private var assetTypeTag: some View {
        Text(assetTypeDisplayName)
            .font(.caption)
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(assetTypeColor.opacity(0.2))
            .foregroundColor(isSelected ? .white : assetTypeColor)
            .cornerRadius(8)
    }
    
    private var assetNameView: some View {
        Text(asset.name)
            .font(.subheadline)
            .foregroundColor(isSelected ? .white.opacity(0.9) : .secondary)
            .lineLimit(2)
            .multilineTextAlignment(.leading)
    }
    
    private var bottomView: some View {
        HStack {
            priceView
            Spacer()
            selectionIndicator
        }
        .frame(maxWidth: .infinity)
    }
    
    @ViewBuilder
    private var selectionIndicator: some View {
        if isSelected {
            Image(systemName: "checkmark.circle.fill")
                .foregroundColor(.white)
                .font(.title3)
        }
    }
    
    private var cardBackground: Color {
        isSelected ? Color.blue : Color(.systemBackground)
    }
    
    private var cardBorder: some View {
        RoundedRectangle(cornerRadius: 12)
            .stroke(isSelected ? Color.blue : Color(.systemGray4), lineWidth: isSelected ? 2 : 1)
    }
    
    private var priceView: some View {
        VStack(alignment: .leading, spacing: 2) {
            priceText
            priceLabel
        }
    }
    
    private var priceText: some View {
        // Check if we have live price data for this specific asset
        let priceValue = if let currentPrice = stockLoader.getCurrentPrice(for: asset.symbol) {
            currentPrice
        } else {
            asset.default_price
        }
        
        return Text("$\(priceValue, specifier: "%.2f")")
            .font(.title3)
            .fontWeight(.semibold)
            .foregroundColor(isSelected ? .white : .primary)
            .onAppear {
                // Load current price for this asset when the card appears
                if !stockLoader.hasLoadedData(for: asset.symbol) {
                    stockLoader.loadCurrentPrice(symbol: asset.symbol)
                }
            }
    }
    
    private var priceLabel: some View {
        // Show "Live" if we have current price data for this specific asset, otherwise "Default"
        let labelText = stockLoader.hasLoadedData(for: asset.symbol) ? "Live" : "Default"
        return Text(labelText)
            .font(.caption2)
            .foregroundColor(isSelected ? .white.opacity(0.8) : .gray)
    }
    
    private var assetTypeDisplayName: String {
        switch asset.asset_type.lowercased() {
        case "stock":
            return "Stock"
        case "index":
            return "Index"
        case "crypto":
            return "Crypto"
        case "forex":
            return "Forex"
        default:
            return asset.asset_type.capitalized
        }
    }
    
    private var assetTypeColor: Color {
        switch asset.asset_type.lowercased() {
        case "stock":
            return .blue
        case "index":
            return .purple
        case "crypto":
            return .orange
        case "forex":
            return .green
        default:
            return .gray
        }
    }
}

// Preview
struct CardSelectStock_Previews: PreviewProvider {
    @State static var selectedSymbol: String? = nil
    
    static var previews: some View {
        let previewAuthManager = AuthManager()
        let previewStockLoader = StockDataLoader(authManager: previewAuthManager)
        
        Group {
            CardSelectStock(selectedSymbol: $selectedSymbol, authManager: previewAuthManager, stockLoader: previewStockLoader)
                .frame(maxWidth: .infinity)
                .preferredColorScheme(.light)
                .previewDisplayName("Light Mode")
            
            CardSelectStock(selectedSymbol: $selectedSymbol, authManager: previewAuthManager, stockLoader: previewStockLoader)
                .frame(maxWidth: .infinity)
                .preferredColorScheme(.dark)
                .previewDisplayName("Dark Mode")
        }
    }
}

#Preview {
    let mockAuthManager = AuthManager()
    let mockStockLoader = StockDataLoader(authManager: mockAuthManager)
    CardSelectStock(selectedSymbol: .constant("AAPL"), authManager: mockAuthManager, stockLoader: mockStockLoader)
}
