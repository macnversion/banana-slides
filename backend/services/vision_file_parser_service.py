"""
Vision-based File Parser Service - 使用视觉模型替代 MinerU

通过将文件转换为图片，然后用视觉模型分析内容，实现文件解析功能。
"""
import os
import io
import logging
import tempfile
import base64
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from PIL import Image
from pdf2image import convert_from_path
from docx import Document
from markitdown import MarkItDown

logger = logging.getLogger(__name__)


class VisionFileParserService:
    """
    基于视觉模型的文件解析服务

    工作流程：
    1. 将 PDF/DOCX 转换为图片
    2. 使用视觉模型分析每页图片
    3. 提取文字、表格、图片等内容和位置信息
    4. 返回结构化数据（类似 MinerU 格式）
    """

    def __init__(self, ai_service):
        """
        初始化视觉文件解析服务

        Args:
            ai_service: AIService 实例（需要支持 generate_json_with_image）
        """
        self.ai_service = ai_service
        logger.info("VisionFileParserService 初始化完成")

    def parse_pdf_to_images(
        self,
        pdf_path: str,
        dpi: int = 200,
        first_page: int = 1,
        last_page: Optional[int] = None
    ) -> List[Image.Image]:
        """
        将 PDF 转换为图片列表

        Args:
            pdf_path: PDF 文件路径
            dpi: 分辨率（默认 200）
            first_page: 起始页
            last_page: 结束页（None 表示到最后一页）

        Returns:
            PIL Image 列表
        """
        try:
            logger.info(f"开始转换 PDF 为图片: {pdf_path}")
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                first_page=first_page,
                last_page=last_page
            )
            logger.info(f"PDF 转换完成，共 {len(images)} 页")
            return images
        except Exception as e:
            logger.error(f"PDF 转换失败: {e}")
            return []

    def parse_docx_to_text(self, docx_path: str) -> str:
        """
        将 DOCX 转换为文本

        Args:
            docx_path: DOCX 文件路径

        Returns:
            提取的文本内容
        """
        try:
            doc = Document(docx_path)
            text_content = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())

            return "\n\n".join(text_content)
        except Exception as e:
            logger.error(f"DOCX 解析失败: {e}")
            return ""

    def parse_docx_to_markdown(self, docx_path: str) -> str:
        """
        将 DOCX 转换为 Markdown（保留表格等结构）

        Args:
            docx_path: DOCX 文件路径

        Returns:
            Markdown 格式内容
        """
        try:
            md = MarkItDown()
            result = md.convert(docx_path)
            return result.text_content
        except Exception as e:
            logger.error(f"DOCX Markdown 转换失败: {e}")
            return self.parse_docx_to_text(docx_path)

    def analyze_page_with_vision(
        self,
        image: Image.Image,
        page_num: int = 1,
        thinking_budget: int = 1000
    ) -> Dict[str, Any]:
        """
        使用视觉模型分析页面内容

        Args:
            image: 页面图片
            page_num: 页码
            thinking_budget: 思考预算

        Returns:
            结构化的页面内容，包含：
            - text_blocks: 文字块列表
            - tables: 表格列表
            - images: 图片区域
            - layout: 版面结构
        """
        # 构建分析 prompt
        prompt = self._build_vision_analysis_prompt()

        # 保存图片到临时文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            image.save(tmp.path)
            tmp_path = tmp.path

        try:
            # 调用视觉模型
            result = self.ai_service.generate_json_with_image(
                prompt=prompt,
                image_path=tmp_path,
                thinking_budget=thinking_budget
            )

            # 添加页码信息
            result['page_number'] = page_num
            result['image_size'] = image.size

            return result

        except Exception as e:
            logger.error(f"视觉分析失败（第 {page_num} 页）: {e}")
            return {
                'page_number': page_num,
                'text_blocks': [],
                'tables': [],
                'images': [],
                'error': str(e)
            }
        finally:
            # 清理临时文件
            try:
                os.unlink(tmp_path)
            except:
                pass

    def _build_vision_analysis_prompt(self) -> str:
        """
        构建视觉分析 prompt
        """
        return """请分析这张图片中的内容，并返回以下 JSON 格式的结构化数据：

{
  "text_blocks": [
    {
      "text": "文字内容",
      "bbox": [x0, y0, x1, y1],  // 边界框坐标（像素）
      "type": "title" | "paragraph" | "list"  // 文字类型
    }
  ],
  "tables": [
    {
      "bbox": [x0, y0, x1, y1],  // 表格边界
      "rows": 行数,
      "cols": 列数,
      "cells": [  // 可选，表格单元格内容
        {
          "row": 行索引,
          "col": 列索引,
          "text": "单元格内容"
        }
      ]
    }
  ],
  "images": [
    {
      "bbox": [x0, y0, x1, y1],  // 图片边界
      "description": "图片简要描述"
    }
  ],
  "layout": "标题在顶部 | 多栏布局 | 其他布局特征"
}

注意：
- bbox 坐标格式为 [左上角x, 左上角y, 右下角x, 右下角y]
- 只返回明确识别到的元素，不确定的元素可以省略
- 表格如果内容复杂，可以只返回边界框信息"""

    def parse_file(
        self,
        file_path: str,
        extract_images: bool = True,
        max_pages: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        解析文件（PDF 或 DOCX）

        Args:
            file_path: 文件路径
            extract_images: 是否提取图片
            max_pages: 最大解析页数

        Returns:
            解析结果，包含：
            - content: 文本内容
            - pages: 每页的结构化数据
            - images: 提取的图片列表
        """
        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.pdf':
            return self._parse_pdf(file_path, extract_images, max_pages)
        elif file_ext in ['.docx', '.doc']:
            return self._parse_docx(file_path)
        elif file_ext in ['.txt', '.md']:
            return self._parse_text_file(file_path)
        else:
            return {
                'error': f'不支持的文件格式: {file_ext}',
                'content': '',
                'pages': [],
                'images': []
            }

    def _parse_pdf(
        self,
        pdf_path: str,
        extract_images: bool,
        max_pages: Optional[int]
    ) -> Dict[str, Any]:
        """解析 PDF 文件"""
        logger.info(f"开始解析 PDF: {pdf_path}")

        # 转换 PDF 为图片
        images = self.parse_pdf_to_images(pdf_path, dpi=200)

        if max_pages:
            images = images[:max_pages]

        # 分析每一页
        pages_data = []
        full_text = []

        for i, image in enumerate(images, start=1):
            logger.info(f"分析第 {i}/{len(images)} 页...")
            page_data = self.analyze_page_with_vision(image, page_num=i)
            pages_data.append(page_data)

            # 提取文本
            for block in page_data.get('text_blocks', []):
                full_text.append(block.get('text', ''))

        content = "\n\n".join(full_text)

        return {
            'content': content,
            'pages': pages_data,
            'images': [],  # 可选：提取图片
            'total_pages': len(images)
        }

    def _parse_docx(self, docx_path: str) -> Dict[str, Any]:
        """解析 DOCX 文件"""
        logger.info(f"开始解析 DOCX: {docx_path}")

        # 转换为 Markdown（保留结构）
        content = self.parse_docx_to_markdown(docx_path)

        return {
            'content': content,
            'pages': [{'page_number': 1, 'content': content}],
            'images': [],
            'total_pages': 1
        }

    def _parse_text_file(self, file_path: str) -> Dict[str, Any]:
        """解析纯文本文件"""
        logger.info(f"开始解析文本文件: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                'content': content,
                'pages': [{'page_number': 1, 'content': content}],
                'images': [],
                'total_pages': 1
            }
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, 'r', encoding='gbk') as f:
                content = f.read()

            return {
                'content': content,
                'pages': [{'page_number': 1, 'content': content}],
                'images': [],
                'total_pages': 1
            }


def create_vision_file_parser(ai_service=None) -> VisionFileParserService:
    """
    创建视觉文件解析服务实例

    Args:
        ai_service: AIService 实例（可选，自动获取）

    Returns:
        VisionFileParserService 实例
    """
    if ai_service is None:
        from services.ai_service_manager import get_vision_ai_service
        ai_service = get_vision_ai_service()

    return VisionFileParserService(ai_service)
