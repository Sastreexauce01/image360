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
    quality: Optional[str] = Form("medium"),
    format: Optional[str] = Form("jpg")
):
    """
    Génère une image panoramique 360° à partir d'une liste d'images
    
    - **images**: Liste d'images (2-20 fichiers)
    - **quality**: Qualité de traitement (low, medium, high)
    - **format**: Format de sortie (jpg, png)
    """
    
    # Validation du nombre d'images
    if len(images) < 2:
        raise HTTPException(
            status_code=400,
            detail="Au moins 2 images sont requises"
        )
    
    if len(images) > getattr(settings, 'MAX_FILES', 20):
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {getattr(settings, 'MAX_FILES', 20)} images autorisées"
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
    
    try:
        # Validation des fichiers
        for image in images:
            if not image.content_type or not image.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Le fichier {image.filename} n'est pas une image valide"
                )
        
        # Traitement avec le service de stitching
        stitching_service = StitchingService()
        result_image = await stitching_service.create_360_panorama(
            images=images,
            quality=quality,
            output_format=format
        )
        
        # Préparation de la réponse
        img_io = io.BytesIO()
        
        # Correction du format pour PIL
        pil_format = "JPEG" if format.lower() in ["jpg", "jpeg"] else format.upper()
        result_image.save(img_io, format=pil_format, quality=85)
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
        "default_resolution": "2048x1024",
        "max_files": getattr(settings, 'MAX_FILES', 20),
        "max_file_size_mb": getattr(settings, 'MAX_FILE_SIZE', 10485760) // (1024 * 1024),
        "allowed_extensions": getattr(settings, 'ALLOWED_EXTENSIONS', [".jpg", ".jpeg", ".png"])
    }