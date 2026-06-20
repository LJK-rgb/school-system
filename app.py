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

# --- 🎨 [2] 디자인 및 히든 브릿지 은폐 CSS ---
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
        
        /* 🚨 상단에 노출되던 로그인 유지용 브릿지 인풋을 우주 끝으로 밀어서 완벽하게 숨김 */
        div[data-testid="stTextInput"]:has(input[aria-label="storage_bridge"]) {
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

def load_data(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f: return json.load(f)
    return {}

def save_data(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

@st.cache_resource
def load_pdf_text(filepath):
    if not os.path.exists(filepath): return ""
    text = ""
    reader = pypdf.PdfReader(filepath)
    for page in reader.pages: text += page.extract_text() + "\n"
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

# 데이터 초기 로드
users = load_data(USER_FILE)
chats = load_data(CHAT_FILE)
community = load_data(COMMUNITY_FILE)
pdf_content = load_pdf_text(PDF_FILE)

for key in ["posts", "polls"]:
    if key not in community: community[key] = []
if "notice" not in community: community["notice"] = "아직 등록된 공지사항이 없습니다."
if "notice_likes" not in community: community["notice_likes"] = []
if "notice_comments" not in community: community["notice_comments"] = []

users["admin"] = {"password": "ahsknue2026_2026!", "name": "최고관리자", "role": "master_admin"}
save_data(USER_FILE, users)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.role = "user"

# --- 🔐 [로그인 자동 복구] 브라우저 종료/새로고침 대응 브릿지 ---
if not st.session_state.logged_in:
    storage_bridge = st.text_input("storage_bridge", key="storage_bridge", label_visibility="collapsed")
    st.components.v1.html(
        """
        <script>
            const parentDoc = window.parent.document;
            const savedUser = localStorage.getItem("saved_user_info");
            if (savedUser) {
                const inputs = parentDoc.querySelectorAll('input[type="text"]');
                let bridgeInput = null;
                for (let input of inputs) {
                    if (input.ariaLabel === "storage_bridge" || input.id === "storage_bridge") {
                        bridgeInput = input;
                        break;
                    }
                }
                if (bridgeInput && bridgeInput.value !== savedUser) {
                    bridgeInput.value = savedUser;
                    bridgeInput.dispatchEvent(new Event('input', { bubbles: true }));
                    bridgeInput.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        </script>
        """,
        height=0
    )
    if st.session_state.storage_bridge:
        try:
            user_info = json.loads(st.session_state.storage_bridge)
            st.session_state.logged_in = True
            st.session_state.user_id = user_info["id"]
            st.session_state.user_name = user_info["name"]
            st.session_state.role = user_info["role"]
            st.rerun()
        except:
            pass

# 상단 헤더 로고
col_logo, col_title = st.columns([1, 4])
with col_logo: st.image("https://i.namu.wiki/i/-eAroAg-qXbT2pJ1ZA7PmtbFwbmwAxEwBCc3oLa4UhKh2DixIyG2i6kJw-TrTqEsLkVAOhlGN0nASpm690SRmA.webp", width=110)
with col_title:
    st.markdown("<div style='padding-top: 15px;'></div>", unsafe_allow_html=True)
    st.title("신입생 학교생활 가이드 & 소통망")

st.markdown("---")

# --- 미로그인 화면 ---
if not st.session_state.logged_in:
    st.info("👋 안녕하세요! 서비스를 이용하시려면 로그인이나 회원가입을 진행해 주세요.")
    auth_tab1, auth_tab2 = st.tabs(["🔑 로그인", "📝 회원가입"])

    with auth_tab1:
        st.subheader("로그인")
        user_id = st.text_input("학번 / 아이디", key="login_id_input")
        user_pw = st.text_input("비밀번호", type="password", key="login_pw_input")

        if st.button("로그인하기", use_container_width=True):
            if user_id in users and users[user_id]["password"] == user_pw:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.user_name = users[user_id]["name"]
                st.session_state.role = "master_admin" if user_id == "admin" else users[user_id].get("role", "user")
                
                st.components.v1.html(f"""
                    <script>
                        localStorage.setItem("saved_user_info", JSON.stringify({{
                            id: "{st.session_state.user_id}", name: "{st.session_state.user_name}", role: "{st.session_state.role}"
                        }}));
                    </script>
                """, height=0)
                st.success(f"🎉 {st.session_state.user_name}님 로그인 성공!")
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    with auth_tab2:
        st.subheader("회원가입")
        new_id = st.text_input("학번 (숫자만)", key="join_id_input")
        new_name = st.text_input("이름 (한글 3~4자)", key="join_name_input")
        new_pw = st.text_input("비밀번호", type="password", key="join_pw_input")
        if st.button("가입하기", use_container_width=True):
            if new_id and new_name and new_pw:
                users[new_id] = {"password": new_pw, "name": new_name, "role": "user"}
                save_data(USER_FILE, users)
                st.success("회원가입이 완료되었습니다!")

# --- 로그인 완료 화면 ---
else:
    st.sidebar.markdown(f"### 👤 {st.session_state.user_name}님")
    if st.session_state.role == "master_admin": st.sidebar.markdown("👑 **등급:** `최고 관리자`")
    elif st.session_state.role == "sub_admin": st.sidebar.markdown("🛡️ **등급:** `일반 관리자`")
    else: st.sidebar.markdown("🎓 **등급:** `일반 학생 사용자`")

    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.components.v1.html("<script>localStorage.removeItem('saved_user_info');</script>", height=0)
        st.rerun()

    # ==================== [[ 🛠️ 1. 관리자 전용 대시보드 구역 ]] ====================
    if st.session_state.role in ["master_admin", "sub_admin"]:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🛠️ 관리자 메뉴")
        admin_menu = ["🔍 전체 계정 관리", "📢 공지 및 투표 관리", "🏛️ 커뮤니티 게시글 관리", "💬 학생 질문 로그", "🔥 최다 질문 통계"]
        if st.session_state.role == "master_admin": admin_menu.append("➕ 일반 관리자 계정 생성")
        sub_choice = st.sidebar.radio("제어할 기능을 선택하세요", admin_menu)
        
        @st.fragment(run_every="3s")
        def admin_dashboard(choice):
            current_users = load_data(USER_FILE)
            current_chats = load_data(CHAT_FILE)
            current_community = load_data(COMMUNITY_FILE)
            
            st.subheader(f"⚙️ 관리 제어판 -> {choice}")
            
            if choice == "🔍 전체 계정 관리":
                search_uid = st.text_input("🔍 학번 또는 관리자 ID 입력 검색 (빈칸이면 전체 조회)")
                target_users = {k: v for k, v in current_users.items() if v.get("role") != "master_admin"}
                if search_uid in current_users: target_users = {search_uid: current_users[search_uid]}
                
                for u_id, u_info in target_users.items():
                    with st.expander(f"ID/학번: {u_id} | 이름: {u_info['name']}"):
                        edit_name = st.text_input("이름", value=u_info['name'], key=f"adm_n_{u_id}")
                        edit_pw = st.text_input("비밀번호", value=u_info['password'], key=f"adm_p_{u_id}")
                        if st.button("💾 수정 저장", key=f"btn_save_{u_id}"):
                            current_users[u_id].update({"name": edit_name, "password": edit_pw})
                            save_data(USER_FILE, current_users)
                            st.rerun()

            elif choice == "📢 공지 및 투표 관리":
                new_notice = st.text_area("공지사항 내용 수정", value=current_community.get("notice", ""))
                if st.button("📢 공지 업데이트"):
                    current_community["notice"] = new_notice
                    save_data(COMMUNITY_FILE, current_community)
                    st.success("공지 완료!")
                st.write("---")
                poll_title = st.text_input("투표 안건 주제")
                poll_o1 = st.text_input("선택지 1")
                poll_o2 = st.text_input("선택지 2")
                if st.button("🗳️ 투표 발의") and poll_title and poll_o1 and poll_o2:
                    current_community["polls"].append({
                        "title": poll_title, "options": [poll_o1, poll_o2],
                        "votes": {poll_o1: 0, poll_o2: 0}, "voted_users": [], "is_closed": False
                    })
                    save_data(COMMUNITY_FILE, current_community)
                    st.rerun()

            elif choice == "🏛️ 커뮤니티 게시글 관리":
                for idx, post in enumerate(current_community.get("posts", [])):
                    st.write(f"✍️ **{post['author']}:** {post['content']}")
                    if st.button("🗑️ 글 삭제", key=f"adm_del_p_{idx}"):
                        current_community["posts"].pop(idx)
                        save_data(COMMUNITY_FILE, current_community)
                        st.rerun()

            elif choice == "💬 학생 질문 로그":
                for uid, history in current_chats.items():
                    st.write(f"👤 **학번 {uid}:**")
                    for chat in history: st.caption(f"- [{chat['time']}] {chat['query']}")

            elif choice == "🔥 최다 질문 통계":
                all_words = []
                for uid, history in current_chats.items():
                    for chat in history: all_words.extend(chat['query'].split())
                st.write(f"📊 수집된 검색 키워드 총 {len(all_words)}개")

            elif choice == "➕ 일반 관리자 계정 생성":
                sub_id = st.text_input("생성할 관리자 ID")
                sub_name = st.text_input("관리자 이름")
                sub_pw = st.text_input("비밀번호", type="password")
                if st.button("🛡️ 계정 생성") and sub_id and sub_name and sub_pw:
                    current_users[sub_id] = {"password": sub_pw, "name": sub_name, "role": "sub_admin"}
                    save_data(USER_FILE, current_users)
                    st.success("생성 완료!")

        admin_dashboard(sub_choice)

    # ==================== [[ 🎓 2. 학생/일반 사용자 전용 대시보드 구역 ]] ====================
    else:
        @st.fragment(run_every="3s")
        def student_dashboard():
            current_community = load_data(COMMUNITY_FILE)
            
            st.markdown("### 📢 실시간 학교 공지사항")
            st.info(current_community.get('notice', '등록된 공지사항이 없습니다.'))
            
            tab1, tab2, tab3 = st.tabs(["🤖 규정 질문 챗봇", "🏛️ 학생 소통 커뮤니티", "📊 실시간 투표존"])

            with tab1:
                st.write("### 🤖 학교 생활 규정집 검색기")
                user_query = st.text_input("궁금한 규정 키워드를 입력하세요:", key="stu_query")
                if st.button("🔎 검색하기", key="stu_query_btn") and user_query:
                    st.markdown(search_pdf_with_highlight(user_query, pdf_content), unsafe_allow_html=True)

            with tab2:
                st.write("### 🏛️ 익명/실명 학생 대나무숲")
                with st.form("stu_post_form", clear_on_submit=True):
                    post_content = st.text_area("학교 생활 이야기를 들려주세요!")
                    is_anonymous = st.checkbox("익명으로 게시")
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
                    
                    if st.button(f"❤️ {len(post['likes'])}", key=f"stu_l_{idx}_{len(post['likes'])}"):
                        if st.session_state.user_id in post["likes"]: post["likes"].remove(st.session_state.user_id)
                        else: post["likes"].append(st.session_state.user_id)
                        save_data(COMMUNITY_FILE, current_community)
                        st.rerun()

                    with st.expander(f"💬 댓글 ({len(post['comments'])}개)"):
                        for comment in post["comments"]: st.write(f"↳ **{comment['author']}**: {comment['text']}")
                        with st.form(f"stu_cmt_form_{idx}", clear_on_submit=True):
                            cmt_text = st.text_input("댓글 작성", key=f"stu_i_cmt_{idx}")
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
                        st.warning("참여 완료 또는 마감된 투표입니다.")
                        for opt, val in poll["votes"].items(): st.write(f"✔️ **{opt}** : {val}표")
                    else:
                        selected_opt = st.radio("보기를 선택하세요", poll["options"], key=f"stu_p_opt_{p_idx}")
                        if st.button("투표 제출", key=f"stu_p_btn_{p_idx}"):
                            poll["votes"][selected_opt] += 1
                            poll["voted_users"].append(st.session_state.user_id)
                            save_data(COMMUNITY_FILE, current_community)
                            st.rerun()

        student_dashboard()