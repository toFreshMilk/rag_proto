#!/bin/bash

# 법틀비즈 RAG 프로토타입 설치 스크립트
echo "법틀비즈 RAG 프로토타입 설치를 시작합니다..."

# 가상환경 생성
python -m venv venv
source venv/bin/activate

# 필요한 패키지 설치
pip install -r requirements.txt

# 디렉토리 구조 생성
mkdir -p data/raw
mkdir -p data/processed
mkdir -p db/chroma

echo "설치가 완료되었습니다!"
echo "서버를 시작하려면 다음 명령어를 실행하세요:"
echo "source venv/bin/activate"
echo "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
