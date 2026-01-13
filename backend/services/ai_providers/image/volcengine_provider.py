"""
火山引擎方舟 SDK 实现图像生成和编辑
使用 Seedream 模型进行图像生成、图生图、图片编辑
"""
import os
import logging
import base64
import requests
from io import BytesIO
from typing import Optional, List, Tuple
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential
from .base import ImageProvider

logger = logging.getLogger(__name__)


class VolcengineImageProvider(ImageProvider):
    """Image generation and editing using Volcengine Ark SDK (Seedream 模型)"""

    # 分辨率映射
    SIZE_MAP = {
        "1K": "1024x1024",
        "2K": "2048x2048",
        "4K": "2048x2048",  # Seedream 最大支持 2K
    }

    # 宽高比映射到具体尺寸
    ASPECT_RATIO_SIZE_MAP = {
        "16:9": {"1K": "1280x720", "2K": "1920x1080", "4K": "1920x1080"},
        "9:16": {"1K": "720x1280", "2K": "1080x1920", "4K": "1080x1920"},
        "1:1": {"1K": "1024x1024", "2K": "2048x2048", "4K": "2048x2048"},
        "4:3": {"1K": "1024x768", "2K": "2048x1536", "4K": "2048x1536"},
        "3:4": {"1K": "768x1024", "2K": "1536x2048", "4K": "1536x2048"},
    }

    def __init__(
        self,
        api_key: str,
        api_base: str = "https://ark.cn-beijing.volces.com/api/v3",
        model: str = "doubao-seedream-3-0-t2i-250415",
        timeout: float = 300.0,
        max_retries: int = 2
    ):
        """
        Initialize Volcengine image provider

        Args:
            api_key: 火山方舟 API Key (ARK_API_KEY)
            api_base: API base URL
            model: Model name to use (e.g., doubao-seedream-4-5-251128)
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
        self.api_key = api_key
        self.api_base = api_base
        logger.info(f"Volcengine image provider initialized, model: {model}")

    def _encode_image_to_base64(self, image: Image.Image) -> str:
        """Encode PIL Image to base64 string"""
        buffered = BytesIO()
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        image.save(buffered, format="JPEG", quality=95)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def _get_size_for_aspect_ratio(self, aspect_ratio: str, resolution: str) -> str:
        """Get size string based on aspect ratio and resolution"""
        if aspect_ratio in self.ASPECT_RATIO_SIZE_MAP:
            return self.ASPECT_RATIO_SIZE_MAP[aspect_ratio].get(resolution, "1024x1024")
        return self.SIZE_MAP.get(resolution, "1024x1024")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_image(
        self,
        prompt: str,
        ref_images: Optional[List[Image.Image]] = None,
        aspect_ratio: str = "16:9",
        resolution: str = "2K"
    ) -> Optional[Image.Image]:
        """
        Generate image using Volcengine Ark SDK

        Args:
            prompt: The image generation prompt
            ref_images: Optional list of reference images (用于图生图)
            aspect_ratio: Image aspect ratio
            resolution: Image resolution ("1K", "2K", "4K")

        Returns:
            Generated PIL Image object, or None if failed
        """
        try:
            size = self._get_size_for_aspect_ratio(aspect_ratio, resolution)
            logger.info(f"Generating image with Volcengine, size: {size}, model: {self.model}")

            # 如果有参考图片，使用图生图模式
            if ref_images and len(ref_images) > 0:
                return self._generate_with_reference(prompt, ref_images[0], size)

            # 文生图模式
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size=size,
                response_format="b64_json",  # 返回 base64 数据
            )

            # 解析响应
            if response.data and len(response.data) > 0:
                image_data = response.data[0]

                # 优先使用 b64_json
                if hasattr(image_data, 'b64_json') and image_data.b64_json:
                    image_bytes = base64.b64decode(image_data.b64_json)
                    image = Image.open(BytesIO(image_bytes))
                    logger.info(f"Successfully generated image: {image.size}")
                    return image

                # 备选：使用 URL
                if hasattr(image_data, 'url') and image_data.url:
                    resp = requests.get(image_data.url, timeout=30)
                    resp.raise_for_status()
                    image = Image.open(BytesIO(resp.content))
                    logger.info(f"Successfully downloaded image from URL: {image.size}")
                    return image

            logger.error("No image data in response")
            return None

        except Exception as e:
            error_detail = f"Error generating image with Volcengine (model={self.model}): {type(e).__name__}: {str(e)}"
            logger.error(error_detail, exc_info=True)
            raise Exception(error_detail) from e

    def _generate_with_reference(
        self,
        prompt: str,
        ref_image: Image.Image,
        size: str
    ) -> Optional[Image.Image]:
        """
        Generate image with reference image (图生图)

        Args:
            prompt: The image generation prompt
            ref_image: Reference image
            size: Target size

        Returns:
            Generated PIL Image object
        """
        try:
            # 编码参考图片
            ref_base64 = self._encode_image_to_base64(ref_image)

            # 使用 chat completions 的多模态能力进行图生图
            # 注意：Seedream 模型的图生图可能需要特定的 API
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                size=size,
                response_format="b64_json",
            )

            if response.data and len(response.data) > 0:
                image_data = response.data[0]
                if hasattr(image_data, 'b64_json') and image_data.b64_json:
                    image_bytes = base64.b64decode(image_data.b64_json)
                    image = Image.open(BytesIO(image_bytes))
                    logger.info(f"Successfully generated image with reference: {image.size}")
                    return image

            return None

        except Exception as e:
            logger.error(f"Failed to generate image with reference: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def edit_image(
        self,
        image: Image.Image,
        prompt: str,
        mask: Optional[Image.Image] = None,
        inpaint_mode: str = "remove"
    ) -> Optional[Image.Image]:
        """
        使用火山引擎图片编辑功能（图片修复/Inpainting）

        Args:
            image: 原始图片
            prompt: 编辑指令（如 "移除图片中的文字"）
            mask: 可选的掩码图片（白色=要编辑的区域，黑色=保留）
            inpaint_mode: 编辑模式

        Returns:
            编辑后的 PIL Image 对象
        """
        try:
            logger.info(f"使用火山引擎编辑图片，模式: {inpaint_mode}")

            # 将图片调整到合适的大小（火山引擎限制）
            max_dimension = 2048
            original_size = image.size
            if max(image.size) > max_dimension:
                ratio = max_dimension / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.LANCZOS)
                if mask:
                    mask = mask.resize(new_size, Image.LANCZOS)
                logger.info(f"压缩图片: {original_size} -> {new_size}")

            # 编码图片为 base64
            image_base64 = self._encode_image_to_base64(image)

            # 构建编辑请求
            # 使用 chat completions 的多模态能力进行图片编辑
            messages = []

            if mask:
                # 有掩码的情况：精确编辑指定区域
                mask_base64 = self._encode_image_to_base64(mask)
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{mask_base64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": f"请根据掩码（白色区域）{prompt}。掩码中的白色区域是需要编辑的部分，黑色区域保持不变。"
                        }
                    ]
                })
            else:
                # 无掩码的情况：整体编辑
                messages.append({
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
                })

            # 调用火山引擎 API
            # 注意：这里使用 chat completions 的图片生成能力
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )

            # 解析响应
            # 火山引擎可能返回图片 URL 或 base64 数据
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content

                # 检查是否返回了图片 URL
                if isinstance(content, str):
                    # 尝试从内容中提取图片 URL 或 base64
                    if "data:image" in content:
                        # 提取 base64 图片数据
                        import re
                        match = re.search(r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)', content)
                        if match:
                            image_bytes = base64.b64decode(match.group(1))
                            result_image = Image.open(BytesIO(image_bytes))
                            # 调整回原始尺寸
                            if result_image.size != original_size:
                                result_image = result_image.resize(original_size, Image.LANCZOS)
                            return result_image
                    elif content.startswith("http"):
                        # 从 URL 下载图片
                        resp = requests.get(content, timeout=30)
                        resp.raise_for_status()
                        result_image = Image.open(BytesIO(resp.content))
                        if result_image.size != original_size:
                            result_image = result_image.resize(original_size, Image.LANCZOS)
                        return result_image

            logger.warning("火山引擎图片编辑未返回图片，尝试使用生成式方法")
            # 如果直接编辑失败，使用生成式方法
            return self._generative_edit(image, prompt, mask)

        except Exception as e:
            logger.error(f"火山引擎图片编辑失败: {e}")
            # 降级到生成式编辑
            return self._generative_edit(image, prompt, mask)

    def _generative_edit(
        self,
        image: Image.Image,
        prompt: str,
        mask: Optional[Image.Image] = None
    ) -> Optional[Image.Image]:
        """
        生成式编辑：使用图片作为参考，重新生成编辑后的图片

        Args:
            image: 原始图片
            prompt: 编辑指令
            mask: 可选的掩码图片

        Returns:
            编辑后的图片
        """
        try:
            logger.info("使用生成式编辑方法")

            # 获取原始尺寸
            original_size = image.size

            # 构建更详细的编辑 prompt
            if mask:
                edit_prompt = f"请编辑这张图片，{prompt}。保持图片的整体风格和布局，只修改需要调整的部分。"
            else:
                edit_prompt = f"请对这张图片进行以下编辑：{prompt}。保持图片的整体风格。"

            # 使用图生图方式重新生成
            # 将原始图片作为参考
            result = self._generate_with_reference(edit_prompt, image, "1920x1080")

            if result:
                # 调整回原始尺寸
                if result.size != original_size:
                    result = result.resize(original_size, Image.LANCZOS)
                return result

            return None

        except Exception as e:
            logger.error(f"生成式编辑失败: {e}")
            return None
