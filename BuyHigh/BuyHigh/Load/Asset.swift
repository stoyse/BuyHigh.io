import Foundation

struct Asset: Codable, Identifiable, Hashable {
    let id: Int // Geändert zu Int
    let symbol: String
    let name: String
    let assetType: String // Hinzugefügt
    let defaultPrice: Double // Umbenannt und Typ angepasst (Double für Preise)
    let url: String? // Hinzugefügt
    let imageUrl: String? // Hinzugefügt
    // currency bleibt vorerst weg, da nicht im Beispiel; kann später hinzugefügt werden.

    // CodingKeys, um JSON-Schlüssel auf Swift-Eigenschaften abzubilden
    enum CodingKeys: String, CodingKey {
        case id
        case symbol
        case name
        case assetType = "asset_type"
        case defaultPrice = "default_price"
        case url
        case imageUrl = "image_url"
    }

    // Implement Hashable manuell, wenn nötig, oder lasse es Swift synthetisieren,
    // wenn alle gespeicherten Eigenschaften Hashable sind.
    // Für Identifiable wird 'id' verwendet.
}

// AssetsResponse wird nicht mehr benötigt, da die API direkt ein Array [Asset] zurückgibt.
// struct AssetsResponse: Codable {
//     let success: Bool
//     let assets: [Asset]
//     let message: String?
// }
