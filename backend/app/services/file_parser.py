"""
文件解析服务 - 处理txt和docx文件上传
"""
import os
from typing import Tuple
import chardet
from docx import Document
from fastapi import UploadFile, HTTPException


class FileParserService:
    """文件解析服务"""

    # 配置常量
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_CHARS = 100000  # 10万字
    SUPPORTED_FORMATS = {'.txt', '.docx'}
    SUPPORTED_ENCODINGS = ['utf-8', 'gbk', 'gb2312', 'big5']

    async def parse_uploaded_file(
        self,
        file: UploadFile
    ) -> Tuple[str, str, int]:
        """
        解析上传的文件

        Args:
            file: FastAPI UploadFile对象

        Returns:
            (文本内容, 版本名, 字符数)

        Raises:
            HTTPException: 文件格式/大小/编码错误
        """
        # 1. 验证文件扩展名
        filename = file.filename or "未命名文件"
        file_ext = os.path.splitext(filename)[1].lower()

        if file_ext not in self.SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式 {file_ext}，仅支持 .txt 和 .docx"
            )

        # 2. 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)

        # 3. 验证文件大小
        if file_size > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件过大 ({file_size / 1024 / 1024:.1f}MB)，最大支持 10MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="文件为空"
            )

        # 4. 根据文件类型解析
        try:
            if file_ext == '.txt':
                text = self._parse_txt(file_content)
            elif file_ext == '.docx':
                text = self._parse_docx(file_content)
            else:
                raise ValueError(f"未实现的文件类型: {file_ext}")
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"文件解析失败: {str(e)}"
            )

        # 5. 验证文本内容
        if not text or not text.strip():
            raise HTTPException(
                status_code=400,
                detail="文件内容为空"
            )

        text = text.strip()
        char_count = len(text)

        # 6. 验证字符数
        if char_count > self.MAX_CHARS:
            raise HTTPException(
                status_code=400,
                detail=f"文本过长 ({char_count} 字)，最大支持 {self.MAX_CHARS} 字"
            )

        # 7. 提取版本名（去掉扩展名）
        version_name = os.path.splitext(filename)[0]

        return text, version_name, char_count

    def _parse_txt(self, content: bytes) -> str:
        """
        解析txt文件，自动检测编码

        Args:
            content: 文件二进制内容

        Returns:
            解析后的文本
        """
        # 使用chardet检测编码
        detected = chardet.detect(content)
        encoding = detected.get('encoding', 'utf-8')
        confidence = detected.get('confidence', 0)

        print(f"[文件解析] 检测到编码: {encoding} (置信度: {confidence:.2%})")

        # 尝试使用检测到的编码
        if encoding and encoding.lower() in [e.lower() for e in self.SUPPORTED_ENCODINGS]:
            try:
                text = content.decode(encoding)
                return text
            except UnicodeDecodeError as e:
                print(f"[文件解析] 使用 {encoding} 解码失败: {e}")

        # 如果检测失败，依次尝试常见编码
        for encoding in self.SUPPORTED_ENCODINGS:
            try:
                text = content.decode(encoding)
                print(f"[文件解析] 成功使用编码: {encoding}")
                return text
            except (UnicodeDecodeError, LookupError):
                continue

        # 所有编码都失败
        raise ValueError(
            "无法识别文件编码，请确保文件是 UTF-8、GBK 或 Big5 编码的文本文件"
        )

    def _parse_docx(self, content: bytes) -> str:
        """
        解析docx文件，提取文本并保留标点

        Args:
            content: 文件二进制内容

        Returns:
            解析后的文本
        """
        try:
            # 保存到临时文件（python-docx需要文件路径）
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name

            try:
                # 使用python-docx解析
                doc = Document(tmp_path)

                # 提取所有段落文本
                paragraphs = []
                for para in doc.paragraphs:
                    text = para.text.strip()
                    if text:
                        paragraphs.append(text)

                # 合并段落（保留换行）
                full_text = '\n'.join(paragraphs)

                print(f"[文件解析] docx解析成功，提取 {len(paragraphs)} 个段落")

                return full_text

            finally:
                # 删除临时文件
                os.unlink(tmp_path)

        except Exception as e:
            raise ValueError(f"docx文件解析失败: {str(e)}")


# 创建全局实例
file_parser_service = FileParserService()
