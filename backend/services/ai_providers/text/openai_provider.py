"""
OpenAI SDK implementation for text generation
"""
import logging
from openai import OpenAI
from .base import TextProvider
from config import get_config

logger = logging.getLogger(__name__)


class OpenAITextProvider(TextProvider):
    """Text generation using OpenAI SDK (compatible with Gemini via proxy)"""
    
    def __init__(self, api_key: str, api_base: str = None, model: str = "gemini-3-flash-preview"):
        """
        Initialize OpenAI text provider
        
        Args:
            api_key: API key
            api_base: API base URL (e.g., https://aihubmix.com/v1)
            model: Model name to use
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base,
            timeout=get_config().OPENAI_TIMEOUT,  # set timeout from config
            max_retries=get_config().OPENAI_MAX_RETRIES  # set max retries from config
        )
        self.model = model
    
    def generate_text(self, prompt: str, thinking_budget: int = 1000) -> str:
        """
        Generate text using OpenAI SDK
        
        Args:
            prompt: The input prompt
            thinking_budget: Not used in OpenAI format, kept for interface compatibility
            
        Returns:
            Generated text
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    def generate_with_image(self, prompt: str, image_path: str, thinking_budget: int = 1000) -> str:
        """
        Generate text with image input (multimodal)

        Args:
            prompt: The input prompt
            image_path: Path to the image file
            thinking_budget: Thinking budget (not used, kept for interface compatibility)

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
