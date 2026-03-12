import os
import random
from typing import Dict, List

import pandas as pd
import streamlit as st


# ------------------------------------------------------
# 기본 설정
# ------------------------------------------------------
st.set_page_config(
    page_title="음료 자동 배합 시뮬레이터",
    layout="wide",
)

st.title("음료 자동 배합 시뮬레이터")
st.caption("엑셀 기반 원재료 DB + 화면 입력형 API Key + 컬럼 자동 검증")


# ------------------------------------------------------
# 화면 입력용 API Key
# ------------------------------------------------------
with st.sidebar:
    st.header("설정")
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-...",
        help="필요 시 화면에서 직접 입력. 입력하지 않아도 시뮬레이터 자체는 동작 가능.",
    )
    excel_path = st.text_input(
        "엑셀 파일 경로",
        value="beverage_AI_DB_v1.xlsx",
        help="Streamlit 앱과 같은 폴더에 있으면 파일명만 입력하면 된다.",
    )

    st.markdown("### 입력 상태")
    st.write(f"API Key 입력 여부: {'입력됨' if api_key else '미입력'}")
    st.write(f"엑셀 경로: {excel_path}")


# ------------------------------------------------------
# 유틸 함수
# ------------------------------------------------------
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    원본 컬럼명을 표준 컬럼명으로 정규화.
    KeyError 방지를 위해 괄호, 공백, 한글 변형 등을 흡수한다.
    """
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    rename_map: Dict[str, str] = {
        "Brix(°)": "Brix",
        "Brix": "Brix",
        "브릭스": "Brix",
        "brix": "Brix",
        "pH": "pH",
        "PH": "pH",
        "산도(%)": "산도",
        "산도": "산도",
        "예상단가(원/kg)": "단가",
        "예상단가": "단가",
        "단가(원/kg)": "단가",
        "단가": "단가",
        "Brix기여도(1%)": "Brix기여도",
        "Brix기여도": "Brix기여도",
        "pH영향도(1%)": "pH영향도",
        "pH영향도": "pH영향도",
        "산도기여도(1%)": "산도기여도",
        "산도기여도": "산도기여도",
        "원료명": "원료명",
        "분류": "분류",
    }

    df = df.rename(columns=rename_map)
    return df


def safe_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """
    숫자 컬럼을 안전하게 숫자로 변환.
    변환 실패 값은 NaN -> 0 처리.
    """
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


def validate_file_exists(path: str) -> bool:
    if not path:
        st.error("엑셀 파일 경로가 비어 있다.")
        return False
    if not os.path.exists(path):
        st.error(f"엑셀 파일을 찾을 수 없다: {path}")
        return False
    return True


def validate_sheet_exists(xls: pd.ExcelFile, sheet_name: str) -> bool:
    if sheet_name not in xls.sheet_names:
        st.error(
            f"시트를 찾을 수 없다: '{sheet_name}' / 현재 시트: {xls.sheet_names}"
        )
        return False
    return True


@st.cache_data
def load_excel_safely(path: str) -> Dict[str, pd.DataFrame]:
    """
    엑셀 전체 로드.
    """
    xls = pd.ExcelFile(path)
    data = {}
    for sheet in xls.sheet_names:
        data[sheet] = pd.read_excel(xls, sheet_name=sheet)
    return data


def find_best_sheet_name(sheet_names: List[str]) -> str:
    """
    원재료 시트명을 자동 탐색.
    """
    priority = [
        "원재료R&D마스터",
        "원재료 R&D 마스터",
        "원재료R&D마스터DB",
        "Sheet3",
    ]
    for p in priority:
        if p in sheet_names:
            return p

    # 유사 이름 탐색
    for s in sheet_names:
        if "원재료" in s:
            return s

    return ""


def validate_required_columns(df: pd.DataFrame, required_cols: List[str]) -> List[str]:
    """
    필수 컬럼 누락 검사
    """
    return [c for c in required_cols if c not in df.columns]


def build_simulation_table(df: pd.DataFrame, category: str) -> pd.DataFrame:
    """
    선택 분류의 샘플 배합표 생성
    """
    sample = df[df["분류"] == category].copy()

    if sample.empty:
        return sample

    # 원료별 사용비율 랜덤 부여
    sample["사용비율(%)"] = [
        round(random.uniform(0.1, 5.0), 4) for _ in range(len(sample))
    ]

    # 기여값 계산
    sample["Brix기여값"] = sample["Brix기여도"] * sample["사용비율(%)"]
    sample["pH영향값"] = sample["pH영향도"] * sample["사용비율(%)"]
    sample["산도기여값"] = sample["산도기여도"] * sample["사용비율(%)"]
    sample["원가기여값"] = sample["단가"] * (sample["사용비율(%)"] / 100.0)

    return sample


def calculate_summary(sample: pd.DataFrame) -> Dict[str, float]:
    """
    배합 결과 요약값 계산
    """
    if sample.empty:
        return {
            "예상 Brix": 0.0,
            "예상 pH": 7.0,
            "예상 산도": 0.0,
            "예상 원가": 0.0,
        }

    final_brix = round(sample["Brix기여값"].sum(), 4)
    final_ph = round(7.0 + sample["pH영향값"].sum(), 4)
    final_acidity = round(sample["산도기여값"].sum(), 4)
    final_cost = round(sample["원가기여값"].sum(), 2)

    return {
        "예상 Brix": final_brix,
        "예상 pH": final_ph,
        "예상 산도": final_acidity,
        "예상 원가": final_cost,
    }


# ------------------------------------------------------
# 데이터 로드 및 검증
# ------------------------------------------------------
if not validate_file_exists(excel_path):
    st.stop()

try:
    all_sheets = load_excel_safely(excel_path)
except Exception as e:
    st.error(f"엑셀 파일 로드 중 오류가 발생했다: {e}")
    st.stop()

sheet_names = list(all_sheets.keys())

st.subheader("엑셀 시트 목록")
st.write(sheet_names)

raw_sheet_name = find_best_sheet_name(sheet_names)
if not raw_sheet_name:
    st.error("원재료 시트를 찾지 못했다. 시트명에 '원재료'가 포함되어야 한다.")
    st.stop()

raw_df = all_sheets[raw_sheet_name].copy()
df = normalize_columns(raw_df)

required_cols = [
    "원료명",
    "분류",
    "Brix",
    "pH",
    "산도",
    "단가",
    "Brix기여도",
    "pH영향도",
    "산도기여도",
]

missing_cols = validate_required_columns(df, required_cols)

st.subheader("컬럼 검증")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**원본 컬럼명**")
    st.write(list(raw_df.columns))
with col2:
    st.markdown("**정규화 후 컬럼명**")
    st.write(list(df.columns))

if missing_cols:
    st.error(f"필수 컬럼이 누락되었다: {missing_cols}")
    st.stop()

df = safe_numeric(
    df,
    ["Brix", "pH", "산도", "단가", "Brix기여도", "pH영향도", "산도기여도"],
)

# 빈값/결손 최소 검증
row_count_before = len(df)
df = df.dropna(subset=["원료명", "분류"]).copy()
row_count_after = len(df)

if row_count_after == 0:
    st.error("원료명/분류 데이터가 없어 시뮬레이션을 진행할 수 없다.")
    st.stop()

if row_count_before != row_count_after:
    st.warning(
        f"원료명 또는 분류가 비어 있는 행 {row_count_before - row_count_after}개를 제외했다."
    )

# ------------------------------------------------------
# 데이터 미리보기
# ------------------------------------------------------
st.subheader("원재료 데이터 미리보기")
st.dataframe(df, use_container_width=True)

# ------------------------------------------------------
# 시뮬레이션 UI
# ------------------------------------------------------
categories = sorted(df["분류"].dropna().astype(str).unique().tolist())

if not categories:
    st.error("선택 가능한 분류가 없다.")
    st.stop()

selected_category = st.selectbox("원료 분류 선택", categories)

sample = build_simulation_table(df, selected_category)

if sample.empty:
    st.warning("선택한 분류에 해당하는 데이터가 없다.")
    st.stop()

summary = calculate_summary(sample)

# ------------------------------------------------------
# 결과 출력
# ------------------------------------------------------
st.subheader("배합 샘플 결과")

m1, m2, m3, m4 = st.columns(4)
m1.metric("예상 Brix", summary["예상 Brix"])
m2.metric("예상 pH", summary["예상 pH"])
m3.metric("예상 산도", summary["예상 산도"])
m4.metric("예상 원가", summary["예상 원가"])

st.dataframe(sample, use_container_width=True)

# ------------------------------------------------------
# 추가 진단 정보
# ------------------------------------------------------
with st.expander("디버그 정보"):
    st.write("사용 시트명:", raw_sheet_name)
    st.write("현재 행 수:", len(df))
    st.write("현재 분류 목록:", categories)
    st.write("API Key 입력 여부:", bool(api_key))
