"""
TTS服务 - 文本转语音
支持Azure TTS和浏览器端备选方案
"""
from typing import Optional, Dict, Any
import base64
from pathlib import Path
import hashlib
from loguru import logger

from app.core.config import settings


class TTSService:
    """TTS服务"""

    def __init__(self):
        """初始化TTS服务"""
        self.azure_key = getattr(settings, 'AZURE_SPEECH_KEY', None)
        self.azure_region = getattr(settings, 'AZURE_SPEECH_REGION', 'eastasia')
        self.output_dir = Path("audio_cache")
        self.output_dir.mkdir(exist_ok=True)

    def _get_cache_path(self, text: str, voice: str, speed: float) -> Path:
        """获取缓存文件路径"""
        hash_key = hashlib.md5(f"{text}_{voice}_{speed}".encode()).hexdigest()
        return self.output_dir / f"{hash_key}.mp3"

    async def text_to_speech(
            self,
            text: str,
            voice: str = "zh-CN-XiaoxiaoNeural",
            speed: float = 1.0,
            pitch: float = 0
    ) -> Dict[str, Any]:
        """
        文本转语音

        Args:
            text: 要转换的文本
            voice: 音色
            speed: 语速 (0.5-2.0)
            pitch: 音调 (-50 to 50)

        Returns:
            包含音频数据或URL的字典
        """
        # 检查缓存
        cache_path = self._get_cache_path(text, voice, speed)
        if cache_path.exists():
            with open(cache_path, 'rb') as f:
                audio_data = f.read()
            return {
                "success": True,
                "audio_base64": base64.b64encode(audio_data).decode(),
                "format": "mp3",
                "cached": True,
                "duration_estimate": len(text) * 0.3  # 粗略估计
            }

        # 如果没有Azure配置，返回浏览器端TTS的指示
        if not self.azure_key:
            return {
                "success": True,
                "use_browser_tts": True,
                "text": text,
                "voice": voice,
                "speed": speed,
                "message": "使用浏览器端TTS（Azure TTS未配置）"
            }

        # Azure TTS
        try:
            audio_data = await self._azure_tts(text, voice, speed, pitch)
            if audio_data:
                # 保存缓存
                with open(cache_path, 'wb') as f:
                    f.write(audio_data)

                return {
                    "success": True,
                    "audio_base64": base64.b64encode(audio_data).decode(),
                    "format": "mp3",
                    "cached": False,
                    "duration_estimate": len(text) * 0.3
                }
        except Exception as e:
            logger.error(f"Azure TTS失败: {e}")

        return {
            "success": False,
            "error": "TTS转换失败",
            "use_browser_tts": True,
            "text": text
        }

    async def _azure_tts(
            self,
            text: str,
            voice: str,
            speed: float,
            pitch: float
    ) -> Optional[bytes]:
        """调用Azure TTS API"""
        import httpx

        # 处理文本，添加SSML标记
        processed_text = self._process_text_for_speech(text)

        ssml = f"""
        <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='zh-CN'>
            <voice name='{voice}'>
                <prosody rate='{speed}' pitch='{int(pitch)}%'>
                    {processed_text}
                </prosody>
            </voice>
        </speak>
        """

        url = f"https://{self.azure_region}.tts.speech.microsoft.com/cognitiveservices/v1"
        headers = {
            "Ocp-Apim-Subscription-Key": self.azure_key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, content=ssml, timeout=60)
            if response.status_code == 200:
                return response.content

        return None

    def _process_text_for_speech(self, text: str) -> str:
        """预处理文本，添加SSML停顿标记"""
        # 句号后添加停顿
        text = text.replace("。", "。<break time='500ms'/>")
        text = text.replace("！", "！<break time='500ms'/>")
        text = text.replace("？", "？<break time='500ms'/>")

        # 逗号后短停顿
        text = text.replace("，", "，<break time='300ms'/>")
        text = text.replace("、", "、<break time='200ms'/>")
        text = text.replace("；", "；<break time='400ms'/>")

        # 佛经特殊词汇发音
        # 注：这些是常见的佛经多音字
        special_pronunciations = {
            "般若": "<phoneme alphabet='sapi' ph='bo 1 re 3'>般若</phoneme>",
            "南无": "<phoneme alphabet='sapi' ph='na 1 mo 2'>南无</phoneme>",
        }

        for word, phoneme in special_pronunciations.items():
            text = text.replace(word, phoneme)

        return text

    def get_available_voices(self) -> list:
        """获取可用的音色列表"""
        return [
            {"id": "zh-CN-XiaoxiaoNeural", "name": "晓晓（女声）", "gender": "female"},
            {"id": "zh-CN-YunxiNeural", "name": "云希（男声）", "gender": "male"},
            {"id": "zh-CN-XiaoyiNeural", "name": "晓伊（女声）", "gender": "female"},
            {"id": "zh-CN-YunjianNeural", "name": "云健（男声）", "gender": "male"},
            {"id": "zh-CN-XiaochenNeural", "name": "晓辰（女声）", "gender": "female"},
        ]


# 创建全局实例
tts_service = TTSService()
