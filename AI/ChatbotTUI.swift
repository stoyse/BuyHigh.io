import Foundation
import CoreML

struct ChatbotTUI {
    let model: MLModel

    init(modelPath: String) throws {
        let modelURL = URL(fileURLWithPath: modelPath)
        self.model = try MLModel(contentsOf: modelURL)
    }

    func predictResponse(for input: String) -> String {
        do {
            let inputFeatures = try MLDictionaryFeatureProvider(dictionary: ["input_ids": input])
            let prediction = try model.prediction(from: inputFeatures)
            if let response = prediction.featureValue(for: "output")?.stringValue {
                return response
            } else {
                return "⚠️ Keine Antwort vom Modell."
            }
        } catch {
            return "❌ Fehler bei der Vorhersage: \(error.localizedDescription)"
        }
    }

    func startChat() {
        print("🤖 Willkommen beim CoreML Chatbot!")
        print("Geben Sie Ihre Nachricht ein (oder 'exit' zum Beenden):")

        while true {
            print("\n👤 Sie: ", terminator: "")
            guard let userInput = readLine(), !userInput.isEmpty else {
                print("⚠️ Bitte geben Sie eine Nachricht ein.")
                continue
            }

            if userInput.lowercased() == "exit" {
                print("👋 Auf Wiedersehen!")
                break
            }

            let response = predictResponse(for: userInput)
            print("🤖 Bot: \(response)")
        }
    }
}

// Hauptprogramm
do {
    let modelPath = "./coreml_models/.mlpackage" // Pfad zur CoreML Modell-Datei
    let chatbot = try ChatbotTUI(modelPath: modelPath)
    chatbot.startChat()
} catch {
    print("❌ Fehler beim Laden des Modells: \(error.localizedDescription)")
}
