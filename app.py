import streamlit as st
import json
import os
from datetime import datetime
import pypdf
import re

# --- 📱 [1] 브라우저 기본 페이지 설정 (사이드바 열림 상태 강제 유지) ---
st.set_page_config(
    page_title="신입생 학교생활 가이드",
    page_icon="https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp",
    layout="centered",
    initial_sidebar_state="expanded"  # 무조건 열린 채로 시작
)

# --- 🎨 [2] 메뉴창이 안 사라지게 잡는 새로운 CSS (버튼 차단 해제) ---
st.markdown(
    """
    <style>
        .stApp { background-color: #0e1117 !important; padding-bottom: 150px !important; }
        h1, h2, h3, h4, p, span, label, li { color: #ffffff !important; }
        
        /* 사이드바 배경 및 폰트 무조건 보이게 고정 */
        [data-testid="stSidebar"] { 
            background-color: #1e293b !important; 
            border-right: 2px solid #1d4ed8 !important;
            visibility: visible !important;
            display: block !important;
        }
        
        /* 사이드바 내부 라디오 버튼 스타일 */
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] label {
            background-color: #0f172a !important; border: 1px solid #334155 !important;
            padding: 8px 12px !important; border-radius: 6px !important; margin-bottom: 6px !important;
        }
        
        .stButton>button {
            background-color: #1d4ed8 !important; color: #ffffff !important;
            border-radius: 6px !important; border: none !important; font-weight: bold !important;
        }
        .stButton>button:hover { background-color: #2563eb !important; box-shadow: 0px 0px 8px rgba(37, 99, 235, 0.6); }
        input[type="text"], input[type="password"], textarea { color: #ffffff !important; background-color: #1f2937 !important; border: 1px solid #4b5563 !important; }
        
        /* 로그인 브릿지 인풋 완전 차단 */
        div[data-testid="stTextInput"]:has(input[aria-label="hidden_login_bridge"]) {
            display: none !important;
            visibility: hidden !important;
            height: 0px !important;
            position: absolute !important;
            top: -9999px !important;
        }

        /* ⚠️ 기존에 header 전체를 지우던 코드를 수정하여 사이드바 버튼이 깨지지 않게 방지 */
        footer { visibility: hidden !important; display: none !important; }
        [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
        
        .log-box {
            background-color: #1e293b;
            border: 1px solid #3b82f6;
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
            max-height: 400px;
            overflow-y: auto;
        }
    </style>
    """,
    unsafe_allow_html=True
)

USER_FILE = "users.json"
CHAT_FILE = "chats.json"
COMMUNITY_FILE = "community.json"
PDF_FILE = "2025. 학생생활규정.pdf"
BAD_WORDS = ["바보", "멍청이", "지랄", "존나", "개새끼", "시발", "새끼", "미친"]

def check_bad_words(text):
    for word in BAD_WORDS:
        if word in text: return False, word
    return True, ""

def load_data(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content: return json.loads(content)
        except: pass
    return {}

def save_data(filepath, data):
    if not data and os.path.exists(filepath):
        return
    with open(filepath, "w", encoding="utf-8") as f: 
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_community_safe():
    data = load_data(COMMUNITY_FILE)
    if not isinstance(data, dict): data = {}
    if "posts" not in data: data["posts"] = []
    if "polls" not in data: data["polls"] = []
    if "notice" not in data: data["notice"] = "아직 등록된 공지사항이 없습니다."
    return data

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

users = load_data(USER_FILE)
chats = load_data(CHAT_FILE)
community = load_community_safe()
pdf_content = load_pdf_text(PDF_FILE)

if "admin" not in users:
    users["admin"] = {"password": "ahsknue2026_2026!", "name": "최고관리자", "role": "master_admin"}
    save_data(USER_FILE, users)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.role = "user"

# --- 🔐 로그인 복구 브릿지 ---
if not st.session_state.logged_in:
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
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        </script>
        """,
        height=0
    )
    if bridge_val:
        try:
            u_info = json.loads(bridge_val)
            st.session_state.logged_in = True
            st.session_state.user_id = u_info["id"]
            st.session_state.user_name = u_info["name"]
            st.session_state.role = u_info["role"]
            st.rerun()
        except: pass

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
        st.subheader("로그인")
        u_id_input = st.text_input("학번 / 아이디", key="login_id_main")
        u_pw_input = st.text_input("비밀번호", type="password", key="login_pw_main")

        if st.button("로그인하기", use_container_width=True):
            users = load_data(USER_FILE)
            if u_id_input in users and users[u_id_input]["password"] == u_pw_input:
                st.session_state.logged_in = True
                st.session_state.user_id = u_id_input
                st.session_state.user_name = users[u_id_input]["name"]
                st.session_state.role = "master_admin" if u_id_input == "admin" else users[u_id_input].get("role", "user")
                
                sess_str = json.dumps({"id": st.session_state.user_id, "name": st.session_state.user_name, "role": st.session_state.role}, ensure_ascii=False)
                st.components.v1.html(f"""
                    <script>
                        localStorage.setItem("saved_user_info", JSON.stringify({sess_str}));
                    </script>
                """, height=0)
                st.success(f"🎉 {st.session_state.user_name}님 로그인 성공!")
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    with auth_tab2:
        st.subheader("회원가입")
        new_id = st.text_input("학번 (숫자만)", key="join_id_main")
        new_name = st.text_input("이름 (한글 3~4자)", key="join_name_main")
        new_pw = st.text_input("비밀번호", type="password", key="join_pw_main")
        if st.button("가입하기", use_container_width=True):
            if new_id and new_name and new_pw:
                users = load_data(USER_FILE)
                users[new_id] = {"password": new_pw, "name": new_name, "role": "user"}
                save_data(USER_FILE, users)
                st.success("🎉 회원가입 성공! 로그인 탭으로 이동해 주세요.")

else:
    # ----------------------------------------------------
    # 🖥️ [사이드바 UI 구조 렌더링 검증 고정]
    # ----------------------------------------------------
    st.sidebar.markdown(f"### 👤 {st.session_state.user_name}님")
    is_admin_user = (st.session_state.user_id == "admin" or st.session_state.role in ["master_admin", "sub_admin"])
    
    if is_admin_user:
        if st.session_state.user_id == "admin" or st.session_state.role == "master_admin":
            st.sidebar.markdown("👑 **등급:** `최고 관리자`")
        else:
            st.sidebar.markdown("🛡️ **등급:** `일반 관리자`")
    else:
        st.sidebar.markdown("🎓 **등급:** `일반 학생 사용자`")

    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.components.v1.html("<script>localStorage.removeItem('saved_user_info');</script>", height=0)
        st.rerun()

    st.sidebar.markdown("---")
    
    # 🌟 이제 등급 구분 없이 사이드바 선택지가 비어있지 않도록 확실히 보정
    if is_admin_user:
        st.sidebar.markdown("### 🛠️ 관리자 메뉴")
        admin_menu = ["🔍 전체 계정 관리", "📢 공지 및 투표 관리", "🏛️ 커뮤니티 게시글 관리", "💬 학생 질문 통계 및 로그"]
        if st.session_state.user_id == "admin" or st.session_state.role == "master_admin":
            admin_menu.append("➕ 일반 관리자 계정 생성")
        menu_choice = st.sidebar.radio("제어할 기능을 선택하세요", admin_menu, key="admin_menu_select")
    else:
        st.sidebar.markdown("### 🧭 가이드 링크")
        student_menu = ["🏠 가이드 메인 홈"]
        menu_choice = st.sidebar.radio("바로가기", student_menu, key="student_menu_select")

    # ==================== [[ 🛠️ 1. 관리자 전용 제어판 분기 ]] ====================
    if is_admin_user:
        def admin_dashboard(choice):
            current_users = load_data(USER_FILE)
            current_chats = load_data(CHAT_FILE)
            current_community = load_community_safe()
            
            st.subheader(f"⚙️ 관리 제어판 -> {choice}")
            
            if choice == "🔍 전체 계정 관리":
                search_uid = st.text_input("🔍 학번 또는 관리자 ID 검색")
                target_users = {k: v for k, v in current_users.items() if v.get("role") != "master_admin"}
                if search_uid in current_users: target_users = {search_uid: current_users[search_uid]}
                
                for u_id, u_info in target_users.items():
                    with st.expander(f"학번/ID: {u_id} | 이름: {u_info['name']}"):
                        edit_name = st.text_input("이름 변경", value=u_info['name'], key=f"a_n_{u_id}")
                        edit_pw = st.text_input("비밀번호 변경", value=u_info['password'], key=f"a_p_{u_id}")
                        if st.button("💾 수정 저장", key=f"b_s_{u_id}"):
                            current_users[u_id].update({"name": edit_name, "password": edit_pw})
                            save_data(USER_FILE, current_users)
                            st.success("수정 완료!")

            elif choice == "📢 공지 및 투표 관리":
                new_notice = st.text_area("공지사항 수정", value=current_community.get("notice", ""))
                col_n1, col_n2 = st.columns(2)
                with col_n1:
                    if st.button("📢 공지 업데이트", use_container_width=True):
                        current_community["notice"] = new_notice
                        save_data(COMMUNITY_FILE, current_community)
                        st.success("업데이트 완료!")
                with col_n2:
                    if st.button("🗑️ 공지사항 초기화", use_container_width=True):
                        current_community["notice"] = "아직 등록된 공지사항이 없습니다."
                        save_data(COMMUNITY_FILE, current_community)
                        st.rerun()
                
                st.write("---")
                st.write("#### 🗳️ 신규 투표 발의 및 삭제")
                poll_title = st.text_input("투표 안건 주제")
                poll_o1 = st.text_input("보기 1")
                poll_o2 = st.text_input("보기 2")
                if st.button("🗳️ 투표 공식 발의") and poll_title and poll_o1 and poll_o2:
                    current_community["polls"].append({
                        "title": poll_title, "options": [poll_o1, poll_o2],
                        "votes": {poll_o1: 0, poll_o2: 0}, "voted_users": [], "is_closed": False
                    })
                    save_data(COMMUNITY_FILE, current_community)
                    st.success("투표 배포 완료!")
                
                if current_community.get("polls"):
                    st.write("---")
                    st.write("#### 🗑️ 현재 진행 중인 투표 리스트 (삭제 가능)")
                    for p_idx, poll in enumerate(current_community["polls"]):
                        col_p1, col_p2 = st.columns([4, 1])
                        with col_p1: st.caption(f"안건: {poll['title']}")
                        with col_p2:
                            if st.button("❌ 삭제", key=f"del_poll_{p_idx}"):
                                current_community["polls"].pop(p_idx)
                                save_data(COMMUNITY_FILE, current_community)
                                st.rerun()

            elif choice == "🏛️ 커뮤니티 게시글 관리":
                if not current_community.get("posts"):
                    st.info("현재 커뮤니티에 올라온 게시글이 없습니다.")
                for idx, post in enumerate(current_community.get("posts", [])):
                    with st.expander(f"✍️ [{post.get('author', '익명')}] {post.get('content', '')[:20]}..."):
                        st.write(f"**원문 내용:** {post.get('content', '')}")
                        
                        if st.button("🗑️ 게시글 전체 삭제", key=f"a_d_p_{idx}"):
                            current_community["posts"].pop(idx)
                            save_data(COMMUNITY_FILE, current_community)
                            st.rerun()
                        
                        st.write("---")
                        st.caption("💬 이 게시글에 달린 댓글 리스트")
                        comments = post.get("comments", [])
                        if not comments:
                            st.caption("등록된 댓글이 없습니다.")
                        else:
                            for c_idx, cmt in enumerate(comments):
                                col_c1, col_c2 = st.columns([4, 1])
                                with col_c1:
                                    st.write(f"↳ **{cmt.get('author','익명')}**: {cmt.get('text','')}")
                                with col_c2:
                                    if st.button("❌ 댓글 삭제", key=f"a_d_c_{idx}_{c_idx}"):
                                        post["comments"].pop(c_idx)
                                        save_data(COMMUNITY_FILE, current_community)
                                        st.rerun()

            elif choice == "💬 학생 질문 통계 및 로그":
                st.write("### 💬 학생 질문 통계 및 로그 검색 제어판")
                col_left, col_right = st.columns([1, 1])
                
                VALID_TARGET_WORDS = [
                    "휴대폰", "스마트폰", "두발", "복장", "교복", "지각", "조퇴", "결석", 
                    "벌점", "상점", "포상", "징계", "소지품", "화장", "귀걸이", "피어싱", 
                    "체육복", "등교", "하교", "전자기기", "태블릿", "노트북", "이성교제", "흡연"
                ]
                
                with col_left:
                    search_uid = st.text_input("👤 검색할 학생 학번 입력 (미입력 시 전체 통계)", key="admin_search_uid")
                    st.write("---")
                    word_counts = {}
                    
                    def get_strict_filtered_words(chat_history_list):
                        counts = {}
                        for chat in chat_history_list:
                            query_text = chat['query'].replace(" ", "")
                            for target_word in VALID_TARGET_WORDS:
                                if target_word in query_text:
                                    counts[target_word] = counts.get(target_word, 0) + 1
                        return counts

                    if search_uid and search_uid in current_chats:
                        word_counts = get_strict_filtered_words(current_chats[search_uid])
                        st.markdown(f"📊 **학번 [{search_uid}] 학생의 핵심 규정 키워드 분석 (상위 5개)**")
                    else:
                        all_chats = []
                        for uid, history in current_chats.items():
                            all_chats.extend(history)
                        word_counts = get_strict_filtered_words(all_chats)
                        st.markdown("📊 **전체 학생 실시간 핵심 규정 키워드 분석 (상위 5개)**")
                    
                    if word_counts:
                        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                        total_top_clicks = sum([x[1] for x in sorted_words])
                        for word, count in sorted_words:
                            percentage = (count / total_top_clicks) if total_top_clicks > 0 else 0
                            st.write(f"🏷️ **{word}** ({count}회)")
                            st.progress(min(float(percentage), 1.0))
                    else:
                        st.info("통계에 반영할 만한 유효한 학교 규정 관련 질문 데이터가 없습니다.")

                with col_right:
                    st.markdown("#### 📦 학생 개별 로그 출력 박스")
                    log_html = "<div class='log-box'>"
                    if search_uid:
                        if search_uid in current_chats:
                            student_name = current_users.get(search_uid, {}).get('name', '미등록 유저')
                            log_html += f"<p style='color:#3b82f6; font-weight:bold;'>👤 {student_name} ({search_uid})의 기록</p><hr style='border:0.5px solid #334155;'> "
                            for chat in reversed(current_chats[search_uid]):
                                log_html += f"<p style='font-size:13px; margin-bottom:4px;'><span style='color:#94a3b8;'>[{chat['time']}]</span> {chat['query']}</p>"
                        else:
                            log_html += "<p style='color:#ef4444;'>⚠️ 해당 학번의 질문 기록이 존재하지 않습니다.</p>"
                    else:
                        log_html += "<p style='color:#94a3b8; font-size:13px;'>상단의 학번 검색창에 학번을 입력하시면 해당 학생의 실시간 질문 히스토리가 이 박스 영역에 표기됩니다.</p>"
                    log_html += "</div>"
                    st.markdown(log_html, unsafe_allow_html=True)

            elif choice == "➕ 일반 관리자 계정 생성":
                sub_id = st.text_input("일반 관리자 ID")
                sub_name = st.text_input("담당 교사 이름")
                sub_pw = st.text_input("비밀번호", type="password")
                if st.button("🛡️ 서브 관리자 추가") and sub_id and sub_name and sub_pw:
                    current_users[sub_id] = {"password": sub_pw, "name": sub_name, "role": "sub_admin"}
                    save_data(USER_FILE, current_users)
                    st.success("관리자 등록 성공!")

        admin_dashboard(menu_choice)

    # ==================== [[ 🎓 2. 학생 전용 대시보드 분기 ]] ====================
    else:
        if "search_result" not in st.session_state:
            st.session_state.search_result = ""
        if "last_query" not in st.session_state:
            st.session_state.last_query = ""

        def student_dashboard():
            current_community = load_community_safe()
            current_chats = load_data(CHAT_FILE)
            
            st.markdown("### 📢 실시간 학교 공지사항")
            st.info(current_community.get('notice', '등록된 공지사항이 없습니다.'))
            
            tab1, tab2, tab3 = st.tabs(["🤖 규정 질문 챗봇", "🏛️ 학생 소통 커뮤니티", "📊 실시간 투표존"])

            with tab1:
                st.write("### 🤖 학교 생활 규정집 검색기")
                user_query = st.text_input(
                    "궁금한 규정 키워드를 입력하세요:", 
                    value=st.session_state.last_query, 
                    placeholder="💡 단어로 입력해 주세요! 예: 두발, 휴대폰 (문장X)", 
                    key="s_query_main"
                )
                
                if st.button("🔎 검색하기", key="s_query_btn_main") and user_query:
                    st.session_state.last_query = user_query
                    st.session_state.search_result = search_pdf_with_highlight(user_query, pdf_content)
                    
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if st.session_state.user_id not in current_chats:
                        current_chats[st.session_state.user_id] = []
                    
                    current_chats[st.session_state.user_id].append({
                        "time": now_str,
                        "query": user_query
                    })
                    save_data(CHAT_FILE, current_chats)
                    st.rerun()

                if st.session_state.search_result:
                    st.markdown(st.session_state.search_result, unsafe_allow_html=True)

            with tab2:
                st.write("### 🏛️ 익명/실명 학생 대나무숲")
                with st.form("s_post_form_main", clear_on_submit=True):
                    post_content = st.text_area("학교 생활이나 건의사항을 공유해보세요!")
                    is_anonymous = st.checkbox("익명으로 안전하게 게시")
                    if st.form_submit_button("게시글 올리기") and post_content:
                        if check_bad_words(post_content)[0]:
                            author_name = "익명의 새내기" if is_anonymous else st.session_state.user_name
                            current_community["posts"].insert(0, {"author": author_name, "content": post_content, "likes": [], "comments": []})
                            save_data(COMMUNITY_FILE, current_community)
                            st.rerun()

                st.write("---")
                for idx, post in enumerate(current_community.get("posts", [])):
                    st.markdown(f"👤 **{post.get('author', '익명')}**")
                    st.info(post.get("content", ""))
                    
                    likes_list = post.get("likes", [])
                    if st.button(f"❤️ {len(likes_list)}", key=f"s_l_{idx}_{len(likes_list)}"):
                        if st.session_state.user_id in likes_list: likes_list.remove(st.session_state.user_id)
                        else: likes_list.append(st.session_state.user_id)
                        post["likes"] = likes_list
                        save_data(COMMUNITY_FILE, current_community)
                        st.rerun()

                    comments_list = post.get("comments", [])
                    with st.expander(f"💬 댓글 ({len(comments_list)}개)"):
                        for comment in comments_list: st.write(f"↳ **{comment.get('author','익명')}**: {comment.get('text','')}")
                        
                        with st.form(f"s_cmt_form_{idx}", clear_on_submit=True):
                            cmt_text = st.text_input("댓글 작성란", key=f"s_i_cmt_{idx}")
                            cmt_anonymous = st.checkbox("익명으로 안전하게 댓글 작성", key=f"s_c_anon_{idx}")
                            if st.form_submit_button("등록") and cmt_text:
                                if check_bad_words(cmt_text)[0]:
                                    author_name = "익명의 새내기" if cmt_anonymous else st.session_state.user_name
                                    comments_list.append({"author": author_name, "text": cmt_text})
                                    post["comments"] = comments_list
                                    save_data(COMMUNITY_FILE, current_community)
                                    st.rerun()

            with tab3:
                st.write("### 📊 실시간 학생 투표광장")
                if not current_community.get("polls"):
                    st.info("현재 진행 중인 교내 투표가 없습니다.")
                for p_idx, poll in enumerate(current_community.get("polls", [])):
                    st.write(f"#### ❓ 주제: {poll.get('title', '무제 투표')}")
                    voted_users = poll.get("voted_users", [])
                    if poll.get("is_closed", False) or st.session_state.user_id in voted_users:
                        st.warning("참여 완료 되었거나 마감된 안건입니다.")
                        for opt, val in poll.get("votes", {}).items(): st.write(f"✔️ **{opt}** : {val}표")
                    else:
                        selected_opt = st.radio("보기를 선택하세요", poll.get("options", []), key=f"s_p_opt_{p_idx}")
                        if st.button("투표 제출", key=f"s_p_btn_{p_idx}"):
                            poll["votes"][selected_opt] = poll.get("votes", {}).get(selected_opt, 0) + 1
                            voted_users.append(st.session_state.user_id)
                            poll["voted_users"] = voted_users
                            save_data(COMMUNITY_FILE, current_community)
                            st.rerun()

        student_dashboard()