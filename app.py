import streamlit as st
import random

st.set_page_config(page_title="Spain Spanish Slang Tutor")
st.title("🇪🇸 Spain Spanish Slang Tutor")

corpus = [
    {"english": "What’s up?", "spanish": "¿Qué pasa?", "tag": "slang"},
    {"english": "That party was really fun", "spanish": "La fiesta estuvo guapísima", "tag": "adjective"},
    {"english": "He’s very annoying", "spanish": "Es muy pesado", "tag": "slang"},
    {"english": "I’m tired", "spanish": "Estoy hecho polvo", "tag": "idiom"},
]

if "mistakes" not in st.session_state:
    st.session_state.mistakes = []

example = random.choice(
    st.session_state.mistakes if st.session_state.mistakes else corpus
)

st.subheader("Study")
st.write("Translate into Spain Spanish:")
st.write(f"**{example['english']}**")

user_input = st.text_input("Your translation:")

if st.button("Submit"):
    if user_input.strip().lower() == example["spanish"].lower():
        st.success("✅ Correct!")
        if example in st.session_state.mistakes:
            st.session_state.mistakes.remove(example)
    else:
        st.error("❌ Not quite.")
        st.write(f"Correct answer: **{example['spanish']}**")
        if example not in st.session_state.mistakes:
            st.session_state.mistakes.append(example)

st.divider()
st.write(f"Examples to review: {len(st.session_state.mistakes)}")
