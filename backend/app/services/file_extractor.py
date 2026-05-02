"""
文件内容提取服务
支持从多种文件格式中提取文本内容
"""
from pathlib import Path
from typing import Optional
import chardet
import tempfile
import os
from docx import Document
from PyPDF2 import PdfReader
from bs4 import BeautifulSoup
import markdown
from loguru import logger


def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    从文件内容中提取文本（便捷函数）

    Args:
        file_content: 文件的二进制内容
        filename: 文件名（用于判断文件类型）

    Returns:
        提取的文本内容，失败时返回空字符串
    """
    # 创建临时文件
    file_ext = Path(filename).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        tmp_file.write(file_content)
        tmp_path = Path(tmp_file.name)

    try:
        text, error = FileExtractor.extract(tmp_path, filename)
        if error:
            logger.warning(f"文件提取警告: {error}")
            return ""
        return text
    finally:
        # 清理临时文件
        if tmp_path.exists():
            os.unlink(tmp_path)


class FileExtractor:
    """文件内容提取器"""

    SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.docx', '.md', '.html'}
    MAX_TEXT_LENGTH = 5000  # 最大字符数限制

    @classmethod
    def extract(cls, file_path: Path, filename: str) -> tuple[str, Optional[str]]:
        """
        从文件中提取文本内容

        Args:
            file_path: 文件路径
            filename: 原始文件名（用于判断文件类型）

        Returns:
            (extracted_text, error_message)
            成功时返回 (文本内容, None)
            失败时返回 ("", 错误信息)
        """
        try:
            # 获取文件扩展名
            file_ext = Path(filename).suffix.lower()

            if file_ext not in cls.SUPPORTED_EXTENSIONS:
                return "", f"不支持的文件格式：{file_ext}。支持的格式：{', '.join(cls.SUPPORTED_EXTENSIONS)}"

            # 根据文件类型调用相应的提取方法
            if file_ext == '.txt':
                text = cls._extract_txt(file_path)
            elif file_ext == '.pdf':
                text = cls._extract_pdf(file_path)
            elif file_ext == '.docx':
                text = cls._extract_docx(file_path)
            elif file_ext == '.md':
                text = cls._extract_markdown(file_path)
            elif file_ext == '.html':
                text = cls._extract_html(file_path)
            else:
                return "", f"未实现的文件类型处理：{file_ext}"

            # 清理文本
            text = cls._clean_text(text)

            # 检查字符数限制
            if len(text) > cls.MAX_TEXT_LENGTH:
                return "", f"文件内容超出字符限制（{len(text)}/{cls.MAX_TEXT_LENGTH}字符）"

            if not text.strip():
                return "", "文件内容为空"

            logger.info(f"成功提取文件内容：{filename}，字符数：{len(text)}")
            return text, None

        except Exception as e:
            logger.error(f"文件内容提取失败：{filename}，错误：{str(e)}")
            return "", f"文件解析失败：{str(e)}"

    @staticmethod
    def _detect_encoding(file_path: Path) -> str:
        """检测文件编码"""
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # 读取前10KB用于检测
            result = chardet.detect(raw_data)
            encoding = result['encoding']
            # 处理GB2312识别为GB18030的情况
            if encoding and encoding.lower() in ['gb2312', 'gb18030']:
                return 'gb18030'
            return encoding or 'utf-8'

    @classmethod
    def _extract_txt(cls, file_path: Path) -> str:
        """提取TXT文件内容"""
        encoding = cls._detect_encoding(file_path)
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            # 如果检测的编码失败，尝试常见编码
            for enc in ['utf-8', 'gb18030', 'gbk', 'big5']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise ValueError("无法识别文件编码")

    @staticmethod
    def _extract_pdf(file_path: Path) -> str:
        """提取PDF文件内容"""
        text_parts = []
        with open(file_path, 'rb') as f:
            reader = PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return '\n'.join(text_parts)

    @staticmethod
    def _extract_docx(file_path: Path) -> str:
        """提取Word文档内容"""
        doc = Document(file_path)
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        return '\n'.join(text_parts)

    @classmethod
    def _extract_markdown(cls, file_path: Path) -> str:
        """提取Markdown文件内容，转换为纯文本"""
        encoding = cls._detect_encoding(file_path)
        with open(file_path, 'r', encoding=encoding) as f:
            md_content = f.read()

        # 将Markdown转换为HTML
        html = markdown.markdown(md_content)

        # 使用BeautifulSoup提取纯文本
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator='\n')

    @classmethod
    def _extract_html(cls, file_path: Path) -> str:
        """提取HTML文件内容"""
        encoding = cls._detect_encoding(file_path)
        with open(file_path, 'r', encoding=encoding) as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        # 移除script和style标签
        for script in soup(['script', 'style', 'meta', 'link']):
            script.decompose()

        # 提取文本
        text = soup.get_text(separator='\n')
        return text

    @staticmethod
    def _clean_text(text: str) -> str:
        """清理提取的文本"""
        # 移除多余空行
        lines = [line.rstrip() for line in text.split('\n')]
        # 合并多个空行为单个空行
        cleaned_lines = []
        prev_empty = False
        for line in lines:
            if not line.strip():
                if not prev_empty:
                    cleaned_lines.append('')
                prev_empty = True
            else:
                cleaned_lines.append(line)
                prev_empty = False

        result = '\n'.join(cleaned_lines).strip()
        return result
