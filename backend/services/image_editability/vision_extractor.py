"""
Vision Element Extractor - 基于视觉模型的元素提取器

使用火山引擎视觉模型的OCR能力，替代 MinerU + 百度OCR
"""
import logging
from typing import Dict, Any, List, Optional
from .extractors import ElementExtractor, ExtractionResult, ExtractionContext
from .data_models import BBox

logger = logging.getLogger(__name__)


class VisionElementExtractor(ElementExtractor):
    """
    基于视觉模型的元素提取器

    使用火山引擎视觉模型的OCR能力，同时识别：
    - 文字内容和位置
    - 表格结构和单元格
    - 图片区域

    替代 MinerU + 百度OCR 的组合
    """

    def __init__(self, ai_service):
        """
        初始化视觉元素提取器

        Args:
            ai_service: AIService实例（需要支持 generate_json_with_image）
        """
        self.ai_service = ai_service
        logger.info("✅ VisionElementExtractor 初始化完成（使用火山引擎视觉模型）")

    def supports_type(self, element_type: Optional[str]) -> bool:
        """支持所有类型"""
        return True

    def extract(
        self,
        image_path: str,
        element_type: Optional[str] = None,
        **kwargs
    ) -> ExtractionResult:
        """
        从图像中提取元素（使用视觉模型）

        Args:
            image_path: 图像文件路径
            element_type: 元素类型提示（可选）
            **kwargs:
                - depth: int, 递归深度（用于日志）

        Returns:
            ExtractionResult，包含提取的元素列表
        """
        depth = kwargs.get('depth', 0)
        indent = '  ' * depth

        try:
            logger.info(f"{indent}🔍 VisionElementExtractor: 开始分析图片 {image_path}")

            # 构建视觉分析prompt
            prompt = self._build_element_extraction_prompt()

            # 调用视觉模型（带重试机制）
            result = self.ai_service.generate_json_with_image(
                prompt=prompt,
                image_path=image_path,
                thinking_budget=1000
            )

            if not result:
                logger.warning(f"{indent}⚠️ 视觉模型返回空结果")
                return ExtractionResult(elements=[])

            # 解析结果为标准格式
            elements = self._parse_vision_result(result, image_path)

            logger.info(f"{indent}✅ VisionElementExtractor: 提取了 {len(elements)} 个元素")

            # 分类统计
            type_count = {}
            for elem in elements:
                elem_type = elem.get('type', 'unknown')
                type_count[elem_type] = type_count.get(elem_type, 0) + 1
            logger.debug(f"{indent}   统计: {type_count}")

            # 创建上下文
            from PIL import Image
            img = Image.open(image_path)
            image_size = img.size

            context = ExtractionContext(
                result_dir=None,  # 视觉模型不需要结果目录
                metadata={
                    'source': 'vision',
                    'image_size': image_size
                }
            )

            return ExtractionResult(elements=elements, context=context)

        except Exception as e:
            logger.error(f"{indent}❌ VisionElementExtractor 提取失败: {e}", exc_info=True)
            return ExtractionResult(elements=[])

    def _build_element_extraction_prompt(self) -> str:
        """
        构建元素提取的Prompt

        返回结构化的JSON提取指令
        """
        return """请分析这张图片，识别所有可见的元素，并返回以下JSON格式：

{
  "elements": [
    {
      "type": "text" | "title" | "list" | "table" | "image" | "chart",
      "bbox": [x0, y0, x1, y1],
      "content": "文字内容或描述",
      "cells": [  // 仅table类型需要
        {
          "row": 0,
          "col": 0,
          "text": "单元格内容"
        }
      ]
    }
  ]
}

元素类型说明：
- text: 普通段落文字
- title: 标题文字（字号较大、居中或加粗）
- list: 列表项文字（带序号或符号）
- table: 表格（需要提取所有单元格内容）
- image: 图片或插图
- chart: 图表（柱状图、饼图等）

bbox格式：[左上角x, 左上角y, 右下角x, 右下角y]，单位为像素

注意事项：
1. 确保bbox坐标在图片尺寸范围内
2. 对于表格，请提取所有单元格的文本内容和行列位置
3. 对于图片/图表，content字段填写简短描述
4. 只返回明确识别到的元素，不确定的可以省略
5. 按照从上到下、从左到右的顺序排列元素"""

    def _parse_vision_result(
        self,
        vision_result: Dict[str, Any],
        image_path: str
    ) -> List[Dict[str, Any]]:
        """
        解析视觉模型的返回结果

        Args:
            vision_result: 视觉模型返回的JSON
            image_path: 原始图片路径

        Returns:
            标准化的元素列表
        """
        elements = []

        # 获取元素列表
        vision_elements = vision_result.get('elements', [])

        if not vision_elements:
            logger.warning("视觉模型未返回任何元素")
            return []

        # 转换为标准格式
        for idx, elem in enumerate(vision_elements):
            try:
                # 验证必需字段
                elem_type = elem.get('type', 'text')
                bbox = elem.get('bbox', [])

                if not bbox or len(bbox) != 4:
                    logger.warning(f"元素 {idx} bbox格式错误: {bbox}")
                    continue

                # 标准化元素类型
                normalized_type = self._normalize_element_type(elem_type)

                # 构建标准元素
                standard_elem = {
                    'bbox': self._normalize_bbox(bbox),
                    'type': normalized_type,
                    'content': elem.get('content', ''),
                    'metadata': {
                        'source': 'vision',
                        'confidence': elem.get('confidence', 1.0)
                    }
                }

                # 表格特殊处理
                if normalized_type == 'table':
                    cells = elem.get('cells', [])
                    if cells:
                        standard_elem['content'] = self._format_table_cells(cells)
                        standard_elem['metadata']['cells'] = cells

                # 图片/图表添加唯一标识
                if normalized_type in ['image', 'chart']:
                    standard_elem['image_path'] = f"{normalized_type}_{idx}.png"
                    # 实际裁剪在后续处理中完成

                elements.append(standard_elem)

            except Exception as e:
                logger.warning(f"解析元素 {idx} 失败: {e}")
                continue

        return elements

    def _normalize_element_type(self, elem_type: str) -> str:
        """标准化元素类型"""
        type_mapping = {
            'title': 'title',
            'header': 'title',
            'heading': 'title',
            'list': 'list',
            'bullet': 'list',
            'paragraph': 'text',
            'text': 'text',
            'table': 'table',
            'image': 'image',
            'figure': 'image',
            'chart': 'chart',
            'graph': 'chart'
        }
        return type_mapping.get(elem_type.lower(), 'text')

    def _normalize_bbox(self, bbox: List[float]) -> List[float]:
        """标准化bbox坐标"""
        # 确保是浮点数
        normalized = [float(x) for x in bbox]

        # 确保顺序：x0 < x1, y0 < y1
        if normalized[0] > normalized[2]:
            normalized[0], normalized[2] = normalized[2], normalized[0]
        if normalized[1] > normalized[3]:
            normalized[1], normalized[3] = normalized[3], normalized[1]

        # 确保非负
        normalized = [max(0, x) for x in normalized]

        return normalized

    def _format_table_cells(self, cells: List[Dict[str, Any]]) -> str:
        """
        格式化表格单元格为Markdown表格

        Args:
            cells: 单元格列表，每个包含 row, col, text

        Returns:
            Markdown表格字符串
        """
        if not cells:
            return ""

        # 找出最大行列
        max_row = max(cell.get('row', 0) for cell in cells) + 1
        max_col = max(cell.get('col', 0) for cell in cells) + 1

        # 创建二维数组
        table = [['' for _ in range(max_col)] for _ in range(max_row)]

        # 填充单元格
        for cell in cells:
            row = cell.get('row', 0)
            col = cell.get('col', 0)
            text = cell.get('text', '')
            if 0 <= row < max_row and 0 <= col < max_col:
                table[row][col] = text

        # 格式化为Markdown
        lines = []
        for row_idx, row in enumerate(table):
            line = '| ' + ' | '.join(row) + ' |'
            lines.append(line)
            if row_idx == 0:
                # 表头分隔线
                separator = '|' + '|'.join(['---' for _ in range(max_col)]) + '|'
                lines.append(separator)

        return '\n'.join(lines)
