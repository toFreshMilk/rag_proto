#!/bin/bash

# 가상환경 활성화
source venv/bin/activate

# 서버 시작
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
