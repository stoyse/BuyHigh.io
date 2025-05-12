import os
import logging
from flask import current_app

class LogManager:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = LogManager()
        return cls._instance
    
    def __init__(self):
        self.configured = False
        self.logger = None
    
    def configure_logger(self, app):
        """Konfiguriert den Logger, stellt sicher dass er nur einmal konfiguriert wird."""
        if self.configured:
            return self.logger
            
        logger = logging.getLogger('buyhigh')
        
        # Bestehende Handler entfernen um Duplikate zu vermeiden
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Log-Level aus Konfiguration oder Default
        log_level = getattr(logging, app.config.get('LOG_LEVEL', 'DEBUG'))
        logger.setLevel(log_level)
        
        # Formatter für alle Handler
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
        
        # Datei-Handler wenn konfiguriert
        if app.config.get('LOG_TO_FILE', True):
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, 'app.log')
            
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # Console-Handler wenn konfiguriert
        if app.config.get('LOG_TO_CONSOLE', app.debug):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        self.logger = logger
        self.configured = True
        logger.info("Logger initialisiert mit eindeutiger Konfiguration.")
        
        return logger
    
    def get_logger(self):
        """Gibt den konfigurierten Logger zurück."""
        if not self.configured:
            if current_app:
                return self.configure_logger(current_app)
            else:
                # Fallback wenn keine App verfügbar
                return logging.getLogger('buyhigh')
        return self.logger
