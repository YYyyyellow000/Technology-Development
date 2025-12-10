from celery import Celery

# 配置 Celery 连接 Redis
# 格式: redis://:密码@地址:端口/库
celery_app = Celery(
    "video_worker",
    broker="redis://127.0.0.1:6379/0",
    backend="redis://127.0.0.1:6379/0"
)

# 配置任务模块
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
)