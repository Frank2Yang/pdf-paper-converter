import streamlit as st
import os
import tempfile
import shutil
import json
import time
from pathlib import Path
import zipfile
from typing import Optional, Dict, Any
import traceback
import pandas as pd
from datetime import datetime

# 设置页面配置
st.set_page_config(
    page_title="PDF论文转写工具 - 中财数碳科技",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 检测部署环境
IS_VERCEL = os.getenv('VERCEL') == '1'
IS_LOCAL = not IS_VERCEL

# 自定义 CSS 样式
st.markdown("""
<style>
    /* 主题色彩 */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --success-color: #28a745;
        --warning-color: #ffc107;
        --error-color: #dc3545;
        --info-color: #17a2b8;
    }
    
    /* 主标题样式 */
    .main-header {
        background: linear-gradient(90deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* 功能卡片样式 */
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 15px rgba(0,0,0,0.1);
        border-left: 4px solid var(--primary-color);
        margin: 1rem 0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 25px rgba(0,0,0,0.15);
    }
    
    .feature-card h3 {
        color: var(--primary-color);
        margin: 0 0 0.5rem 0;
        font-size: 1.2rem;
    }
    
    .feature-card p {
        color: #666;
        margin: 0;
        font-size: 0.9rem;
    }
    
    /* 指标卡片样式 */
    .metric-card {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .metric-card h3 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    
    .metric-card p {
        margin: 0.5rem 0 0 0;
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* 上传区域样式 */
    .upload-area {
        border: 2px dashed var(--primary-color);
        border-radius: 15px;
        padding: 3rem 2rem;
        text-align: center;
        background: linear-gradient(135deg, #f8f9ff 0%, #e8f0ff 100%);
        margin: 2rem 0;
    }
    
    .upload-area h3 {
        color: var(--primary-color);
        margin: 0 0 1rem 0;
        font-size: 1.5rem;
    }
    
    .upload-area p {
        color: #666;
        margin: 0;
        font-size: 1rem;
    }
    
    /* 成功消息样式 */
    .success-message {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: var(--success-color);
        padding: 1rem 1.5rem;
        border-radius: 10px;
        border-left: 4px solid var(--success-color);
        margin: 1rem 0;
        font-weight: 500;
    }
    
    /* Vercel 标识 */
    .vercel-badge {
        background: linear-gradient(135deg, #000 0%, #333 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 0.5rem 0;
        display: inline-block;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    /* 响应式设计 */
    @media (max-width: 768px) {
        .main-header {
            padding: 1.5rem;
        }
        
        .main-header h1 {
            font-size: 2rem;
        }
        
        .feature-card {
            padding: 1rem;
        }
        
        .upload-area {
            padding: 2rem 1rem;
        }
    }
    
    /* 隐藏 Streamlit 默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 自定义滚动条 */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--secondary-color);
    }
</style>
""", unsafe_allow_html=True)

# 导入处理器
try:
    from mineru_processor import MinerUProcessor
    MINERU_AVAILABLE = True
except ImportError:
    MINERU_AVAILABLE = False

def create_temp_dirs():
    """创建临时目录"""
    temp_dir = tempfile.mkdtemp(prefix="mineru_")
    input_dir = os.path.join(temp_dir, "input")
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    return input_dir, output_dir

def cleanup_temp_dirs(temp_dir: str):
    """清理临时目录"""
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        st.warning(f"清理临时文件时出错: {e}")

def process_pdf_file(pdf_path: str, output_dir: str, config: dict, progress_callback=None) -> dict:
    """处理 PDF 文件"""
    try:
        if MINERU_AVAILABLE:
            # 使用完整的 MinerU 处理器
            processor = MinerUProcessor()
            return processor.process_pdf(
                pdf_path=pdf_path,
                output_dir=output_dir,
                language=config.get('language', 'ch'),
                parse_method=config.get('parse_method', 'auto'),
                formula_enable=config.get('formula_enable', True),
                table_enable=config.get('table_enable', True),
                progress_callback=progress_callback
            )
        else:
            # 使用基础处理器
            return process_pdf_basic(pdf_path, output_dir, config, progress_callback)
            
    except Exception as e:
        error_msg = f"处理 PDF 时出错: {str(e)}"
        if progress_callback:
            progress_callback(1.0, f"处理失败: {str(e)}")
        return {
            'success': False,
            'error': error_msg,
            'traceback': traceback.format_exc()
        }

def process_pdf_basic(pdf_path: str, output_dir: str, config: dict, progress_callback=None) -> dict:
    """基础 PDF 处理（当 MinerU 不可用时）"""
    try:
        import fitz  # PyMuPDF
        
        if progress_callback:
            progress_callback(0.1, "初始化基础处理器...")
        
        doc = fitz.open(pdf_path)
        
        markdown_content = []
        text_content = []
        total_pages = len(doc)
        
        if progress_callback:
            progress_callback(0.2, f"开始处理 {total_pages} 页内容...")
        
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            
            # 提取文本
            page_text = page.get_text()
            if page_text.strip():
                markdown_content.append(f"# 页面 {page_num + 1}\n\n{page_text}\n\n")
                text_content.append(page_text)
            
            # 更新进度
            if progress_callback:
                progress = 0.2 + (page_num + 1) / total_pages * 0.6
                progress_callback(progress, f"处理第 {page_num + 1}/{total_pages} 页...")
        
        doc.close()
        
        if progress_callback:
            progress_callback(0.9, "生成输出文件...")
        
        # 合并内容
        full_markdown = "".join(markdown_content)
        full_text = "\n\n".join(text_content)
        
        # 生成 HTML
        html_content = f"""
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
        h1 {{ 
            color: #667eea; 
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        h2 {{ color: #764ba2; }}
        p {{ margin: 1rem 0; }}
    </style>
</head>
<body>
    <h1>PDF 解析结果</h1>
    <div>{full_text.replace(chr(10), '<br>')}</div>
</body>
</html>
"""
        
        # 生成 JSON
        json_data = {
            "document": {
                "title": Path(pdf_path).stem,
                "pages": total_pages,
                "processed_at": datetime.now().isoformat(),
                "method": "basic_extraction",
                "processor": "PyMuPDF"
            },
            "content": {
                "text": full_text,
                "markdown": full_markdown
            },
            "metadata": {
                "file_size": os.path.getsize(pdf_path),
                "processing_time": time.time()
            }
        }
        
        if progress_callback:
            progress_callback(1.0, "处理完成！")
        
        return {
            'success': True,
            'outputs': {
                'markdown_content': full_markdown,
                'html_content': html_content,
                'text_content': full_text,
                'json_content': json.dumps(json_data, ensure_ascii=False, indent=2)
            },
            'stats': {
                'total_pages': total_pages,
                'text_blocks': len([p for p in text_content if p.strip()]),
                'tables': 0,
                'formulas': 0
            },
            'method': 'basic'
        }
        
    except Exception as e:
        raise Exception(f"基础处理失败: {str(e)}")

def main():
    """主应用函数"""

    # 公司 Logo 和标题
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # 显示 Logo
        try:
            with open("static/logo.svg", "r", encoding="utf-8") as f:
                logo_svg = f.read()
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 1rem;">
                {logo_svg}
            </div>
            """, unsafe_allow_html=True)
        except:
            # 如果 logo 文件不存在，显示文字版本
            st.markdown("""
            <div style="text-align: center; padding: 1rem 0;">
                <h2 style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    font-weight: bold;
                    margin-bottom: 0.5rem;
                ">📄 中财数碳（北京）科技有限公司</h2>
                <h3 style="color: #666; margin-bottom: 0;">PDF论文转写工具</h3>
            </div>
            """, unsafe_allow_html=True)

    # 主标题
    st.markdown("""
    <div class="main-header">
        <h1>📄 PDF论文转写工具</h1>
        <p>基于先进 AI 技术的 PDF 文档智能解析与格式转换平台</p>
        <p style="font-size: 0.9rem; color: #999; margin-top: 0.5rem;">中财数碳（北京）科技有限公司 出品</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 部署环境标识
    if IS_VERCEL:
        st.markdown("""
        <div class="vercel-badge">
            ⚡ Powered by Vercel | 🌐 GitHub 自动部署 | 🚀 全球 CDN 加速
        </div>
        """, unsafe_allow_html=True)
    
    # 功能介绍
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🎯 智能识别</h3>
            <p>文本、表格、公式、图像全方位识别</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>📄 多格式输出</h3>
            <p>Markdown、HTML、TXT、JSON 多种格式</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>⚡ 快速部署</h3>
            <p>GitHub + Vercel 自动化部署</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="feature-card">
            <h3>🌐 全球访问</h3>
            <p>Vercel CDN 全球加速访问</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 处理配置")
        
        # 语言设置
        language = st.selectbox(
            "🌐 文档语言",
            options=['ch', 'en', 'auto'],
            index=0,
            help="选择文档的主要语言"
        )
        
        # 解析方法
        parse_method = st.selectbox(
            "🔧 解析模式",
            options=['auto', 'ocr', 'txt'],
            index=0,
            help="auto: 自动选择\nocr: OCR识别\ntxt: 文本提取"
        )
        
        # 功能开关
        st.subheader("🎯 识别功能")
        enable_formula = st.checkbox("🧮 公式识别", value=True)
        enable_table = st.checkbox("📊 表格识别", value=True)
        
        # 输出格式
        st.subheader("📄 输出格式")
        output_formats = {
            'markdown': st.checkbox("📝 Markdown", value=True),
            'html': st.checkbox("🌐 HTML", value=True),
            'text': st.checkbox("📄 纯文本", value=True),
            'json': st.checkbox("🔧 JSON数据", value=False)
        }
        
        # 系统状态
        st.subheader("📊 系统状态")
        if MINERU_AVAILABLE:
            st.success("✅ MinerU 引擎已就绪")
            st.info("🤖 完整 AI 解析模式")
        else:
            st.warning("⚠️ 基础解析模式")
            st.info("📄 使用 PyMuPDF 文本提取")
        
        if IS_VERCEL:
            st.success("✅ Vercel 环境运行")
        else:
            st.info("💻 本地开发环境")
    
    # 主界面
    st.header("📤 文件上传")
    
    # 文件上传区域
    max_size = 50 if IS_VERCEL else 200  # Vercel 限制较小
    uploaded_files = st.file_uploader(
        "",
        type=['pdf'],
        accept_multiple_files=True,
        help=f"支持上传单个或多个 PDF 文件，最大 {max_size}MB"
    )
    
    if uploaded_files:
        total_size = sum(f.size for f in uploaded_files) / 1024 / 1024
        st.markdown(f"""
        <div class="success-message">
            ✅ 已上传 {len(uploaded_files)} 个文件，总大小: {total_size:.2f} MB
        </div>
        """, unsafe_allow_html=True)
        
        # 检查文件大小
        if total_size > max_size:
            st.error(f"❌ 文件总大小超出限制（{max_size}MB），请减少文件数量或选择较小的文件")
            return
        
        # 文件列表
        with st.expander("📋 文件详情", expanded=True):
            for i, file in enumerate(uploaded_files):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"📄 {file.name}")
                with col2:
                    st.write(f"{file.size / 1024 / 1024:.2f} MB")
                with col3:
                    st.write("PDF")
        
        # 处理按钮
        if st.button("🚀 开始处理", type="primary", use_container_width=True):
            # 创建配置
            config = {
                'language': language,
                'parse_method': parse_method,
                'formula_enable': enable_formula,
                'table_enable': enable_table
            }
            
            # 创建临时目录
            input_dir, output_dir = create_temp_dirs()
            temp_base_dir = os.path.dirname(input_dir)
            
            try:
                results = []
                
                # 处理进度
                progress_container = st.container()
                
                for i, uploaded_file in enumerate(uploaded_files):
                    with progress_container:
                        st.subheader(f"📄 处理文件 {i+1}/{len(uploaded_files)}: {uploaded_file.name}")
                        
                        # 保存文件
                        pdf_path = os.path.join(input_dir, uploaded_file.name)
                        with open(pdf_path, 'wb') as f:
                            f.write(uploaded_file.getvalue())
                        
                        # 创建进度条
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        def update_progress(progress: float, message: str):
                            progress_bar.progress(progress)
                            status_text.text(message)
                        
                        # 处理文件
                        file_output_dir = os.path.join(output_dir, Path(uploaded_file.name).stem)
                        os.makedirs(file_output_dir, exist_ok=True)
                        
                        result = process_pdf_file(
                            pdf_path, 
                            file_output_dir,
                            config,
                            progress_callback=update_progress
                        )
                        result['file_name'] = uploaded_file.name
                        results.append(result)
                
                # 显示结果
                successful_results = [r for r in results if r['success']]
                failed_results = [r for r in results if not r['success']]
                
                if successful_results:
                    st.success(f"🎉 成功处理 {len(successful_results)} 个文件！")
                    
                    # 统计信息
                    if len(successful_results) == 1:
                        result = successful_results[0]
                        if 'stats' in result:
                            st.subheader("📊 处理统计")
                            stats = result['stats']
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.markdown(f"""
                                <div class="metric-card">
                                    <h3>{stats.get('total_pages', 0)}</h3>
                                    <p>总页数</p>
                                </div>
                                """, unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"""
                                <div class="metric-card">
                                    <h3>{stats.get('text_blocks', 0)}</h3>
                                    <p>文本块</p>
                                </div>
                                """, unsafe_allow_html=True)
                            with col3:
                                st.markdown(f"""
                                <div class="metric-card">
                                    <h3>{stats.get('tables', 0)}</h3>
                                    <p>表格</p>
                                </div>
                                """, unsafe_allow_html=True)
                            with col4:
                                st.markdown(f"""
                                <div class="metric-card">
                                    <h3>{stats.get('formulas', 0)}</h3>
                                    <p>公式</p>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # 结果预览
                    if len(successful_results) == 1:
                        result = successful_results[0]
                        st.subheader("📋 处理结果预览")
                        
                        tabs = []
                        tab_contents = []
                        
                        if output_formats['markdown'] and 'markdown_content' in result['outputs']:
                            tabs.append("📝 Markdown")
                            tab_contents.append(('markdown', result['outputs']['markdown_content']))
                        
                        if output_formats['html'] and 'html_content' in result['outputs']:
                            tabs.append("🌐 HTML")
                            tab_contents.append(('html', result['outputs']['html_content']))
                        
                        if output_formats['text'] and 'text_content' in result['outputs']:
                            tabs.append("📄 纯文本")
                            tab_contents.append(('text', result['outputs']['text_content']))
                        
                        if output_formats['json'] and 'json_content' in result['outputs']:
                            tabs.append("🔧 JSON")
                            tab_contents.append(('json', result['outputs']['json_content']))
                        
                        if tabs:
                            tab_objects = st.tabs(tabs)
                            for i, (format_type, content) in enumerate(tab_contents):
                                with tab_objects[i]:
                                    if format_type == 'markdown':
                                        st.markdown(content[:2000] + "..." if len(content) > 2000 else content)
                                    elif format_type == 'html':
                                        st.components.v1.html(content, height=400, scrolling=True)
                                    elif format_type == 'json':
                                        st.code(content[:1000] + "..." if len(content) > 1000 else content, language='json')
                                    else:
                                        st.text_area("", content[:1000] + "..." if len(content) > 1000 else content, height=300)
                    
                    # 下载功能
                    st.subheader("📥 下载处理结果")
                    
                    if len(successful_results) == 1:
                        result = successful_results[0]
                        enabled_formats = [k for k, v in output_formats.items() if v]
                        
                        if enabled_formats:
                            cols = st.columns(len(enabled_formats))
                            file_name = Path(uploaded_files[0].name).stem
                            
                            for i, format_name in enumerate(enabled_formats):
                                with cols[i]:
                                    content_key = f"{format_name}_content"
                                    if content_key in result['outputs']:
                                        content = result['outputs'][content_key]
                                        file_ext = {'markdown': 'md', 'html': 'html', 'text': 'txt', 'json': 'json'}[format_name]
                                        
                                        st.download_button(
                                            label=f"📄 {format_name.upper()}",
                                            data=content,
                                            file_name=f"{file_name}.{file_ext}",
                                            mime=f"text/{file_ext}",
                                            use_container_width=True
                                        )
                
                if failed_results:
                    st.error(f"❌ {len(failed_results)} 个文件处理失败")
                    for result in failed_results:
                        st.error(f"文件 {result.get('file_name', 'unknown')} 处理失败: {result.get('error', '未知错误')}")
            
            finally:
                # 清理临时文件
                cleanup_temp_dirs(temp_base_dir)
    
    else:
        st.markdown(f"""
        <div class="upload-area">
            <h3>📤 拖拽或点击上传 PDF 文件</h3>
            <p>支持单个或批量上传，最大文件大小 {max_size}MB</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 页面底部
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>🚀 MinerU PDF 智能解析器 | ⚡ Powered by Vercel | 
        <a href="https://github.com/your-repo" target="_blank" style="color: #667eea;">GitHub</a> | 
        <a href="mailto:support@example.com" style="color: #667eea;">技术支持</a></p>
        <p style="font-size: 0.8rem; margin-top: 1rem;">
            🌟 基于 MinerU AI 引擎 | 🔒 安全可靠 | 🌐 全球 CDN 加速
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
