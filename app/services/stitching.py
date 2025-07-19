### app/services/stitching.py
import cv2
import numpy as np
from PIL import Image
from typing import List
from fastapi import UploadFile
import tempfile
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.core.config import settings
from app.utils.file import FileManager

class StitchingService:
    def __init__(self):
        self.file_manager = FileManager()
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def create_360_panorama(
        self,
        images: List[UploadFile],
        quality: str = "medium",
        output_format: str = "jpg",
        resolution: str = "2K"
    ) -> Image.Image:
        """
        Crée un panorama 360° à partir d'une liste d'images
        """
        temp_files = []
        
        try:
            # Sauvegarde temporaire des images
            temp_files = await self.file_manager.save_uploaded_files(images)
            
            # Traitement en arrière-plan pour éviter le blocage
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self._process_images_sync,
                temp_files,
                quality,
                output_format,
                resolution
            )
            
            return result
            
        finally:
            # Nettoyage des fichiers temporaires
            await self.file_manager.cleanup_files(temp_files)
    
    def _process_images_sync(
        self,
        image_paths: List[str],
        quality: str,
        output_format: str,
        resolution: str
    ) -> Image.Image:
        """
        Traitement synchrone des images (exécuté dans un thread séparé)
        """
        
        # Chargement des images avec OpenCV
        cv_images = self._load_and_resize_images(image_paths, quality)
        
        if len(cv_images) < 2:
            raise ValueError("Impossible de charger suffisamment d'images valides")
        
        # Création du stitcher
        stitcher = cv2.Stitcher.create(settings.OPENCV_STITCHER_MODE)
        
        # Configuration du stitcher pour de meilleurs résultats
        stitcher.setPanoConfidenceThresh(0.3)
        
        # Stitching des images
        status, panorama = stitcher.stitch(cv_images)
        
        if status != cv2.Stitcher_OK:
            error_messages = {
                cv2.Stitcher_ERR_NEED_MORE_IMGS: "Pas assez d'images ou images non compatibles",
                cv2.Stitcher_ERR_HOMOGRAPHY_EST_FAIL: "Échec de l'estimation de l'homographie",
                cv2.Stitcher_ERR_CAMERA_PARAMS_ADJUST_FAIL: "Échec de l'ajustement des paramètres"
            }
            error_msg = error_messages.get(status, f"Erreur de stitching: {status}")
            raise ValueError(error_msg)
        
        # Conversion en format équirectangulaire
        equirectangular = self._convert_to_equirectangular(panorama)
        
        # Redimensionnement selon la résolution demandée
        resized = self._resize_for_resolution(equirectangular, resolution)
        
        # Post-traitement pour améliorer la qualité
        processed = self._post_process_image(resized)
        
        # Conversion en PIL Image
        rgb_image = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        
        return pil_image
    
    def _load_and_resize_images(self, image_paths: List[str], quality: str) -> List[np.ndarray]:
        """Charge et redimensionne les images selon la qualité"""
        cv_images = []
        
        # Définition des tailles selon la qualité
        max_dimensions = {
            "low": 1024,
            "medium": 2048,
            "high": 4096
        }
        max_dim = max_dimensions.get(quality, 2048)
        
        for path in image_paths:
            try:
                img = cv2.imread(path)
                if img is None:
                    continue
                
                # Redimensionnement si nécessaire
                height, width = img.shape[:2]
                if max(height, width) > max_dim:
                    if width > height:
                        new_width = max_dim
                        new_height = int(height * max_dim / width)
                    else:
                        new_height = max_dim
                        new_width = int(width * max_dim / height)
                    
                    img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
                
                cv_images.append(img)
                
            except Exception as e:
                print(f"Erreur lors du chargement de {path}: {e}")
                continue
        
        return cv_images
    
    def _convert_to_equirectangular(self, panorama: np.ndarray) -> np.ndarray:
        """Convertit le panorama en format équirectangulaire"""
        height, width = panorama.shape[:2]
        
        # Calcul des dimensions pour un ratio 2:1 (équirectangulaire)
        target_width = width
        target_height = width // 2
        
        if height != target_height:
            panorama = cv2.resize(
                panorama, 
                (target_width, target_height), 
                interpolation=cv2.INTER_LANCZOS4
            )
        
        return panorama
    
    def _resize_for_resolution(self, image: np.ndarray, resolution: str) -> np.ndarray:
        """Redimensionne l'image selon la résolution finale"""
        resolution_widths = {
            "2K": 2048,
            "4K": 4096,
            "8K": 8192
        }
        
        target_width = resolution_widths.get(resolution, 2048)
        target_height = target_width // 2
        
        return cv2.resize(
            image, 
            (target_width, target_height), 
            interpolation=cv2.INTER_LANCZOS4
        )
    
    def _post_process_image(self, image: np.ndarray) -> np.ndarray:
        """Post-traitement pour améliorer la qualité"""
        # Réduction du bruit
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        
        # Amélioration du contraste
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Application de CLAHE sur le canal L
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        
        # Reconstruction de l'image
        enhanced = cv2.merge([l, a, b])
        result = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return resul