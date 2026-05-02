"""
标点迁移 API 路由
"""
from fastapi import APIRouter, HTTPException

from app.services.punctuation_transfer_service import punctuation_transfer_service
from .models import (
    TransferRequest,
    TransferResponse,
    RemovePunctuationRequest,
    RemovePunctuationResponse,
    ExampleResponse
)

router = APIRouter()


@router.post("/transfer", response_model=TransferResponse)
async def transfer_punctuation(request: TransferRequest):
    """
    执行标点迁移

    将源文本的标点符号迁移到目标文本中
    """
    try:
        result = punctuation_transfer_service.transfer(
            source_text=request.source_text,
            target_text=request.target_text,
            preserve_existing_punctuation=request.preserve_existing
        )

        return TransferResponse(
            result_text=result.result_text,
            transferred_count=result.transferred_count,
            total_punctuation_count=result.total_punctuation_count,
            alignment_score=result.alignment_score,
            warnings=result.warnings
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"标点迁移失败: {str(e)}")


@router.post("/remove-punctuation", response_model=RemovePunctuationResponse)
async def remove_punctuation(request: RemovePunctuationRequest):
    """
    清除文本中的标点符号
    """
    try:
        original_length = len(request.text)
        result_text = punctuation_transfer_service.remove_punctuation(request.text)
        removed_count = original_length - len(result_text)

        return RemovePunctuationResponse(
            result_text=result_text,
            removed_count=removed_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清除标点失败: {str(e)}")


@router.get("/example", response_model=ExampleResponse)
async def get_example():
    """
    获取示例文本
    """
    example = punctuation_transfer_service.get_example_texts()
    return ExampleResponse(
        source=example["source"],
        target=example["target"]
    )
