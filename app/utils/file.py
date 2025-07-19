"""
Gestionnaire de fichiers temporaires pour les uploads d'images.

Ce module fournit des utilitaires pour :
- Sauvegarder les fichiers uploadés
- Valider et sauvegarder les images validées
- Nettoyer les fichiers temporaires
"""

import tempfile
import os
import logging
from typing import List, Tuple
from fastapi import UploadFile
from app.core.config import settings

logger = logging.getLogger(__name__)

class FileManager:
    """Gestionnaire de fichiers temporaires pour les uploads d'images."""
    
    def __init__(self):
        # Utilise le répertoire temporaire du système (compatible Windows/Linux)
        self.temp_dir = getattr(settings, 'TEMP_DIR', None)
        
        # Si TEMP_DIR n'est pas défini ou n'existe pas, utilise le répertoire système
        if not self.temp_dir or not os.path.exists(self.temp_dir):
            self.temp_dir = tempfile.gettempdir()
        
        # Création du dossier s'il n'existe pas
        os.makedirs(self.temp_dir, exist_ok=True)
        
        logger.info(f"FileManager initialisé avec temp_dir: {self.temp_dir}")
    
    async def save_uploaded_files(self, files: List[UploadFile]) -> List[str]:
        """
        Sauvegarde les fichiers uploadés dans des fichiers temporaires.
        
        Args:
            files: Liste des fichiers uploadés
            
        Returns:
            Liste des chemins des fichiers temporaires
            
        Raises:
            ValueError: Si un fichier dépasse la taille limite
        """
        temp_files = []
        
        try:
            for i, file in enumerate(files):
                # Validation de la taille
                content = await file.read()
                if len(content) > settings.MAX_FILE_SIZE:
                    raise ValueError(f"Le fichier {file.filename} dépasse la taille limite")
                
                # Création du fichier temporaire
                suffix = self._get_file_extension(file.filename or f"image_{i}")
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=suffix,
                    dir=self.temp_dir
                )
                
                # Écriture du contenu
                temp_file.write(content)
                temp_file.close()
                
                temp_files.append(temp_file.name)
                logger.debug(f"Fichier sauvegardé: {temp_file.name}")
                
                # Reset du pointeur du fichier
                await file.seek(0)
            
            logger.info(f"{len(temp_files)} fichiers sauvegardés")
            return temp_files
            
        except Exception as e:
            # Nettoyage en cas d'erreur
            await self.cleanup_files(temp_files)
            logger.error(f"Erreur lors de la sauvegarde des fichiers: {e}")
            raise
    
    async def save_validated_images(self, validated_images: List[Tuple[UploadFile, bytes]]) -> List[str]:
        """
        Sauvegarde les images validées dans des fichiers temporaires.
        
        Args:
            validated_images: Liste de tuples (UploadFile, contenu_bytes)
            
        Returns:
            Liste des chemins des fichiers temporaires
            
        Raises:
            ValueError: Si erreur lors de la sauvegarde
        """
        temp_files = []
        
        try:
            for i, (file, content) in enumerate(validated_images):
                # Création du fichier temporaire
                suffix = self._get_file_extension(file.filename or f"image_{i}")
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=suffix,
                    dir=self.temp_dir
                )
                
                # Écriture du contenu validé
                temp_file.write(content)
                temp_file.close()
                
                temp_files.append(temp_file.name)
                logger.debug(f"Image validée sauvegardée: {temp_file.name}")
            
            logger.info(f"{len(temp_files)} images validées sauvegardées")
            return temp_files
            
        except Exception as e:
            # Nettoyage en cas d'erreur
            await self.cleanup_files(temp_files)
            logger.error(f"Erreur lors de la sauvegarde des images validées: {e}")
            raise ValueError(f"Erreur lors de la sauvegarde de l'image {i+1}: {str(e)}")
    
    async def cleanup_files(self, file_paths: List[str]):
        """
        Supprime les fichiers temporaires.
        
        Args:
            file_paths: Liste des chemins de fichiers à supprimer
        """
        cleaned_count = 0
        
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    cleaned_count += 1
                    logger.debug(f"Fichier supprimé: {file_path}")
            except Exception as e:
                # Log l'erreur mais ne lève pas d'exception
                logger.warning(f"Impossible de supprimer {file_path}: {e}")
        
        logger.info(f"{cleaned_count} fichiers temporaires nettoyés")
    
    def _get_file_extension(self, filename: str) -> str:
        """
        Extrait l'extension du fichier.
        
        Args:
            filename: Nom du fichier
            
        Returns:
            Extension du fichier (avec le point)
        """
        if '.' in filename:
            extension = '.' + filename.split('.')[-1].lower()
            # Validation des extensions supportées
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.webp']
            if extension in allowed_extensions:
                return extension
        
        return '.jpg'  # Extension par défaut