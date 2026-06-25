import streamlit as st
import json
import os
from datetime import datetime
import pypdf
import re
import base64

# --- 📱 [1] 브라우저 레이아웃 및 앱 설정 ---
st.set_page_config(
    page_title="신입생 학교생활 가이드",
    page_icon="https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- 📂 [2] 데이터 파일 경로 정의 및 로딩 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_FILE = os.path.join(BASE_DIR, "users.json")
CHAT_FILE = os.path.join(BASE_DIR, "chats.json")
COMMUNITY_FILE = os.path.join(BASE_DIR, "community.json")
PDF_FILE = os.path.join(BASE_DIR, "2025. 학생생활규정.pdf")

BAD_WORDS = ["바보", "멍청이", "지랄", "존나", "개새끼", "시발", "새끼", "미친"]

def load_data(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content: return json.loads(content)
        except: pass
    return {}

def save_data(filepath, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f: 
            json.dump(data, f, ensure_ascii=False, indent=4)
    except: pass

def load_community_safe():
    data = load_data(COMMUNITY_FILE)
    if not isinstance(data, dict): data = {}
    if "posts" not in data: data["posts"] = []
    if "polls" not in data: 
        data["polls"] = [{
            "question": "2026학년도 축제 연예인 초청 찬반 투표",
            "options": ["찬성 (예산 활용 선호)", "반대 (동아리 부스 집중)"],
            "votes": {}
        }]
    if "notice" not in data: data["notice"] = "아직 등록된 공지사항이 없습니다."
    if "bg_settings" not in data:
        data["bg_settings"] = {
            "image": "https://images.unsplash.com/photo-1519681393784-d120267933ba",
            "pos_x": 50,
            "pos_y": 50,
            "zoom": 100,
            "opacity": 0.85
        }
    return data

users = load_data(USER_FILE)
chats = load_data(CHAT_FILE)
community = load_community_safe()

# --- 🔄 [3] 세션 상태 초기화 및 공용 파일 데이터 강제 동기화 ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_id" not in st.session_state: st.session_state.user_id = None
if "user_name" not in st.session_state: st.session_state.user_name = None
if "role" not in st.session_state: st.session_state.role = "user"

# 💡 모든 사용자가 community.json에 저장된 동일한 값을 바라보게 설계 (동기화 핵심)
st.session_state.bg_image = community["bg_settings"]["image"]
st.session_state.bg_pos_x = community["bg_settings"]["pos_x"]
st.session_state.bg_pos_y = community["bg_settings"]["pos_y"]
st.session_state.bg_zoom = community["bg_settings"]["zoom"]
st.session_state.bg_opacity = community["bg_settings"]["opacity"]

if "device_info" not in st.session_state: st.session_state.device_info = "분석 중..."
if "hardware_detail" not in st.session_state: st.session_state.hardware_detail = "확인 중..."
if "trigger_vibrate" not in st.session_state: st.session_state.trigger_vibrate = False
if "trigger_speak" not in st.session_state: st.session_state.trigger_speak = ""

# --- 🎨 [4] 실시간 배경 렌더링 함수 ---
def render_live_background():
    st.markdown(
        f"""
        <style>
            header, [data-testid="stHeader"], .st-emotion-cache-18ni7th, .stAppHeader {{
                background-color: transparent !important; background: transparent !important; border: none !important; box-shadow: none !important; height: 0px !important;
            }}
            .main .block-container {{ padding-top: 2rem !important; }}
            .stApp {{
                background-image: linear-gradient(rgba(14, 17, 23, {st.session_state.bg_opacity}), rgba(14, 17, 23, {st.session_state.bg_opacity})), url("{st.session_state.bg_image}") !important;
                background-size: {st.session_state.bg_zoom}% !important; 
                background-position: {st.session_state.bg_pos_x}% {st.session_state.bg_pos_y}% !important;
                background-repeat: no-repeat !important; 
                background-attachment: fixed !important; 
                padding-bottom: 150px !important;
            }}
            h1, h2, h3, h4, p, span, label, li {{ color: #ffffff !important; text-shadow: 1px 1px 4px rgba(0,0,0,0.85); }}
            .stMarkdown div p {{ color: #ffffff !important; }}
            [data-testid="stSidebar"] {{ 
                background-color: rgba(30, 41, 59, 0.95) !important; 
                border-right: 2px solid #1d4ed8 !important;
            }}
            [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {{
                background-color: #0f172a !important; border: 1px solid #334155 !important;
                padding: 8px 12px !important; border-radius: 6px !important; margin-bottom: 6px !important; color: #ffffff !important;
            }}
            .stButton>button {{
                background-color: #1d4ed8 !important; color: #ffffff !important; border-radius: 6px !important; border: none !important; font-weight: bold !important;
            }}
            .stButton>button:hover {{ background-color: #2563eb !important; box-shadow: 0px 0px 8px rgba(37, 99, 235, 0.6); }}
            input[type="text"], input[type="password"], textarea {{ color: #ffffff !important; background-color: #1f2937 !important; border: 1px solid #4b5563 !important; }}
            
            div[data-testid="stTextInput"]:has(input[aria-label="hidden_login_bridge"]),
            div[data-testid="stTextInput"]:has(input[aria-label="hidden_device_bridge"]),
            div[data-testid="stTextInput"]:has(input[aria-label="hidden_detail_hardware_bridge"]) {{
                display: none !important; visibility: hidden !important; height: 0px !important; position: absolute !important; top: -9999px !important;
            }}
            footer {{ visibility: hidden !important; display: none !important; }}
            .log-box {{ background-color: #1e293b; border: 1px solid #3b82f6; border-radius: 8px; padding: 15px; margin-top: 10px; max-height: 400px; overflow-y: auto; }}
        </style>
        """,
        unsafe_allow_html=True
    )

render_live_background()

# --- 🛠 Ori [5] 자바스크립트 브릿지 (로그인 유지력) ---
bridge_val = st.text_input("hidden_login_bridge", key="hidden_login_bridge", label_visibility="collapsed")
st.components.v1.html(
    """
    <script>
        const parentDoc = window.parent.document;
        const saved = localStorage.getItem("saved_user_info");
        if (saved) {
            const input = parentDoc.querySelector('input[aria-label="hidden_login_bridge"]');
            if (input && input.value !== saved) {
                input.value = saved;
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    </script>
    """, height=0
)

if not st.session_state.logged_in and bridge_val:
    try:
        u_info = json.loads(bridge_val)
        if u_info["id"] in users:
            st.session_state.logged_in = True
            st.session_state.user_id = u_info["id"]
            st.session_state.user_name = users[u_info["id"]]["name"]
            st.session_state.role = users[u_info["id"]].get("role", "user")
            st.rerun()
    except: pass

device_ua = st.text_input("hidden_device_bridge", key="hidden_device_bridge", label_visibility="collapsed")
st.components.v1.html(
    """
    <script>
        const parentDoc = window.parent.document;
        const ua = navigator.userAgent;
        const input = parentDoc.querySelector('input[aria-label="hidden_device_bridge"]');
        if (input && input.value !== ua) {
            input.value = ua;
            input.dispatchEvent(new Event('input', { bubbles: true }));
        }
    </script>
    """, height=0
)
def parse_device_info(ua_string):
    if not ua_string: return "알 수 없는 기기"
    ua = ua_string.lower()
    if "android" in ua: return "Android 📱"
    elif "iphone" in ua or "ipad" in ua: return "iOS 🍏"
    elif "windows" in ua: return "Windows PC 💻"
    elif "macintosh" in ua: return "Mac 💻"
    return "기타 기기"
if device_ua: st.session_state.device_info = parse_device_info(device_ua)

hardware_json = st.text_input("hidden_detail_hardware_bridge", key="hidden_detail_hardware_bridge", label_visibility="collapsed")
st.components.v1.html(
    """
    <script>
        const parentDoc = window.parent.document;
        const input = parentDoc.querySelector('input[aria-label="hidden_detail_hardware_bridge"]');
        async function getHardwareSpecs() {
            let batteryInfo = "지원 안 함";
            try {
                if (navigator.getBattery) {
                    const battery = await navigator.getBattery();
                    batteryInfo = `${Math.round(battery.level * 100)}% (${battery.charging ? '⚡충전중' : '🔋배터리'})`;
                }
            } catch(e) {}
            const specData = { "battery": batteryInfo, "network": navigator.onLine ? "🌐 온라인" : "❌ 오프라인" };
            const strData = JSON.stringify(specData);
            if (input && input.value !== strData) {
                input.value = strData;
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
        getHardwareSpecs();
    </script>
    """, height=0
)
if hardware_json:
    try:
        h_data = json.loads(hardware_json)
        st.session_state.hardware_detail = f"배터리: {h_data.get('battery')} | 네트워크: {h_data.get('network')}"
    except: pass

js_controls = f"""
<script>
    if ({'true' if st.session_state.trigger_vibrate else 'false'}) {{
        if (navigator.vibrate) {{ navigator.vibrate([200, 100, 200]); }}
    }}
    const speechText = "{st.session_state.trigger_speak}";
    if (speechText !== "") {{
        if ('speechSynthesis' in window) {{
            const utterance = new SpeechSynthesisUtterance(speechText);
            utterance.lang = 'ko-KR';
            window.speechSynthesis.speak(utterance);
        }}
    }}
    window.toggleFullScreen = function() {{
        if (!document.fullscreenElement) {{ document.documentElement.requestFullscreen().catch(err => {{}}); }}
        else {{ document.exitFullscreen(); }}
    }}
</script>
"""
st.components.v1.html(js_controls, height=0)
st.session_state.trigger_vibrate = False
st.session_state.trigger_speak = ""

# --- 📄 [6] PDF 텍스트 파서 및 검색 고도화 완료 ---
@st.cache_resource
def load_pdf_text(filepath):
    if not os.path.exists(filepath): return ""
    text = ""
    try:
        reader = pypdf.PdfReader(filepath)
        for page in reader.pages: text += page.extract_text() + "\n"
    except: pass
    return text

def search_pdf_with_highlight(query, pdf_text):
    if not pdf_text: return "⚠️ 현재 서버에 학교 규정집 PDF 파일이 없습니다."
    keywords = [kw for kw in query.split() if len(kw) > 1]
    if not keywords: return "🔍 검색어를 두 글자 이상 입력해 주세요."
    sections = re.split(r'(제\s*\d+\s*조)', pdf_text)
    results = []
    for i in range(1, len(sections), 2):
        section_title = sections[i].strip()
        section_content = sections[i+1] if i+1 < len(sections) else ""
        if any(kw in section_content for kw in keywords):
            full_text = section_title + section_content
            for kw in keywords:
                full_text = re.sub(f"({re.escape(kw)})", r"<mark style='background-color: #FFEB3B; color: #000000; padding: 2px 4px; border-radius: 3px; font-weight: bold;'>\1</mark>", full_text)
            results.append(full_text.strip())
            if len(results) >= 3: break
    if results:
        output = "🔍 **규정집 내부 매칭된 조항 검색 결과:**\n\n"
        for res in results: output += f"<div style='background-color: #F8F9FA; color: #1E293B; padding: 18px; border-radius: 8px; margin-bottom: 12px; border-left: 5px solid #FF4B4B; white-space: pre-wrap;'>{res}</div>"
        return output
    return "🔍 규정집에서 관련 조항을 찾지 못했습니다."

pdf_content = load_pdf_text(PDF_FILE)

if "admin" not in users:
    users["admin"] = {"password": "ahsknue2026_2026!", "name": "최고관리자", "role": "master_admin"}
    save_data(USER_FILE, users)

def check_bad_words(text):
    for word in BAD_WORDS:
        if word in text: return False, word
    return True, ""

# --- 🖥️ 메인 랜더링 인터페이스 ---
col_logo, col_title = st.columns([1, 4])
with col_logo: st.image("https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp", width=110)
with col_title:
    st.markdown("<div style='padding-top: 15px;'></div>", unsafe_allow_html=True)
    st.title("신입생 학교생활 가이드 & 소통망")

st.markdown("---")

if not st.session_state.logged_in:
    st.info("👋 안녕하세요! 서비스를 이용하시려면 로그인이나 회원가입을 진행해 주세요.")
    auth_tab1, auth_tab2 = st.tabs(["🔑 로그인", "📝 회원가입"])

    with auth_tab1:
        u_id_input = st.text_input("학번 / 아이디", key="login_id_main")
        u_pw_input = st.text_input("비밀번호", type="password", key="login_pw_main")
        if st.button("로그인하기", use_container_width=True):
            if u_id_input in users and users[u_id_input]["password"] == u_pw_input:
                st.session_state.logged_in = True
                st.session_state.user_id = u_id_input
                st.session_state.user_name = users[u_id_input]["name"]
                st.session_state.role = "master_admin" if u_id_input == "admin" else users[u_id_input].get("role", "user")
                
                sess_str = json.dumps({"id": st.session_state.user_id, "name": st.session_state.user_name, "role": st.session_state.role}, ensure_ascii=False)
                st.components.v1.html(f"<script>localStorage.setItem('saved_user_info', JSON.stringify({sess_str}));</script>", height=0)
                st.rerun()
            else: st.error("계정 정보가 올바르지 않습니다.")

    with auth_tab2:
        new_id = st.text_input("학번 (숫자만)", key="join_id_main")
        new_name = st.text_input("이름 (한글 3~4자)", key="join_name_main")
        new_pw = st.text_input("비밀번호", type="password", key="join_pw_main")
        if st.button("가입하기", use_container_width=True):
            if new_id and new_name and new_pw:
                if new_id in users: st.error("이미 존재하는 학번입니다.")
                else:
                    users[new_id] = {"password": new_pw, "name": new_name, "role": "user"}
                    save_data(USER_FILE, users)
                    st.success("회원가입 완료! 로그인해 주세요.")

else:
    st.sidebar.markdown(f"### 👤 {st.session_state.user_name}님")
    is_admin_user = (st.session_state.user_id == "admin" or st.session_state.role in ["master_admin", "sub_admin"])
    st.sidebar.markdown(f"👑 **등급:** `관리자`" if is_admin_user else "🎓 **등급:** `일반 학생`")
    st.sidebar.markdown(f"🌐 **기기:** `{st.session_state.device_info}`")
    st.sidebar.markdown(f"🔋 **상태:** `{st.session_state.hardware_detail}`")

    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.components.v1.html("<script>localStorage.removeItem('saved_user_info');</script>", height=0)
        st.rerun()

    st.sidebar.markdown("---")
    
    # 🔒 관리자 권한 철통 방어 분기점 (일반 학생에게는 배경 설정 노출 안 됨)
    if is_admin_user:
        admin_menu = ["🏠 가이드 메인 홈", "🎨 실시간 배경 설정실", "🔍 전체 계정 관리", "📢 공지 및 투표 관리", "🏛️ 커뮤니티 게시글 관리", "💬 학생 질문 통계 및 로그"]
        menu_choice = st.sidebar.radio("제어판 선택", admin_menu, key="adm_sel")
    else:
        menu_choice = "🏠 가이드 메인 홈"

    # ==================== [[ 🎨 실시간 배경 설정실 (오직 관리자 전용) ]] ====================
    if is_admin_user and menu_choice == "🎨 실시간 배경 설정실":
        st.subheader("🎨 실시간 배경화면 관리용 대시보드")
        st.write("여기서 속성을 변경하면 공용 DB 파일에 즉시 영구 저장되어 전교생의 배경화면이 실시간 동기화됩니다.")
        st.write("---")
        col_bg1, col_bg2 = st.columns([1, 1])
        
        with col_bg1:
            uploaded_file = st.file_uploader("이미지 업로드 (png, jpg)", type=["png", "jpg", "jpeg"], key="rt_up")
            if uploaded_file is not None:
                file_bytes = uploaded_file.read()
                file_ext = uploaded_file.name.split('.')[-1].lower()
                mime = "image/png" if file_ext == "png" else "image/jpeg"
                base64_str = base64.b64encode(file_bytes).decode('utf-8')
                
                community["bg_settings"]["image"] = f"data:{mime};base64,{base64_str}"
                save_data(COMMUNITY_FILE, community)
                st.rerun()
                
            new_zoom = st.slider("🔍 확대/축소 (%)", 30, 300, int(st.session_state.bg_zoom), step=5)
            if new_zoom != st.session_state.bg_zoom:
                community["bg_settings"]["zoom"] = new_zoom
                save_data(COMMUNITY_FILE, community); st.rerun()
                
            new_opacity = st.slider("🌙 배경 불투명도 가독성 필터", 0.0, 1.0, float(st.session_state.bg_opacity), step=0.05)
            if new_opacity != st.session_state.bg_opacity:
                community["bg_settings"]["opacity"] = new_opacity
                save_data(COMMUNITY_FILE, community); st.rerun()
        
        with col_bg2:
            st.write(f"위치 매핑 -> X: `{st.session_state.bg_pos_x}%` | Y: `{st.session_state.bg_pos_y}%`")
            bc1, bc2, bc3 = st.columns([1, 1, 1])
            with bc2:
                if st.button("▲ 위로"):
                    community["bg_settings"]["pos_y"] = max(0, st.session_state.bg_pos_y - 10)
                    save_data(COMMUNITY_FILE, community); st.rerun()
            bl, bc, br = st.columns([1, 1, 1])
            with bl:
                if st.button("◀ 왼쪽"):
                    community["bg_settings"]["pos_x"] = max(0, st.session_state.bg_pos_x - 10)
                    save_data(COMMUNITY_FILE, community); st.rerun()
            with bc:
                if st.button("🎯 중앙"):
                    community["bg_settings"]["pos_x"] = 50; community["bg_settings"]["pos_y"] = 50
                    save_data(COMMUNITY_FILE, community); st.rerun()
            with br:
                if st.button("오른쪽 ▶"):
                    community["bg_settings"]["pos_x"] = min(100, st.session_state.bg_pos_x + 10)
                    save_data(COMMUNITY_FILE, community); st.rerun()
            with bc2:
                if st.button("▼ 아래"):
                    community["bg_settings"]["pos_y"] = min(100, st.session_state.bg_pos_y + 10)
                    save_data(COMMUNITY_FILE, community); st.rerun()

    # ==================== [[ 🛠️ 관리자 대시보드 ]] ====================
    elif is_admin_user and menu_choice != "🏠 가이드 메인 홈":
        st.subheader(f"⚙️ 관리 제어판 -> {menu_choice}")
        
        if menu_choice == "🔍 전체 계정 관리":
            search_uid = st.text_input("학번 검색")
            t_users = {search_uid: users[search_uid]} if search_uid in users else users
            for u_id, u_info in t_users.items():
                if u_id == "admin": continue
                with st.expander(f"👤 {u_info['name']} ({u_id})"):
                    en = st.text_input("이름 변경", value=u_info['name'], key=f"e_n_{u_id}")
                    ep = st.text_input("비번 변경", value=u_info['password'], key=f"e_p_{u_id}")
                    if st.button("수정 저장", key=f"s_b_{u_id}"):
                        users[u_id].update({"name": en, "password": ep})
                        save_data(USER_FILE, users)
                        st.success("수정 완료!")

        elif menu_choice == "📢 공지 및 투표 관리":
            new_notice = st.text_area("공지 수정", value=community.get("notice", ""))
            if st.button("📢 공지 업데이트", use_container_width=True):
                community["notice"] = new_notice
                save_data(COMMUNITY_FILE, community)
                st.success("반영 완료!")

        elif menu_choice == "🏛️ 커뮤니티 게시글 관리":
            for idx, post in enumerate(community.get("posts", [])):
                with st.expander(f"✍️ [{post.get('author')}] {post.get('content')[:15]}..."):
                    if st.button("🗑️ 삭제", key=f"d_p_{idx}"):
                        community["posts"].pop(idx)
                        save_data(COMMUNITY_FILE, community)
                        st.rerun()

        elif menu_choice == "💬 학생 질문 통계 및 로그":
            col_l, col_r = st.columns(2)
            with col_l: search_uid = st.text_input("조회할 학생 학번")
            with col_r:
                st.markdown("#### 📦 하드웨어 상태 로그")
                log_html = "<div class='log-box'>"
                if search_uid and search_uid in chats:
                    for chat in reversed(chats[search_uid]):
                        hw_tag = f" <br><span style='color:#e11d48; font-size:11px;'>↳ [{chat.get('device', '미상')}] {chat.get('hardware', '데이터 없음')}</span>"
                        log_html += f"<p style='font-size:13px;'><span style='color:#94a3b8;'>[{chat['time']}]</span> <b>{chat['query']}</b>{hw_tag}</p>"
                else: log_html += "<p style='color:#94a3b8; font-size:13px;'>학번을 입력하시면 정보가 노출됩니다.</p>"
                log_html += "</div>"
                st.markdown(log_html, unsafe_allow_html=True)

    # ==================== [[ 🏠 가이드 메인 홈 (학생 & 관리자 모두 이용 가능) ]] ====================
    elif menu_choice == "🏠 가이드 메인 홈":
        if "search_result" not in st.session_state: st.session_state.search_result = ""
        if "last_query" not in st.session_state: st.session_state.last_query = ""

        st.markdown("### 📢 실시간 학교 공지사항")
        st.info(community.get('notice', '등록된 공지사항이 없습니다.'))
        
        tab1, tab2, tab3, tab4 = st.tabs(["🤖 규정 질문 챗봇", "🏛️ 학생 소통 공간", "📊 실시간 학생 투표", "📳 모바일 제어존"])

        with tab1:
            user_query = st.text_input("궁금한 규정 키워드 입력:", value=st.session_state.last_query, placeholder="예: 두발, 휴대폰")
            if st.button("🔎 검색하기") and user_query:
                st.session_state.last_query = user_query
                st.session_state.search_result = search_pdf_with_highlight(user_query, pdf_content)
                
                if st.session_state.user_id not in chats: chats[st.session_state.user_id] = []
                chats[st.session_state.user_id].append({
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "query": user_query,
                    "device": st.session_state.device_info,
                    "hardware": st.session_state.hardware_detail
                })
                save_data(CHAT_FILE, chats)
                st.rerun()
            if st.session_state.search_result: st.markdown(st.session_state.search_result, unsafe_allow_html=True)

        with tab2:
            with st.form("p_form", clear_on_submit=True):
                pc = st.text_area("글 쓰기")
                anon = st.checkbox("익명")
                if st.form_submit_button("등록") and pc:
                    if check_bad_words(pc)[0]:
                        community["posts"].insert(0, {"author": "익명" if anon else st.session_state.user_name, "content": pc, "likes": []})
                        save_data(COMMUNITY_FILE, community)
                        st.rerun()
            for idx, post in enumerate(community.get("posts", [])):
                st.markdown(f"👤 **{post.get('author')}**")
                st.info(post.get("content", ""))

        with tab3:
            st.write("### 📊 전교생 실시간 의견 조율 투표")
            polls = community.get("polls", [])
            if polls:
                for p_idx, poll in enumerate(polls):
                    st.markdown(f"#### 🗳️ {poll['question']}")
                    votes = poll.get("votes", {})
                    current_user_vote = votes.get(st.session_state.user_id, None)
                    
                    counts = [0] * len(poll["options"])
                    for u, v_opt in votes.items():
                        if v_opt in poll["options"]: counts[poll["options"].index(v_opt)] += 1
                    
                    selected_option = st.radio(
                        "투표 항목을 선택하세요:", 
                        poll["options"], 
                        index=poll["options"].index(current_user_vote) if current_user_vote in poll["options"] else 0,
                        key=f"poll_opt_{p_idx}"
                    )
                    
                    if st.button("🗳️ 투표 제출 / 변경하기", key=f"poll_btn_{p_idx}"):
                        votes[st.session_state.user_id] = selected_option
                        community["polls"][p_idx]["votes"] = votes
                        save_data(COMMUNITY_FILE, community)
                        st.success("투표가 정상 반영되었습니다!")
                        st.rerun()
                    
                    st.write("")
                    st.write("📊 **현재 실시간 투표 집계 현황**")
                    for opt, count in zip(poll["options"], counts):
                        st.write(f"- {opt}: **{count}표**")

        with tab4:
            st.write("### 📳 모바일 하드웨어 센서 피드백 요청")
            st.write("사용자가 직접 버튼을 누르는 이벤트 인터랙션 시 작동하는 기기 제어 기능입니다.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("📳 기기 물리 진동 유도", use_container_width=True):
                    st.session_state.trigger_vibrate = True
                    st.rerun()
                if st.button("📢 시스템 스피커 음성 가이드 출력", use_container_width=True):
                    st.session_state.trigger_speak = "가이드 검색 결과가 준비되었습니다."
                    st.rerun()
            with c2:
                st.components.v1.html('<button onclick="window.parent.toggleFullScreen()" style="width:100%; background-color:#1d4ed8; color:white; border:none; padding:12px; border-radius:6px; font-weight:bold; cursor:pointer;">🖥️ 모바일 전체 화면 On/Off</button>', height=55)