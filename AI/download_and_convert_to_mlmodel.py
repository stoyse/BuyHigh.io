import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer, AutoConfig, LlamaModel, LlamaTokenizer
import coremltools as ct
import numpy as np
import os
import warnings
from typing import Tuple, Optional, Dict, Any, Union
warnings.filterwarnings("ignore")

class ModelWrapper(nn.Module):
    """
    Wrapper-Klasse für Modelle, die ein Dictionary zurückgeben
    """
    def __init__(self, model, output_key='last_hidden_state'):
        super().__init__()
        self.model = model
        self.output_key = output_key
    
    def forward(self, input_ids):
        outputs = self.model(input_ids)
        if isinstance(outputs, dict):
            return outputs[self.output_key]
        elif hasattr(outputs, self.output_key):
            return getattr(outputs, self.output_key)
        else:
            # Fallback: Nimm das erste Element falls es ein Tupel/Liste ist
            if isinstance(outputs, (tuple, list)):
                return outputs[0]
            return outputs

class HuggingFaceToCoreMl:
    def __init__(self, model_name: str, cache_dir: Optional[str] = None, model_type: str = "auto"):
        """
        Initialisiert die Konvertierungsklasse
        
        Args:
            model_name: Name des Hugging Face Modells (z.B. 'bert-base-uncased')
            cache_dir: Optionales Verzeichnis für Model-Cache
            model_type: Typ des Modells ('auto', 'llama', 'deepseek', 'bert')
        """
        self.model_name = model_name
        self.cache_dir = cache_dir or "./models_cache"
        self.model_type = model_type.lower()
        self.tokenizer = None
        self.model = None
        self.wrapped_model = None
        self.traced_model = None
        self.scripted_model = None
        
    def _detect_model_type(self) -> str:
        """
        Erkennt automatisch den Modelltyp basierend auf dem Namen
        """
        model_name_lower = self.model_name.lower()
        
        if any(x in model_name_lower for x in ['llama', 'alpaca', 'vicuna']):
            return 'llama'
        elif any(x in model_name_lower for x in ['deepseek', 'deep-seek']):
            return 'deepseek'
        elif any(x in model_name_lower for x in ['bert', 'roberta', 'distilbert']):
            return 'bert'
        elif any(x in model_name_lower for x in ['gpt', 'bloom', 'opt']):
            return 'generative'
        else:
            return 'auto'
        
    def download_model(self, use_auth_token: Optional[str] = None) -> Tuple[nn.Module, any]:
        """
        Lädt das Modell und den Tokenizer von Hugging Face
        
        Args:
            use_auth_token: Optional Hugging Face Token für private Modelle
            
        Returns:
            Tuple von (model, tokenizer)
        """
        print(f"Lade Modell '{self.model_name}' von Hugging Face...")
        
        # Automatische Modelltypenerkennung
        if self.model_type == "auto":
            self.model_type = self._detect_model_type()
            print(f"🔍 Erkannter Modelltyp: {self.model_type}")
        
        try:
            # Spezielle Behandlung für verschiedene Modelltypen
            if self.model_type == 'llama':
                self._load_llama_model(use_auth_token)
            elif self.model_type == 'deepseek':
                self._load_deepseek_model(use_auth_token)
            else:
                self._load_standard_model(use_auth_token)
            
            # Wrapping für Dictionary-Outputs
            self._wrap_model_if_needed()
            
            print("✅ Modell erfolgreich geladen")
            return self.wrapped_model or self.model, self.tokenizer
            
        except Exception as e:
            print(f"❌ Fehler beim Laden des Modells: {str(e)}")
            raise
    
    def _load_llama_model(self, use_auth_token: Optional[str] = None):
        """Lädt Llama-spezifische Modelle"""
        try:
            # Versuche zuerst LlamaTokenizer
            self.tokenizer = LlamaTokenizer.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                use_auth_token=use_auth_token
            )
        except:
            # Fallback auf AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                use_auth_token=use_auth_token
            )
        
        # Pad Token setzen falls nicht vorhanden
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Modell laden mit reduzierten Parametern für CoreML
        self.model = AutoModel.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir,
            torch_dtype=torch.float32,
            device_map="cpu",  # Forciere CPU für CoreML Kompatibilität
            low_cpu_mem_usage=True,
            use_auth_token=use_auth_token
        )
    
    def _load_deepseek_model(self, use_auth_token: Optional[str] = None):
        """Lädt DeepSeek-spezifische Modelle"""
        # DeepSeek Modelle verwenden meist Standard AutoModel/AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir,
            use_auth_token=use_auth_token,
            trust_remote_code=True  # Wichtig für DeepSeek
        )
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.model = AutoModel.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir,
            torch_dtype=torch.float32,
            device_map="cpu",
            low_cpu_mem_usage=True,
            use_auth_token=use_auth_token,
            trust_remote_code=True
        )
    
    def _load_standard_model(self, use_auth_token: Optional[str] = None):
        """Lädt Standard-Modelle (BERT, etc.)"""
        # Tokenizer laden
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir,
            use_auth_token=use_auth_token
        )
        
        # Modell laden
        self.model = AutoModel.from_pretrained(
            self.model_name,
            cache_dir=self.cache_dir,
            torch_dtype=torch.float32,  # CoreML benötigt float32
            use_auth_token=use_auth_token
        )
    
    def _wrap_model_if_needed(self):
        """
        Wrapt das Modell falls es Dictionary-Outputs hat
        """
        # Modell in Evaluation-Modus setzen
        self.model.eval()
        
        # Test ob das Modell Dictionary zurückgibt
        sample_input = torch.randint(0, 100, (1, 10), dtype=torch.long)
        
        with torch.no_grad():
            try:
                output = self.model(sample_input)
                if isinstance(output, dict) or (hasattr(output, '__dict__') and 'last_hidden_state' in str(output)):
                    print("🔧 Modell gibt Dictionary zurück - verwende Wrapper")
                    self.wrapped_model = ModelWrapper(self.model, 'last_hidden_state')
                    self.wrapped_model.eval()
                else:
                    print("✅ Modell gibt Tensor zurück - kein Wrapper nötig")
                    self.wrapped_model = None
            except Exception as e:
                print(f"⚠️ Konnte Output-Typ nicht testen: {e}")
                # Fallback: Verwende Wrapper für Sicherheit
                self.wrapped_model = ModelWrapper(self.model, 'last_hidden_state')
                self.wrapped_model.eval()
    
    def create_sample_input(self, max_length: int = 128) -> torch.Tensor:
        """
        Erstellt Sample-Input für das Tracing
        
        Args:
            max_length: Maximale Sequenzlänge
            
        Returns:
            Sample input tensor
        """
        # Erstelle Sample-Text
        sample_text = "This is a sample text for model tracing."
        
        # Tokenisiere den Text
        inputs = self.tokenizer(
            sample_text,
            max_length=max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return inputs['input_ids']
    
    def trace_model(self, sample_input: torch.Tensor) -> torch.jit.TracedModule:
        """
        Traced das Modell mit torch.jit.trace
        
        Args:
            sample_input: Sample-Input für das Tracing
            
        Returns:
            Traced model
        """
        print("🔍 Starte Model Tracing...")
        
        # Verwende das gewrappte Modell falls vorhanden
        model_to_trace = self.wrapped_model if self.wrapped_model is not None else self.model
        
        with torch.no_grad():
            # Model tracing
            self.traced_model = torch.jit.trace(
                model_to_trace,
                sample_input,
                strict=False  # Weniger strikt für bessere Kompatibilität
            )
        
        print("✅ Model Tracing abgeschlossen")
        return self.traced_model
    
    def script_model(self) -> torch.jit.ScriptModule:
        """
        Konvertiert das traced model zu einem scripted model
        
        Returns:
            Scripted model
        """
        print("📝 Starte Model Scripting...")
        
        if self.traced_model is None:
            raise ValueError("Modell muss zuerst getraced werden")
        
        # Scripting des traced models
        self.scripted_model = torch.jit.script(self.traced_model)
        
        print("✅ Model Scripting abgeschlossen")
        return self.scripted_model
    
    def convert_to_coreml(self, 
                         input_shape: Tuple[int, ...],
                         output_path: str,
                         model_name: Optional[str] = None) -> str:
        """
        Konvertiert das scripted model zu CoreML
        
        Args:
            input_shape: Shape des Inputs (z.B. (1, 128) für Sequenzlänge 128)
            output_path: Pfad für die .mlmodel Datei
            model_name: Optionaler Name für das Modell
            
        Returns:
            Pfad zur gespeicherten .mlmodel Datei
        """
        print("🍎 Starte CoreML Konvertierung...")
        
        if self.scripted_model is None:
            raise ValueError("Modell muss zuerst gescripted werden")
        
        # Erstelle Input für CoreML Konvertierung
        sample_input = torch.randint(0, 1000, input_shape, dtype=torch.long)
        
        try:
            # Konvertierung zu CoreML
            coreml_model = ct.convert(
                self.scripted_model,
                inputs=[ct.TensorType(
                    name="input_ids",
                    shape=input_shape,
                    dtype=np.int32
                )],
                outputs=[ct.TensorType(name="output")],
                convert_to="mlprogram",  # Neues Format für bessere Performance
                compute_precision=ct.precision.FLOAT32
            )
            
            # Metadaten hinzufügen
            coreml_model.short_description = f"Hugging Face {self.model_name} Model"
            coreml_model.author = "Converted from Hugging Face"
            coreml_model.license = "See original model license"
            
            if model_name:
                coreml_model.user_defined_metadata["model_name"] = model_name
            coreml_model.user_defined_metadata["source"] = f"huggingface:{self.model_name}"
            
            # Speichere das CoreML Modell
            if not output_path.endswith('.mlpackage'):
                output_path = output_path.replace('.mlmodel', '.mlpackage')
            
            coreml_model.save(output_path)
            
            print(f"✅ CoreML Modell gespeichert unter: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Fehler bei CoreML Konvertierung: {str(e)}")
            raise
    
    def full_conversion_pipeline(self, 
                               max_length: int = 128,
                               output_dir: str = "./coreml_models") -> str:
        """
        Führt die komplette Konvertierungspipeline aus
        
        Args:
            max_length: Maximale Sequenzlänge
            output_dir: Ausgabeverzeichnis für das CoreML Modell
            
        Returns:
            Pfad zum konvertierten CoreML Modell
        """
        print("🚀 Starte vollständige Konvertierungspipeline...")
        
        # Erstelle Output-Verzeichnis
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Schritt 1: Modell downloaden
            self.download_model()
            
            # Schritt 2: Sample Input erstellen
            sample_input = self.create_sample_input(max_length)
            print(f"📐 Sample Input Shape: {sample_input.shape}")
            
            # Schritt 3: Model Tracing
            self.trace_model(sample_input)
            
            # Schritt 4: Model Scripting
            self.script_model()
            
            # Schritt 5: CoreML Konvertierung
            model_filename = f"{self.model_name.replace('/', '_')}.mlpackage"
            output_path = os.path.join(output_dir, model_filename)
            
            final_path = self.convert_to_coreml(
                input_shape=(1, max_length),
                output_path=output_path,
                model_name=self.model_name
            )
            
            print("🎉 Konvertierung erfolgreich abgeschlossen!")
            return final_path
            
        except Exception as e:
            print(f"💥 Fehler in der Konvertierungspipeline: {str(e)}")
            raise

def main():
    """
    Hauptfunktion zum Testen der Konvertierung
    """
    # Beispiel-Modelle zum Testen
    models_to_convert = [
        "distilbert-base-uncased",  # Kleineres Modell für schnelle Tests
        # "bert-base-uncased",      # Größeres Modell
        # "microsoft/DialoGPT-small",  # Anderer Modelltyp
        # "deepseek-ai/deepseek-coder-1.3b-base",  # DeepSeek Modell (benötigt Auth)
        # "TinyLlama/TinyLlama-1.1B-Chat-v1.0",    # Kleines Llama Modell
    ]
    
    for model_name in models_to_convert:
        print(f"\n{'='*60}")
        print(f"Konvertiere Modell: {model_name}")
        print(f"{'='*60}")
        
        try:
            converter = HuggingFaceToCoreMl(model_name, model_type="auto")
            output_path = converter.full_conversion_pipeline(
                max_length=128,
                output_dir="./coreml_models"
            )
            print(f"✅ Erfolgreich konvertiert: {output_path}")
            
        except Exception as e:
            print(f"❌ Fehler bei {model_name}: {str(e)}")
            continue

if __name__ == "__main__":
    main()