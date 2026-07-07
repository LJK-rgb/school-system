import streamlit as st
import json
import os
from datetime import datetime
import pypdf
import re

# --- 📱 [1] 브라우저 레이아웃 및 앱 설정 ---
st.set_page_config(
    page_title="학생생활규정 안내 서비스",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 📂 [2] 데이터 파일 경로 정의 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STUDENT_USER_FILE = os.path.join(BASE_DIR, "users_student.json")
ADMIN_USER_FILE = os.path.join(BASE_DIR, "users_admin.json")
CHAT_FILE = os.path.join(BASE_DIR, "chats.json")
COMMUNITY_FILE = os.path.join(BASE_DIR, "community.json")
PDF_FILE = os.path.join(BASE_DIR, "2025. 학생생활규정.pdf")

BAD_WORDS = ["바보", "멍청이", "지랄", "존나", "개새끼", "시발", "새끼", "미친"]

# --- 💾 [3] 데이터 로드 및 저장 함수 ---
def load_json_safe(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content: return json.loads(content)
        except: pass
    return {}

def save_json_safe(filepath, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f: 
            json.dump(data, f, ensure_ascii=False, indent=4)
    except: pass

def load_community_safe():
    data = load_json_safe(COMMUNITY_FILE)
    if not isinstance(data, dict): data = {}
    if "posts" not in data: data["posts"] = []
    if "polls" not in data: 
        data["polls"] = [{
            "question": "2026학년도 축제 연예인 초청 찬반 투표",
            "options": ["찬성 (예산 활용 선호)", "반대 (동아리 부스 집중)"],
            "votes": {}
        }]
    if "notice" not in data: data["notice"] = "아직 등록된 공지사항이 없습니다."
    return data

students = load_json_safe(STUDENT_USER_FILE)
admins = load_json_safe(ADMIN_USER_FILE)
chats = load_json_safe(CHAT_FILE)
community = load_community_safe()

if "admin" not in admins:
    admins["admin"] = {"password": "ahsknue2026_2026!", "name": "최고관리자", "role": "master_admin"}
    save_json_safe(ADMIN_USER_FILE, admins)

# --- 🔄 [4] 세션 상태 초기화 ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_id" not in st.session_state: st.session_state.user_id = None
if "user_name" not in st.session_state: st.session_state.user_name = None
if "role" not in st.session_state: st.session_state.role = "user"
if "device_info" not in st.session_state: st.session_state.device_info = "분석 중..."

# --- 🎨 [5] 화이트 스킨 모던 UI 스타일 커스텀 ---
st.markdown(
    """
    <style>
        .stApp { background-color: #f9fafb !important; color: #1f2937 !important; }
        header, [data-testid="stHeader"] { background-color: #ffffff !important; box-shadow: 0px 1px 3px rgba(0,0,0,0.05) !important; }
        .main .block-container { padding-top: 3rem !important; max-width: 1100px; }
        [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e5e7eb !important; }
        [data-testid="stSidebar"] h3, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span { color: #374151 !important; }
        .custom-card { background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; margin-bottom: 15px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
        .log-box { background-color: #f3f4f6; border: 1px solid #e5e7eb; border-radius: 8px; padding: 15px; margin-top: 10px; max-height: 400px; overflow-y: auto; color: #1f2937; }
        .stButton>button { background-color: #1e3a8a !important; color: #ffffff !important; border-radius: 8px !important; border: none !important; font-weight: 500 !important; }
        .stButton>button:hover { background-color: #2563eb !important; }
        div[data-testid="stTextInput"]:has(input[aria-label="hidden_login_bridge"]),
        div[data-testid="stTextInput"]:has(input[aria-label="hidden_device_bridge"]) { display: none !important; visibility: hidden !important; height: 0px !important; position: absolute !important; }
        footer { visibility: hidden !important; display: none !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 🛠️ [6] 로그인 유지를 위한 자바스크립트 브릿지 ---
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
        target_uid = u_info["id"]
        if target_uid in admins:
            st.session_state.logged_in = True
            st.session_state.user_id = target_uid
            st.session_state.user_name = admins[target_uid]["name"]
            st.session_state.role = admins[target_uid].get("role", "sub_admin")
        elif target_uid in students:
            st.session_state.logged_in = True
            st.session_state.user_id = target_uid
            st.session_state.user_name = students[target_uid]["name"]
            st.session_state.role = "user"
    except: pass

device_ua = st.text_input("hidden_device_bridge", key="hidden_device_bridge", label_visibility="collapsed")
st.components.v1.html(
    """
    <script>
        const parentDoc = window.parent.document;
        const ua = navigator.userAgent;
        const input = parentDoc.querySelector('input[aria-label="hidden_device_bridge"]');
        if (input && input.value !== ua) { input.value = ua; input.dispatchEvent(new Event('input', { bubbles: true })); }
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

# --- 📄 [7] PDF 규정집 검색 엔진 ---
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
                full_text = re.sub(f"({re.escape(kw)})", r"<mark style='background-color: #FEF08A; color: #1e3a8a; padding: 2px 4px; border-radius: 3px; font-weight: bold;'>\1</mark>", full_text)
            results.append(full_text.strip())
            if len(results) >= 3: break
    if results:
        output = "🔍 **규정집 내부 매칭된 조항 검색 결과:**\n\n"
        for res in results: output += f"<div style='background-color: #ffffff; color: #1f2937; padding: 18px; border-radius: 8px; margin-bottom: 12px; border-left: 5px solid #1e3a8a; box-shadow: 0 1px 3px rgba(0,0,0,0.05); white-space: pre-wrap;'>{res}</div>"
        return output
    return "🔍 규정집에서 관련 조항을 찾지 못했습니다."

pdf_content = load_pdf_text(PDF_FILE)

def check_bad_words(text):
    for word in BAD_WORDS:
        if word in text: return False, word
    return True, ""

# --- 🖥️ 메인 랜더링 인터페이스 ---
col_logo, col_title = st.columns([1, 7])
with col_logo: st.image("https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp", width=80)
with col_title: st.markdown("<h2 style='margin-top:10px; color:#1e3a8a;'>학생생활규정 안내 서비스</h2>", unsafe_allow_html=True)

st.markdown("<hr style='margin: 10px 0 25px 0; border-color:#e5e7eb;'>", unsafe_allow_html=True)

if not st.session_state.logged_in:
    st.info("👋 안녕하세요! 규정 검색 및 소통망 서비스를 이용하시려면 로그인이나 회원가입을 진행해 주세요.")
    auth_tab1, auth_tab2 = st.tabs(["🔑 로그인", "📝 회원가입"])

    with auth_tab1:
        u_id_input = st.text_input("학번 / 아이디", key="login_id_main")
        u_pw_input = st.text_input("비밀번호", type="password", key="login_pw_main")
        if st.button("로그인하기", use_container_width=True):
            if u_id_input in admins and admins[u_id_input]["password"] == u_pw_input:
                st.session_state.logged_in = True
                st.session_state.user_id = u_id_input
                st.session_state.user_name = admins[u_id_input]["name"]
                st.session_state.role = admins[u_id_input].get("role", "sub_admin")
                sess_str = json.dumps({"id": st.session_state.user_id, "name": st.session_state.user_name, "role": st.session_state.role}, ensure_ascii=False)
                st.components.v1.html(f"<script>localStorage.setItem('saved_user_info', JSON.stringify({sess_str}));</script>", height=0)
                st.rerun()
            elif u_id_input in students and students[u_id_input]["password"] == u_pw_input:
                st.session_state.logged_in = True
                st.session_state.user_id = u_id_input
                st.session_state.user_name = students[u_id_input]["name"]
                st.session_state.role = "user"
                sess_str = json.dumps({"id": st.session_state.user_id, "name": st.session_state.user_name, "role": "user"}, ensure_ascii=False)
                st.components.v1.html(f"<script>localStorage.setItem('saved_user_info', JSON.stringify({sess_str}));</script>", height=0)
                st.rerun()
            else: st.error("계정 정보가 올바르지 않습니다.")

    with auth_tab2:
        new_id = st.text_input("학번 / 아이디 (숫자 위주)", key="join_id_main")
        new_name = st.text_input("이름", key="join_name_main")
        new_pw = st.text_input("비밀번호", type="password", key="join_pw_main")
        reg_role = st.selectbox("가입 유형", ["일반 학생 사용자", "일반 관리자"])
        
        if st.button("가입하기", use_container_width=True):
            if new_id and new_name and new_pw:
                if new_id in students or new_id in admins:
                    st.error("이미 존재하는 학번/아이디입니다.")
                else:
                    if reg_role == "일반 관리자":
                        admins[new_id] = {"password": new_pw, "name": new_name, "role": "sub_admin"}
                        save_json_safe(ADMIN_USER_FILE, admins)
                    else:
                        students[new_id] = {"password": new_pw, "name": new_name, "role": "user"}
                        save_json_safe(STUDENT_USER_FILE, students)
                    st.success(f"🎉 [{reg_role}] 회원가입 성공! 로그인해 주세요.")

else:
    st.sidebar.markdown(f"### 👤 {st.session_state.user_name}님")
    is_admin_user = (st.session_state.user_id == "admin" or st.session_state.role in ["master_admin", "sub_admin"])
    st.sidebar.markdown(f"👑 **등급:** `관리자`" if is_admin_user else "🎓 **등급:** `일반 학생`")
    st.sidebar.markdown(f"📡 `{st.session_state.device_info}`")

    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.components.v1.html("<script>localStorage.removeItem('saved_user_info');</script>", height=0)
        st.rerun()

    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    if is_admin_user:
        menu_list = ["🏠 가이드 홈 & 공지", "🤖 규정 질문 챗봇", "🏛️ 학생 소통 커뮤니티", "📊 실시간 학생 투표", "🔗 학교 필수 링크 모음", "⚙️ [관리] 전체 계정 관리", "⚙️ [관리] 메인 공지/투표 관리", "⚙️ [관리] 커뮤니티 글 관리", "⚙️ [관리] 질문 통계 로그"]
    else:
        menu_list = ["🏠 가이드 홈 & 공지", "🤖 규정 질문 챗봇", "🏛️ 학생 소통 커뮤니티", "📊 실시간 학생 투표", "🔗 학교 필수 링크 모음"]
        
    menu_choice = st.sidebar.radio("메뉴 네비게이션", menu_list, key="menu_sel")

    # ==================== [[ 🏠 가이드 홈 & 공지 ]] ====================
    if menu_choice == "🏠 가이드 홈 & 공지":
        st.markdown("<h3 style='color:#1e3a8a;'>✨ 당당한 사람으로 모두 성장하는 학교</h3>", unsafe_allow_html=True)
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.markdown("#### 📢 실시간 학교 공지사항")
        st.info(community.get('notice', '등록된 공지사항이 없습니다.'))
        st.markdown("</div>", unsafe_allow_html=True)

    # ==================== [[ 🤖 규정 질문 챗봇 ]] ====================
    elif menu_choice == "🤖 규정 질문 챗봇":
        st.markdown("### 🤖 학생생활규정 안내 챗봇")
        if "search_result" not in st.session_state: st.session_state.search_result = ""
        if "last_query" not in st.session_state: st.session_state.last_query = ""

        user_query = st.text_input("규정에 대해 궁금한 점을 입력해 주세요...", value=st.session_state.last_query, placeholder="예: 두발, 휴대폰, 복장")
        if st.button("🚀 규정 검색") and user_query:
            st.session_state.last_query = user_query
            st.session_state.search_result = search_pdf_with_highlight(user_query, pdf_content)
            if st.session_state.user_id not in chats: chats[st.session_state.user_id] = []
            chats[st.session_state.user_id].append({"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "query": user_query})
            save_json_safe(CHAT_FILE, chats)
            st.rerun()
        if st.session_state.search_result: st.markdown(st.session_state.search_result, unsafe_allow_html=True)

    # ==================== [[ 🏛️ 학생 소통 커뮤니티 ]] ====================
    elif menu_choice == "🏛️ 학생 소통 커뮤니티":
        st.markdown("### 🏛️ 커뮤니티 소통 공간")
        with st.form("p_form", clear_on_submit=True):
            pc = st.text_area("학우들과 나누고 싶은 이야기를 들려주세요.")
            anon = st.checkbox("익명 게시글로 등록하기")
            if st.form_submit_button("📝 게시글 올리기") and pc:
                if check_bad_words(pc)[0]:
                    community["posts"].insert(0, {"author": "익명" if anon else st.session_state.user_name, "content": pc, "likes": [], "comments": []})
                    save_json_safe(COMMUNITY_FILE, community)
                    st.rerun()
                    
        for idx, post in enumerate(community.get("posts", [])):
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            st.markdown(f"👤 **{post.get('author', '알 수 없음')}**")
            st.write(post.get("content", ""))
            st.markdown("</div>", unsafe_allow_html=True)

    # ==================== [[ 📊 실시간 학생 투표 ]] ====================
    elif menu_choice == "📊 실시간 학생 투표":
        st.markdown("### 📊 실시간 의견 조율 투표")
        polls = community.get("polls", [])
        if polls:
            for p_idx, poll in enumerate(polls):
                st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
                st.markdown(f"#### 🗳️ {poll['question']}")
                votes = poll.get("votes", {})
                current_user_vote = votes.get(st.session_state.user_id, None)
                selected_option = st.radio("선택 항목:", poll["options"], index=poll["options"].index(current_user_vote) if current_user_vote in poll["options"] else 0, key=f"poll_opt_{p_idx}")
                if st.button("🗳️ 투표 제출 및 변경", key=f"poll_btn_{p_idx}"):
                    votes[st.session_state.user_id] = selected_option
                    community["polls"][p_idx]["votes"] = votes
                    save_json_safe(COMMUNITY_FILE, community)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    # ==================== [[ 🔗 학교 필수 링크 모음 ]] ====================
    elif menu_choice == "🔗 학교 필수 링크 모음":
        st.markdown("### 🔗 학교 생활 필수 링크 모음")
        st.write("학사일정, 급식, 시간표는 아래의 공식 서비스 링크를 통해 가장 정확하게 확인할 수 있습니다.")
        
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.markdown("#### ⏱️ 오늘의 반별 실시간 시간표")
        st.link_button("🏫 컴시간알리미 바로가기", "https://comcigan.com/", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.markdown("#### 📅 학사일정 & 🍱 급식 & 📄 가정통신문")
        st.link_button("🚀 리로스쿨 바로가기", "https://riroschool.kr/", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ==================== [[ ⚙️ 관리자 메뉴 ]] ====================
    elif is_admin_user:
        st.markdown(f"### ⚙️ 관리 컨트롤러 — {menu_choice}")
        
        if menu_choice == "⚙️ [관리] 전체 계정 관리":
            tab_std, tab_adm = st.tabs(["🎓 일반 학생 관리", "⚙️ 일반 관리자 관리"])
            
            with tab_std:
                for u_id, u_info in list(students.items()):
                    with st.expander(f"👤 {u_info['name']} ({u_id})"):
                        en = st.text_input("이름 변경", value=u_info['name'], key=f"std_n_{u_id}")
                        ep = st.text_input("비번 변경", value=u_info['password'], key=f"std_p_{u_id}")
                        if st.button("학생 수정 저장", key=f"std_b_{u_id}"):
                            students[u_id].update({"name": en, "password": ep})
                            save_json_safe(STUDENT_USER_FILE, students)
                            st.success("학생 정보 수정 완료!")
                            st.rerun()
                            
            with tab_adm:
                for u_id, u_info in list(admins.items()):
                    if u_id == "admin": continue
                    with st.expander(f"⚙️ {u_info['name']} ({u_id})"):
                        en = st.text_input("이름 변경", value=u_info['name'], key=f"adm_n_{u_id}")
                        ep = st.text_input("비번 변경", value=u_info['password'], key=f"adm_p_{u_id}")
                        if st.button("관리자 수정 저장", key=f"adm_b_{u_id}"):
                            admins[u_id].update({"name": en, "password": ep})
                            save_json_safe(ADMIN_USER_FILE, admins)
                            st.success("관리자 정보 수정 완료!")
                            st.rerun()

        elif menu_choice == "⚙️ [관리] 메인 공지/투표 관리":
            new_notice = st.text_area("📢 메인 공지사항 수정", value=community.get("notice", ""))
            if st.button("💾 공지사항 저장하기", use_container_width=True):
                community["notice"] = new_notice
                save_json_safe(COMMUNITY_FILE, community)
                st.success("업데이트 완료!")

        elif menu_choice == "⚙️ [관리] 커뮤니티 글 관리":
            for idx, post in enumerate(community.get("posts", [])):
                with st.expander(f"✍️ [{post.get('author')}] {post.get('content')[:20]}..."):
                    if st.button("🗑️ 게시글 삭제", key=f"d_p_{idx}"):
                        community["posts"].pop(idx)
                        save_json_safe(COMMUNITY_FILE, community)
                        st.rerun()

        elif menu_choice == "⚙️ [관리] 질문 통계 로그":
            search_uid = st.text_input("조회할 학생 학번")
            if search_uid and search_uid in chats:
                st.markdown("#### 📦 챗봇 유입 기록")
                log_html = "<div class='log-box'>"
                for chat in reversed(chats[search_uid]): log_html += f"<p>[{chat['time']}] 검색어: <b>{chat['query']}</b></p>"
                log_html += "</div>"
                st.markdown(log_html, unsafe_allow_html=True)