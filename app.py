import streamlit as st
import json
import os
from datetime import datetime
import pypdf
import re

# --- 📱 [1] 브라우저 탭 및 타이틀 설정 ---
st.set_page_config(
    page_title="신입생 학교생활 가이드",
    page_icon="https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp",
    layout="centered"
)

# --- 📱 [2] 태블릿/스마트폰 홈 화면 추가 시 이름 및 로고 강제 고정 (Manifest 주입) ---
st.markdown(
    """
    <script>
        // 기존에 등록된 메타 태그가 있다면 삭제
        var link = document.querySelector("link[rel*='icon']");
        if (link) { document.head.removeChild(link); }
    </script>
    <head>
        <meta name="apple-mobile-web-app-title" content="학교생활 가이드">
        <meta name="application-name" content="학교생활 가이드">
        
        <link rel="apple-touch-icon" href="https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp">
        <link rel="apple-touch-icon" sizes="152x152" href="https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp">
        <link rel="apple-touch-icon" sizes="180x180" href="https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp">
        
        <link rel="icon" sizes="192x192" href="https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp">
        <link rel="icon" sizes="512x512" href="https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp">
    </head>
    """,
    unsafe_allow_html=True
)

# 데이터 저장용 파일 설정 (이하 기존 코드 동일...)
USER_FILE = "users.json"