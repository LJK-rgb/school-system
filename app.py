import streamlit as st
import json
import os
from datetime import datetime
import pypdf
import re

# --- 📱 [1] 브라우저 기본 페이지 설정 ---
st.set_page_config(
    page_title="신입생 학교생활 가이드",
    page_icon="https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp",
    layout="centered"
)

# --- 🎨 [2] 디자인 및 히든 브릿지 완전 은폐 CSS ---
st.markdown(
    """
    <style>
        .stApp { background-color: #0e1117 !important; padding-bottom: 150px !important; }
        h1, h2, h3, h4, p, span, label, li { color: #ffffff !important; }
        .stMarkdown div p { color: #ffffff !important; }
        [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 2px solid #1d4ed8 !important; }
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
        
        /* 🚨 로그인 브릿지 인풋을 완전히 숨겨서 상단에 아무것도 노출 안 되게 차단 */
        div[data-testid="stTextInput"]:has(input[aria-label="hidden_login_bridge"]) {
            display: none !important;
            visibility: hidden !important;
            height: 0px !important;
            position: absolute !important;
            top: -9999px !important;
        }

        #MainMenu, header, footer { visibility: hidden !important; display: none !important; }
        [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] { display: none !important; }
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

# 데이터 로드/저장 안정성 강화 (기존 회원이 있다면 덮어쓰기 방지)
def load_data(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content: return json.loads(content)
        except:
            pass
    return {}

def save_data(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f: 
        json.dump(data, f, ensure_ascii=False, indent=4)

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

# 초기 데이터 바인딩
users = load_data(USER_FILE)
chats = load_data(CHAT_FILE)
community = load_data(COMMUNITY_FILE)
pdf_content = load_pdf_text(PDF_FILE)

for key in ["posts", "polls"]:
    if key not in community: community[key] = []
if "notice" not in community: community["notice"] = "아직 등록된 공지사항이 없습니다."

# 마스터 관리자 계정 강제 고정 보존
if "admin" not in users:
    users["admin"] = {"password": "ahsknue2026_2026!", "name": "최고관리자", "role": "master_admin"}
    save_data(USER_FILE, users)

# 세션 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.role = "user"

# --- 🔐 [안전한 로그인 복구 브릿지] 외부 노출 및 URL 변형이 없는 로컬스토리지 방식 ---
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
        except:
            pass

# 상단 레이아웃 로고
col_logo, col_title = st.columns([1, 4])
with col_logo: st.image("https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp", width=110)
with col_title:
    st.markdown("<div style='padding-top: 15px;'></div>", unsafe_allow_html=True)
    st.title("신입생 학교생활 가이드 & 소통망")

st.markdown("---")

# --- 미로그인 상태 UI ---
if not st.session_state.logged_in:
    st.info("👋 안녕하세요! 서비스를 이용하시려면 로그인이나 회원가입을 진행해 주세요.")
    auth_tab1, auth_tab2 = st.tabs(["🔑 로그인", "📝 회원가입"])

    with auth_tab1:
        st.subheader("로그인")
        u_id_input = st.text_input("학번 / 아이디", key="login_id_main")
        u_pw_input = st.text_input("비밀번호", type="password", key="login_pw_main")

        if st.button("로그인하기", use_container_width=True):
            # 최신 데이터 확인
            users = load_data(USER_FILE)
            if u_id_input in users and users[u_id_input]["password"] == u_pw_input:
                st.session_state.logged_in = True
                st.session_state.user_id = u_id_input
                st.session_state.user_name = users[u_id_input]["name"]
                st.session_state.role = "master_admin" if u_id_input == "admin" else users[u_id_input].get("role", "user")
                
                # 브라우저 로컬 스토리지에 세션 안전하게 저장
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

# --- 로그인 완료 상태 UI ---
else:
    st.sidebar.markdown(f"### 👤 {st.session_state.user_name}님")
    if st.session_state.role == "master_admin": st.sidebar.markdown("👑 **등급:** `최고 관리자`")
    elif st.session_state.role == "sub_admin": st.sidebar.markdown("🛡️ **등급:** `일반 관리자`")
    else: st.sidebar.markdown("🎓 **등급:** `일반 학생 사용자`")

    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.components.v1.html("<script>localStorage.removeItem('saved_user_info');</script>", height=0)
        st.rerun()

    # ==================== [[ 🛠️ 1. 관리자 전용 제어판 분기 ]] ====================
    if st.session_state.role in ["master_admin", "sub_admin"]:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🛠️ 관리자 메뉴")
        admin_menu = ["🔍 전체 계정 관리", "📢 공지 및 투표 관리", "🏛️ 커뮤니티 게시글 관리", "💬 학생 질문 로그", "🔥 최다 질문 통계"]
        if st.session_state.role == "master_admin": admin_menu.append("➕ 일반 관리자 계정 생성")
        sub_choice = st.sidebar.radio("제어할 기능을 선택하세요", admin_menu)
        
        # 관리자 대시보드 프래그먼트 (3초 실시간 감시동기화)
        @st.fragment(run_every="3s")
        def admin_dashboard(choice):
            current_users = load_data(USER_FILE)
            current_chats = load_data(CHAT_FILE)
            current_community = load_data(COMMUNITY_FILE)
            
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
                if st.button("📢 공지 업데이트"):
                    current_community["notice"] = new_notice
                    save_data(COMMUNITY_FILE, current_community)
                    st.success("공지사항 실시간 업데이트 완료!")
                st.write("---")
                poll_title = st.text_input("투표 안건 주제")
                poll_o1 = st.text_input("보기 1")
                poll_o2 = st.text_input("보기 2")
                if st.button("🗳️ 투표 공식 발의") and poll_title and poll_o1 and poll_o2:
                    current_community["polls"].append({
                        "title": poll_title, "options": [poll_o1, poll_o2],
                        "votes": {poll_o1: 0, poll_o2: 0}, "voted_users": [], "is_closed": False
                    })
                    save_data(COMMUNITY_FILE, current_community)
                    st.success("투표가 실시간으로 배포되었습니다!")

            elif choice == "🏛️ 커뮤니티 게시글 관리":
                for idx, post in enumerate(current_community.get("posts", [])):
                    st.write(f"✍️ **{post['author']}:** {post['content']}")
                    if st.button("🗑️ 게시글 무조건 삭제", key=f"a_d_p_{idx}"):
                        current_community["posts"].pop(idx)
                        save_data(COMMUNITY_FILE, current_community)
                        st.rerun()

            elif choice == "💬 학생 질문 로그":
                for uid, history in current_chats.items():
                    st.write(f"👤 **학번 {uid} 기록:**")
                    for chat in history: st.caption(f"- [{chat['time']}] {chat['query']}")

            elif choice == "🔥 최다 질문 통계":
                all_words = []
                for uid, history in current_chats.items():
                    for chat in history: all_words.extend(chat['query'].split())
                st.write(f"📊 수집된 실시간 검색어 키워드 총 {len(all_words)}개")

            elif choice == "➕ 일반 관리자 계정 생성":
                sub_id = st.text_input("일반 관리자 ID")
                sub_name = st.text_input("담당 교사 이름")
                sub_pw = st.text_input("비밀번호", type="password")
                if st.button("🛡️ 서브 관리자 추가") and sub_id and sub_name and sub_pw:
                    current_users[sub_id] = {"password": sub_pw, "name": sub_name, "role": "sub_admin"}
                    save_data(USER_FILE, current_users)
                    st.success("관리자 등록 성공!")

        admin_dashboard(sub_choice)

    # ==================== [[ 🎓 2. 학생 전용 대시보드 분기 ]] ====================
    else:
        # 학생 대시보드 프래그먼트 (전체 새로고침 없이 하트/공지/투표 실시간 수신)
        @st.fragment(run_every="3s")
        def student_dashboard():
            current_community = load_data(COMMUNITY_FILE)
            
            st.markdown("### 📢 실시간 학교 공지사항")
            st.info(current_community.get('notice', '등록된 공지사항이 없습니다.'))
            
            tab1, tab2, tab3 = st.tabs(["🤖 규정 질문 챗봇", "🏛️ 학생 소통 커뮤니티", "📊 실시간 투표존"])

            with tab1:
                st.write("### 🤖 학교 생활 규정집 검색기")
                user_query = st.text_input("궁금한 규정 키워드를 입력하세요:", key="s_query_main")
                if st.button("🔎 검색하기", key="s_query_btn_main") and user_query:
                    st.markdown(search_pdf_with_highlight(user_query, pdf_content), unsafe_allow_html=True)

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
                    st.markdown(f"👤 **{post['author']}**")
                    st.info(post["content"])
                    
                    # 하트 버튼 실시간 반응 및 동기화 처리
                    if st.button(f"❤️ {len(post['likes'])}", key=f"s_l_{idx}_{len(post['likes'])}"):
                        if st.session_state.user_id in post["likes"]: post["likes"].remove(st.session_state.user_id)
                        else: post["likes"].append(st.session_state.user_id)
                        save_data(COMMUNITY_FILE, current_community)
                        st.rerun()

                    with st.expander(f"💬 댓글 ({len(post['comments'])}개)"):
                        for comment in post["comments"]: st.write(f"↳ **{comment['author']}**: {comment['text']}")
                        with st.form(f"s_cmt_form_{idx}", clear_on_submit=True):
                            cmt_text = st.text_input("댓글 작성란", key=f"s_i_cmt_{idx}")
                            if st.form_submit_button("등록") and cmt_text:
                                if check_bad_words(cmt_text)[0]:
                                    post["comments"].append({"author": st.session_state.user_name, "text": cmt_text})
                                    save_data(COMMUNITY_FILE, current_community)
                                    st.rerun()

            with tab3:
                st.write("### 📊 실시간 학생 투표광장")
                for p_idx, poll in enumerate(current_community.get("polls", [])):
                    st.write(f"#### ❓ 주제: {poll['title']}")
                    if poll.get("is_closed", False) or st.session_state.user_id in poll["voted_users"]:
                        st.warning("참여 완료 되었거나 마감된 안건입니다.")
                        for opt, val in poll["votes"].items(): st.write(f"✔️ **{opt}** : {val}표")
                    else:
                        selected_opt = st.radio("보기를 선택하세요", poll["options"], key=f"s_p_opt_{p_idx}")
                        if st.button("투표 제출", key=f"s_p_btn_{p_idx}"):
                            poll["votes"][selected_opt] += 1
                            poll["voted_users"].append(st.session_state.user_id)
                            save_data(COMMUNITY_FILE, current_community)
                            st.rerun()

        student_dashboard()