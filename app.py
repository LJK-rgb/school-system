import streamlit as st
import json
import os
from datetime import datetime
import pypdf
import re

# 데이터 저장용 파일 설정
USER_FILE = "users.json"
CHAT_FILE = "chats.json"
COMMUNITY_FILE = "community.json"
PDF_FILE = "2025. 학생생활규정.pdf"

# --- [관리자 기능] 기본 금지어 리스트 설정 ---
BAD_WORDS = ["바보", "멍청이", "지랄", "존나", "개새끼", "시발", "새끼", " 미친"]

def check_bad_words(text):
    """텍스트에 금지어가 포함되어 있는지 확인하는 함수"""
    for word in BAD_WORDS:
        if word in text:
            return False, word
    return True, ""

# --- 데이터 입출력 함수 ---
def load_data(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- PDF 텍스트 추출 및 구조화 검색 함수 ---
@st.cache_resource
def load_pdf_text(filepath):
    if not os.path.exists(filepath):
        return ""
    text = ""
    reader = pypdf.PdfReader(filepath)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def search_pdf_with_highlight(query, pdf_text):
    if not pdf_text:
        return "⚠️ 현재 서버에 학교 규정집 PDF 파일이 없거나 읽을 수 없습니다."
    
    keywords = [kw for kw in query.split() if len(kw) > 1]
    if not keywords:
        return "🔍 검색어를 두 글자 이상 입력해 주세요."
        
    sections = re.split(r'(제\s*\d+\s*조)', pdf_text)
    results = []
    
    for i in range(1, len(sections), 2):
        section_title = sections[i].strip()
        section_content = sections[i+1] if i+1 < len(sections) else ""
        
        if any(kw in section_content for kw in keywords):
            full_text = section_title + section_content
            
            highlighted_text = full_text
            for kw in keywords:
                highlighted_text = re.sub(f"({re.escape(kw)})", r"<mark style='background-color: #FFEB3B; color: #000000; padding: 2px 4px; border-radius: 3px; font-weight: bold;'>\1</mark>", highlighted_text)
            
            results.append(highlighted_text.strip())
            if len(results) >= 3:
                break
                
    if results:
        output = "🔍 **규정집 내부 매칭된 조항 검색 결과:**\n\n"
        for res in results:
            output += f"<div style='background-color: #F8F9FA; color: #1E293B; padding: 18px; border-radius: 8px; margin-bottom: 12px; border-left: 5px solid #FF4B4B; white-space: pre-wrap; font-size: 15px; line-height: 1.6;'>{res}</div>"
        return output
    else:
        return "🔍 규정집에서 관련 조항을 찾지 못했습니다. 보다 정확한 단어(예: 두발, 전자기기, 복장, 휴대전화 등)로 다시 질문해 주세요."

# 데이터 기본 로드
users = load_data(USER_FILE)
chats = load_data(CHAT_FILE)
community = load_data(COMMUNITY_FILE)
pdf_content = load_pdf_text(PDF_FILE)

# 데이터 구조 초기화 및 방어 코드
if "posts" not in community: community["posts"] = []
if "polls" not in community: community["polls"] = []
if "notice" not in community: community["notice"] = "아직 등록된 공지사항이 없습니다."
if "notice_author" not in community: community["notice_author"] = "시스템"
if "notice_time" not in community: community["notice_time"] = ""
if "notice_likes" not in community: community["notice_likes"] = []
if "notice_comments" not in community: community["notice_comments"] = []

# 최고 관리자 계정 정보 강제 동기화
users["admin"] = {
    "password": "ahsknue2026_2026!", 
    "name": "최고관리자", 
    "role": "master_admin"
}
save_data(USER_FILE, users)

# 스트림릿 앱 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.role = "user"

# --- 메인 화면 타이틀 ---
st.title("🏫 신입생 학교생활 가이드 & 커뮤니티")

# --- 1. 로그아웃 상태일 때 ---
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
                
                if user_id == "admin":
                    st.session_state.role = "master_admin"
                elif users[user_id].get("role") == "sub_admin":
                    st.session_state.role = "sub_admin"
                else:
                    st.session_state.role = "user"
                    
                st.success(f"🎉 {st.session_state.user_name}님 로그인 성공!")
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    with auth_tab2:
        st.subheader("회원가입")
        new_id = st.text_input("학번 (숫자만 입력 가능)", placeholder="예: 10101", key="join_id_input")
        new_name = st.text_input("이름 (한글 3~4글자, 초성 불가)", placeholder="예: 홍길동", key="join_name_input")
        new_pw = st.text_input("비밀번호 (영문+숫자+특수문자 필수)", type="password", placeholder="특수문자: !@#$%^&*_", key="join_pw_input")
        
        if st.button("가입하기", use_container_width=True):
            if not new_id or not new_name or not new_pw: 
                st.error("❌ 모든 칸을 입력해주세요.")
            elif not re.match(r"^\d+$", new_id):
                st.error("❌ 학번 칸에는 숫자만 입력할 수 있습니다.")
            elif not re.match(r"^[가-힣]{3,4}$", new_name):
                st.error("❌ 이름은 공백이나 초성 없이 정확히 한글 3~4글자로 입력해 주세요.")
            elif not (re.search(r"[a-zA-Z]", new_pw) and re.search(r"\d", new_pw) and re.search(r"[!@#\$%\^&\*_]", new_pw)):
                st.error("❌ 비밀번호는 영문자, 숫자, 특수문자(!@#$%^&*_)가 각각 최소 1개 이상씩 포함되어야 합니다.")
            elif new_id in users or new_id == "admin": 
                st.error("❌ 이미 존재하는 학번이거나 사용할 수 없는 ID입니다.")
            else:
                users[new_id] = {"password": new_pw, "name": new_name, "role": "user"}
                save_data(USER_FILE, users)
                st.success("🎉 회원가입이 완료되었습니다! 로그인 탭으로 이동해 로그인해주세요.")

# --- 2. 로그인 완료 상태일 때 ---
else:
    st.sidebar.markdown(f"### 👤 {st.session_state.user_name}님")
    
    if st.session_state.role == "master_admin":
        st.sidebar.markdown("👑 **등급:** `최고 관리자 (마스터)`")
    elif st.session_state.role == "sub_admin":
        st.sidebar.markdown("🛡️ **등급:** `일반 관리자`")
    else:
        st.sidebar.markdown("🎓 **등급:** `일반 학생 사용자`")
        
    if st.sidebar.button("로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.role = "user"
        st.rerun()

    # ==================== [[ ⚙️ 관리자 전용 사이드바 창 ]] ====================
    if st.session_state.role in ["master_admin", "sub_admin"]:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🛠️ 관리자 전용 메뉴")
        
        admin_menu = ["🔍 전체 계정 관리", "📢 공지 및 투표 관리", "🏛️ 커뮤니티 게시글 관리", "💬 학생 질문 로그", "🔥 최다 질문 통계"]
        
        if st.session_state.role == "sub_admin":
            admin_menu.append("🏛️ 학생 커뮤니티 보기")
            admin_menu.append("📊 실시간 투표존 보기")
            
        if st.session_state.role == "master_admin":
            admin_menu.append("➕ 일반 관리자 계정 생성")
            
        sub_choice = st.sidebar.radio("제어할 기능을 선택하세요", admin_menu)

        st.subheader(f"⚙️ 관리 제어판 -> {sub_choice}")

        # ---- 🔍 전체 계정 관리 패널 ----
        if sub_choice == "🔍 전체 계정 관리":
            st.write("#### 👤 교내 멤버 정보 검색 및 수정/삭제")
            search_uid = st.text_input("🔍 학번 또는 관리자 ID 입력 검색 (빈칸이면 전체 조회)", placeholder="예: 10101 또는 교사ID")
            st.markdown("---")
            
            target_users = {}
            if search_uid:
                if search_uid in users and users[search_uid].get("role") != "master_admin":
                    target_users[search_uid] = users[search_uid]
                else:
                    st.info("검색된 대상 계정이 없거나 최고관리자 계정은 수정할 수 없습니다.")
            else:
                target_users = {k: v for k, v in users.items() if v.get("role") != "master_admin"}

            if target_users:
                for u_id, u_info in target_users.items():
                    u_role = u_info.get("role", "user")
                    role_badge = "🛡️ [일반 관리자]" if u_role == "sub_admin" else "🎓 [일반학생]"
                    
                    if u_role == "sub_admin" and st.session_state.role != "master_admin":
                        with st.expander(f"{role_badge} ID: {u_id} | 이름: {u_info['name']}"):
                            st.warning("🔒 일반 관리자 계정 정보는 최고관리자(master_admin)만 조회 및 수정할 수 있습니다.")
                        continue
                        
                    with st.expander(f"{role_badge} ID/학번: {u_id} | 이름: {u_info['name']} 계정 설정"):
                        edit_name = st.text_input(f"이름 수정 ({u_id})", value=u_info['name'], key=f"name_{u_id}")
                        edit_pw = st.text_input(f"비밀번호 조회/수정 ({u_id})", value=u_info['password'], key=f"pw_{u_id}")
                        
                        col_u1, col_u2 = st.columns(2)
                        with col_u1:
                            if st.button(f"💾 {u_id} 정보 수정 저장", key=f"save_u_{u_id}"):
                                users[u_id]['name'] = edit_name
                                users[u_id]['password'] = edit_pw
                                save_data(USER_FILE, users)
                                st.success(f"{u_id} 계정 정보가 성공적으로 변경되었습니다!")
                                st.rerun()
                        with col_u2:
                            if st.button(f"🗑️ {u_id} 계정 권한 회수 및 삭제", key=f"del_u_{u_id}"):
                                users.pop(u_id)
                                save_data(USER_FILE, users)
                                st.warning(f"{u_id} 계정이 파기되었습니다.")
                                st.rerun()

        # ---- 📢 공지 및 투표 관리 패널 ----
        elif sub_choice == "📢 공지 및 투표 관리":
            st.write("#### 1. 대시보드 공지사항 제어")
            new_notice = st.text_area("수정할 공지사항 내용", value=community["notice"])
            col_n1, col_n2 = st.columns(2)
            with col_n1:
                if st.button("📢 공지사항 업데이트", use_container_width=True):
                    # 공지사항 내용 금지어 체크
                    is_clean, bad_w = check_bad_words(new_notice)
                    if not is_clean:
                        st.error(f"❌ 공지사항에 부적절한 단어({bad_w})가 포함되어 등록할 수 없습니다.")
                    else:
                        community["notice"] = new_notice
                        community["notice_author"] = st.session_state.user_name
                        community["notice_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        save_data(COMMUNITY_FILE, community)
                        st.success("공지사항이 새로운 작성자 정보와 함께 업데이트되었습니다.")
                        st.rerun()
            with col_n2:
                if st.button("🗑️ 공지사항 및 피드백 전체 초기화", use_container_width=True):
                    community["notice"] = "아직 등록된 공지사항이 없습니다."
                    community["notice_author"] = "시스템"
                    community["notice_time"] = ""
                    community["notice_likes"] = []
                    community["notice_comments"] = []
                    save_data(COMMUNITY_FILE, community)
                    st.warning("공지사항이 초기화되었습니다.")
                    st.rerun()

            st.write("---")
            st.write("#### 2. 실시간 학생 투표 개설, 마감 및 삭제")
            poll_title = st.text_input("투표 안건 주제 입력")
            poll_opt1 = st.text_input("선택지 보기 1")
            poll_opt2 = st.text_input("선택지 보기 2")
            if st.button("🗳️ 투표 공식 발의"):
                if poll_title and poll_opt1 and poll_opt2:
                    community["polls"].append({
                        "id": len(community["polls"]),
                        "title": poll_title,
                        "options": [poll_opt1, poll_opt2],
                        "votes": {poll_opt1: 0, poll_opt2: 0},
                        "voted_users": [],
                        "is_closed": False,
                        "likes": [],
                        "comments": []
                    })
                    save_data(COMMUNITY_FILE, community)
                    st.success("새로운 학생 투표가 등록되었습니다.")
                    st.rerun()
            
            st.write("---")
            st.markdown("**[현재 진행 중인 투표 목록 제어]**")
            if not community["polls"]:
                st.info("현재 개설된 투표가 없습니다.")
            else:
                for p_idx, poll in enumerate(community["polls"]):
                    status_text = "🔒 [마감됨]" if poll.get("is_closed", False) else "🔓 [진행중]"
                    st.write(f"📊 **{status_text} 주제:** {poll['title']} (참여수: {len(poll['voted_users'])}명)")
                    
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        if not poll.get("is_closed", False):
                            if st.button(f"🔒 '{poll['title'][:6]}...' 마감하기", key=f"close_poll_{p_idx}", use_container_width=True):
                                community["polls"][p_idx]["is_closed"] = True
                                save_data(COMMUNITY_FILE, community)
                                st.success("투표가 마감 처리되었습니다.")
                                st.rerun()
                        else:
                            st.caption("이미 마감된 투표입니다.")
                    with col_p2:
                        if st.button(f"🗑️ '{poll['title'][:6]}...' 완전 삭제", key=f"del_poll_{p_idx}", use_container_width=True):
                            community["polls"].pop(p_idx)
                            save_data(COMMUNITY_FILE, community)
                            st.success("투표가 삭제되었습니다.")
                            st.rerun()

        # ---- 🏛️ 커뮤니티 게시글 관리 패널 ----
        elif sub_choice == "🏛️ 커뮤니티 게시글 관리":
            st.write("#### 🚨 학생 커뮤니티 전체 게시물 관리")
            st.caption("게시글 파기뿐만 아니라 특정 댓글 삭제 및 악의적인 공감수(좋아요) 강제 초기화 제어가 가능합니다.")
            
            if not community["posts"]:
                st.info("현재 대나무숲에 등록된 글이 없습니다.")
            else:
                for idx, post in enumerate(community["posts"]):
                    with st.container():
                        st.markdown(f"✍️ **작성자:** `{post['author']}` | ❤️ 공감: {len(post['likes'])}개 | 💬 댓글: {len(post['comments'])}개")
                        st.info(post["content"])
                        
                        col_adm1, col_adm2 = st.columns(2)
                        with col_adm1:
                            if st.button(f"🗑️ 게시글 내용 전면 삭제", key=f"del_post_{idx}", use_container_width=True):
                                removed_post = community["posts"].pop(idx)
                                save_data(COMMUNITY_FILE, community)
                                st.warning(f"[{removed_post['author']}]님의 글이 삭제되었습니다.")
                                st.rerun()
                        with col_adm2:
                            if st.button(f"❤️ 공감 수 초기화 (0으로 세팅)", key=f"reset_likes_{idx}", use_container_width=True):
                                community["posts"][idx]["likes"] = []
                                save_data(COMMUNITY_FILE, community)
                                st.success("해당 게시글의 공감 수가 초기화되었습니다.")
                                st.rerun()
                        
                        if post["comments"]:
                            st.markdown("<p style='font-size:13px; font-weight:bold; color:#555; margin-top:8px;'>▼ 댓글 내역 리스트 제어</p>", unsafe_allow_html=True)
                            for c_idx, comment in enumerate(post["comments"]):
                                c_col1, c_col2 = st.columns([4, 1])
                                with c_col1:
                                    st.caption(f"↳ **{comment['author']}**: {comment['text']}")
                                with c_col2:
                                    if st.button("🗑️ 댓글 삭제", key=f"del_cmt_{idx}_{c_idx}"):
                                        community["posts"][idx]["comments"].pop(c_idx)
                                        save_data(COMMUNITY_FILE, community)
                                        st.warning("선택한 댓글이 삭제되었습니다.")
                                        st.rerun()
                                        
                        st.markdown("<hr style='margin: 12px 0 24px 0; border-top: 1px dashed #ccc;'>", unsafe_allow_html=True)

        elif sub_choice == "💬 학생 질문 로그":
            st.write("#### 📋 학생별 규정집 실시간 질문 로그")
            if not chats:
                st.info("아직 학생들이 검색한 데이터 내역이 없습니다.")
            else:
                for uid, history in chats.items():
                    student_name = users.get(uid, {}).get("name", "미등록 사용자")
                    with st.expander(f"👤 학번: {uid} ({student_name})의 검색 기록"):
                        for chat in history:
                            st.write(f"**[{chat['time']}]** 입력어: `{chat['query']}`")

        elif sub_choice == "🔥 최다 질문 통계":
            st.write("#### 📊 학생들의 최고 관심 규정 키워드")
            all_words = []
            for uid, history in chats.items():
                for chat in history:
                    all_words.extend(chat['query'].split())
            
            filtered = [w for w in all_words if len(w) > 1]
            if not filtered:
                st.info("통계 분석을 수행할 검색 데이터가 아직 축적되지 않았습니다.")
            else:
                counts = {}
                for w in filtered: counts[w] = counts.get(w, 0) + 1
                top_five = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
                
                st.metric("📈 전체 실시간 검색어 수", len(filtered))
                for rank, (word, cnt) in enumerate(top_five, 1):
                    st.write(f"🥇 **{rank}위** : `{word}` (총 {cnt}회 조회)")

        elif sub_choice == "🏛️ 학생 커뮤니티 보기":
            st.write("### 🏛️ 익명/실명 학생 대나무숲 (일반 관리자 모니터링 뷰)")
            if not community["posts"]:
                st.info("현재 대나무숲에 등록된 게시글이 없습니다.")
            else:
                for idx, post in enumerate(community["posts"]):
                    st.markdown(f"👤 **{post['author']}**")
                    st.info(post["content"])
                    st.write(f"❤️ 공감 {len(post['likes'])}개 | 💬 댓글 {len(post['comments'])}개")
                    for comment in post["comments"]:
                        st.write(f"↳ **{comment['author']}**: {comment['text']}")
                    st.markdown("---")

        elif sub_choice == "📊 실시간 투표존 보기":
            st.write("### 📊 실시간 학생 투표광장 (일반 관리자 모니터링 뷰)")
            if not community["polls"]:
                st.info("현재 개설된 투표가 없습니다.")
            else:
                for p_idx, poll in enumerate(community["polls"]):
                    status_label = "🔒 [마감됨]" if poll.get("is_closed", False) else "🔓 [진행중]"
                    st.write(f"#### {status_label} 주제: {poll['title']}")
                    st.markdown("**📊 실시간 투표 현황 집계:**")
                    for opt, val in poll["votes"].items():
                        st.write(f"✔️ **{opt}** : {val}표")
                    for p_comment in poll.get("comments", []):
                        st.write(f"↳ **{p_comment['author']}**: {p_comment['text']}")
                    st.markdown("---")

        elif sub_choice == "➕ 일반 관리자 계정 생성":
            st.write("#### 🛡️ 신규 일반 관리자(General Admin) 계정 발급")
            sub_id = st.text_input("일반 관리자용 로그인 ID")
            sub_name = st.text_input("일반 관리자 담당자 이름")
            sub_pw = st.text_input("일반 관리자용 비밀번호", type="password")
            
            if st.button("일반 관리자 계정 등록"):
                if not sub_id or not sub_name or not sub_pw:
                    st.error("빈칸 없이 모두 입력해 주세요.")
                elif sub_id in users or sub_id == "admin":
                    st.error("이미 사용 중인 중복 ID입니다.")
                else:
                    users[sub_id] = {"password": sub_pw, "name": sub_name, "role": "sub_admin"}
                    save_data(USER_FILE, users)
                    st.success(f"🎉 {sub_name} 일반 관리자 계정이 활성화되었습니다!")

    # ==================== [[ 학생 / 사용자 전용 일반 메인 화면 ]] ====================
    else:
        time_label = f" ({community['notice_time']})" if community["notice_time"] else ""
        st.markdown(f"📢 **학교 공지사항** <span style='font-size:12px; color:#777;'>[작성자: {community['notice_author']}{time_label}]</span>", unsafe_allow_html=True)
        st.info(community['notice'])
        
        with st.expander(f"💬 공지사항 반응 남기기 (❤️ {len(community['notice_likes'])} | 댓글 {len(community['notice_comments'])}개)"):
            col_n_like, _ = st.columns([1, 4])
            with col_n_like:
                notice_like_label = f"❤️ 공감 {len(community['notice_likes'])}"
                if st.button(notice_like_label, key="notice_like_btn"):
                    if st.session_state.user_id in community["notice_likes"]:
                        community["notice_likes"].remove(st.session_state.user_id)
                    else:
                        community["notice_likes"].append(st.session_state.user_id)
                    save_data(COMMUNITY_FILE, community)
                    st.rerun()
            
            for n_cmt in community["notice_comments"]:
                st.write(f"↳ **{n_cmt['author']}**: {n_cmt['text']}")
            
            with st.form("notice_comment_form", clear_on_submit=True):
                n_comment_text = st.text_input("공지사항에 댓글 남기기", placeholder="공지 내용을 확인했다면 댓글을 달아주세요.")
                if st.form_submit_button("공지 댓글 등록"):
                    if n_comment_text:
                        # 댓글 금지어 우회 필터링
                        is_clean, bad_w = check_bad_words(n_comment_text)
                        if not is_clean:
                            st.error(f"❌ 댓글에 부적절한 단어({bad_w})가 포함되어 등록할 수 없습니다.")
                        else:
                            community["notice_comments"].append({
                                "author": st.session_state.user_name,
                                "text": n_comment_text
                            })
                            save_data(COMMUNITY_FILE, community)
                            st.rerun()

        st.write("---")
        tab1, tab2, tab3 = st.tabs(["🤖 규정 질문 챗봇", "🏛️ 학생 소통 커뮤니티", "📊 실시간 투표존"])

        # ---- 탭 1: 규정 질문 챗봇 ----
        with tab1:
            st.write("### 🤖 학교 생활 규정집 검색기")
            st.caption("질문 단어를 입력하고 버튼을 누르면 해당 키워드가 들어있는 정확한 '조·항'을 찾아 형광펜 표시해 줍니다.")
            st.info("🔥 **학생들이 가장 많이 찾은 단어** : `두발`, `휴대폰`, `지각`, `복장`")
            
            user_query = st.text_input("궁금한 규정 키워드를 입력하세요 (예: 두발 규정):", key="chatbot_query")
            
            if st.button("🔎 규정집 실시간 검색하기"):
                if user_query:
                    answer_html = search_pdf_with_highlight(user_query, pdf_content)
                    st.markdown(answer_html, unsafe_allow_html=True)

                    if st.session_state.user_id not in chats:
                        chats[st.session_state.user_id] = []
                    
                    chats[st.session_state.user_id].append({
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "query": user_query,
                        "answer": "검색 완료(HTML 표출)"
                    })
                    save_data(CHAT_FILE, chats)

        # ---- 탭 2: 커뮤니티 ----
        with tab2:
            st.write("### 🏛️ 익명/실명 학생 대나무숲")
            
            with st.form("community_form", clear_on_submit=True):
                post_content = st.text_area("학교 생활이나 궁금한 점을 자유롭게 이야기해 보세요!", placeholder="매너를 지켜 글을 작성해 주세요.")
                is_anonymous = st.checkbox("익명으로 올리기")
                submit_post = st.form_submit_button("게시글 올리기")
                
                if submit_post and post_content:
                    # 게시글 작성 시 금지어 자동 필터링 적용
                    is_clean, bad_w = check_bad_words(post_content)
                    if not is_clean:
                        st.error(f"❌ 작성하신 내용에 부적절한 단어({bad_w})가 포함되어 게시할 수 없습니다. 바른 말을 사용해 주세요!")
                    else:
                        author_name = "익명의 새내기" if is_anonymous else st.session_state.user_name
                        community["posts"].insert(0, {
                            "id": len(community["posts"]),
                            "author": author_name,
                            "content": post_content,
                            "likes": [],
                            "comments": []
                        })
                        save_data(COMMUNITY_FILE, community)
                        st.success("글이 정상적으로 등록되었습니다!")
                        st.rerun()

            st.write("---")
            if not community["posts"]:
                st.info("가장 먼저 첫 게시글의 주인공이 되어보세요!")
            else:
                for idx, post in enumerate(community["posts"]):
                    st.markdown(f"👤 **{post['author']}**")
                    st.info(post["content"])
                    
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        like_label = f"❤️ {len(post['likes'])}"
                        if st.button(like_label, key=f"like_{idx}"):
                            if st.session_state.user_id in post["likes"]:
                                post["likes"].remove(st.session_state.user_id)
                            else:
                                post["likes"].append(st.session_state.user_id)
                            save_data(COMMUNITY_FILE, community)
                            st.rerun()
                            
                    with st.expander(f"💬 댓글 ({len(post['comments'])}개) 열기"):
                        for comment in post["comments"]:
                            st.write(f"↳ **{comment['author']}**: {comment['text']}")
                        
                        with st.form(f"comment_form_{idx}", clear_on_submit=True):
                            comment_text = st.text_input("댓글 쓰기", placeholder="따뜻한 댓글을 남겨주세요.")
                            if st.form_submit_button("등록"):
                                if comment_text:
                                    # 댓글 등록 시 금지어 자동 필터링 적용
                                    is_clean, bad_w = check_bad_words(comment_text)
                                    if not is_clean:
                                        st.error(f"❌ 댓글 내용에 부적절한 단어({bad_w})가 포함되어 있습니다.")
                                    else:
                                        post["comments"].append({
                                            "author": st.session_state.user_name,
                                            "text": comment_text
                                        })
                                        save_data(COMMUNITY_FILE, community)
                                        st.rerun()
                    st.markdown("---")

        # ---- 탭 3: 실시간 투표존 ----
        with tab3:
            st.write("### 📊 실시간 학생 투표광장")
            if not community["polls"]:
                st.info("현재 진행 중인 학생 투표가 없습니다. 관리자의 새로운 투표를 기다려주세요!")
            else:
                for p_idx, poll in enumerate(community["polls"]):
                    if "is_closed" not in poll: poll["is_closed"] = False
                    if "likes" not in poll: poll["likes"] = []
                    if "comments" not in poll: poll["comments"] = []
                    
                    is_closed = poll["is_closed"]
                    st.write(f"#### ❓ 주제: {poll['title']}")
                    
                    if is_closed:
                        st.error("📥 본 투표는 관리자에 의해 마감되었습니다. 더 이상 투표를 제출하거나 수정할 수 없습니다.")
                        st.markdown("**📊 최종 투표 집계 결과:**")
                        for opt, val in poll["votes"].items():
                            st.write(f"✔️ **{opt}** : {val}표")
                    else:
                        if st.session_state.user_id in poll["voted_users"]:
                            st.warning("이미 투표에 참여하셨습니다! 실시간 집계 결과:")
                            for opt, val in poll["votes"].items():
                                st.write(f"✔️ **{opt}** : {val}표")
                        else:
                            selected_opt = st.radio("보기를 선택하세요", poll["options"], key=f"poll_select_{p_idx}")
                            if st.button("투표 제출하기", key=f"poll_btn_{p_idx}"):
                                poll["votes"][selected_opt] += 1
                                poll["voted_users"].append(st.session_state.user_id)
                                save_data(COMMUNITY_FILE, community)
                                st.success("투표가 성공적으로 반영되었습니다!")
                                st.rerun()
                    
                    col_pl, _ = st.columns([1, 4])
                    with col_pl:
                        p_like_label = f"❤️ {len(poll['likes'])}"
                        if st.button(p_like_label, key=f"poll_like_{p_idx}", disabled=is_closed):
                            if st.session_state.user_id in poll["likes"]:
                                poll["likes"].remove(st.session_state.user_id)
                            else:
                                poll["likes"].append(st.session_state.user_id)
                            save_data(COMMUNITY_FILE, community)
                            st.rerun()
                            
                    with st.expander(f"💬 투표 댓글 ({len(poll['comments'])}개) 보기"):
                        for p_comment in poll["comments"]:
                            st.write(f"↳ **{p_comment['author']}**: {p_comment['text']}")
                        
                        if is_closed:
                            st.caption("🔒 투표가 마감되어 댓글 작성이 제한됩니다.")
                        else:
                            with st.form(f"poll_cmt_form_{p_idx}", clear_on_submit=True):
                                p_comment_text = st.text_input("투표에 한마디 남기기", placeholder="투표 안건에 대한 본인의 생각을 공유해 주세요.")
                                if st.form_submit_button("댓글 등록"):
                                    if p_comment_text:
                                        # 투표 댓글에도 금지어 자동 필터링 적용
                                        is_clean, bad_w = check_bad_words(p_comment_text)
                                        if not is_clean:
                                            st.error(f"❌ 한마디 내용에 부적절한 단어({bad_w})가 포함되어 있습니다.")
                                        else:
                                            poll["comments"].append({
                                                "author": st.session_state.user_name,
                                                "text": p_comment_text
                                            })
                                            save_data(COMMUNITY_FILE, community)
                                            st.rerun()
                    st.markdown("---")