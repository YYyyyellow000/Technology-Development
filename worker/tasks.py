import os
from .celery_app import celery_app
from db.database import SessionLocal
from db.models import VideoTask
from core.storage import upload_file_to_minio, download_file_from_minio
from core.ai_agent import transcribe_audio, analyze_segments
from core.video_editor import extract_audio, cut_and_merge_video

@celery_app.task(bind=True)
def process_video_task(self, task_id: str):
    """后台处理视频任务"""
    print(f"🚀 开始处理任务: {task_id}")
    
    db = SessionLocal()
    # 1. 查询数据库任务
    task = db.query(VideoTask).filter(VideoTask.task_id == task_id).first()
    if not task:
        print(f"❌ 任务不存在: {task_id}")
        return "Task Not Found"

    # 更新状态为处理中
    task.status = "processing"
    db.commit()

    # 定义本地临时文件路径
    local_video_path = f"temp_{task.filename}"
    local_audio_path = f"temp_{task_id}.mp3"
    local_output_path = f"final_{task.filename}"

    try:
        # 2. 从 MinIO 下载视频
        # MinIO 中的文件名是 URL 里的最后一部分，或者我们存的时候用了 unique_filename
        # 这里简化处理，假设我们知道存储的文件名。为了严谨，我们应该在 DB 存 object_name
        # 这里的逻辑假设 MinIO URL 格式是 http://ip:9000/bucket/filename
        object_name = task.original_video_url.split('/')[-1]
        
        print(f"⬇️ 正在下载: {object_name}")
        download_file_from_minio(object_name, local_video_path)

        # 3. 核心 AI 流程 (复用之前的逻辑)
        print("🔊 提取音频...")
        extract_audio(local_video_path, local_audio_path)
        
        print("🤖 AI 识别与分析...")
        segments = transcribe_audio(local_audio_path)
        keep_ranges = analyze_segments(segments)
        
        # 保存 AI 分析结果到数据库
        task.analysis_result = keep_ranges
        db.commit()

        print("✂️ 剪辑视频...")
        cut_and_merge_video(local_video_path, local_output_path, keep_ranges)

        # 4. 上传结果回 MinIO
        print("⬆️ 上传结果...")
        with open(local_output_path, 'rb') as f:
            result_url = upload_file_to_minio(f, f"processed_{task.filename}", "video/mp4")

        # 5. 更新数据库状态完成
        task.status = "completed"
        task.processed_video_url = result_url
        db.commit()
        print(f"✅ 任务完成! 结果链接: {result_url}")

    except Exception as e:
        print(f"❌ 任务失败: {e}")
        task.status = "failed"
        db.commit()
    
    finally:
        # 6. 清理垃圾文件
        for f in [local_video_path, local_audio_path, local_output_path]:
            if os.path.exists(f):
                os.remove(f)
        db.close()

    return "Done"