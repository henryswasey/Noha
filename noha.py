import streamlit as st

# Page config
st.set_page_config(
    page_title="Noha Test App",
    layout="wide"
)

# Test session state
if 'counter' not in st.session_state:
    st.session_state.counter = 0

# Main content
st.title("Noha Development Test")

# Test button with session state
if st.button("Click Me"):
    st.session_state.counter += 1

st.write(f"Button clicked {st.session_state.counter} times")

# Test theme colors
st.markdown("""
    <div style='background-color: var(--secondary-background-color); padding: 20px;'>
        Testing theme configuration
    </div>
    """, unsafe_allow_html=True)