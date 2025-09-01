# 🚀 MinerU PDF 解析器 - GitHub + Vercel 完整部署

## 📋 项目概述

这是一个专门为 GitHub + Vercel 部署优化的 MinerU PDF 智能解析器，提供完整的 AI 解析功能和现代化的 Web 界面。

## ✨ 核心特性

- 🎨 **现代化界面**: 简洁美观的 Streamlit Web 应用
- 🤖 **AI 智能解析**: 完整的 MinerU 引擎集成
- 📄 **多格式输出**: Markdown、HTML、TXT、JSON
- ⚡ **自动部署**: GitHub 推送自动触发 Vercel 部署
- 🌐 **全球 CDN**: Vercel 提供的全球加速访问
- 🔒 **安全可靠**: HTTPS 加密，环境变量保护

## 🚀 快速部署

### 第一步：Fork 仓库

1. 点击右上角 "Fork" 按钮
2. 选择您的 GitHub 账号
3. 等待 Fork 完成

### 第二步：连接 Vercel

1. 访问 [vercel.com](https://vercel.com)
2. 使用 GitHub 账号登录
3. 点击 "New Project"
4. 选择您 Fork 的仓库
5. 点击 "Deploy"

### 第三步：配置环境变量

在 Vercel 项目设置中添加：

```bash
# MinerU 配置
HF_ENDPOINT=https://hf-mirror.com
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# 可选：MinerU API 服务地址（如果有独立部署的 API）
MINERU_API_URL=https://your-api-server.com
```

### 第四步：访问应用

部署完成后，您将获得一个 Vercel 域名：
- `https://your-project-name.vercel.app`

## 📁 项目结构

```
github-vercel-deploy/
├── 📱 app.py                       # 主应用文件
├── 🔧 mineru_processor.py          # MinerU 处理器
├── ⚙️ vercel.json                  # Vercel 配置
├── 📦 requirements.txt             # Python 依赖
├── 🎨 static/                      # 静态资源
│   ├── style.css                  # 自定义样式
│   └── logo.png                   # 应用图标
├── 📖 README.md                    # 项目说明
└── 🔄 .github/                     # GitHub Actions
    └── workflows/
        └── deploy.yml              # 自动部署工作流
```

## 🛠️ 本地开发

### 环境要求

- Python 3.8+
- Git

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/mineru-vercel-deploy.git
cd mineru-vercel-deploy

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动应用
streamlit run app.py
```

### 访问应用

本地开发地址：`http://localhost:8501`

## 🔧 配置说明

### Vercel 配置 (vercel.json)

- **构建配置**: 使用 Python 运行时
- **路由配置**: 所有请求转发到主应用
- **环境变量**: 自动注入配置
- **函数超时**: 设置为 300 秒

### 依赖管理 (requirements.txt)

- **核心框架**: Streamlit, Pandas, NumPy
- **AI 引擎**: MinerU 完整版本
- **PDF 处理**: PyMuPDF, pdfplumber
- **图像处理**: OpenCV, Pillow

## 🎯 使用指南

### 上传文件

1. 拖拽或点击上传 PDF 文件
2. 支持单个或批量上传
3. 文件大小限制：50MB（Vercel Pro）

### 配置参数

- **语言设置**: 中文、英文、自动检测
- **解析模式**: 自动、OCR、文本提取
- **功能开关**: 公式识别、表格识别
- **输出格式**: 选择需要的输出格式

### 处理结果

- **实时进度**: 显示处理进度和状态
- **结果预览**: 多格式内容预览
- **文件下载**: 一键下载处理结果
- **统计信息**: 详细的处理统计

## 🔄 自动部署

### GitHub Actions

每次推送到 `main` 分支时：

1. **代码检查**: 语法检查和基础测试
2. **构建测试**: 验证应用可以正常构建
3. **自动部署**: 触发 Vercel 重新部署
4. **通知状态**: 部署结果通知

### 部署流程

```
GitHub Push → GitHub Actions → Vercel Build → Live Deployment
```

## 🌐 生产环境

### 性能优化

- **CDN 加速**: Vercel 全球 CDN
- **缓存策略**: 静态资源缓存
- **压缩优化**: Gzip 压缩传输
- **懒加载**: 按需加载资源

### 监控告警

- **错误追踪**: Vercel 内置错误监控
- **性能监控**: 响应时间和资源使用
- **访问统计**: 用户访问分析
- **日志查看**: 实时日志查看

## 🔒 安全配置

### 数据安全

- **HTTPS 加密**: 全站 HTTPS 访问
- **环境变量**: 敏感信息环境变量存储
- **临时文件**: 自动清理临时文件
- **访问控制**: 可选的访问密码保护

### 隐私保护

- **文件处理**: 本地处理，不上传第三方
- **数据清理**: 处理完成后自动清理
- **无日志存储**: 不存储用户文件内容

## 🆙 升级指南

### 更新代码

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 更新依赖
pip install -r requirements.txt --upgrade

# 3. 推送到 GitHub（自动触发部署）
git push origin main
```

### 版本管理

- **语义化版本**: 遵循 SemVer 规范
- **变更日志**: 详细的更新记录
- **回滚支持**: 快速回滚到稳定版本

## 📞 技术支持

### 获取帮助

- 🐛 **问题报告**: [GitHub Issues](https://github.com/your-repo/issues)
- 💬 **功能建议**: [GitHub Discussions](https://github.com/your-repo/discussions)
- 📧 **邮件支持**: support@your-domain.com
- 📖 **文档中心**: [完整文档](https://docs.your-domain.com)

### 社区贡献

- 🤝 **代码贡献**: 欢迎提交 Pull Request
- 📝 **文档改进**: 帮助完善文档
- 🌟 **项目支持**: 给项目点星支持
- 📢 **推广分享**: 分享给更多用户

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

**🎉 立即开始使用 GitHub + Vercel 部署您的 MinerU PDF 解析器！**
