"""
火山引擎方舟 SDK 实现文本生成
使用豆包大模型 (doubao) 进行文本生成
"""
import os
import logging
from tenacity import retry, stop_after_attempt, wait_exponential
from .base import TextProvider

logger = logging.getLogger(__name__)


class VolcengineTextProvider(TextProvider):
    """Text generation using Volcengine Ark SDK (豆包大模型)"""
    
    def __init__(
        self,
        api_key: str,
        api_base: str = "https://ark.cn-beijing.volces.com/api/v3",
        model: str = "doubao-1-5-pro-32k-250115",
        timeout: float = 300.0,
        max_retries: int = 2
    ):
        """
        Initialize Volcengine text provider
        
        Args:
            api_key: 火山方舟 API Key (ARK_API_KEY)
            api_base: API base URL
            model: Model name to use (e.g., doubao-1-5-pro-32k-250115)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        # 延迟导入，避免未安装时报错
        try:
            from volcenginesdkarkruntime import Ark
        except ImportError:
            raise ImportError(
                "请安装火山引擎 SDK: pip install 'volcengine-python-sdk[ark]'"
            )
        
        self.client = Ark(
            base_url=api_base,
            api_key=api_key,
            timeout=timeout,
            max_retries=max_retries
        )
        self.model = model
        self.max_retries = max_retries
        logger.info(f"Volcengine text provider initialized, model: {model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_text(self, prompt: str, thinking_budget: int = 1000) -> str:
        """
        Generate text using Volcengine Ark SDK
        
        Args:
            prompt: The input prompt
            thinking_budget: 深度思考预算（火山引擎支持但默认禁用）
            
        Returns:
            Generated text
        """
        try:
            # 使用 responses API（新版 API）
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Volcengine text generation failed: {e}")
            raise
    
    def generate_with_image(self, prompt: str, image_path: str, thinking_budget: int = 1000) -> str:
        """
        Generate text with image input (multimodal)
        
        Args:
            prompt: The input prompt
            image_path: Path to the image file
            thinking_budget: Thinking budget (not used)
            
        Returns:
            Generated text
        """
        import base64
        from PIL import Image
        from io import BytesIO
        
        # 加载并编码图片
        img = Image.open(image_path)
        buffered = BytesIO()
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        img.save(buffered, format="JPEG", quality=85)
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # 构建多模态请求
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        return response.choices[0].message.content
