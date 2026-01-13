"""
火山引擎方舟图片编辑 Provider
使用统一的图片生成模型进行图片修复/Inpainting
"""
import logging
from typing import Optional, List, Tuple, Union
from PIL import Image

logger = logging.getLogger(__name__)


class VolcengineArkInpaintingProvider:
    """
    火山引擎方舟图片编辑 Provider

    使用 VolcengineImageProvider 的 edit_image 方法进行图片修复
    """

    def __init__(self, image_provider):
        """
        初始化火山引擎方舟图片编辑 Provider

        Args:
            image_provider: VolcengineImageProvider 实例
        """
        self.image_provider = image_provider
        logger.info("VolcengineArkInpaintingProvider 初始化完成（使用方舟图片生成模型）")

    def inpaint(
        self,
        image: Image.Image,
        mask: Optional[Image.Image] = None,
        prompt: str = "移除图片中的文字和图标，生成干净的背景"
    ) -> Optional[Image.Image]:
        """
        修复图片（移除指定区域并重新生成）

        Args:
            image: 原始图片
            mask: 可选的掩码图片（白色=要移除的区域，黑色=保留）
            prompt: 编辑指令

        Returns:
            修复后的图片
        """
        try:
            logger.info(f"使用火山引擎方舟模型进行图片修复")

            result = self.image_provider.edit_image(
                image=image,
                prompt=prompt,
                mask=mask,
                inpaint_mode="remove"
            )

            if result:
                logger.info(f"图片修复成功: {result.size}")
                return result
            else:
                logger.warning("图片修复返回空结果")
                return None

        except Exception as e:
            logger.error(f"图片修复失败: {e}")
            return None

    def inpaint_bboxes(
        self,
        image: Image.Image,
        bboxes: List[Union[Tuple[int, int, int, int], dict]],
        prompt: str = "移除指定区域的内容，生成干净的背景"
    ) -> Optional[Image.Image]:
        """
        批量修复图片中的多个区域（基于边界框）

        Args:
            image: 原始图片
            bboxes: 边界框列表，每个边界框格式为 (x0, y0, x1, y1) 或 dict
            prompt: 编辑指令

        Returns:
            修复后的图片
        """
        try:
            logger.info(f"批量修复 {len(bboxes)} 个区域")

            # 将 bboxes 转换为掩码
            from utils.mask_utils import create_mask_from_bboxes
            mask = create_mask_from_bboxes(image, bboxes)

            # 使用掩码进行修复
            return self.inpaint(image, mask=mask, prompt=prompt)

        except Exception as e:
            logger.error(f"批量修复失败: {e}")
            return None


def create_volcengine_ark_inpainting_provider(
    api_key: str,
    api_base: str = "https://ark.cn-beijing.volces.com/api/v3",
    model: str = "ep-20251204072545-8d7hn"
) -> Optional[VolcengineArkInpaintingProvider]:
    """
    创建火山引擎方舟图片编辑 Provider

    Args:
        api_key: 火山方舟 API Key (ARK_API_KEY)
        api_base: API base URL
        model: 图片生成模型端点

    Returns:
        VolcengineArkInpaintingProvider 实例
    """
    try:
        from services.ai_providers.image.volcengine_provider import VolcengineImageProvider

        # 创建图片生成 provider
        image_provider = VolcengineImageProvider(
            api_key=api_key,
            api_base=api_base,
            model=model
        )

        return VolcengineArkInpaintingProvider(image_provider)

    except Exception as e:
        logger.error(f"创建火山引擎方舟图片编辑 Provider 失败: {e}")
        return None
