"""
古籍酷 OCR API：图片 → 识别文本。

后端代理模式：gj.cool 的凭据/Token 全在服务端，前端只上传图片。
"""
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import settings
from app.services.gjcool_ocr_service import GjcoolOCRService, GjcoolOCRError

router = APIRouter()


@router.get("/status")
async def ocr_status():
    """返回 OCR 是否已配置可用（供前端在未配置时友好提示，而非直接报错）。"""
    return {"enabled": GjcoolOCRService.is_configured()}


@router.post("/recognize")
async def ocr_recognize(img: UploadFile = File(..., description="待识别的古籍图片")):
    """对单张图片做古籍 OCR，返回识别文本与统计信息。"""
    if not GjcoolOCRService.is_configured():
        raise HTTPException(
            status_code=503, detail="OCR 未配置：请在 backend/.env 填写古籍酷凭据"
        )

    content_type = (img.content_type or "").lower()
    if content_type not in settings.OCR_ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"不支持的图片类型: {content_type or '未知'}；"
                f"支持 {', '.join(settings.OCR_ALLOWED_CONTENT_TYPES)}"
            ),
        )

    img_bytes = await img.read()
    if not img_bytes:
        raise HTTPException(status_code=400, detail="上传的图片为空")
    if len(img_bytes) > settings.OCR_MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=(
                f"图片过大（{len(img_bytes)} 字节），"
                f"上限 {settings.OCR_MAX_UPLOAD_SIZE} 字节"
            ),
        )

    try:
        result = await GjcoolOCRService.recognize(
            img_bytes, img.filename or "image", content_type
        )
    except GjcoolOCRError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    return {"success": True, **result}
