import uuid
import shutil
import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import VideoTask
from core.storage import upload_file_to_minio
from worker.tasks import process_video_task
router = APIRouter()

@router.post("/upload", summary="上传视频并创建任务")
def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # 1. 验证文件格式
    if not file.filename.endswith(('.mp4', '.mov', '.avi')):
        raise HTTPException(status_code=400, detail="仅支持视频文件 (mp4/mov/avi)")

    # 2. 生成唯一任务 ID
    task_id = str(uuid.uuid4())
    # 为了防止文件名冲突，给文件名加个前缀
    unique_filename = f"{task_id}_{file.filename}"

    try:
        # 3. 上传到 MinIO (核心步骤)
        # file.file 是一个类似文件的对象
        minio_url = upload_file_to_minio(file.file, unique_filename, file.content_type)
        
        # 4. 写入数据库 (MySQL)
        new_task = VideoTask(
            task_id=task_id,
            filename=file.filename,
            original_video_url=minio_url,
            status="pending" # 状态设为排队中
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)

        process_video_task.delay(new_task.task_id)

        return {
            "code": 200,
            "message": "上传成功，任务已创建",
            "data": {
                "task_id": new_task.task_id,
                "url": new_task.original_video_url,
                "status": new_task.status
            }
        }

    except Exception as e:
        print(f"上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}", summary="查询任务状态")
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    task = db.query(VideoTask).filter(VideoTask.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "task_id": task.task_id,
        "status": task.status,
        "result_url": task.processed_video_url
    }