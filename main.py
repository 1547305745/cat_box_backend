from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os

from api.chat_routes import router as chat_router
from models.database import init_db

app = FastAPI(
    title="不会失忆的AI陪伴应用",
    description="具有长期记忆的AI角色聊天应用",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置静态文件服务
app.mount("/static", StaticFiles(directory="."), name="static")

app.include_router(chat_router)


@app.on_event("startup")
def startup_event():
    os.makedirs("./data", exist_ok=True)
    init_db()


@app.get("/")
def root():
    return FileResponse("index.html")


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
