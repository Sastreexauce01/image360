import tempfile
import os
import aiofiles
from typing import List
from fastapi import UploadFile
from app.core.config import settings

class FileManager:
    def __init__(self):
        self.temp_dir = settings.TEMP_DIR
    
    async def save_uploaded_files(self, files: List[UploadFile]) -> List[str]:
        """
        Sauvegarde les fichiers uploadés dans des fichiers temporaires
        """
        temp_files = []
        
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
            
            # Reset du pointeur du fichier
            await file.seek(0)
        
        return temp_files
    
    async def cleanup_files(self, file_paths: List[str]):
        """
        Supprime les fichiers temporaires
        """
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Erreur lors de la suppression de {file_path}: {e}")
    
    def _get_file_extension(self, filename: str) -> str:
        """
        Extrait l'extension du fichier
        """
        if '.' in filename:
            return '.' + filename.split('.')[-1].lower()
        return '.jpg'  # Extension par défaut