"""
临时调试路由 - 检查对齐数据
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class DebugCompareRequest(BaseModel):
    text1: str
    text2: str

@router.post("/debug-compare")
async def debug_compare(request: DebugCompareRequest):
    """
    调试对比端点 - 返回完整的对齐数据
    """
    from app.services.collation_service import collation_service

    result = collation_service.collate_texts(
        text1=request.text1,
        text2=request.text2,
        version1_name="测试版本1",
        version2_name="测试版本2"
    )

    # 返回完整数据用于调试
    return {
        "success": True,
        "aligned_sentences_count": len(result.get('aligned_sentences', [])),
        "first_aligned": result['aligned_sentences'][0] if result.get('aligned_sentences') else None,
        "similarity": result['similarity'],
        "statistics": result['statistics'],
        **result
    }
