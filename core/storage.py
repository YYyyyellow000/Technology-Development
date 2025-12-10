import os
from minio import Minio
from dotenv import load_dotenv

load_dotenv()

# MinIO 配置
MINIO_ENDPOINT = "127.0.0.1:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
BUCKET_NAME = "videos"

# 初始化客户端
client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

def upload_file_to_minio(file_data, file_name, content_type):
    """上传文件到 MinIO 并返回访问 URL"""
    
    # 1. 检查桶是否存在
    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)
        policy = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":["*"]},"Action":["s3:GetObject"],"Resource":["arn:aws:s3:::%s/*"]}]}' % BUCKET_NAME
        client.set_bucket_policy(BUCKET_NAME, policy)

    # 2. 上传文件
    # 这里的 length=-1 配合 part_size 适用于流式上传
    client.put_object(
        BUCKET_NAME, 
        file_name, 
        file_data, 
        length=-1, 
        part_size=10*1024*1024, 
        content_type=content_type
    )

    # 3. 返回链接
    url = f"http://{MINIO_ENDPOINT}/{BUCKET_NAME}/{file_name}"
    return url

# --- 刚才报错就是缺下面这个函数，请务必加上 ---
def download_file_from_minio(object_name, file_path):
    """从 MinIO 下载文件到本地路径"""
    try:
        # get_object 返回的是一个 HTTPResponse 流
        response = client.get_object(BUCKET_NAME, object_name)
        with open(file_path, 'wb') as file_data:
            for d in response.stream(32*1024):
                file_data.write(d)
        response.close()
        response.release_conn()
        return True
    except Exception as e:
        print(f"MinIO 下载失败: {e}")
        return False