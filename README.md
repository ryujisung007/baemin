# 🔬 음료 트렌드 분석 & 배합 설계 플랫폼

**Gemini 2.5 Flash + ChromaDB RAG 기반**

PDF 업로드 → AI 챗봇 대화 → 실시간 보고서 → 배합비 유추까지 원스톱

---

## 🚀 설치 & 실행

```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. 앱 실행
streamlit run app.py
```

## 🔑 필요한 것

- **Gemini API Key** (무료): https://aistudio.google.com/app/apikey
- **PDF 파일 3개**: 거시시장 / 음료시장 / 소비자태도 분석 보고서
- **음료 DB** (선택): 음료개발_데이터베이스_v4-1.xlsx

## 📱 화면 구성

| 페이지 | 기능 |
|--------|------|
| 🏠 홈 | 프로젝트 개요 + 분석 현황 |
| 📊 거시시장 | PDF 업로드 + 자동 요약 + 토픽 필터 챗봇 + 실시간 보고서 |
| 🥤 음료시장 | PDF 업로드 + 자동 요약 + 토픽 필터 챗봇 + 실시간 보고서 |
| 👥 소비자 태도 | PDF 업로드 + 자동 요약 + 토픽 필터 챗봇 + 실시간 보고서 |
| 🧪 음료 DB | DB 업로드 + 트렌드 기반 배합비 설계 챗봇 |
| 📋 통합 보고서 | 크로스 분석 + PDF 다운로드 |

## 🔄 사용 흐름

```
1. API Key 입력 (사이드바)
2. 각 분석 탭에서 PDF 업로드 → 자동 요약 + 벡터화
3. 챗봇으로 질문 → 보고서 섹션 자동 생성
4. "통합 보고서로 보내기" 버튼
5. 통합 분석 탭에서 크로스 분석
6. PDF 다운로드
```

## 🛠️ 기술 스택

| 구성 | 기술 |
|------|------|
| LLM | Gemini 2.5 Flash (cascading fallback) |
| 임베딩 | Gemini text-embedding-004 |
| 벡터DB | ChromaDB (in-memory) |
| PDF 추출 | PyMuPDF |
| UI | Streamlit |
| PDF 생성 | fpdf2 |

## 📁 파일 구조

```
trend_analyzer/
├── app.py              # 메인 Streamlit 앱 (6개 페이지)
├── rag_engine.py       # RAG 파이프라인 (추출→청킹→벡터→챗봇)
├── requirements.txt    # 의존성
└── README.md           # 이 파일
```
