import uvicorn
from fastapi import FastAPI
from api.routes import router
from db.database import engine, Base

# 1. 确保数据库表已创建
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI 视频剪辑服务")

# 2. 注册路由
app.include_router(router, prefix="/api/video", tags=["Video"])

@app.get("/")
def root():
    return {"message": "Video AI Backend is Running!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)