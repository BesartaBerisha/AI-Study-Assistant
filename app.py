from dotenv import load_dotenv
load_dotenv()

import streamlit as st

from agents.concierge_agent import chat
from utils.file_parser import parse_file

st.set_page_config(page_title="AI Study Assistant", page_icon="📚", layout="wide")

# ── Session State ────────────────────────────────────────────────────────────
_DEFAULTS = {
    "document_text": None,
    "document_name": None,
    "chat_display": [],        # [{role, content}] shown in chat UI
    "concierge_history": [],   # simple text-only history for the API
    "summary": None,
    "flashcards": [],
    "quiz": [],
    "exam_questions": [],
    "quiz_answers": {},
    "quiz_submitted": False,
    "card_index": 0,
    "card_flipped": False,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


def _reset_generated():
    st.session_state.summary = None
    st.session_state.flashcards = []
    st.session_state.quiz = []
    st.session_state.exam_questions = []
    st.session_state.quiz_answers = {}
    st.session_state.quiz_submitted = False
    st.session_state.card_index = 0
    st.session_state.card_flipped = False


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📚 AI Study Assistant")
    st.caption("Upload a document and let AI help you study.")
    st.divider()

    uploaded = st.file_uploader(
        "Upload Study Material",
        type=["pdf", "pptx", "ppt", "docx", "doc", "txt", "md"],
        help="Supports PDF, PowerPoint, Word, and plain text",
    )

    if uploaded and st.session_state.document_name != uploaded.name:
        with st.spinner(f"Reading {uploaded.name}…"):
            try:
                text = parse_file(uploaded.getvalue(), uploaded.name)
                st.session_state.document_text = text
                st.session_state.document_name = uploaded.name
                st.session_state.concierge_history = []
                st.session_state.chat_display = []
                _reset_generated()
                st.success(f"Loaded: **{uploaded.name}**")
                st.caption(f"{len(text):,} characters extracted")
            except Exception as exc:
                st.error(f"Could not parse file: {exc}")

    if st.session_state.document_name:
        st.divider()
        st.markdown(f"**File:** {st.session_state.document_name}")
        st.markdown("**Quick Generate:**")

        c1, c2 = st.columns(2)

        with c1:
            if st.button("📝 Summary", use_container_width=True):
                from agents.document_agent import summarize

                with st.spinner("Summarizing…"):
                    try:
                        st.session_state.summary = summarize(st.session_state.document_text)
                        st.success("Done!")
                    except Exception as exc:
                        st.error(str(exc))

            if st.button("🃏 Flashcards", use_container_width=True):
                from agents.flashcard_agent import create_flashcards

                with st.spinner("Creating flashcards…"):
                    try:
                        st.session_state.flashcards = create_flashcards(
                            st.session_state.document_text
                        )
                        st.session_state.card_index = 0
                        st.session_state.card_flipped = False
                        st.success("Done!")
                    except Exception as exc:
                        st.error(str(exc))

        with c2:
            if st.button("📋 Quiz", use_container_width=True):
                from agents.quiz_agent import generate_quiz

                with st.spinner("Generating quiz…"):
                    try:
                        st.session_state.quiz = generate_quiz(st.session_state.document_text)
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_submitted = False
                        st.success("Done!")
                    except Exception as exc:
                        st.error(str(exc))

            if st.button("🎓 Exam", use_container_width=True):
                from agents.exam_agent import create_exam_questions

                with st.spinner("Creating exam questions…"):
                    try:
                        st.session_state.exam_questions = create_exam_questions(
                            st.session_state.document_text
                        )
                        st.success("Done!")
                    except Exception as exc:
                        st.error(str(exc))


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_chat, tab_summary, tab_flash, tab_quiz, tab_exam = st.tabs(
    ["💬 Chat", "📝 Summary", "🃏 Flashcards", "📋 Quiz", "🎓 Exam Questions"]
)


# ════════════════════════════════════════════════════════════════════════════════
# CHAT
# ════════════════════════════════════════════════════════════════════════════════
with tab_chat:
    st.header("Chat with Your Study Buddy")

    if not st.session_state.document_text:
        st.info("Upload a document from the sidebar to get started.")

    for msg in st.session_state.chat_display:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask anything about your document…"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.chat_display.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    reply, results = chat(
                        user_message=prompt,
                        document_text=st.session_state.document_text,
                        messages_history=st.session_state.concierge_history.copy(),
                    )

                    # Store tool outputs in session state
                    if results.get("summary"):
                        st.session_state.summary = results["summary"]
                    if results.get("quiz"):
                        st.session_state.quiz = results["quiz"]
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_submitted = False
                    if results.get("flashcards"):
                        st.session_state.flashcards = results["flashcards"]
                        st.session_state.card_index = 0
                        st.session_state.card_flipped = False
                    if results.get("exam_questions"):
                        st.session_state.exam_questions = results["exam_questions"]

                    # Append tab hints to reply
                    tab_hints = []
                    if "summary" in results:
                        tab_hints.append("📝 Summary")
                    if "quiz" in results:
                        tab_hints.append("📋 Quiz")
                    if "flashcards" in results:
                        tab_hints.append("🃏 Flashcards")
                    if "exam_questions" in results:
                        tab_hints.append("🎓 Exam Questions")
                    if tab_hints:
                        reply += f"\n\n*Check the {', '.join(tab_hints)} tab(s) above.*"

                    st.markdown(reply)
                    st.session_state.chat_display.append({"role": "assistant", "content": reply})
                    st.session_state.concierge_history.append({"role": "user", "content": prompt})
                    st.session_state.concierge_history.append(
                        {"role": "assistant", "content": reply}
                    )

                except Exception as exc:
                    err = f"Sorry, something went wrong: {exc}"
                    st.error(err)
                    st.session_state.chat_display.append({"role": "assistant", "content": err})


# ════════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════════════════════
with tab_summary:
    st.header("Document Summary")

    if st.session_state.summary:
        st.markdown(st.session_state.summary)

    elif st.session_state.document_text:
        st.info("No summary yet — click **📝 Summary** in the sidebar or ask the chat.")
        if st.button("Generate Summary", key="btn_summary"):
            from agents.document_agent import summarize

            with st.spinner("Summarizing…"):
                try:
                    st.session_state.summary = summarize(st.session_state.document_text)
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
    else:
        st.info("Upload a document to generate a summary.")


# ════════════════════════════════════════════════════════════════════════════════
# FLASHCARDS
# ════════════════════════════════════════════════════════════════════════════════
with tab_flash:
    st.header("Flashcards")

    if st.session_state.flashcards:
        cards = st.session_state.flashcards
        idx = st.session_state.card_index
        total = len(cards)

        # Navigation row
        nav1, nav2, nav3 = st.columns([1, 4, 1])
        with nav1:
            if st.button("◀", key="prev_card", disabled=(idx == 0)):
                st.session_state.card_index -= 1
                st.session_state.card_flipped = False
                st.rerun()
        with nav2:
            st.markdown(
                f"<p style='text-align:center;font-weight:bold'>Card {idx+1} / {total}</p>",
                unsafe_allow_html=True,
            )
        with nav3:
            if st.button("▶", key="next_card", disabled=(idx == total - 1)):
                st.session_state.card_index += 1
                st.session_state.card_flipped = False
                st.rerun()

        st.progress((idx + 1) / total)

        card = cards[idx]
        flipped = st.session_state.card_flipped

        if not flipped:
            bg = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
            label = "TERM"
            content = card.get("front", "")
        else:
            bg = "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"
            label = "DEFINITION"
            content = card.get("back", "")

        st.markdown(
            f"""<div style="
                background:{bg};border-radius:16px;padding:40px 32px;
                min-height:180px;display:flex;flex-direction:column;
                align-items:center;justify-content:center;text-align:center;
                color:white;box-shadow:0 8px 24px rgba(0,0,0,0.15);margin:12px 0;">
                <small style="opacity:.8;letter-spacing:.08em">{label}</small>
                <p style="font-size:1.25em;margin-top:12px;font-weight:500">{content}</p>
            </div>""",
            unsafe_allow_html=True,
        )

        flip_col, _ = st.columns([1, 3])
        with flip_col:
            flip_label = "Show Definition" if not flipped else "Show Term"
            if st.button(f"🔄 {flip_label}", use_container_width=True):
                st.session_state.card_flipped = not st.session_state.card_flipped
                st.rerun()

        with st.expander("View all flashcards"):
            for i, c in enumerate(cards):
                st.markdown(f"**{i+1}. {c.get('front','')}**")
                st.markdown(f"&nbsp;&nbsp;&nbsp;{c.get('back','')}")
                if i < len(cards) - 1:
                    st.divider()

    elif st.session_state.document_text:
        st.info("No flashcards yet — click **🃏 Flashcards** in the sidebar or ask the chat.")
        if st.button("Create Flashcards", key="btn_flash"):
            from agents.flashcard_agent import create_flashcards

            with st.spinner("Creating flashcards…"):
                try:
                    st.session_state.flashcards = create_flashcards(
                        st.session_state.document_text
                    )
                    st.session_state.card_index = 0
                    st.session_state.card_flipped = False
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
    else:
        st.info("Upload a document to create flashcards.")


# ════════════════════════════════════════════════════════════════════════════════
# QUIZ
# ════════════════════════════════════════════════════════════════════════════════
with tab_quiz:
    st.header("Quiz")

    if st.session_state.quiz:
        quiz = st.session_state.quiz

        if not st.session_state.quiz_submitted:
            with st.form("quiz_form"):
                for i, q in enumerate(quiz):
                    st.markdown(f"**Q{i+1}. {q.get('question','')}**")
                    options = q.get("options", [])
                    labels = [f"{chr(65+j)}. {opt}" for j, opt in enumerate(options)]
                    choice = st.radio(
                        f"q{i}",
                        options=list(range(len(options))),
                        format_func=lambda x, lb=labels: lb[x],
                        key=f"qr_{i}",
                        label_visibility="collapsed",
                    )
                    st.session_state.quiz_answers[i] = choice
                    st.divider()

                if st.form_submit_button("Submit Quiz", use_container_width=True):
                    st.session_state.quiz_submitted = True
                    st.rerun()

        else:
            correct_count = 0
            for i, q in enumerate(quiz):
                user_ans = st.session_state.quiz_answers.get(i, -1)
                correct_ans = q.get("correct", 0)
                options = q.get("options", [])
                is_correct = user_ans == correct_ans
                if is_correct:
                    correct_count += 1

                icon = "✅" if is_correct else "❌"
                st.markdown(f"{icon} **Q{i+1}. {q.get('question','')}**")
                for j, opt in enumerate(options):
                    label = f"{chr(65+j)}. {opt}"
                    if j == correct_ans and j == user_ans:
                        st.markdown(f"&nbsp;&nbsp;✅ **{label}** ← Your answer (Correct!)")
                    elif j == correct_ans:
                        st.markdown(f"&nbsp;&nbsp;✅ **{label}** ← Correct answer")
                    elif j == user_ans:
                        st.markdown(f"&nbsp;&nbsp;❌ {label} ← Your answer")
                    else:
                        st.markdown(f"&nbsp;&nbsp;○ {label}")
                if q.get("explanation"):
                    st.info(f"**Explanation:** {q['explanation']}")
                st.divider()

            score_pct = int(correct_count / len(quiz) * 100)
            if score_pct == 100:
                st.balloons()
                st.success(f"**{correct_count}/{len(quiz)} ({score_pct}%) — Perfect score!**")
            elif score_pct >= 80:
                st.success(f"**{correct_count}/{len(quiz)} ({score_pct}%) — Great job!**")
            elif score_pct >= 60:
                st.warning(f"**{correct_count}/{len(quiz)} ({score_pct}%) — Good effort, review the wrong answers.**")
            else:
                st.error(f"**{correct_count}/{len(quiz)} ({score_pct}%) — Keep studying and try again!**")

            if st.button("Retake Quiz", use_container_width=True):
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
                st.rerun()

    elif st.session_state.document_text:
        st.info("No quiz yet — click **📋 Quiz** in the sidebar or ask the chat.")
        c1, c2 = st.columns(2)
        with c1:
            num_q = st.number_input("Questions", min_value=3, max_value=20, value=5)
        with c2:
            diff = st.selectbox("Difficulty", ["easy", "medium", "hard"], index=1)
        if st.button("Generate Quiz", key="btn_quiz"):
            from agents.quiz_agent import generate_quiz

            with st.spinner("Generating quiz…"):
                try:
                    st.session_state.quiz = generate_quiz(
                        st.session_state.document_text,
                        num_questions=num_q,
                        difficulty=diff,
                    )
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_submitted = False
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
    else:
        st.info("Upload a document to generate a quiz.")


# ════════════════════════════════════════════════════════════════════════════════
# EXAM QUESTIONS
# ════════════════════════════════════════════════════════════════════════════════
with tab_exam:
    st.header("Exam Questions")

    if st.session_state.exam_questions:
        questions = st.session_state.exam_questions
        type_labels = {"essay": "📝 Essay", "short_answer": "✏️ Short Answer", "problem": "🔢 Problem"}

        for i, q in enumerate(questions):
            q_type = q.get("type", "essay")
            badge = type_labels.get(q_type, "📝 Essay")
            preview = q.get("question", "")[:60]
            with st.expander(f"Q{i+1}. [{badge}] {preview}…", expanded=(i == 0)):
                st.markdown(f"**{q.get('question','')}**")

                hints = q.get("hints", [])
                if hints:
                    st.markdown("**Hints:**")
                    for h in hints:
                        st.markdown(f"- {h}")

                st.text_area(
                    "Your answer:",
                    placeholder="Write your answer here…",
                    key=f"exam_input_{i}",
                    height=120,
                )

                if st.button("Show model answer", key=f"show_model_{i}"):
                    st.success(q.get("model_answer", "No model answer available."))

        # Download
        st.divider()
        exam_text = ""
        for i, q in enumerate(questions):
            exam_text += (
                f"Question {i+1} [{q.get('type','').upper()}]\n"
                f"{q.get('question','')}\n\n"
            )
            if q.get("hints"):
                exam_text += "Hints:\n" + "\n".join(f"- {h}" for h in q["hints"]) + "\n\n"
            exam_text += f"Model Answer:\n{q.get('model_answer','')}\n\n{'='*60}\n\n"

        st.download_button(
            "📥 Download Exam Questions",
            data=exam_text,
            file_name="exam_questions.txt",
            mime="text/plain",
        )

    elif st.session_state.document_text:
        st.info("No exam questions yet — click **🎓 Exam** in the sidebar or ask the chat.")
        num_eq = st.number_input("Number of questions", min_value=3, max_value=15, value=5)
        if st.button("Generate Exam Questions", key="btn_exam"):
            from agents.exam_agent import create_exam_questions

            with st.spinner("Creating exam questions…"):
                try:
                    st.session_state.exam_questions = create_exam_questions(
                        st.session_state.document_text, num_questions=num_eq
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
    else:
        st.info("Upload a document to generate exam questions.")
