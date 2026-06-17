import streamlit as st
import json
import os
from datetime import datetime

# 데이터 저장용 파일 설정
USER_FILE = "users.json"
CHAT_FILE = "chats.json"

# 파일 초기화 함수
def load_data(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 데이터 불러오기
users = load_data(USER_FILE)
chats = load_data(CHAT_FILE)

# 초기 관리자 계정 생성 (계정 없을 때만)
if "admin" not in users:
    users["admin"] = {"password": "admin1234", "name": "최고관리자", "role": "admin"}
    save_data(USER_FILE, users)

# 스트림릿 세션 상태(로그인 유지용) 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.role = "user"

# --- 화면 구현 ---
st.title("🏫 신입생 학교생활 가이드 & 커뮤니티")

# 로그아웃 상태일 때: 로그인 / 회원가입 창
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
            elif new_id in users:
                st.error("이미 가입된 학번입니다.")
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

# 로그인 상태일 때
else:
    # 사이드바 프로필 및 로그아웃
    st.sidebar.markdown(f"### 👤 {st.session_state.user_name}님 로그인 중")
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.role = "user"
        st.rerun()

    # --- [관리자 화면] ---
    if st.session_state.role == "admin":
        st.subheader("⚙️ 관리자 마스터 패널")
        admin_menu = ["학생 대화 로그 확인", "공지사항/커뮤니티 관리(준비중)"]
        sub_choice = st.selectbox("관리 기능 선택", admin_menu)

        if sub_choice == "학생 대화 로그 확인":
            st.write("### 💬 학생들의 질문 기록")
            all_chats = load_data(CHAT_FILE)
            if not all_chats:
                st.info("아직 누적된 대화 기록이 없습니다.")
            else:
                for uid, history in all_chats.items():
                    student_name = users.get(uid, {}).get("name", "알 수 없는 사용자")
                    with st.expander(f"학번: {uid} ({student_name})의 대화 기록"):
                        for chat in history:
                            st.write(f"**[{chat['time']}]** 질문: {chat['query']}")
                            st.write(f"🤖 답변: {chat['answer']}")
                            st.markdown("---")

    # --- [일반 사용자 화면] ---
    else:
        st.subheader(f"👋 반갑습니다, {st.session_state.user_name}님!")
        
        # 탭 나누기 (챗봇 / 커뮤니티 / 문의하기)
        tab1, tab2, tab3 = st.tabs(["🤖 규정 질문 챗봇", "🏛️ 학생 커뮤니티", "📩 1:1 문의하기"])

        with tab1:
            st.write("### 학교 규정에 대해 물어보세요!")
            
            # (인기 질문 샘플 표시 예시 - 추후 데이터 누적되어 자동 계산되게 고도화 가능)
            st.info("🔥 **인기 질문 TOP 3**\n1. 두발 규정이 어떻게 되나요?\n2. 전자기기 사용 시간은 언제인가요?\n3. 지각하면 어떤 처벌을 받나요?")
            
            user_query = st.text_input("질문을 입력하세요:", key="chatbot_query")
            
            if st.button("질문하기"):
                if user_query:
                    # 간단한 답변 로직 예시 (기존 PDF 검색 로직을 여기에 연결하면 됩니다)
                    answer = f"'{user_query}'에 대한 규정 답변 예시입니다. (실제 PDF 검색 연동 구역)"
                    st.write(f"🤖 **답변:** {answer}")

                    # 대화 로그 저장
                    if st.session_state.user_id not in chats:
                        chats[st.session_state.user_id] = []
                    
                    chats[st.session_state.user_id].append({
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "query": user_query,
                        "answer": answer
                    })
                    save_data(CHAT_FILE, chats)

        with tab2:
            st.write("### 🏛️ 학생 자치 커뮤니티")
            st.warning("투표, 댓글, 좋아요 기능은 2단계 업데이트에서 추가될 예정입니다!")

        with tab3:
            st.write("### 📩 건의 및 문의하기")
            st.text_area("학교나 학생회에 바라는 점을 적어주세요.")
            if st.button("제출하기"):
                st.success("건의사항이 성공적으로 접수되었습니다.")