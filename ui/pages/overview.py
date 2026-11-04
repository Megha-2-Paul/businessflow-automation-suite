"""Initial BusinessFlow overview page."""
import streamlit as st

st.title("BusinessFlow Automation Suite")
st.caption("Automate repetitive business operations with Python.")
st.info(
    "Your workspace is ready. Connect a public dataset or upload business data "
    "when the file automation module is available."
)
st.subheader("Workspace status")
left, right = st.columns(2)
with left:
    st.markdown("**Data processing**")
    st.write("File automation is planned for the next development phase.")
with right:
    st.markdown("**Business workflows**")
    st.write("Invoice, order and inventory modules will be added in their approved phases.")
