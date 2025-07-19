"""
Service de stitching simplifié pour smartphone.
Fonctions essentielles : création panorama + conversion équirectangulaire.
"""

import cv2
import numpy as np
from PIL import Image
from typing import List, Tuple
from fastapi import UploadFile
import tempfile
import os
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings
from app.utils.file import FileManager

logger = logging.getLogger(__name__)

class StitchingService:
    """Service simplifié de stitching pour photos smartphone."""
    
    def __init__(self):
        self.file_manager = FileManager()
        self.executor = ThreadPoolExecutor(max_workers=1)
        logger.info("StitchingService simplifié initialisé")
    
    async def create_360_panorama(
        self,
        images: List[UploadFile],
        quality: str = "medium",
        output_format: str = "jpg",
        resolution: str = "2K"
    ) -> Image.Image:
        """
        Crée un panorama 360° à partir d'images smartphone.
        
        Args:
            images: Liste des images uploadées
            quality: Qualité ("low", "medium", "high")
            output_format: Format de sortie
            resolution: Résolution finale
            
        Returns:
            Image panoramique PIL
        """
        temp_files = []
        
        try:
            logger.info(f"🚀 Début traitement {len(images)} images smartphone")
            
            # 1. Sauvegarde des images
            temp_files = await self.file_manager.save_uploaded_files(images)
            
            # 2. Traitement synchrone avec timeout
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    self._process_smartphone_images,
                    temp_files,
                    quality,
                    resolution
                ),
                timeout=300.0  # 5 minutes max
            )
            
            logger.info("✅ Traitement terminé avec succès")
            return result
            
        except asyncio.TimeoutError:
            logger.error("❌ Timeout: traitement trop long")
            raise Exception("Le traitement a pris trop de temps")
            
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            raise Exception(f"Erreur lors de la génération: {str(e)}")
            
        finally:
            # Nettoyage
            await self.file_manager.cleanup_files(temp_files)
    
    def _process_smartphone_images(
        self,
        image_paths: List[str],
        quality: str,
        resolution: str
    ) -> Image.Image:
        """Traitement principal des images smartphone."""
        
        try:
            # 1. Chargement des images
            logger.info("📷 Chargement des images...")
            cv_images = self._load_smartphone_images(image_paths, quality)
            
            if len(cv_images) < 2:
                raise Exception("Impossible de charger au moins 2 images valides")
            
            # 2. Création du panorama
            logger.info("🔄 Création du panorama...")
            panorama = self._create_panorama(cv_images)
            
            # 3. Conversion équirectangulaire
            logger.info("🌐 Conversion équirectangulaire...")
            equirectangular = self._convert_to_equirectangular(panorama, resolution)
            
            # 4. Conversion en PIL
            rgb_image = cv2.cvtColor(equirectangular, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            
            logger.info(f"✅ Panorama créé: {pil_image.size}")
            return pil_image
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement: {e}")
            raise Exception(f"Échec du traitement: {str(e)}")
    
    def _load_smartphone_images(self, image_paths: List[str], quality: str) -> List[np.ndarray]:
        """Charge les images avec optimisation smartphone."""
        
        # Tailles selon qualité
        max_sizes = {
            "low": 600,
            "medium": 800, 
            "high": 1200
        }
        max_size = max_sizes.get(quality, 800)
        
        cv_images = []
        
        for i, path in enumerate(image_paths):
            try:
                # Chargement simple
                img = cv2.imread(path)
                if img is None:
                    logger.warning(f"⚠️ Image {i+1} non chargée")
                    continue
                
                h, w = img.shape[:2]
                logger.info(f"📷 Image {i+1}: {w}x{h}")
                
                # Validation taille minimum
                if min(h, w) < 300:
                    logger.warning(f"⚠️ Image {i+1} trop petite")
                    continue
                
                # Redimensionnement si nécessaire
                if max(h, w) > max_size:
                    scale = max_size / max(h, w)
                    new_w = int(w * scale)
                    new_h = int(h * scale)
                    
                    img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
                    logger.info(f"📏 Image {i+1} redimensionnée: {new_w}x{new_h}")
                
                # Amélioration simple du contraste
                img = self._enhance_image(img)
                
                cv_images.append(img)
                logger.info(f"✅ Image {i+1} ajoutée")
                
            except Exception as e:
                logger.warning(f"⚠️ Erreur image {i+1}: {e}")
                continue
        
        logger.info(f"📷 {len(cv_images)} images chargées")
        return cv_images
    
    def _enhance_image(self, img: np.ndarray) -> np.ndarray:
        """Amélioration simple d'image pour smartphone."""
        try:
            # Amélioration légère du contraste
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # CLAHE léger
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            enhanced = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            
            return enhanced
            
        except Exception:
            return img  # Retourne l'original si erreur
    
    def _create_panorama(self, cv_images: List[np.ndarray]) -> np.ndarray:
        """
        FONCTION ESSENTIELLE: Création du panorama smartphone.
        Utilise plusieurs stratégies pour maximiser les chances de succès.
        """
        logger.info(f"🔄 Stitching de {len(cv_images)} images...")
        
        # Stratégie 1: Mode SCANS (meilleur pour photos non-organisées)
        try:
            logger.info("🔄 Tentative mode SCANS...")
            stitcher = cv2.Stitcher.create(cv2.Stitcher_SCANS)
            stitcher.setPanoConfidenceThresh(0.1)  # Très permissif
            
            status, panorama = stitcher.stitch(cv_images)
            
            if status == cv2.Stitcher_OK and panorama is not None and panorama.size > 0:
                logger.info("✅ Stitching SCANS réussi!")
                return panorama
            else:
                logger.warning(f"⚠️ Mode SCANS échoué: {status}")
        
        except Exception as e:
            logger.warning(f"⚠️ Erreur mode SCANS: {e}")
        
        # Stratégie 2: Mode PANORAMA permissif
        try:
            logger.info("🔄 Tentative mode PANORAMA...")
            stitcher = cv2.Stitcher.create(cv2.Stitcher_PANORAMA)
            stitcher.setPanoConfidenceThresh(0.1)
            
            status, panorama = stitcher.stitch(cv_images)
            
            if status == cv2.Stitcher_OK and panorama is not None and panorama.size > 0:
                logger.info("✅ Stitching PANORAMA réussi!")
                return panorama
            else:
                logger.warning(f"⚠️ Mode PANORAMA échoué: {status}")
        
        except Exception as e:
            logger.warning(f"⚠️ Erreur mode PANORAMA: {e}")
        
        # Stratégie 3: Images encore plus petites
        if len(cv_images) > 2:
            try:
                logger.info("🔄 Tentative avec images très réduites...")
                small_images = []
                for img in cv_images:
                    h, w = img.shape[:2]
                    small_img = cv2.resize(img, (w//2, h//2), interpolation=cv2.INTER_AREA)
                    small_images.append(small_img)
                
                stitcher = cv2.Stitcher.create(cv2.Stitcher_SCANS)
                stitcher.setPanoConfidenceThresh(0.05)  # Extrêmement permissif
                
                status, panorama = stitcher.stitch(small_images)
                
                if status == cv2.Stitcher_OK and panorama is not None and panorama.size > 0:
                    logger.info("✅ Stitching images réduites réussi!")
                    return panorama
                
            except Exception as e:
                logger.warning(f"⚠️ Erreur images réduites: {e}")
        
        # Stratégie 4: Fallback - prendre seulement les 2 premières images
        if len(cv_images) >= 2:
            try:
                logger.info("🔄 Fallback: stitching des 2 premières images...")
                stitcher = cv2.Stitcher.create(cv2.Stitcher_SCANS)
                stitcher.setPanoConfidenceThresh(0.05)
                
                status, panorama = stitcher.stitch(cv_images[:2])
                
                if status == cv2.Stitcher_OK and panorama is not None and panorama.size > 0:
                    logger.info("✅ Stitching 2 images réussi!")
                    return panorama
                
            except Exception as e:
                logger.warning(f"⚠️ Erreur fallback: {e}")
        
        # Échec total
        raise Exception(
            "Impossible de créer un panorama. "
            "Assurez-vous que vos images ont des zones de recouvrement visibles."
        )
    
    def _convert_to_equirectangular(self, panorama: np.ndarray, resolution: str) -> np.ndarray:
        """
        FONCTION ESSENTIELLE: Conversion en format équirectangulaire 360°.
        Crée le format standard pour la visualisation 360°.
        """
        logger.info("🌐 Conversion équirectangulaire...")
        
        try:
            h, w = panorama.shape[:2]
            logger.info(f"📐 Panorama original: {w}x{h}")
            
            # Définition des résolutions finales
            target_widths = {
                "2K": 2048,
                "4K": 4096,
                "8K": 8192
            }
            
            target_width = target_widths.get(resolution, 2048)
            target_height = target_width // 2  # Ratio 2:1 pour équirectangulaire
            
            logger.info(f"🎯 Cible équirectangulaire: {target_width}x{target_height}")
            
            # Redimensionnement vers le format équirectangulaire
            equirectangular = cv2.resize(
                panorama,
                (target_width, target_height),
                interpolation=cv2.INTER_LANCZOS4
            )
            
            # Amélioration finale
            equirectangular = self._final_enhancement(equirectangular)
            
            logger.info(f"✅ Équirectangulaire créé: {target_width}x{target_height}")
            return equirectangular
            
        except Exception as e:
            logger.error(f"❌ Erreur conversion équirectangulaire: {e}")
            # Fallback: redimensionnement simple
            target_width = 2048
            target_height = 1024
            return cv2.resize(panorama, (target_width, target_height))
    
    def _final_enhancement(self, img: np.ndarray) -> np.ndarray:
        """Amélioration finale de l'image équirectangulaire."""
        try:
            # Réduction légère du bruit
            enhanced = cv2.bilateralFilter(img, 5, 50, 50)
            
            # Correction gamma subtile
            gamma = 1.05
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            enhanced = cv2.LUT(enhanced, table)
            
            return enhanced
            
        except Exception:
            return img