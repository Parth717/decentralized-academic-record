import streamlit as st

st.set_page_config(
    page_title="Blockchain Credential System",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Blockchain Credential System")
st.subheader("Welcome!")

st.write("""
This application demonstrates a two-organization Hyperledger Fabric network  
for issuing, sharing, verifying, and revoking academic credentials.

Use the navigation pages on the left to switch between:
- **Org1 Portal (University)**  
- **Org2 Portal (Employer)**
""")

st.info("➡️ Use the left sidebar to open **Org1** or **Org2** portal.")

st.markdown("---")

st.caption("Built using Streamlit + Hyperledger Fabric Gateway APIs.")
