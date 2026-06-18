import streamlit as st
import json
import os
from datetime import datetime
import pypdf
import re

# --- 📱 [1] 브라우저 기본 페이지 설정 (가장 먼저 실행되어야 합니다) ---
st.set_page_config(
    page_title="신입생 학교생활 가이드",
    page_icon="https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp",
    layout="centered"
)

# --- 📱 [2] 태블릿/스마트폰 홈 화면 추가용 메타 태그 안전하게 주입 ---
# (st.markdown 내부에서 중복 따옴표 에러가 나지 않도록 싱글 쿼테이션과 더블 쿼테이션을 올바르게 격리했습니다.)
st.markdown(
    """
    <div style="display:none;">
        <head>
            <meta name="apple-mobile-web-app-title" content="학교생활 가이드">
            <meta name="application-name" content="학교생활 가이드">
            
            <link rel="apple-touch-icon" href="https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp">
            <link rel="apple-touch-icon" sizes="152x152" href="https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp">
            <link rel="apple-touch-icon" sizes="180x180" href="https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp">
            
            <link rel="icon" sizes="192x192" href="https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp">
            <link rel="icon" sizes="512x512" href="https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp">
        </head>
    </div>
    """,
    unsafe_allow_html=True
)

# 데이터 저장용 파일 설정
USER_FILE = "users.json"
# (이하 기존 코드 그대로 유지...)