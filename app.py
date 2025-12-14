import streamlit as st
import random
import re
import unicodedata
from datetime import datetime

# ----------------------------
# Helpers
# ----------------------------
def normalize(s: str) -> str:
    """Normalize strings for forgiving comparison (case, punctuation, spacing)."""
    s = s.strip().lower()
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[¿¡]", "", s)              # remove Spanish inverted punctuation
    s = re.sub(r"[^\w\sáéíóúüñ]", "", s)    # keep letters/numbers/space + common Spanish chars
    s = re.sub(r"\s+", " ", s)              # collapse whitespace
    return s

def now_stamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ----------------------------
# App config
# ----------------------------
st.set_page_config(page_title="Spain Spanish Slang Tutor", page_icon="🇪🇸", layout="centered")

st.title("🇪🇸 Spain Spanish Slang Tutor")
st.caption("Learn → Quiz → Review your misses. Built for quick practice.")

# ----------------------------
# Data
# ----------------------------
DEFAULT_CORPUS = [
    {"english": "What’s up?", "spanish": "¿Qué pasa?", "tag": "slang"},
    {"english": "That party was really fun", "spanish": "La fiesta estuvo guapísima", "tag": "adjective"},
    {"english": "He’s very annoying", "spanish": "Es muy pesado", "tag": "slang"},
    {"english": "I’m tired", "spanish": "Estoy hecho polvo", "tag": "idiom"},
]

# ----------------------------
# Session state
# ----------------------------
if "corpus" not in st.session_state:
    st.session_state.corpus = DEFAULT_CORPUS.copy()

if "mistakes" not in st.session_state:
    st.session_state.mistakes = []  # list of dicts (same shape as corpus)

if "stats" not in st.session_state:
    st.session_state.stats = {
        "attempts": 0,
        "correct": 0,
        "streak": 0,
        "last_seen": {},  # key -> timestamp
    }

if "card" not in st.session_state:
    st.session_state.card = None

if "show_answer" not in st.session_state:
    st.session_state.show_answer = False

# ----------------------------
# Sidebar (controls)
# ----------------------------
with st.sidebar:
    st.header("Controls")

    mode = st.radio(
        "Mode",
        ["Learn (Flashcards)", "Quiz (Type)", "Review Mistakes", "Browse Phrases"],
        index=0,
    )

    st.divider()

    colA, colB = st.columns(2)
    with colA:
        if st.button("Reset session", use_container_width=True):
            st.session_state.mistakes = []
            st.session_state.stats = {"attempts": 0, "correct": 0, "streak": 0, "last_seen": {}}
            st.session_state.card = None
            st.session_state.show_answer = False
            st.toast("Session reset ✅")

    with colB:
        if st.button("Clear mistakes", use_container_width=True):
            st.session_state.mistakes = []
            st.toast("Mistakes cleared ✅")

    st.divider()
    st.subheader("Add your own phrase")
    new_en = st.text_input("English", key="new_en")
    new_es = st.text_input("Spain Spanish", key="new_es")
    new_tag = st.text_input("Tag (optional)", key="new_tag")

    if st.button("Add phrase"):
        if new_en.strip() and new_es.strip():
            st.session_state.corpus.append(
                {"english": new_en.strip(), "spanish": new_es.strip(), "tag": (new_tag.strip() or "custom")}
            )
            st.session_state.new_en = ""
            st.session_state.new_es = ""
            st.session_state.new_tag = ""
            st.toast("Added ✅")
        else:
            st.warning("Add both English and Spanish.")

# ----------------------------
# Stats bar
# ----------------------------
attempts = st.session_state.stats["attempts"]
correct = st.session_state.stats["correct"]
streak = st.session_state.stats["streak"]
accuracy = (correct / attempts * 100) if attempts else 0.0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Attempts", attempts)
m2.metric("Correct", correct)
m3.metric("Accuracy", f"{accuracy:.0f}%")
m4.metric("Streak", streak)

st.write("")  # spacing

# ----------------------------
# Card selection logic
# ----------------------------
def pick_card(source: str):
    """Pick a card from corpus/mistakes. Mildly favors unseen + mistakes."""
    pool = st.session_state.corpus if source == "corpus" else st.session_state.mistakes
    if not pool:
        return None

    # Favor items not recently seen
    weights = []
    for item in pool:
        key = f"{item['english']}||{item['spanish']}"
        last = st.session_state.stats["last_seen"].get(key)
        w = 3.0 if last is None else 1.0
        weights.append(w)

    card = random.choices(pool, weights=weights, k=1)[0]
    key = f"{card['english']}||{card['spanish']}"
    st.session_state.stats["last_seen"][key] = now_stamp()
    return card

# ----------------------------
# Mode: Learn (Flashcards)
# ----------------------------
if mode == "Learn (Flashcards)":
    st.subheader("Learn (Flashcards)")

    if st.session_state.card is None:
        st.session_state.card = pick_card("corpus")
        st.session_state.show_answer = False

    card = st.session_state.card

    if not card:
        st.info("No phrases yet. Add one in the sidebar.")
    else:
        st.write("**English:**")
        st.markdown(f"### {card['english']}")
        st.caption(f"Tag: `{card.get('tag','')}`")

        st.write("")

        if st.button("Show / hide answer"):
            st.session_state.show_answer = not st.session_state.show_answer

        if st.session_state.show_answer:
            st.write("**Spain Spanish:**")
            st.markdown(f"### {card['spanish']}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ I knew it", use_container_width=True):
                # If it was in mistakes, remove it
                if card in st.session_state.mistakes:
                    st.session_state.mistakes.remove(card)
                st.session_state.stats["streak"] += 1
                st.session_state.card = pick_card("corpus")
                st.session_state.show_answer = False

        with c2:
            if st.button("❌ I missed it", use_container_width=True):
                if card not in st.session_state.mistakes:
                    st.session_state.mistakes.append(card)
                st.session_state.stats["streak"] = 0
                st.session_state.card = pick_card("corpus")
                st.session_state.show_answer = False

# ----------------------------
# Mode: Quiz (Type)
# ----------------------------
elif mode == "Quiz (Type)":
    st.subheader("Quiz (Type)")

    source = st.radio(
        "Question source",
        ["Mix (recommended)", "Only New", "Only Mistakes"],
        horizontal=True
    )

    if st.session_state.card is None:
        if source == "Only Mistakes":
            st.session_state.card = pick_card("mistakes")
        elif source == "Only New":
            st.session_state.card = pick_card("corpus")
        else:
            # Mix: if there are mistakes, 60% chance pick from mistakes
            if st.session_state.mistakes and random.random() < 0.6:
                st.session_state.card = pick_card("mistakes")
            else:
                st.session_state.card = pick_card("corpus")

    card = st.session_state.card
    if not card:
        st.info("No available questions (try adding phrases or making a mistake 😅).")
    else:
        st.write("Translate into Spain Spanish:")
        st.markdown(f"### {card['english']}")
        user = st.text_input("Your answer", key="quiz_input")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Submit", use_container_width=True):
                st.session_state.stats["attempts"] += 1
                if normalize(user) == normalize(card["spanish"]):
                    st.success("✅ Correct!")
                    st.session_state.stats["correct"] += 1
                    st.session_state.stats["streak"] += 1
                    if card in st.session_state.mistakes:
                        st.session_state.mistakes.remove(card)
                else:
                    st.error("❌ Not quite.")
                    st.write(f"Correct answer: **{card['spanish']}**")
                    st.session_state.stats["streak"] = 0
                    if card not in st.session_state.mistakes:
                        st.session_state.mistakes.append(card)

                # next question
                st.session_state.quiz_input = ""
                st.session_state.card = None
                st.rerun()

        with col2:
            if st.button("Skip", use_container_width=True):
                st.session_state.quiz_input = ""
                st.session_state.card = None
                st.rerun()

# ----------------------------
# Mode: Review Mistakes
# ----------------------------
elif mode == "Review Mistakes":
    st.subheader("Review Mistakes")
    st.write("These are your current weak spots. Drill them until the list hits zero.")

    if not st.session_state.mistakes:
        st.success("No mistakes to review 🎉")
    else:
        card = pick_card("mistakes")
        st.markdown(f"### {card['english']}")
        user = st.text_input("Type the Spain Spanish", key="review_input")

        if st.button("Check"):
            st.session_state.stats["attempts"] += 1
            if normalize(user) == normalize(card["spanish"]):
                st.success("✅ Correct — removed from mistakes.")
                st.session_state.stats["correct"] += 1
                st.session_state.stats["streak"] += 1
                if card in st.session_state.mistakes:
                    st.session_state.mistakes.remove(card)
            else:
                st.error("❌ Still not quite.")
                st.write(f"Correct answer: **{card['spanish']}**")
                st.session_state.stats["streak"] = 0

            st.session_state.review_input = ""
            st.rerun()

    st.divider()
    st.write(f"**Mistakes left:** {len(st.session_state.mistakes)}")

# ----------------------------
# Mode: Browse
# ----------------------------
else:
    st.subheader("Browse Phrases")
    st.write("Use this to show your corpus in class or quickly add more items.")

    tags = sorted({x.get("tag", "uncategorized") for x in st.session_state.corpus})
    tag_filter = st.multiselect("Filter by tag", tags, default=tags)

    filtered = [x for x in st.session_state.corpus if x.get("tag", "uncategorized") in tag_filter]

    for item in filtered:
        with st.expander(f"{item['english']}  •  {item.get('tag','')}"):
            st.write(f"**Spain Spanish:** {item['spanish']}")
            colx, coly = st.columns(2)
            with colx:
                if st.button("Add to mistakes", key=f"addmist_{item['english']}"):
                    if item not in st.session_state.mistakes:
                        st.session_state.mistakes.append(item)
                    st.toast("Added to mistakes ✅")
            with coly:
                if st.button("Remove phrase", key=f"rm_{item['english']}"):
                    # remove from corpus and mistakes if present
                    st.session_state.corpus = [c for c in st.session_state.corpus if c is not item]
                    st.session_state.mistakes = [m for m in st.session_state.mistakes if m is not item]
                    st.toast("Removed ✅")
                    st.rerun()

st.divider()
st.caption("Tip: For demos, use Learn mode first, then switch to Quiz and intentionally miss one to show Review Mistakes.")
st.divider()
st.write(f"Examples to review: {len(st.session_state.mistakes)}")
