import streamlit as st
import json
import os
from datetime import datetime
import pypdf  # PDF 텍스트 추출용 라이브러리 추가

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

# --- PDF 텍스트 추출 및 심플 검색 함수 ---
@st.cache_resource
def load_pdf_text(filepath):
    if not os.path.exists(filepath):
        return ""
    text = ""
    reader = pypdf.PdfReader(filepath)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def search_pdf(query, pdf_text):
    if not pdf_text:
        return "⚠️ 현재 서버에 학교 규정집 PDF 파일이 없거나 읽을 수 없습니다."
    
    # 입력한 키워드가 포함된 문단을 찾는 아주 심플한 검색 엔진 규칙
    keywords = query.split()
    lines = pdf_text.split("\n")
    results = []
    
    for line in lines:
        if any(kw in line for kw in keywords if len(kw) > 1):
            results.append(line.strip())
            if len(results) >= 5:  # 너무 길어지지 않게 최대 5줄만 추출
                break
                
    if results:
        return "📄 **학교 규정집 관련 내용 검색 결과:**\n\n" + "\n".join([f"- {r}" for r in results])
    else:
        return "🔍 규정집에서 관련 키워드를 찾지 못했습니다. 보다 정확한 단어(예: 두발, 전자기기, 복장 등)로 다시 질문해 주세요."

# 데이터 로드
users = load_data(USER_FILE)
chats = load_data(CHAT_FILE)
community = load_data(COMMUNITY_FILE)
pdf_content = load_pdf_text(PDF_FILE)

# 초기 커뮤니티 데이터 구조 설정
if "posts" not in community: community["posts"] = []
if "polls" not in community: community["polls"] = []
if "notice" not in community: community["notice"] = "아직 등록된 공지사항이 없습니다."

# 초기 관리자 계정 생성
if "admin" not in users:
    users["admin"] = {"password": "admin1234", "name": "최고관리자", "role": "admin"}
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
        user_pw = st.text_input("비밀번호", type="password")

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
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.role = "user"
        st.rerun()

    # ==================== [ 관리자 마스터 패널 ] ====================
    if st.session_state.role == "admin":
        st.subheader("⚙️ 관리자 마스터 패널")
        admin_menu = ["📢 공지 및 투표 등록", "💬 학생 대화 로그 확인", "🚨 커뮤니티 악성 게시글 관리"]
        sub_choice = st.selectbox("관리 기능 선택", admin_menu)

        if sub_choice == "📢 공지 및 투표 등록":
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

        elif sub_choice == "💬 학생 대화 로그 확인":
            st.write("### 💬 학생들의 질문 기록 및 통계")
            
            # 간단한 인기 질문 통계 내기
            all_queries = []
            for uid, history in chats.items():
                for c in history: all_queries.append(c['query'])
            
            st.metric("🔥 총 누적 질문 개수", len(all_queries))

            for uid, history in chats.items():
                student_name = users.get(uid, {}).get("name", "알 수 없는 사용자")
                with st.expander(f"학번: {uid} ({student_name})의 대화 기록"):
                    for chat in history:
                        st.write(f"**[{chat['time']}]** 질문: {chat['query']}")
                        st.write(f"🤖 답변: {chat['answer']}")
                        st.markdown("---")

        elif sub_choice == "🚨 커뮤니티 악성 게시글 관리":
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

    # ==================== [ 학생 / 사용자 메인 화면 ] ====================
    else:
        # 상단 공지사항 상시 띄우기
        st.notice(f"📢 **학교 공지사항:** {community['notice']}")
        
        tab1, tab2, tab3 = st.tabs(["🤖 규정 질문 챗봇", "🏛️ 학생 소통 커뮤니티", "📊 실시간 투표존"])

        # ---- 탭 1: 규정 질문 챗봇 ----
        with tab1:
            st.write("### 🤖 학교 규정에 대해 물어보세요!")
            st.info("🔥 **학생들이 가장 많이 찾은 단어** : `두발`, `휴대폰`, `지각`, `복장`")
            
            user_query = st.text_input("질문을 입력하세요 (예: 두발 규정 알려줘):", key="chatbot_query")
            
            if st.button("질문하기"):
                if user_query:
                    # PDF 기반 실시간 키워드 검색 답변 작동!
                    answer = search_pdf(user_query, pdf_content)
                    st.write(answer)

                    # 대화 로그 저장
                    if st.session_state.user_id not in chats:
                        chats[st.session_state.user_id] = []
                    
                    chats[st.session_state.user_id].append({
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "query": user_query,
                        "answer": answer
                    })
                    save_data(CHAT_FILE, chats)

        # ---- 탭 2: 커뮤니티 (글쓰기, 하트, 댓글) ----
        with tab2:
            st.write("### 🏛️ 익명/실명 학생 대나무숲")
            
            # 새 글 쓰기 구역
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

            # 글 목록 피드 띄우기
            st.write("---")
            if not community["posts"]:
                st.info("가장 먼저 첫 게시글의 주인공이 되어보세요!")
            else:
                for idx, post in enumerate(community["posts"]):
                    st.markdown(f"👤 **{post['author']}**")
                    st.info(post["content"])
                    
                    # 좋아요(하트) 기능
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        like_label = f"❤️ {len(post['likes'])}"
                        if st.button(like_label, key=f"like_{idx}"):
                            if st.session_state.user_id in post["likes"]:
                                post["likes"].remove(st.session_state.user_id) # 이미 눌렀으면 취소
                            else:
                                post["likes"].append(st.session_state.user_id)
                            save_data(COMMUNITY_FILE, community)
                            st.rerun()
                            
                    # 댓글 달기 및 보기
                    with st.expander(f"💬 댓글 ({len(post['comments'])}개) 열기"):
                        for comment in post["comments"]:
                            st.write(f"↳ **{comment['author']}**: {comment['text']}")
                        
                        # 새 댓글 입력
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