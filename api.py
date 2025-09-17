from app.models.document import Document, DocumentChunk, DocumentMetadata
from app.models.api import (
    UploadRequest, UploadResponse, 
    QueryRequest, QueryResponse, QueryResponseSource
)

__all__ = [
    'Document', 'DocumentChunk', 'DocumentMetadata',
    'UploadRequest', 'UploadResponse',
    'QueryRequest', 'QueryResponse', 'QueryResponseSource',
]

# 파일 시스템 구조 확인용 코드
import os

def list_directory_structure(startpath, indent=0):
    print('|' + '-' * indent + startpath.split('/')[-1])
    for f in os.listdir(startpath):
        path = os.path.join(startpath, f)
        if os.path.isdir(path):
            list_directory_structure(path, indent + 4)
        else:
            print('|' + '-' * (indent + 4) + f)

# 루트 디렉토리 경로를 현재 디렉토리로 설정
root_dir = '.'
print('현재 프로젝트 폴더 구조:')
list_directory_structure(root_dir)
