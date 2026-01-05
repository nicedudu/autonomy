#!/usr/bin/env python3
import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

def main():
    print("=== Autonomy Engine 控制平面启动 ===")
    # 启动 FastAPI 服务
    # 切换至新的 api 模块化架构
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
