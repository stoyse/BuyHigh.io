import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM, 
    BitsAndBytesConfig,
    pipeline
)
from huggingface_hub import snapshot_download, hf_hub_download
import logging
import os
from pathlib import Path
from tqdm import tqdm
import psutil
import gc

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelStreamer:
    def __init__(self, cache_dir: str = "./model_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def get_memory_usage(self):
        """Aktuelle Speichernutzung in GB"""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024 / 1024
    
    def stream_download_model(
        self,
        model_name: str,
        use_auth_token: str = None,
        resume_download: bool = True
    ):
        """
        Streamt ein Modell von Hugging Face mit Progress-Tracking
        """
        logger.info(f"Starte Streaming-Download für: {model_name}")
        logger.info(f"Aktueller Speicherverbrauch: {self.get_memory_usage():.2f} GB")
        
        try:
            # Snapshot Download mit Progress
            local_dir = snapshot_download(
                repo_id=model_name,
                cache_dir=str(self.cache_dir),
                resume_download=resume_download,
                token=use_auth_token,
                local_files_only=False
            )
            
            logger.info(f"Modell heruntergeladen nach: {local_dir}")
            return local_dir
            
        except Exception as e:
            logger.error(f"Fehler beim Streaming-Download: {str(e)}")
            raise
    
    def load_quantized_model(
        self,
        model_name: str,
        quantization_type: str = "8bit",  # "8bit", "4bit", "none"
        device_map: str = "auto",
        max_memory: dict = None,
        use_auth_token: str = None
    ):
        """
        Lädt ein Modell mit Quantisierung für reduzierten Speicherverbrauch
        """
        logger.info(f"Lade quantisiertes Modell: {model_name}")
        logger.info(f"Quantisierung: {quantization_type}")
        logger.info(f"Speicher vor Laden: {self.get_memory_usage():.2f} GB")
        
        # Quantisierung konfigurieren
        quantization_config = None
        load_in_8bit = False
        load_in_4bit = False
        
        if quantization_type == "8bit":
            load_in_8bit = True
            logger.info("Verwende 8-bit Quantisierung")
            
        elif quantization_type == "4bit":
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
            logger.info("Verwende 4-bit Quantisierung mit NF4")
        
        try:
            # Tokenizer laden
            tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                cache_dir=str(self.cache_dir),
                token=use_auth_token
            )
            
            # Modell mit Quantisierung laden
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=quantization_config,
                load_in_8bit=load_in_8bit,
                device_map=device_map,
                max_memory=max_memory,
                torch_dtype=torch.float16 if quantization_type != "none" else torch.float32,
                cache_dir=str(self.cache_dir),
                token=use_auth_token,
                low_cpu_mem_usage=True,  # Reduziert CPU Memory Usage
                trust_remote_code=True
            )
            
            logger.info(f"Modell geladen! Speicher nach Laden: {self.get_memory_usage():.2f} GB")
            
            # Garbage Collection
            gc.collect()
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            
            return model, tokenizer
            
        except Exception as e:
            logger.error(f"Fehler beim Laden des quantisierten Modells: {str(e)}")
            raise
    
    def create_pipeline(
        self,
        model,
        tokenizer,
        task: str = "text-generation",
        max_length: int = 512,
        temperature: float = 0.7
    ):
        """
        Erstellt eine optimierte Pipeline für Inferenz
        """
        logger.info(f"Erstelle Pipeline für Task: {task}")
        
        pipe = pipeline(
            task,
            model=model,
            tokenizer=tokenizer,
            max_length=max_length,
            temperature=temperature,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            device_map="auto"
        )
        
        return pipe
    
    def benchmark_model(
        self,
        model,
        tokenizer,
        test_prompts: list = None
    ):
        """
        Benchmarkt das geladene Modell
        """
        if test_prompts is None:
            test_prompts = [
                "Hello, how are you?",
                "Explain artificial intelligence in simple terms.",
                "Write a short story about a robot."
            ]
        
        logger.info("Starte Model Benchmarking...")
        
        pipe = self.create_pipeline(model, tokenizer)
        
        for i, prompt in enumerate(test_prompts):
            logger.info(f"Test {i+1}: '{prompt[:50]}...'")
            
            start_memory = self.get_memory_usage()
            
            try:
                import time
                start_time = time.time()
                
                result = pipe(prompt, max_length=100, num_return_sequences=1)
                
                end_time = time.time()
                end_memory = self.get_memory_usage()
                
                logger.info(f"  Zeit: {end_time - start_time:.2f}s")
                logger.info(f"  Memory: {start_memory:.2f}GB -> {end_memory:.2f}GB")
                logger.info(f"  Output: {result[0]['generated_text'][:100]}...")
                
            except Exception as e:
                logger.error(f"  Fehler: {str(e)}")

def main():
    """
    Hauptfunktion zum Testen des Model Streamers
    """
    streamer = ModelStreamer()
    
    # Verschiedene Modelle zum Testen (von klein zu groß)
    test_models = [
        {
            "name": "microsoft/DialoGPT-small",
            "quantization": "8bit",
            "description": "Kleines Test-Modell"
        },
        {
            "name": "microsoft/DialoGPT-medium", 
            "quantization": "4bit",
            "description": "Mittleres Modell mit 4-bit Quantisierung"
        },
        # Auskommentiert wegen Größe:
        # {
        #     "name": "meta-llama/Llama-2-7b-chat-hf",
        #     "quantization": "4bit", 
        #     "description": "Llama 2 7B mit 4-bit Quantisierung"
        # }
    ]
    
    for model_config in test_models:
        try:
            logger.info(f"\n{'='*50}")
            logger.info(f"Teste Modell: {model_config['name']}")
            logger.info(f"Beschreibung: {model_config['description']}")
            logger.info(f"{'='*50}")
            
            # Modell laden
            model, tokenizer = streamer.load_quantized_model(
                model_name=model_config["name"],
                quantization_type=model_config["quantization"]
            )
            
            # Benchmark durchführen
            streamer.benchmark_model(model, tokenizer)
            
            # Memory cleanup
            del model, tokenizer
            gc.collect()
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            
            logger.info(f"Speicher nach Cleanup: {streamer.get_memory_usage():.2f} GB")
            
        except Exception as e:
            logger.error(f"Fehler beim Testen von {model_config['name']}: {str(e)}")
            continue

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Programm durch Benutzer abgebrochen")
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {str(e)}")
