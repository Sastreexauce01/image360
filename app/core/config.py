"""
Configuration de l'application Image 360°.

Ce module contient tous les paramètres de configuration
pour l'API de génération d'images panoramiques.
"""

from pydantic_settings import BaseSettings
from typing import List
import tempfile
import os

class Settings(BaseSettings):
    """Configuration principale de l'application."""
    
    # Configuration de l'application
    APP_NAME: str = "Image 360° Generator"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    
    # Configuration des uploads
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB par fichier
    MAX_FILES: int = 20
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".tiff", ".webp"]
    
    # Configuration du répertoire temporaire
    TEMP_DIR: str = tempfile.gettempdir()
    
    # Configuration par défaut du traitement
    DEFAULT_QUALITY: str = "medium"
    DEFAULT_FORMAT: str = "jpg"
    DEFAULT_RESOLUTION: str = "2K"
    
    # Configuration OpenCV
    OPENCV_STITCHER_MODE: int = 1  # cv2.Stitcher_PANORAMA
    
    # Configuration des timeouts
    PROCESSING_TIMEOUT: int = 300  # 5 minutes en secondes
    
    # Configuration des formats supportés
    SUPPORTED_QUALITIES: List[str] = ["low", "medium", "high"]
    SUPPORTED_FORMATS: List[str] = ["jpg", "jpeg", "png", "webp"]
    SUPPORTED_RESOLUTIONS: List[str] = ["2K", "4K", "8K"]
    
    # Configuration des logs
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "app.log"
    
    def __post_init__(self):
        """Post-initialisation pour créer les répertoires nécessaires."""
        # Assure que le répertoire temporaire existe
        os.makedirs(self.TEMP_DIR, exist_ok=True)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instance globale des settings
settings = Settings()

# Post-initialisation manuelle (car __post_init__ ne fonctionne pas avec pydantic-settings)
os.makedirs(settings.TEMP_DIR, exist_ok=True)