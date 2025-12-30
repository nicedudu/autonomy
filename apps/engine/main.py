#!/usr/bin/env python3
import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

def main():
    print("=== Autonomy Engine 控制平面启动 ===")
    # 启动 FastAPI 服务
    # 使用字符串形式 "core.api_server:app" 以支持 reload 模式
    uvicorn.run("core.api_server:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
