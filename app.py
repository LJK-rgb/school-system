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
                highlighted_text = re.sub(f"({re.escape(kw)})", r"<mark style='background-color: #FFFFA0; color: #000000; font-weight: bold;'>\1</mark>", highlighted_text)
            
            results.append(highlighted_text.strip())
            if len(results) >= 3:
                break
                
    if results:
        output = "🔍 **규정집 내부 매칭된 조항 검색 결과:**\n\n"
        for res in results:
            # 화이트/다크 모드 양쪽 다 글자가 명확히 보이도록 배경색(연한 회색)과 글자색(진한 네이비/블랙)을 고정
            output += f"<div style='background-color: #F0F2F6; color: #131722; padding: 15px; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid #FF4B4B; white-space: pre-wrap; font-size: 15px;'>{res}</div>"
        return output
    else:
        return "🔍 규정집에서 관련 조항을 찾지 못했습니다. 보다 정확한 단어(예: 두발, 전자기기, 복장, 휴대전화 등)로 다시 질문해 주세요."

# 데이터 로드
users = load_data(USER_FILE)
chats = load_data(CHAT_FILE)
community = load_data(COMMUNITY_FILE)
pdf_content = load_pdf_text(PDF_FILE)

# 초기 커뮤니티 데이터 구조 설정
if "posts" not in community: community["posts"] = []
if "polls" not in community: community["polls"] = []
if "notice" not in community: community["notice"] = "아직 등록된 공지사항이 없습니다."

# 초기 최고(마스터) 관리자 계정 생성
if "admin" not in users:
    users["admin"] = {"password": "admin1234", "name": "최고관리자", "role": "master_admin"}
    save_data(USER_FILE, users)

# 스트림릿 세션 로그인 상태 유지
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.role = "user"

# --- 메인 화면 타이틀 ---
st.title("🏫 신입생 학교생활 가이드 & 커뮤니티")

# --- 로그아웃 상태일 때 ---
if not st.session_state.logged_in:
    menu = ["로그인", "회원가입"]
    choice = st.sidebar.selectbox("메뉴", menu)

    if choice == "회원가입":
        st.subheader("📝 회원가입")
        new_id = st.text_input("학번 (아이디로 사용)", placeholder="예: 10101")
        new_name = st.text_input("이름")
        new_pw = st.text_input("비밀번호", type="password")
        
        if st.button("가입하기"):
            if not new_id or not new_name or not new_pw: st.error("모든 칸을 입력해주세요.")
            elif new_id in users: st.error("이미 가입된 학번입니다.")
            else:
                users[new_id] = {"password": new_pw, "name": new_name, "role": "user"}
                save_data(USER_FILE, users)
                st.success("회원가입이 완료되었습니다! 로그인해주세요.")

    elif choice == "로그인":
        st.subheader("🔑 로그인")
        user_id = st.text_input("학번")
        user_pw = st.text_input("비밀번호", type="password") # 변수 오타 버그 수정 완료!

        if st.button("로그인"):
            if user_id in users and users[user_id]["password"] == user_pw:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.user_name = users[user_id]["name"]
                st.session_state.role = users[user_id]["role"]
                st.success(f"{st.session_state.user_name}님, 환영합니다!")
                st.rerun()
            else:
                st.error("학번 또는 비밀번호가 틀렸습니다.")

# --- 로그인 상태일 때 ---
else:
    st.sidebar.markdown(f"### 👤 {st.session_state.user_name}님")
    
    if st.session_state.role == "master_admin":
        st.sidebar.caption("👑 최고 관리자 (마스터)")
    elif st.session_state.role == "sub_admin":
        st.sidebar.caption("🛡️ 일반 부관리자")
        
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.role = "user"
        st.rerun()

    # ==================== [ ⚙️ 관리자 사이드바 전용 패널 ] ====================
    if st.session_state.role in ["master_admin", "sub_admin"]:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ⚙️ 마스터 관리 메뉴")
        
        admin_menu = ["📢 공지 및 투표 관리", "🏛️ 커뮤니티 게시글 관리", "💬 학생 질문 로그", "🔥 최다 질문 통계"]
        
        if st.session_state.role == "master_admin":
            admin_menu.append("➕ 부관리자 계정 생성")
            
        sub_choice = st.sidebar.radio("원하는 관리 기능 선택", admin_menu)

        st.subheader(f"🛠️ 관리자 모드 - {sub_choice}")

        if sub_choice == "📢 공지 및 투표 관리":
            st.write("#### 1. 새로운 학교 공지사항 작성")
            new_notice = st.text_area("공지 내용 입력", value=community["notice"])
            if st.button("공지사항 업데이트"):
                community["notice"] = new_notice
                save_data(COMMUNITY_FILE, community)
                st.success("공지가 성공적으로 변경되었습니다!")

            st.write("---")
            st.write("#### 2. 새로운 학생 투표 만들기")
            poll_title = st.text_input("투표 주제", placeholder="예: 축제 연예인 누가 오면 좋을까요?")
            poll_opt1 = st.text_input("보기 1", placeholder="아이돌")
            poll_opt2 = st.text_input("보기 2", placeholder="힙합가수")
            if st.button("투표 올리기"):
                if poll_title and poll_opt1 and poll_opt2:
                    community["polls"].append({
                        "id": len(community["polls"]),
                        "title": poll_title,
                        "options": [poll_opt1, poll_opt2],
                        "votes": {poll_opt1: 0, poll_opt2: 0},
                        "voted_users": []
                    })
                    save_data(COMMUNITY_FILE, community)
                    st.success("새로운 투표가 발의되었습니다!")

        elif sub_choice == "🏛️ 커뮤니티 게시글 관리":
            st.write("### 🗑️ 전체 게시글 일람 및 삭제 권한")
            if not community["posts"]:
                st.info("현재 커뮤니티에 올라온 글이 없습니다.")
            else:
                for idx, post in enumerate(community["posts"]):
                    st.write(f"**[{post['author']}]** {post['content']} (❤️ {len(post['likes'])})")
                    if st.button(f"위 게시글 삭제하기", key=f"del_{idx}"):
                        community["posts"].pop(idx)
                        save_data(COMMUNITY_FILE, community)
                        st.success("게시글이 삭제되었습니다.")
                        st.rerun()

        elif sub_choice == "💬 학생 질문 로그":
            st.write("### 💬 학생별 전체 질문 기록 체크")
            if not chats:
                st.info("아직 학생들이 한 질문이 없습니다.")
            else:
                for uid, history in chats.items():
                    student_name = users.get(uid, {}).get("name", "알 수 없는 사용자")
                    with st.expander(f"학번: {uid} ({student_name})의 대화 기록"):
                        for chat in history:
                            st.write(f"**[{chat['time']}]** 질문: {chat['query']}")
                            st.write(f"🤖 답변 요약됨")
                            st.markdown("---")

        elif sub_choice == "🔥 최다 질문 통계":
            st.write("### 🔥 학생들이 가장 많이 검색한 키워")
            all_queries = []
            for uid, history in chats.items():
                for chat in history: 
                    all_queries.extend(chat['query'].split())
            
            filtered_words = [word for word in all_queries if len(word) > 1]
            
            if not filtered_words:
                st.info("통계를 내기 위한 질문 데이터가 부족합니다.")
            else:
                word_counts = {}
                for w in filtered_words:
                    word_counts[w] = word_counts.get(w, 0) + 1
                
                sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                
                st.metric("📊 총 누적 검색 단어 수", len(filtered_words))
                st.write("#### 🔝 실시간 학생 관심 키워드 Top 5")
                for rank, (word, count) in enumerate(sorted_words, 1):
                    st.write(f"**{rank}위** : `{word}` ({count}회 검색됨)")

        elif sub_choice == "➕ 부관리자 계정 생성":
            st.write("### 🛡️ 일반 부관리자 계정 발급 전용")
            
            sub_admin_id = st.text_input("부관리자 ID (로그인용 아이디)")
            sub_admin_name = st.text_input("부관리자 이름 (표시용)")
            sub_admin_pw = st.text_input("부관리자 비밀번호", type="password")
            
            if st.button("부관리자 생성하기"):
                if not sub_admin_id or not sub_admin_name or not sub_admin_pw:
                    st.error("모든 정보를 입력해 주세요.")
                elif sub_admin_id in users:
                    st.error("이미 사용 중인 아이디입니다.")
                else:
                    users[sub_admin_id] = {
                        "password": sub_admin_pw,
                        "name": sub_admin_name,
                        "role": "sub_admin"
                    }
                    save_data(USER_FILE, users)
                    st.success(f"🎉 {sub_admin_name} 부관리자 계정이 성공적으로 생성되었습니다!")

    # ==================== [ 🧑‍🎓 학생 / 사용자 메인 화면 ] ====================
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