import streamlit as st
import pandas as pd
from datetime import datetime
from collections import Counter
from pypdf import PdfReader
import os
import re

# 1. 스트림릿 페이지 기본 설정
st.set_page_config(page_title="신입생 규정 안내 시스템", page_icon="🏫", layout="centered")

# 2. 모든 구역 가독성 완벽 고정 CSS 주입
st.markdown("""
    <style>
    /* 전체 배경색 */
    .stApp {
        background-color: #f4f9f5 !important;
    }
    
    /* 1. 입력창 배경 흰색, 글씨 완전 새까만 검은색 강제 고정 */
    input {
        color: #000000 !important;
        background-color: #ffffff !important;
        -webkit-text-fill-color: #000000 !important;
    }
    
    /* 입력창 내부 힌트 텍스트 색상 */
    input::placeholder {
        color: #777777 !important;
    }
    
    /* 2. 아코디언 관련 모든 글씨 진한 검은색으로 강제 고정 */
    .streamlit-expanderHeader, .st-emotion-cache-sh2vno, p, span, li {
        color: #111111 !important;
    }
    
    svg {
        fill: #111111 !important;
    }
    
    /* 3. 왼쪽 사이드바(메뉴 이동) 어두운 배경 대응 - 글씨 밝게 올리기 */
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {
        color: #f0f5f2 !important; 
    }
    
    /* 사이드바 제목 글씨는 더 뚜렷하고 밝게 */
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        font-weight: 800 !important;
    }
    
    /* 4. 스트림릿 기본 버튼 커스텀 스타일 (초록 그라데이션 + 흰 글씨) */
    div.stButton > button {
        background: linear-gradient(135deg, #2b5c3a, #4caf50) !important;
        color: #ffffff !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
    }
    
    div.stButton > button:hover {
        background: linear-gradient(135deg, #1e4228, #3b873e) !important;
        color: #ffffff !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15) !important;
    }
    
    /* 상단 대형 웰컴 헤더 박스 */
    .welcome-banner {
        background: linear-gradient(135deg, #2b5c3a, #4caf50);
        padding: 40px 20px;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(43, 92, 58, 0.15);
        margin-bottom: 30px;
    }
    
    .welcome-banner h1 {
        color: #ffffff !important;
        font-size: 32px !important;
        font-weight: 800 !important;
        margin: 0 0 10px 0 !important;
    }
    
    .welcome-banner p {
        color: #e8f5e9 !important;
        font-size: 16px !important;
        margin: 0 !important;
        opacity: 0.9;
    }
    
    /* 가이드 안내 카드 */
    .guide-card {
        background-color: #ffffff;
        border: 1px solid #e0ebd3;
        border-left: 6px solid #2b5c3a;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 30px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        color: #3a6b4c !important;
    }
    
    .guide-card-title {
        font-size: 16px !important;
        font-weight: 700 !important;
        color: #2b5c3a;
        margin-bottom: 6px;
    }
    
    /* 입력창 상단 라벨 */
    .search-label {
        font-size: 16px !important;
        font-weight: 700 !important;
        color: #2b5c3a;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# 3. 파일 경로 설정 (동일 폴더 기준)
PDF_FILE_PATH = "2025. 학생생활규정.pdf"

# --- [PDF 텍스트 추출 함수 (캐싱)] ---
@st.cache_data
def load_pdf_text(file_path):
    if not os.path.exists(file_path):
        return None
    reader = PdfReader(file_path)
    pages_text = []
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            clean_text = " ".join(text.split())
            pages_text.append({"page": page_num + 1, "text": clean_text})
    return pages_text

pdf_data = load_pdf_text(PDF_FILE_PATH)

if "logs" not in st.session_state:
    st.session_state.logs = []

# 사이드바 메뉴
st.sidebar.markdown("### 🗺️ 메뉴 이동")
menu = st.sidebar.radio("원하는 창을 선택하세요", ["학생용 규정 검색창", "관리자 모드"])

# --- [메뉴 1: 학생용 검색창] ---
if menu == "학생용 규정 검색창":
    st.markdown("""
        <div class="welcome-banner">
            <h1>🏫 반가워요, 신입생 여러분!</h1>
            <p>우리 학교의 생활 규정 및 교복 규정을 통합 검색하는 시스템입니다.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="guide-card">
            <div class="guide-card-title">💡 스마트 검색 가이드</div>
            복잡한 문장 대신 <span style="color:#2b5c3a; font-weight:700;">'두발', '체육복', '치마', '휴대폰'</span> 같이 궁금한 핵심 단어만 입력하시면 규정집에서 관련된 조항과 정확한 페이지를 즉시 찾아드립니다.
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='search-label'>🔍 어떤 규정이 궁금한가요?</div>", unsafe_allow_html=True)
    
    user_question = st.text_input(
        "질문을 입력하세요", 
        placeholder="단어를 입력하고 아래 버튼을 누르거나 엔터를 치세요.", 
        label_visibility="collapsed"
    )
    
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    
    if st.button("✨ 학교 규정집 검색하기"):
        if user_question.strip() != "":
            query = user_question.strip()
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.logs.append({"일시": now, "질문": query})
            
            if pdf_data is None:
                st.error("❌ 학교 규정집 PDF 파일을 찾을 수 없습니다. 파일명을 확인해 주세요.")
            else:
                results = []
                for page_info in pdf_data:
                    text = page_info["text"]
                    if query in text:
                        # 🌟 [기능 업그레이드] 전체 페이지를 보여주는 대신, 정규식을 사용하여 문장 단위로 쪼갭니다.
                        # 제X조, 마침표(.), 혹은 주요 조항 단위를 기준으로 문장을 분리합니다.
                        sentences = re.split(r'(?=제\s*\d+\s*조)|(?<=\.)', text)
                        
                        for sentence in sentences:
                            if query in sentence:
                                clean_sentence = sentence.strip()
                                # 너무 짧은 찌꺼기 문장은 제외
                                if len(clean_sentence) > len(query) + 2:
                                    results.append({
                                        "page": page_info["page"], 
                                        "matched_text": clean_sentence
                                    })
                
                if results:
                    st.success(f"🎉 '{query}' 관련 핵심 조항을 총 {len(results)}개 찾아냈습니다!")
                    for idx, res in enumerate(results):
                        # 페이지의 불필요한 정보는 숨기고 깔끔하게 핵심 문장만 노출
                        with st.expander(f"📄 관련 조항 {idx+1} (학교 규정집 {res['page']}페이지 부근)"):
                            highlighted_text = res["matched_text"].replace(
                                query, 
                                f"<span style='background-color: #fff176; font-weight: bold; padding: 2px 4px; border-radius: 4px;'>{query}</span>"
                            )
                            st.markdown(f"<p style='color:#111111 !important; line-height: 1.8; font-size:15px;'>{highlighted_text}</p>", unsafe_allow_html=True)
                else:
                    st.warning(f"💡 '{query}'에 대한 직접적인 단어가 규정집에 명시되어 있지 않습니다.")
        else:
            st.warning("검색어를 입력해 주세요.")

# --- [메뉴 2: 관리자 창] ---
elif menu == "관리자 모드":
    st.markdown("<h2 style='color:#2b5c3a; font-weight:800;'>🔒 관리자 전용 페이지</h2>", unsafe_allow_html=True)
    password = st.text_input("관리자 비밀번호를 입력하세요", type="password")
    
    if password == "12345":
        st.success("인증 완료되었습니다.")
        st.divider()
        if st.session_state.logs:
            df = pd.DataFrame(st.session_state.logs)
            st.markdown("<h3 style='color:#2b5c3a;'>📊 가장 많이 검색된 키워드 TOP 5</h3>", unsafe_allow_html=True)
            question_counts = Counter(df["질문"])
            top_5 = question_counts.most_common(5)
            top_5_data = [{"순위": i+1, "검색어": item[0], "검색 횟수": f"{item[1]}회"} for i, item in enumerate(top_5)]
            st.table(pd.DataFrame(top_5_data))
            st.divider()
            st.markdown("<h3 style='color:#2b5c3a;'>📋 전체 검색 기록 실시간 로그</h3>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("아직 학생들이 검색한 기록이 없습니다.")
    elif password != "" and password != "12345":
        st.error("비밀번호가 틀렸습니다. 다시 시도해 주세요.")