"""
基础对比路由

包含：
- 文本对比接口
- 标点对比接口
- 健康检查
- 测试对齐
"""
from fastapi import APIRouter, HTTPException, status

from app.services.text_compare import text_comparison_service
from app.services.punctuation_analysis import punctuation_analysis_service
from app.services.collation_service import collation_service

from .models import (
    ComparisonRequest,
    ComparisonResponse,
    PunctuationComparisonRequest,
)

router = APIRouter()


@router.post("/compare", response_model=ComparisonResponse)
async def compare_texts(request: ComparisonRequest):
    """
    文本对比接口（MVP版本）

    对比两个文本版本，返回字符级差异

    - **text1**: 第一个文本版本
    - **text2**: 第二个文本版本
    - **version1_name**: 版本1名称（可选）
    - **version2_name**: 版本2名称（可选）

    返回差异列表、统计信息和相似度
    """
    try:
        # 调用文本对比服务
        result = text_comparison_service.compare_texts(
            text1=request.text1,
            text2=request.text2,
            version1_name=request.version1_name,
            version2_name=request.version2_name
        )

        return ComparisonResponse(
            success=True,
            **result
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文本对比失败: {str(e)}"
        )


@router.post("/compare-punctuation")
async def compare_punctuation(request: PunctuationComparisonRequest):
    """
    标点对比接口（标点分析工作台）

    对比两个版本的标点符号

    - **text1**: 第一个文本版本（带标点）
    - **text2**: 第二个文本版本（带标点）
    - **version1_name**: 版本1名称（可选）
    - **version2_name**: 版本2名称（可选）

    返回完整的标点分析工作台数据
    """
    try:
        # 1. 进行专业的标点差异分析
        punctuation_analysis = punctuation_analysis_service.analyze_punctuation_differences(
            text1=request.text1,
            text2=request.text2,
            version1_name=request.version1_name,
            version2_name=request.version2_name
        )

        # 2. 进行基础的文本对比（获取diff信息）
        basic_result = text_comparison_service.compare_texts(
            text1=request.text1,
            text2=request.text2,
            version1_name=request.version1_name,
            version2_name=request.version2_name
        )

        # 3. 返回综合结果
        return {
            "success": True,
            "version1_name": request.version1_name,
            "version2_name": request.version2_name,
            "text1": request.text1,
            "text2": request.text2,
            "differences": basic_result["differences"],  # diff差异（用于可视化）
            "similarity": basic_result["similarity"],  # 相似度
            "punctuation_analysis": punctuation_analysis  # 标点分析工作台数据
        }

    except HTTPException:
        raise

    except Exception as e:
        import traceback
        print(f"[标点对比] 错误详情: {type(e).__name__}: {str(e)}")
        print(f"[标点对比] 完整堆栈:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"标点对比失败: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "message": "文本对比服务正常"
    }


@router.post("/test-alignment")
async def test_alignment():
    """
    测试逐句对齐功能（调试用）

    固定测试数据，验证返回格式
    """
    test_text1 = "阿毗达磨顺正理论卷第九 尊者紫贤造三藏法师玄奘奉诏译辩差别品第二之一"
    test_text2 = "阿毗达磨顺正理论卷第九 尊者众贤造三藏法师玄奘奉诏译辩差别品第二之一"

    result = collation_service.collate_texts(
        text1=test_text1,
        text2=test_text2,
        version1_name="高丽版（测试）",
        version2_name="福州版（测试）"
    )

    # 返回第一条对齐记录用于验证
    first_aligned = result['aligned_sentences'][0] if result.get('aligned_sentences') else None

    return {
        "success": True,
        "message": "测试数据",
        "aligned_count": len(result.get('aligned_sentences', [])),
        "first_sentence1": first_aligned['sentence1'] if first_aligned else None,
        "first_sentence2": first_aligned['sentence2'] if first_aligned else None,
        "sentence1_length": len(first_aligned['sentence1']) if first_aligned else 0,
        "sentence2_length": len(first_aligned['sentence2']) if first_aligned else 0,
        "has_sentence2": bool(first_aligned and first_aligned.get('sentence2')),
        "full_result": result
    }
