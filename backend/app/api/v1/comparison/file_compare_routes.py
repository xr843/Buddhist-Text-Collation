"""
文件上传对比路由

包含：
- 文件上传对比接口（智能双模式）
"""
import time
import re
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import Optional

from app.services.text_compare import text_comparison_service
from app.services.punctuation_analysis import punctuation_analysis_service
from app.services.file_parser import file_parser_service
from app.services.collation_service import collation_service
from app.services.project_storage import project_storage

router = APIRouter()


def remove_empty_lines(text: str) -> str:
    """消除空行和多余空白，将换行合并为单个空格"""
    # 统一换行符：将\r\n和\r都转换为\n
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # 将多个连续换行（包括只有空白的行）替换为单个空格
    text = re.sub(r'\n[\s\n]*\n', ' ', text)
    # 将单个换行替换为空格
    text = re.sub(r'\n', ' ', text)
    # 将制表符替换为空格
    text = re.sub(r'\t', ' ', text)
    # 将多个连续空格合并为单个空格
    text = re.sub(r' +', ' ', text)
    # 去除全角空格
    text = text.replace('\u3000', ' ')
    # 再次合并空格
    text = re.sub(r' +', ' ', text)
    return text.strip()


@router.post("/compare-files")
async def compare_files(
    file1: UploadFile = File(..., description="版本A文件（txt或docx）"),
    file2: UploadFile = File(..., description="版本B文件（txt或docx）"),
    version1_name: Optional[str] = Form(None, description="版本A名称（可选）"),
    version2_name: Optional[str] = Form(None, description="版本B名称（可选）"),
    force_mode: Optional[str] = Form(None, description="强制模式：punctuation（标点对比）或 collation（文字校勘）"),
    project_title: Optional[str] = Form(None, description="项目标题（可选）"),
    project_id: Optional[str] = Form(None, description="项目ID（传入则更新现有项目）"),
    auto_save: bool = Form(True, description="是否自动保存项目"),
):
    """
    文件上传对比接口（智能双模式）

    上传两个文件，系统自动检测：
    - 纯文本一致 → 标点对比模式（包含AI分析）
    - 纯文本不一致 → 文字校勘模式（基础diff）

    可通过 force_mode 参数强制指定模式：
    - punctuation: 强制使用标点对比模式
    - collation: 强制使用文字校勘模式

    支持格式：txt（UTF-8/GBK/Big5）、docx
    文件限制：10MB、10万字以内
    """
    start_time = time.time()
    try:
        # 1. 解析两个文件
        print(f"[文件对比] 开始解析文件: {file1.filename}, {file2.filename}")
        if force_mode:
            print(f"[文件对比] 强制模式: {force_mode}")

        text1, auto_name1, char_count1 = await file_parser_service.parse_uploaded_file(file1)
        text2, auto_name2, char_count2 = await file_parser_service.parse_uploaded_file(file2)

        # 预处理：消除空行和多余空白
        text1 = remove_empty_lines(text1)
        text2 = remove_empty_lines(text2)

        # 使用用户提供的版本名，如果没有则使用文件名
        final_version1_name = version1_name or auto_name1
        final_version2_name = version2_name or auto_name2

        print(f"[文件对比] 解析完成: {final_version1_name}({char_count1}字), {final_version2_name}({char_count2}字)")

        # 2. 确定分析模式
        is_consistent, clean_text1, clean_text2 = text_comparison_service.check_pure_text_consistency(
            text1, text2
        )

        if force_mode == 'punctuation':
            use_punctuation_mode = True
            if not is_consistent:
                print("[文件对比] 强制标点对比模式 - 检测到文字有差异，将忽略文字差异，专注标点分析")
            else:
                print("[文件对比] 强制标点对比模式 - 文字一致")
        elif force_mode == 'collation':
            use_punctuation_mode = False
            print("[文件对比] 强制使用文字校勘模式")
        else:
            use_punctuation_mode = is_consistent
            print(f"[文件对比] 自动检测 - 纯文本一致性: {is_consistent}")

        # 3. 根据模式执行分析
        if use_punctuation_mode:
            return await _handle_punctuation_mode(
                text1, text2,
                final_version1_name, final_version2_name,
                file1, file2,
                char_count1, char_count2,
                start_time, auto_save, project_title, project_id
            )
        else:
            return await _handle_collation_mode(
                text1, text2,
                final_version1_name, final_version2_name,
                file1, file2,
                char_count1, char_count2,
                start_time, auto_save, project_title, project_id
            )

    except HTTPException:
        raise

    except Exception as e:
        import traceback
        print(f"[文件对比] 错误详情: {type(e).__name__}: {str(e)}")
        print(f"[文件对比] 完整堆栈:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件对比失败: {str(e)}"
        )


async def _handle_punctuation_mode(
    text1: str, text2: str,
    version1_name: str, version2_name: str,
    file1: UploadFile, file2: UploadFile,
    char_count1: int, char_count2: int,
    start_time: float, auto_save: bool,
    project_title: Optional[str], project_id: Optional[str]
):
    """处理标点对比模式"""
    print("[文件对比] 进入标点对比模式")

    # 进行专业的标点差异分析
    punctuation_analysis = punctuation_analysis_service.analyze_punctuation_differences(
        text1=text1,
        text2=text2,
        version1_name=version1_name,
        version2_name=version2_name
    )

    # 进行基础的文本对比
    basic_result = text_comparison_service.compare_texts(
        text1=text1,
        text2=text2,
        version1_name=version1_name,
        version2_name=version2_name
    )

    processing_time = round(time.time() - start_time, 2)

    result_data = {
        "success": True,
        "mode": "punctuation",
        "mode_description": "标点对比模式",
        "version1_name": version1_name,
        "version2_name": version2_name,
        "processing_time": processing_time,
        "file_info": {
            "file1_name": file1.filename,
            "file2_name": file2.filename,
            "char_count1": char_count1,
            "char_count2": char_count2
        },
        "text1": text1,
        "text2": text2,
        "differences": basic_result["differences"],
        "similarity": basic_result["similarity"],
        "punctuation_analysis": punctuation_analysis
    }

    # 自动保存标点对比项目
    if auto_save:
        try:
            title = project_title or f"{version1_name} vs {version2_name} 标点对比"
            saved_project = project_storage.save_punctuation_comparison(
                title=title,
                version1_info={
                    "name": version1_name,
                    "text": text1,
                    "char_count": char_count1,
                    "file": file1.filename,
                },
                version2_info={
                    "name": version2_name,
                    "text": text2,
                    "char_count": char_count2,
                    "file": file2.filename,
                },
                result=result_data,
                project_id=project_id,
            )
            result_data["project"] = {
                "id": saved_project["id"],
                "title": saved_project["title"],
                "created_at": saved_project["created_at"],
                "updated_at": saved_project["updated_at"],
            }
            print(f"[标点对比] 项目已保存: {saved_project['id']}")
        except Exception as e:
            print(f"[标点对比] 保存项目失败: {e}")

    return result_data


async def _handle_collation_mode(
    text1: str, text2: str,
    version1_name: str, version2_name: str,
    file1: UploadFile, file2: UploadFile,
    char_count1: int, char_count2: int,
    start_time: float, auto_save: bool,
    project_title: Optional[str], project_id: Optional[str]
):
    """处理文字校勘模式"""
    print("[文件对比] 进入文字校勘模式")

    # 使用文字校勘服务
    collation_result = collation_service.collate_texts(
        text1=text1,
        text2=text2,
        version1_name=version1_name,
        version2_name=version2_name
    )

    processing_time = round(time.time() - start_time, 2)

    result_data = {
        "success": True,
        "mode": "collation",
        "mode_description": "文字校勘模式",
        "version1_name": version1_name,
        "version2_name": version2_name,
        "processing_time": processing_time,
        "file_info": {
            "file1_name": file1.filename,
            "file2_name": file2.filename,
            "char_count1": char_count1,
            "char_count2": char_count2
        },
        **collation_result
    }

    # 自动保存两版本对勘项目
    if auto_save:
        try:
            title = project_title or f"{version1_name} vs {version2_name} 校勘"
            saved_project = project_storage.save_two_version_collation(
                title=title,
                base_info={
                    "name": version1_name,
                    "text": text1,
                    "char_count": char_count1,
                    "file": file1.filename,
                },
                collation_info={
                    "name": version2_name,
                    "text": text2,
                    "char_count": char_count2,
                    "file": file2.filename,
                },
                result=result_data,
                project_id=project_id,
            )
            result_data["project"] = {
                "id": saved_project["id"],
                "title": saved_project["title"],
                "created_at": saved_project["created_at"],
                "updated_at": saved_project["updated_at"],
            }
            print(f"[两版本对勘] 项目已保存: {saved_project['id']}")
        except Exception as e:
            print(f"[两版本对勘] 保存项目失败: {e}")

    return result_data
