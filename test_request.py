import requests
import json

# 기본 URL
BASE_URL = "http://localhost:8000/api"

def test_upload():
    """문서 업로드 테스트"""
    url = f"{BASE_URL}/upload"

    # 업로드할 파일과 메타데이터 준비
    files = {
        'file': ('sample.txt', open('sample.txt', 'rb'), 'text/plain')
    }

    data = {
        'tenant_id': 'test_tenant',
        'document_type': 'legal_advice',
        'custom_metadata': json.dumps({
            'author': '홍길동',
            'category': '계약법',
            'importance': 'high'
        })
    }

    # 요청 전송
    response = requests.post(url, files=files, data=data)

    # 응답 확인
    print("업로드 응답:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    return response.json()

def test_query():
    """질의 테스트"""
    url = f"{BASE_URL}/query"

    # 질의 데이터 준비
    data = {
        'query': '계약서에서 중요한 법적 고려사항은 무엇인가요?',
        'tenant_id': 'test_tenant',
        'top_k': 3,
        'filters': {
            'document_type': 'legal_advice'
        }
    }

    # 요청 전송
    response = requests.post(url, json=data)

    # 응답 확인
    print("\n질의 응답:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    return response.json()

def create_sample_text():
    """테스트를 위한 샘플 텍스트 파일 생성"""
    sample_text = """
계약서 법률 검토 의견서

1. 계약 개요
본 계약은 A사와 B사 간의 소프트웨어 개발 및 유지보수에 관한 계약입니다.

2. 주요 검토 사항
2.1 지식재산권 조항
- 개발된 소프트웨어의 지식재산권은 A사에 귀속됨
- B사는 개발 과정에서 생성된 모든 산출물의 소유권을 A사에 이전해야 함
- 기존 B사의 지적재산권은 보호되나, A사에게 영구적 사용권 부여

2.2 비밀유지 조항
- 계약 종료 후 5년간 비밀유지 의무 존재
- 정보 유출 시 손해배상 책임 명시

2.3 계약 해지 조항
- 일방적 계약 해지 시 3개월 전 서면 통지 필요
- 중대한 계약 위반 시 최소 2회 시정 기회 부여 후 해지 가능

3. 법적 위험성
- 지식재산권 이전 범위가 지나치게 포괄적임
- 손해배상 한도가 명확하게 설정되어 있지 않음
- 불가항력 조항이 구체적이지 않음

4. 개선 권고사항
- 지식재산권 이전 범위를 구체적으로 한정할 필요 있음
- 손해배상 한도를 계약금액의 100%로 제한하는 조항 추가 필요
- 불가항력 상황의 구체적 예시 및 대응 절차 명시 필요

5. 결론
본 계약은 수정 없이 체결 시 B사에 불리한 조항이 다수 포함되어 있으므로, 위 개선 권고사항을 반영한 수정 협상을 진행할 것을 권고합니다.

작성자: 법무법인 정의
작성일: 2023년 9월 15일
    """

    with open('sample.txt', 'w', encoding='utf-8') as f:
        f.write(sample_text)

    print("샘플 텍스트 파일이 생성되었습니다.")

if __name__ == "__main__":
    # 샘플 텍스트 파일 생성
    create_sample_text()

    # 업로드 테스트
    upload_result = test_upload()

    # 업로드 성공 시 질의 테스트
    if upload_result.get('success'):
        test_query()
