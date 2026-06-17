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
            # 화이트/다크 모드 범용 스타일 (밝은 회색 바탕 + 짙은 네이비색 글씨 고정)
            output += f"<div style='background-color: #F8F9FA; color: #1E293B; padding: 18px; border-radius: 8px; margin-bottom: 12px; border-left: 5px solid #FF4B4B; white-space: pre-wrap; font-size: 15px; line-height: 1.6;'>{res}</div>"
        return output
    else:
        return "🔍 규정집에서 관련 조항을 찾지 못했습니다. 보다 정확한 단어(예: 두발, 전자기기, 복장, 휴대전화 등)로 다시 질문해 주세요."

# 데이터 기본 로드
users = load_data(USER_FILE)
chats = load_data(CHAT_FILE)
community = load_data(COMMUNITY_FILE)
pdf_content = load_pdf_text(PDF_FILE)

# 초기 커뮤니티 및 투표 데이터 구조 세팅
if "posts" not in community: community["posts"] = []
if "polls" not in community: community["polls"] = []
if "notice" not in community: community["notice"] = "아직 등록된 공지사항이 없습니다."

# [새출발 관리자 세팅] 기존 계정 엉킴 방지를 위해 시스템 시작 시 강제 동기화
users["admin"] = {"password": "admin1234", "name": "최고관리자", "role": "master_admin"}
save_data(USER_FILE, users)

# 스트림릿 앱 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.role = "user"

# --- 메인 화면 타이틀 ---
st.title("🏫 신입생 학교생활 가이드 & 커뮤니티")

# --- 1. 로그아웃 상태일 때 (로그인/회원가입 화면) ---
if not st.session_state.logged_in:
    menu = ["로그인", "회원가입"]
    choice = st.sidebar.selectbox("메뉴", menu)

    if choice == "회원가입":
        st.subheader("📝 회원가입")
        new_id = st.text_input("학번 (아이디로 사용)", placeholder="예: 10101")
        new_name = st.text_input("이름")
        new_pw = st.text_input("비밀번호", type="password")
        
        if st.button("가입하기"):
            if not new_id or not new_name or not new_pw: 
                st.error("모든 칸을 입력해주세요.")
            elif new_id in users or new_id == "admin": 
                st.error("이미 존재하는 학번이거나 사용할 수 없는 ID입니다.")
            else:
                users[new_id] = {"password": new_pw, "name": new_name, "role": "user"}
                save_data(USER_FILE, users)
                st.success("회원가입이 완료되었습니다! 로그인해주세요.")

    elif choice == "로그인":
        st.subheader("🔑 로그인")
        user_id = st.text_input("학번 / 아이디")
        user_pw = st.text_input("비밀번호", type="password")

        if st.button("로그인"):
            # 새로 빌드한 직관적인 등급 부여 로직
            if user_id in users and users[user_id]["password"] == user_pw:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.user_name = users[user_id]["name"]
                
                # ID 조건에 따라 확실하게 룰 배정
                if user_id == "admin":
                    st.session_state.role = "master_admin"
                elif users[user_id].get("role") == "sub_admin":
                    st.session_state.role = "sub_admin"
                else:
                    st.session_state.role = "user"
                    
                st.success(f"{st.session_state.user_name}님 로그인 성공!")
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

# --- 2. 로그인 완료 상태일 때 ---
else:
    # 왼쪽 사이드바 프로필 표시 영역
    st.sidebar.markdown(f"### 👤 {st.session_state.user_name}님")
    
    if st.session_state.role == "master_admin":
        st.sidebar.markdown("👑 **등급:** `최고 관리자 (마스터)`")
    elif st.session_state.role == "sub_admin":
        st.sidebar.markdown("🛡️ **등급:** `일반 부관리자`")
    else:
        st.sidebar.markdown("🎓 **등급:** `일반 학생 사용자`")
        
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.role = "user"
        st.rerun()

    # ==================== [[ 새로 만든 관리자 전용 사이드바 창 ]] ====================
    if st.session_state.role in ["master_admin", "sub_admin"]:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🛠️ 관리자 전용 메뉴")
        
        # 관리자 기능 목록 정의
        admin_menu = ["📢 공지 및 투표 관리", "🏛️ 커뮤니티 게시글 관리", "💬 학생 질문 로그", "🔥 최다 질문 통계"]
        
        # 최고 마스터 관리자에게만 추가 권한 메뉴 제공
        if st.session_state.role == "master_admin":
            admin_menu.append("➕ 부관리자 계정 생성")
            
        sub_choice = st.sidebar.radio("제어할 기능을 선택하세요", admin_menu)

        st.subheader(f"⚙️ 관리 제어판 -> {sub_choice}")

        if sub_choice == "📢 공지 및 투표 관리":
            st.write("#### 1. 대시보드 공지사항 변경")
            new_notice = st.text_area("수정할 공지사항 내용", value=community["notice"])
            if st.button("공지사항 수정 완료"):
                community["notice"] = new_notice
                save_data(COMMUNITY_FILE, community)
                st.success("공지사항이 업데이트되었습니다.")

            st.write("---")
            st.write("#### 2. 실시간 학생 투표 개설")
            poll_title = st.text_input("투표 안건 주제 입력")
            poll_opt1 = st.text_input("선택지 보기 1")
            poll_opt2 = st.text_input("선택지 보기 2")
            if st.button("투표 공식 발의"):
                if poll_title and poll_opt1 and poll_opt2:
                    community["polls"].append({
                        "id": len(community["polls"]),
                        "title": poll_title,
                        "options": [poll_opt1, poll_opt2],
                        "votes": {poll_opt1: 0, poll_opt2: 0},
                        "voted_users": []
                    })
                    save_data(COMMUNITY_FILE, community)
                    st.success("새로운 학생 투표가 등록되었습니다.")

        elif sub_choice == "🏛️ 커뮤니티 게시글 관리":
            st.write("#### 🚨 학생 커뮤니티 전체 게시물 관리")
            if not community["posts"]:
                st.info("현재 대나무숲에 등록된 글이 없습니다.")
            else:
                for idx, post in enumerate(community["posts"]):
                    st.write(f"**[{post['author']}]** {post['content']} (❤️ {len(post['likes'])})")
                    if st.button(f"불건전한 게시글 삭제", key=f"del_p_{idx}"):
                        community["posts"].pop(idx)
                        save_data(COMMUNITY_FILE, community)
                        st.success("해당 게시물이 안전하게 삭제되었습니다.")
                        st.rerun()

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
                            st.markdown("---")

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

        elif sub_choice == "➕ 부관리자 계정 생성":
            st.write("#### 🛡️ 신규 부관리자(Sub Admin) 계정 발급")
            st.caption("여기서 생성되는 관리자는 생성 권한을 제외한 모든 투표/게시글 관리/로그 보기 기능 권한을 공유합니다.")
            
            sub_id = st.text_input("부관리자용 로그인 ID")
            sub_name = st.text_input("부관리자 담당자 이름")
            sub_pw = st.text_input("부관리자용 비밀번호", type="password")
            
            if st.button("부관리자 계정 등록"):
                if not sub_id or not sub_name or not sub_pw:
                    st.error("빈칸 없이 모두 입력해 주세요.")
                elif sub_id in users or sub_id == "admin":
                    st.error("이미 사용 중인 중복 ID입니다.")
                else:
                    users[sub_id] = {
                        "password": sub_pw,
                        "name": sub_name,
                        "role": "sub_admin"
                    }
                    save_data(USER_FILE, users)
                    st.success(f"🎉 {sub_name} 부관리자 계정이 성공적으로 활성화되었습니다!")

    # ==================== [[ 학생 / 사용자 전용 일반 메인 화면 ]] ====================
    else:
        st.info(f"📢 **학교 공지사항:** {community['notice']}")
        
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
                                    post["comments"].append({
                                        "author": st.session_state.user_name,
                                        "text": comment_text
                                    })
                                    save_data(COMMUNITY_FILE, community)
                                    st.rerun()
                    st.markdown("---")

        # ---- 탭 3: 실시간 투표 기능 ----
        with tab3:
            st.write("### 📊 실시간 학생 투표광장")
            if not community["polls"]:
                st.info("현재 진행 중인 학생 투표가 없습니다. 관리자의 새로운 투표를 기다려주세요!")
            else:
                for p_idx, poll in enumerate(community["polls"]):
                    st.write(f"#### ❓ 주제: {poll['title']}")
                    
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
                    st.markdown("---")