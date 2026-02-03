# Medical Quality Control System (Medical-QC)

这是一个基于 AI 的医学影像智能质控平台，专注于 CT 头部影像的分析、脑出血检测以及医疗质控流程管理。系统采用前后端分离架构，集成了深度学习模型进行辅助诊断。

## 📁 项目结构

项目分为两个主要部分：

*   **`medical-qc` (Backend)**: 基于 Python FastAPI 的后端服务，负责业务逻辑、API 接口、AI 模型推理（PyTorch）以及数据库交互。
*   **`medical-qc-frontend` (Frontend)**: 基于 Vue 3 + Vite 的前端应用，提供现代化的用户界面、数据可视化看板和交互式影像查看器。

## 🚀 技术栈

### 后端 (Backend)
*   **框架**: FastAPI
*   **AI/深度学习**: PyTorch, Torchvision, NumPy, Pillow
*   **数据库**: MySQL (SQLAlchemy + aiomysql)
*   **安全**: Python-JOSE (JWT), Passlib
*   **其他**: Uvicorn, Python-Multipart

### 前端 (Frontend)
*   **框架**: Vue.js 3 (Composition API)
*   **构建工具**: Vite
*   **UI 组件库**: Element Plus
*   **数据可视化**: ECharts
*   **网络请求**: Axios

## 🛠️ 快速开始

### 1. 环境准备
*   Python 3.10+
*   Node.js 16+
*   MySQL 8.0+
*   NVIDIA GPU (推荐，用于 AI 模型加速)

### 2. 后端设置 (`medical-qc`)

```bash
# 进入后端目录
cd medical-qc

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
# 复制 .env.example 为 .env 并配置数据库连接等信息
cp .env.example .env

# 初始化数据库
python scripts/init_db.py

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 前端设置 (`medical-qc-frontend`)

```bash
# 进入前端目录
cd medical-qc-frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 访问系统
*   前端地址: `http://localhost:5173`
*   后端 API 文档: `http://localhost:8000/docs`

## ✨ 主要功能
*   **用户权限管理**: 医生、管理员等多角色登录与权限控制。
*   **异常汇总看板**: 实时展示质控数据统计、趋势分析及异常分布。
*   **AI 智能质控**:
    *   **CT 头部平扫**: 自动检测体位不正、伪影等质量问题。
    *   **脑出血检测**: 基于深度学习模型自动识别出血区域并预警。
*   **影像管理**: DICOM/图片上传、预览与报告生成。

## 📝 开发指南
*   请确保 `.gitignore` 文件正确配置，避免提交敏感数据（如 `data/` 目录下的影像数据集）和临时文件。
*   后端模型文件 (`.pth`) 默认不包含在仓库中，请联系管理员获取预训练模型并放置在 `medical-qc/app/models/` 目录下。
