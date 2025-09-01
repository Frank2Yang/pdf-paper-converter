import os
import sys
import json
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import logging
import traceback

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MinerUProcessor:
    """MinerU PDF 处理器 - Vercel 优化版本"""
    
    def __init__(self):
        self.mineru_available = False
        self.setup_mineru()
    
    def setup_mineru(self):
        """设置 MinerU 环境"""
        try:
            # 尝试导入 MinerU 相关模块
            import magic_pdf
            from magic_pdf.cli.magicpdf import do_parse
            from magic_pdf.config.make_content_config import DropMode, MakeContentConfig
            
            self.mineru_available = True
            logger.info("MinerU 模块加载成功")
            
        except ImportError as e:
            logger.warning(f"MinerU 模块不可用: {e}")
            self.mineru_available = False
    
    def process_pdf(self, 
                   pdf_path: str, 
                   output_dir: str,
                   language: str = 'ch',
                   parse_method: str = 'auto',
                   formula_enable: bool = True,
                   table_enable: bool = True,
                   progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        处理 PDF 文件
        
        Args:
            pdf_path: PDF 文件路径
            output_dir: 输出目录
            language: 文档语言 ('ch', 'en', 'auto')
            parse_method: 解析方法 ('auto', 'ocr', 'txt')
            formula_enable: 是否启用公式识别
            table_enable: 是否启用表格识别
            progress_callback: 进度回调函数
        
        Returns:
            处理结果字典
        """
        try:
            if progress_callback:
                progress_callback(0.1, "初始化处理器...")
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            if not self.mineru_available:
                # 如果 MinerU 不可用，返回模拟结果
                return self._create_demo_result(pdf_path, output_dir, progress_callback)
            
            # 使用真实的 MinerU 处理
            return self._process_with_mineru(
                pdf_path, output_dir, language, parse_method,
                formula_enable, table_enable, progress_callback
            )
            
        except Exception as e:
            error_msg = f"处理 PDF 时出错: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            if progress_callback:
                progress_callback(1.0, f"处理失败: {str(e)}")
            
            return {
                'success': False,
                'error': error_msg,
                'traceback': traceback.format_exc()
            }
    
    def _process_with_mineru(self, 
                           pdf_path: str, 
                           output_dir: str,
                           language: str,
                           parse_method: str,
                           formula_enable: bool,
                           table_enable: bool,
                           progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """使用真实的 MinerU 处理 PDF"""
        try:
            from magic_pdf.cli.magicpdf import do_parse
            from magic_pdf.config.make_content_config import DropMode, MakeContentConfig
            
            if progress_callback:
                progress_callback(0.2, "配置 MinerU 参数...")
            
            # 创建配置
            config = MakeContentConfig(
                drop_mode=DropMode.WHOLE_PDF,
                lang=language if language != 'auto' else 'ch'
            )
            
            if progress_callback:
                progress_callback(0.3, "开始解析 PDF...")
            
            # 执行解析
            result = do_parse(
                pdf_path=pdf_path,
                output_dir=output_dir,
                method=parse_method,
                start_page_id=0,
                end_page_id=None,
                config=config
            )
            
            if progress_callback:
                progress_callback(0.8, "生成输出文件...")
            
            # 处理输出结果
            outputs = self._process_mineru_output(output_dir, pdf_path)
            
            if progress_callback:
                progress_callback(1.0, "处理完成！")
            
            return {
                'success': True,
                'outputs': outputs,
                'stats': self._calculate_stats(outputs),
                'method': 'mineru'
            }
            
        except Exception as e:
            raise Exception(f"MinerU 处理失败: {str(e)}")
    
    def _process_mineru_output(self, output_dir: str, pdf_path: str) -> Dict[str, Any]:
        """处理 MinerU 的输出结果"""
        outputs = {}
        pdf_name = Path(pdf_path).stem
        
        # 查找 MinerU 生成的文件
        markdown_file = None
        json_file = None
        
        # 遍历输出目录查找文件
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith('.md'):
                    markdown_file = file_path
                elif file.endswith('.json'):
                    json_file = file_path
        
        # 处理 Markdown 文件
        if markdown_file and os.path.exists(markdown_file):
            with open(markdown_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            outputs['markdown_content'] = markdown_content
            outputs['markdown'] = markdown_file
        else:
            outputs['markdown_content'] = "# 处理结果\n\n未能生成 Markdown 内容。"
        
        # 处理 JSON 文件
        if json_file and os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            outputs['json_content'] = json.dumps(json_data, ensure_ascii=False, indent=2)
            outputs['json'] = json_file
        else:
            outputs['json_content'] = '{"message": "未能生成 JSON 数据"}'
        
        # 生成 HTML 内容
        html_content = self._markdown_to_html(outputs.get('markdown_content', ''))
        html_file = os.path.join(output_dir, f"{pdf_name}.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        outputs['html_content'] = html_content
        outputs['html'] = html_file
        
        # 生成纯文本内容
        text_content = self._markdown_to_text(outputs.get('markdown_content', ''))
        text_file = os.path.join(output_dir, f"{pdf_name}.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text_content)
        outputs['text_content'] = text_content
        outputs['text'] = text_file
        
        return outputs
    
    def _create_demo_result(self, 
                          pdf_path: str, 
                          output_dir: str,
                          progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """创建演示结果（当 MinerU 不可用时）"""
        try:
            pdf_name = Path(pdf_path).stem
            
            if progress_callback:
                progress_callback(0.3, "生成演示内容...")
            
            # 创建演示内容
            markdown_content = f"""# {pdf_name} - 演示解析结果

## 📋 文档概述

这是一个演示的 PDF 解析结果。在实际部署中，当 MinerU 引擎可用时，将提供完整的 AI 解析功能。

## 🎯 主要功能

### 文本识别
- 高精度 OCR 文本识别
- 支持中英文混合文档
- 保持原始格式和布局

### 表格解析
| 功能 | 状态 | 说明 |
|------|------|------|
| 表格识别 | ✅ 支持 | 自动识别表格结构 |
| 单元格合并 | ✅ 支持 | 处理复杂表格布局 |
| 数据提取 | ✅ 支持 | 结构化数据输出 |

### 公式识别
数学公式示例：
- 线性方程：$y = ax + b$
- 二次方程：$ax^2 + bx + c = 0$
- 积分公式：$\\int_a^b f(x)dx$

## 📊 处理统计

- **总页数**: 演示页面
- **文本块**: 多个文本区域
- **表格数量**: 1个示例表格
- **公式数量**: 3个数学公式

## 🚀 完整功能

要体验完整的 AI 解析功能，请：
1. 安装 MinerU 引擎
2. 配置相关依赖
3. 重新处理文档

---
*这是演示模式的输出结果*
"""
            
            if progress_callback:
                progress_callback(0.6, "生成输出文件...")
            
            # 保存 Markdown 文件
            markdown_file = os.path.join(output_dir, f"{pdf_name}.md")
            with open(markdown_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            # 生成 HTML 内容
            html_content = self._markdown_to_html(markdown_content)
            html_file = os.path.join(output_dir, f"{pdf_name}.html")
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # 生成纯文本内容
            text_content = self._markdown_to_text(markdown_content)
            text_file = os.path.join(output_dir, f"{pdf_name}.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            # 生成 JSON 数据
            json_data = {
                "document": {
                    "title": pdf_name,
                    "type": "demo",
                    "pages": 1,
                    "content": {
                        "text_blocks": [
                            {"type": "heading", "content": f"{pdf_name} - 演示解析结果"},
                            {"type": "paragraph", "content": "这是一个演示的 PDF 解析结果。"},
                            {"type": "table", "content": "示例表格数据"},
                            {"type": "formula", "content": "数学公式示例"}
                        ],
                        "tables": [
                            {
                                "headers": ["功能", "状态", "说明"],
                                "rows": [
                                    ["表格识别", "✅ 支持", "自动识别表格结构"],
                                    ["单元格合并", "✅ 支持", "处理复杂表格布局"],
                                    ["数据提取", "✅ 支持", "结构化数据输出"]
                                ]
                            }
                        ],
                        "formulas": [
                            "y = ax + b",
                            "ax^2 + bx + c = 0",
                            "∫f(x)dx"
                        ]
                    }
                },
                "metadata": {
                    "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "method": "demo",
                    "version": "1.0.0"
                }
            }
            
            json_file = os.path.join(output_dir, f"{pdf_name}.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            if progress_callback:
                progress_callback(1.0, "演示结果生成完成！")
            
            return {
                'success': True,
                'outputs': {
                    'markdown_content': markdown_content,
                    'html_content': html_content,
                    'text_content': text_content,
                    'json_content': json.dumps(json_data, ensure_ascii=False, indent=2),
                    'markdown': markdown_file,
                    'html': html_file,
                    'text': text_file,
                    'json': json_file
                },
                'stats': {
                    'total_pages': 1,
                    'text_blocks': 4,
                    'tables': 1,
                    'formulas': 3
                },
                'method': 'demo'
            }
            
        except Exception as e:
            raise Exception(f"生成演示结果失败: {str(e)}")
    
    def _markdown_to_html(self, markdown_content: str) -> str:
        """将 Markdown 转换为 HTML"""
        try:
            import markdown
            html = markdown.markdown(markdown_content, extensions=['tables', 'codehilite'])
            
            # 添加 CSS 样式
            styled_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PDF 解析结果</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1, h2, h3 {{ color: #667eea; }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{ background-color: #f8f9fa; }}
        code {{
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
        }}
        blockquote {{
            border-left: 4px solid #667eea;
            margin: 0;
            padding-left: 20px;
            color: #666;
        }}
    </style>
</head>
<body>
{html}
</body>
</html>
"""
            return styled_html
            
        except ImportError:
            # 如果没有 markdown 库，使用简单的 HTML 转换
            html_content = markdown_content.replace('\n', '<br>')
            html_content = html_content.replace('# ', '<h1>').replace('\n', '</h1>\n')
            html_content = html_content.replace('## ', '<h2>').replace('\n', '</h2>\n')
            html_content = html_content.replace('### ', '<h3>').replace('\n', '</h3>\n')
            
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PDF 解析结果</title>
</head>
<body>
{html_content}
</body>
</html>
"""
    
    def _markdown_to_text(self, markdown_content: str) -> str:
        """将 Markdown 转换为纯文本"""
        import re
        
        # 移除 Markdown 标记
        text = re.sub(r'#{1,6}\s*', '', markdown_content)  # 移除标题标记
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # 移除粗体标记
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # 移除斜体标记
        text = re.sub(r'`(.*?)`', r'\1', text)  # 移除代码标记
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # 移除链接，保留文本
        text = re.sub(r'\|.*?\|', '', text)  # 移除表格分隔符
        text = re.sub(r'-{3,}', '', text)  # 移除分隔线
        
        # 清理多余的空行
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _calculate_stats(self, outputs: Dict[str, Any]) -> Dict[str, int]:
        """计算处理统计信息"""
        stats = {
            'total_pages': 1,
            'text_blocks': 0,
            'tables': 0,
            'formulas': 0
        }
        
        try:
            markdown_content = outputs.get('markdown_content', '')
            
            # 统计文本块（段落）
            paragraphs = [p for p in markdown_content.split('\n\n') if p.strip()]
            stats['text_blocks'] = len(paragraphs)
            
            # 统计表格
            table_count = markdown_content.count('|')
            if table_count > 0:
                stats['tables'] = markdown_content.count('|---') or 1
            
            # 统计公式
            formula_count = markdown_content.count('$') // 2  # 成对的 $ 符号
            stats['formulas'] = formula_count
            
        except Exception as e:
            logger.warning(f"计算统计信息时出错: {e}")
        
        return stats

def get_processor() -> MinerUProcessor:
    """获取处理器实例"""
    return MinerUProcessor()
