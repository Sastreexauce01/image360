### app/api/routes.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
import io
from app.services.stitching import StitchingService
from app.core.config import settings

router = APIRouter()

@router.post("/generate-360")
async def generate_360_image(
    images: List[UploadFile] = File(...),
    quality: Optional[str] = Form(settings.DEFAULT_QUALITY),
    format: Optional[str] = Form(settings.DEFAULT_FORMAT),
    resolution: Optional[str] = Form(settings.DEFAULT_RESOLUTION)
):
    """
    Génère une image panoramique 360° à partir d'une liste d'images
    
    - **images**: Liste d'images (2-20 fichiers)
    - **quality**: Qualité de traitement (low, medium, high)
    - **format**: Format de sortie (jpg, png)
    - **resolution**: Résolution finale (2K, 4K, 8K)
    """
    
    # Validation du nombre d'images
    if len(images) < 2:
        raise HTTPException(
            status_code=400,
            detail="Au moins 2 images sont requises"
        )
    
    if len(images) > settings.MAX_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {settings.MAX_FILES} images autorisées"
        )
    
    # Validation des paramètres
    if quality not in ["low", "medium", "high"]:
        raise HTTPException(
            status_code=400,
            detail="Qualité doit être: low, medium ou high"
        )
    
    if format not in ["jpg", "png"]:
        raise HTTPException(
            status_code=400,
            detail="Format doit être: jpg ou png"
        )
    
    if resolution not in ["2K", "4K", "8K"]:
        raise HTTPException(
            status_code=400,
            detail="Résolution doit être: 2K, 4K ou 8K"
        )
    
    try:
        # Validation des fichiers
        for image in images:
            if not image.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Le fichier {image.filename} n'est pas une image valide"
                )
        
        # Traitement avec le service de stitching
        stitching_service = StitchingService()
        result_image = await stitching_service.create_360_panorama(
            images=images,
            quality=quality,
            output_format=format,
            resolution=resolution
        )
        
        # Préparation de la réponse
        img_io = io.BytesIO()
        result_image.save(img_io, format=format.upper())
        img_io.seek(0)
        
        # Définition du type MIME
        media_type = f"image/{format}"
        filename = f"panorama_360.{format}"
        
        return StreamingResponse(
            io.BytesIO(img_io.read()),
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération: {str(e)}"
        )

@router.get("/supported-formats")
async def get_supported_formats():
    """Retourne les formats et options supportés"""
    return {
        "qualities": ["low", "medium", "high"],
        "formats": ["jpg", "png"],
        "resolutions": ["2K", "4K", "8K"],
        "max_files": settings.MAX_FILES,
        "max_file_size_mb": settings.MAX_FILE_SIZE // (1024 * 1024),
        "allowed_extensions": settings.ALLOWED_EXTENSIONS
    }
