#!/usr/bin/env python3
"""
Test-Script für die Hugging Face zu CoreML Konvertierung
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from download_and_convert_to_mlmodel import HuggingFaceToCoreMl

def test_small_model():
    """
    Testet die Konvertierung mit einem kleinen Modell
    """
    print("🧪 Teste Konvertierung mit DistilBERT...")
    
    try:
        # Verwende ein kleines, schnelles Modell zum Testen
        converter = HuggingFaceToCoreMl("distilbert-base-uncased")
        
        # Führe die Konvertierung aus
        output_path = converter.full_conversion_pipeline(
            max_length=64,  # Kleinere Sequenzlänge für schnellere Tests
            output_dir="./test_models"
        )
        
        print(f"✅ Test erfolgreich! Modell gespeichert unter: {output_path}")
        
        # Überprüfe, ob die Datei existiert
        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"📏 Modell-Größe: {size_mb:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {str(e)}")
        return False

def test_custom_model(model_name: str, max_length: int = 128):
    """
    Testet die Konvertierung mit einem benutzerdefinierten Modell
    
    Args:
        model_name: Name des zu testenden Modells
        max_length: Maximale Sequenzlänge
    """
    print(f"🧪 Teste Konvertierung mit {model_name}...")
    
    try:
        converter = HuggingFaceToCoreMl(model_name)
        output_path = converter.full_conversion_pipeline(
            max_length=max_length,
            output_dir="./custom_models"
        )
        
        print(f"✅ Konvertierung erfolgreich! Modell: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Konvertierung fehlgeschlagen: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starte Tests für Hugging Face zu CoreML Konvertierung")
    print("=" * 60)
    
    # Test 1: Standardtest mit kleinem Modell
    success = test_small_model()
    
    if success:
        print("\n🎉 Alle Tests erfolgreich!")
    else:
        print("\n💥 Tests fehlgeschlagen!")
        sys.exit(1)
    
    # Optional: Teste andere Modelle
    if len(sys.argv) > 1:
        custom_model = sys.argv[1]
        max_len = int(sys.argv[2]) if len(sys.argv) > 2 else 128
        
        print(f"\n🔧 Teste benutzerdefiniertes Modell: {custom_model}")
        test_custom_model(custom_model, max_len)
