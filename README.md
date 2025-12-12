# 🎬 AI Intelligent Video Editor Backend (AI 智能视频剪辑后端)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![Celery](https://img.shields.io/badge/Celery-Async-orange)
![Architecture](https://img.shields.io/badge/Architecture-Event--Driven-purple)

> 针对【技术开发岗前测试题 1.2】提交的高性能解决方案。
> 基于 **DeepSeek (LLM)** 和 **Groq Whisper (ASR)** 的全栈视频处理流水线。

## 📖 项目简介 (Introduction)

本项目实现了一个企业级的自动化视频剪辑系统。不同于传统的基于规则的剪辑，本项目利用**大语言模型**理解视频语义，自动识别并移除视频中的无效片段（如口语填充词、重复语句、静默片段）。

系统采用 **Producer-Consumer (生产者-消费者)** 异步架构设计，确保在高并发场景下 API 的极速响应，并将耗时的视频处理任务卸载至后台 Worker 集群。

## 🏗️ 系统架构 (Architecture)

```mermaid
graph LR
    User[客户端] --> |上传/查询| API[FastAPI 网关]
    API --> |元数据| MySQL[("MySQL 8.0")]
    API --> |视频文件| MinIO[("MinIO 对象存储")]
    API --> |任务分发| Redis[("Redis 消息队列")]
    
    Redis --> Worker[Celery 异步工人]
    
    subgraph "AI 处理引擎 (Worker)"
        Worker --> |极速听写| Groq["Groq API (Whisper-v3)"]
        Worker --> |语义分析| DeepSeek["SiliconFlow API"]
        Worker --> |物理剪辑| FFmpeg["视频渲染引擎"]
    end
    
    FFmpeg --> |回传成品| MinIO
✨ 核心特性 (Features)
⚡ 极致性能 ASR：弃用了低效的本地 Whisper 模型，集成 Groq API (Whisper-large-v3)，实现 100x 实时倍速的语音转录，解决本地显存瓶颈。

🧠 智能语义分析：接入 DeepSeek-V3 大模型，精准理解上下文，智能去除 "呃、那个" 等口语废话。

🔄 全异步处理：基于 Celery + Redis 构建稳健的任务队列，支持任务状态轮询与断点重试。

🛡️ 工业级存储：使用 MinIO 替代本地文件存储，模拟真实的云原生生产环境 (S3 协议)。

🛡️ 健壮的兜底策略：内置防崩溃机制，当 AI 无法识别有效内容时自动降级处理，保证服务不中断。

🛠️ 技术栈 (Tech Stack)
后端框架: FastAPI, Uvicorn

异步队列: Celery, Redis

数据库: MySQL 8.0 (SQLAlchemy ORM)

对象存储: MinIO

AI 服务:

ASR: Groq (Whisper-large-v3)

LLM: SiliconFlow (DeepSeek-V3.2)

视频处理: FFmpeg, ffmpeg-python

部署: Docker Compose

🚀 快速开始 (Quick Start)
1. 环境准备
确保本地已安装 Docker Desktop 和 Python 3.8+。

2. 启动基础设施
使用 Docker 一键拉起中间件：

Bash

docker-compose up -d
3. 安装依赖
Bash

# 创建虚拟环境
python -m venv venv
# 激活环境 (Windows)
.\venv\Scripts\activate
# 安装依赖
pip install -r requirements.txt
4. 配置文件
复制 .env.example 为 .env 并填入 API Key：

Ini, TOML

# DeepSeek / 硅基流动配置
OPENAI_API_KEY=sk-xxxx
OPENAI_BASE_URL=[https://api.siliconflow.cn/v1](https://api.siliconflow.cn/v1)
LLM_MODEL_NAME=deepseek-ai/DeepSeek-V3.2

# Groq Whisper 配置 (关键性能优化)
ASR_API_KEY=gsk_xxxx
ASR_API_BASE_URL=[https://api.groq.com/openai/v1](https://api.groq.com/openai/v1)
ASR_MODEL_NAME=whisper-large-v3
5. 启动服务
建议打开两个终端窗口分别运行：

窗口 1: Web API 服务

Bash

python main.py
# 服务运行在: [http://127.0.0.1:8000](http://127.0.0.1:8000)
# 文档地址: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
窗口 2: 异步 Worker

Bash

# Windows 必须加 --pool=solo
celery -A worker.tasks worker --loglevel=info --pool=solo
🧪 自动化测试 (E2E Test)
本项目包含一个端到端测试脚本，可自动验证“上传->处理->下载”全流程。 确保根目录下有 test.mp4 文件，然后运行：

Bash

python test_e2e.py
💡 设计决策与优化 (Design Decisions)
在开发过程中，针对实际业务痛点进行了以下架构优化：

从本地模型迁移至云端 API:

问题: 初始版本使用本地 whisper-small，导致服务器显存占用高，且长视频处理极慢。

优化: 迁移至 Groq API。这不仅将转录速度提升了数倍，还彻底释放了本地算力，使系统能以极低成本运行在普通服务器上。

API 数据格式的鲁棒性处理:

问题: 不同 AI 服务商返回的 JSON 结构差异较大（部分缺少时间戳）。

优化: 编写了适配器模式的解析层，兼容 Object/Dict 多种返回格式，并增加了无时间戳时的兜底逻辑，防止任务崩溃。

Docker 化中间件:

为了保证开发环境与生产环境一致性，所有有状态服务（DB, Redis, MinIO）均通过 Docker Compose 编排。

📂 目录结构
Plaintext

video-ai-backend/
├── api/                # 接口路由层
├── core/               # 核心业务 (AI Agent, Video Editor)
├── db/                 # 数据库模型与连接
├── worker/             # Celery 异步任务定义
├── main.py             # 程序入口
├── docker-compose.yml  # 基础设施编排
└── requirements.txt    # 依赖列表
