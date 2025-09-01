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
import requests

# 设置页面配置
st.set_page_config(
    page_title="MinerU PDF 智能解析器",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 检测是否在 Vercel 环境
IS_VERCEL = os.getenv('VERCEL') == '1'

# 自定义 CSS 样式
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    .upload-area {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: #f8f9ff;
    }
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    .vercel-badge {
        background: linear-gradient(135deg, #000 0%, #333 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

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

def process_pdf_basic(pdf_path: str, output_dir: str, config: dict, progress_callback=None) -> dict:
    """基础 PDF 处理（适用于 Vercel 环境）"""
    try:
        if progress_callback:
            progress_callback(0.1, "初始化处理器...")
        
        # 使用 PyMuPDF 进行基础文本提取
        import fitz  # PyMuPDF
        
        if progress_callback:
            progress_callback(0.3, "读取 PDF 文件...")
        
        doc = fitz.open(pdf_path)
        
        markdown_content = []
        text_content = []
        total_pages = len(doc)
        
        if progress_callback:
            progress_callback(0.4, f"处理 {total_pages} 页内容...")
        
        for page_num in range(total_pages):
            page = doc.load_page(page_num)
            
            # 提取文本
            page_text = page.get_text()
            if page_text.strip():
                markdown_content.append(f"# 页面 {page_num + 1}\n\n{page_text}\n\n")
                text_content.append(page_text)
            
            # 更新进度
            if progress_callback:
                progress = 0.4 + (page_num + 1) / total_pages * 0.4
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
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #667eea; }}
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
                "method": "basic_extraction"
            },
            "content": {
                "text": full_text,
                "markdown": full_markdown
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
                'tables': 0,  # 基础版本不支持表格识别
                'formulas': 0  # 基础版本不支持公式识别
            },
            'method': 'basic'
        }
        
    except Exception as e:
        error_msg = f"处理 PDF 时出错: {str(e)}"
        if progress_callback:
            progress_callback(1.0, f"处理失败: {str(e)}")
        return {
            'success': False,
            'error': error_msg
        }

def call_mineru_api(pdf_path: str, config: dict, progress_callback=None) -> dict:
    """调用 MinerU API 服务（如果可用）"""
    try:
        # 这里可以调用您部署的 MinerU API 服务
        # 例如部署在其他服务器上的完整版本
        
        api_url = os.getenv('MINERU_API_URL')
        if not api_url:
            return None
        
        if progress_callback:
            progress_callback(0.2, "连接 MinerU API 服务...")
        
        # 上传文件到 API
        with open(pdf_path, 'rb') as f:
            files = {'file': f}
            data = {'config': json.dumps(config)}
            
            response = requests.post(
                f"{api_url}/process",
                files=files,
                data=data,
                timeout=300
            )
        
        if response.status_code == 200:
            result = response.json()
            if progress_callback:
                progress_callback(1.0, "API 处理完成！")
            return result
        else:
            return None
            
    except Exception as e:
        return None

def main():
    # 主标题
    st.markdown("""
    <div class="main-header">
        <h1>🚀 MinerU PDF 智能解析器</h1>
        <p>基于先进 AI 技术的 PDF 文档智能解析与格式转换平台</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Vercel 部署标识
    if IS_VERCEL:
        st.markdown("""
        <div class="vercel-badge">
            ⚡ Powered by Vercel | 🌐 GitHub 自动部署
        </div>
        """, unsafe_allow_html=True)
    
    # 功能介绍
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🎯 智能识别</h3>
            <p>文本提取和基础结构识别</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>📄 多格式输出</h3>
            <p>Markdown、HTML、TXT、JSON 格式</p>
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
            <p>Vercel CDN 全球加速</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 处理配置")
        
        # 处理模式
        if IS_VERCEL:
            st.info("🌐 Vercel 环境 - 使用基础文本提取")
            processing_mode = "basic"
        else:
            processing_mode = st.selectbox(
                "🔧 处理模式",
                options=['basic', 'api'],
                index=0,
                help="basic: 基础文本提取\napi: 调用 MinerU API"
            )
        
        # 语言设置
        language = st.selectbox(
            "🌐 文档语言",
            options=['ch', 'en', 'auto'],
            index=0,
            help="选择文档的主要语言"
        )
        
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
        if IS_VERCEL:
            st.success("✅ Vercel 环境就绪")
            st.info("💡 基础文本提取模式")
        else:
            st.success("✅ 本地环境就绪")
        
        # API 配置
        if processing_mode == "api":
            st.subheader("🔗 API 配置")
            api_url = st.text_input(
                "MinerU API 地址",
                value=os.getenv('MINERU_API_URL', ''),
                help="输入您的 MinerU API 服务地址"
            )
    
    # 主界面
    st.header("📤 文件上传")
    
    # 文件上传区域
    uploaded_files = st.file_uploader(
        "",
        type=['pdf'],
        accept_multiple_files=True,
        help="支持上传单个或多个 PDF 文件，最大 25MB（Vercel 限制）"
    )
    
    if uploaded_files:
        st.markdown(f"""
        <div class="success-message">
            ✅ 已上传 {len(uploaded_files)} 个文件，总大小: {sum(f.size for f in uploaded_files) / 1024 / 1024:.2f} MB
        </div>
        """, unsafe_allow_html=True)
        
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
                'processing_mode': processing_mode
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
                        if processing_mode == "api":
                            result = call_mineru_api(pdf_path, config, update_progress)
                            if result is None:
                                st.warning("API 服务不可用，切换到基础模式")
                                result = process_pdf_basic(pdf_path, output_dir, config, update_progress)
                        else:
                            result = process_pdf_basic(pdf_path, output_dir, config, update_progress)
                        
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
                        
                        if tabs:
                            tab_objects = st.tabs(tabs)
                            for i, (format_type, content) in enumerate(tab_contents):
                                with tab_objects[i]:
                                    if format_type == 'markdown':
                                        st.markdown(content[:2000] + "..." if len(content) > 2000 else content)
                                    elif format_type == 'html':
                                        st.components.v1.html(content, height=400, scrolling=True)
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
        st.markdown("""
        <div class="upload-area">
            <h3>📤 拖拽或点击上传 PDF 文件</h3>
            <p>支持单个或批量上传，Vercel 环境最大 25MB</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 页面底部
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p>🚀 MinerU PDF 智能解析器 | ⚡ Powered by Vercel | 
        <a href="https://github.com/your-repo" target="_blank">GitHub</a> | 
        <a href="mailto:support@example.com">技术支持</a></p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
