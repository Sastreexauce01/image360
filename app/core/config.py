### app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Configuration de l'application
    APP_NAME: str = "Image 360° Generator"
    DEBUG: bool = False
    
    # Configuration des uploads
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_FILES: int = 20
    ALLOWED_EXTENSIONS: list = [".jpg", ".jpeg", ".png", ".tiff"]
    
    # Configuration du traitement
    TEMP_DIR: str = "/tmp"
    DEFAULT_QUALITY: str = "medium"
    DEFAULT_FORMAT: str = "jpg"
    DEFAULT_RESOLUTION: str = "2K"
    
    # Configuration OpenCV
    OPENCV_STITCHER_MODE: int = 1  # PANORAMA mode
    
    class Config:
        env_file = ".env"

settings = Settings()
