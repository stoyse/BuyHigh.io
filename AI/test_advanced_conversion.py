#!/usr/bin/env python3
"""
Test-Script für erweiterte Modell-Konvertierung (DeepSeek, Llama, etc.)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from download_and_convert_to_mlmodel import HuggingFaceToCoreMl

def test_deepseek_models():
    """
    Testet die Konvertierung mit DeepSeek Modellen
    """
    print("🧪 Teste DeepSeek Modelle...")
    
    deepseek_models = [
        # Kleine DeepSeek Modelle zum Testen
        "deepseek-ai/deepseek-coder-1.3b-base",
        # "deepseek-ai/deepseek-math-7b-base",  # Größer, nur wenn Speicher vorhanden
    ]
    
    for model_name in deepseek_models:
        print(f"\n🔧 Teste: {model_name}")
        try:
            converter = HuggingFaceToCoreMl(model_name, model_type="deepseek")
            
            # Nutze kleinere Sequenzlänge für große Modelle
            output_path = converter.full_conversion_pipeline(
                max_length=64,  # Reduziert für bessere Performance
                output_dir="./deepseek_models"
            )
            
            print(f"✅ DeepSeek Modell erfolgreich konvertiert: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ DeepSeek Test fehlgeschlagen für {model_name}: {str(e)}")
            if "authentication" in str(e).lower() or "token" in str(e).lower():
                print("💡 Hinweis: Dieses Modell benötigt möglicherweise einen Hugging Face Token")
                print("   Verwende: converter.download_model(use_auth_token='your_token')")
            continue
    
    return False

def test_llama_models():
    """
    Testet die Konvertierung mit Llama Modellen
    """
    print("🧪 Teste Llama Modelle...")
    
    llama_models = [
        # Kleine Llama-ähnliche Modelle
        "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        # "microsoft/DialoGPT-small",  # GPT-ähnlich, aber kleiner
    ]
    
    for model_name in llama_models:
        print(f"\n🦙 Teste: {model_name}")
        try:
            converter = HuggingFaceToCoreMl(model_name, model_type="llama")
            
            output_path = converter.full_conversion_pipeline(
                max_length=64,
                output_dir="./llama_models"
            )
            
            print(f"✅ Llama Modell erfolgreich konvertiert: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Llama Test fehlgeschlagen für {model_name}: {str(e)}")
            continue
    
    return False

def test_bert_with_wrapper():
    """
    Testet BERT Modelle mit dem neuen Wrapper
    """
    print("🧪 Teste BERT Modelle mit Wrapper...")
    
    bert_models = [
        "distilbert-base-uncased",
        "bert-base-uncased",
    ]
    
    for model_name in bert_models:
        print(f"\n🤖 Teste: {model_name}")
        try:
            converter = HuggingFaceToCoreMl(model_name, model_type="bert")
            
            output_path = converter.full_conversion_pipeline(
                max_length=128,
                output_dir="./bert_models"
            )
            
            print(f"✅ BERT Modell erfolgreich konvertiert: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ BERT Test fehlgeschlagen für {model_name}: {str(e)}")
            continue
    
    return False

def test_custom_model_with_token(model_name: str, auth_token: str = None):
    """
    Testet ein benutzerdefiniertes Modell mit optionalem Auth Token
    
    Args:
        model_name: Name des zu testenden Modells
        auth_token: Optional Hugging Face Token
    """
    print(f"🧪 Teste benutzerdefiniertes Modell: {model_name}")
    
    try:
        converter = HuggingFaceToCoreMl(model_name, model_type="auto")
        
        # Lade Modell mit optionalem Token
        if auth_token:
            converter.download_model(use_auth_token=auth_token)
            
            # Führe den Rest der Pipeline aus
            sample_input = converter.create_sample_input(64)
            converter.trace_model(sample_input)
            converter.script_model()
            
            output_path = converter.convert_to_coreml(
                input_shape=(1, 64),
                output_path=f"./custom_models/{model_name.replace('/', '_')}.mlpackage"
            )
        else:
            output_path = converter.full_conversion_pipeline(
                max_length=64,
                output_dir="./custom_models"
            )
        
        print(f"✅ Benutzerdefiniertes Modell erfolgreich konvertiert: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starte erweiterte Tests für Modell-Konvertierung")
    print("=" * 60)
    
    success_count = 0
    total_tests = 0
    
    # Test 1: BERT Modelle mit Wrapper
    print("\n📋 Test 1: BERT Modelle mit Wrapper")
    total_tests += 1
    if test_bert_with_wrapper():
        success_count += 1
    
    # Test 2: Llama Modelle (falls verfügbar)
    print("\n📋 Test 2: Llama Modelle")
    total_tests += 1
    if test_llama_models():
        success_count += 1
    
    # Test 3: DeepSeek Modelle (falls verfügbar und Token vorhanden)
    print("\n📋 Test 3: DeepSeek Modelle")
    total_tests += 1
    if test_deepseek_models():
        success_count += 1
    
    # Optional: Test mit benutzerdefiniertem Modell
    if len(sys.argv) > 1:
        custom_model = sys.argv[1]
        auth_token = sys.argv[2] if len(sys.argv) > 2 else None
        
        print(f"\n📋 Test 4: Benutzerdefiniertes Modell: {custom_model}")
        total_tests += 1
        if test_custom_model_with_token(custom_model, auth_token):
            success_count += 1
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print(f"🎯 Testergebnisse: {success_count}/{total_tests} Tests erfolgreich")
    
    if success_count == total_tests:
        print("🎉 Alle Tests erfolgreich!")
    elif success_count > 0:
        print("⚠️ Einige Tests erfolgreich, andere fehlgeschlagen")
    else:
        print("💥 Alle Tests fehlgeschlagen!")
        sys.exit(1)
    
    print("\n💡 Tipps für verschiedene Modelltypen:")
    print("- BERT/DistilBERT: Funktionieren meist out-of-the-box")
    print("- Llama Modelle: Benötigen oft mehr Speicher, verwende kleinere Varianten")
    print("- DeepSeek Modelle: Benötigen oft Hugging Face Token für den Zugriff")
    print("- Große Modelle: Reduziere max_length für bessere Performance")
