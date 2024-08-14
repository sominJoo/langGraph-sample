# langGraph-sample


## 1차 개발 항목
- LangGraph를 통한 Custom Support Bot 구축


## 2차 개발 항목
- 시나리오와 연관된 샘플코드 작성

## Skills
- Django
- Python
- Langchain


## 프로젝트 설정
1. Clone Repository
```
git clone https://github.com
```
2. Install Package
```
pip install -r requirements.txt
```
3. 가상 환경 활성화
```
source .venv/bin/activate
```
4. 인터프리터 설정(설정이 안되어 있을 시)
- 설정 > 프로젝트 > Python 인터프리터
- 인터프리터 추가 > 로컬 인터프리터 추가 > Virtualenv 환경 > 기존 > 현재 프로젝트의 .venv/bin/python3.11 선택 후 저장

4. Run server
```
python3 manage.py server
```


## 메소드 및 import 경로 수정 시 오류
- 메소드 및 Import 경로 수정을 한 뒤 오류가 나면 가상환경 재설치 필요
1. 가상 환경 비활성화
```
deactivate
```

2. 가상 환경 삭제 (필요 시)
```
rm -rf .venv
```

3. 새로운 가상 환경 생성
```
python -m venv .venv
```

4. 가상 환경 활성화
```
source .venv/bin/activate
```

5. 패키지 재설치
```
pip install -r requirements.txt
```
