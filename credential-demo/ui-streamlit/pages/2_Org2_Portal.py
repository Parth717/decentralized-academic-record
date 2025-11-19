import json
import requests
import streamlit as st

st.set_page_config(page_title="Org2 Portal", page_icon="🏢", layout="wide")

# ---------------- Sidebar ----------------
st.sidebar.title("⚙️ Settings")
API = st.sidebar.text_input("Gateway API URL", "http://localhost:3000")
TIMEOUT = st.sidebar.number_input("Timeout (sec)", min_value=5, max_value=60, value=15)

def call_api(method, path):
    try:
        resp = requests.request(method, f"{API.rstrip('/')}/{path}", timeout=TIMEOUT)
        if resp.ok:
            return True, resp.json()
        return False, resp.text
    except Exception as e:
        return False, str(e)

st.title("🏢 Org2 Portal – Employer Verification Dashboard")
st.caption("Verify Credential → Confirm Hash Integrity")

# Store verification result for download (outside form)
if "verified_result" not in st.session_state:
    st.session_state.verified_result = None
if "verified_credID" not in st.session_state:
    st.session_state.verified_credID = ""

# ---------------- Verify Tab ----------------
st.subheader("🔍 Verify Credential")

# Session states
if "verified_result" not in st.session_state:
    st.session_state.verified_result = None
if "verified_credID" not in st.session_state:
    st.session_state.verified_credID = ""

# ------------------ UPLOAD SECTION ------------------
st.write("### 📤 Upload Credential JSON to Verify")

uploaded_file = st.file_uploader("Upload the credential JSON file", type=["json"])

if uploaded_file:
    try:
        file_data = json.loads(uploaded_file.read().decode("utf-8"))
        credID_from_file = file_data.get("credID") or file_data.get("CredID") or file_data.get("id")

        if not credID_from_file:
            st.error("Could not extract credential ID from uploaded JSON.")
        else:
            st.success(f"Extracted Credential ID: {credID_from_file}")

            ok, data = call_api("GET", f"verify/{credID_from_file}")

            if ok:
                st.success("Credential Verified from File Upload")
                st.json(data)

                ok2, report = call_api("GET", f"verify-hash/{credID_from_file}")

                if ok2:
                    st.info(f"Hash Match: {report.get('isHashValid')}")
                    st.code(json.dumps(report, indent=2))
                else:
                    st.error("Hash integrity check failed.")

                st.session_state.verified_result = data
                st.session_state.verified_credID = credID_from_file
            else:
                st.error("Verification failed from uploaded file")
                st.write(data)
    except Exception as e:
        st.error(f"Error processing uploaded file: {e}")

st.divider()

# ------------------ MANUAL VERIFY FORM ------------------
st.write("### 🔍 Verify Using Credential ID")

with st.form("verify_form"):
    credID = st.text_input("Credential ID", "CRED3001")
    submit_btn = st.form_submit_button("🔍 Verify")

    if submit_btn:
        ok, data = call_api("GET", f"verify/{credID}")

        if ok:
            st.success("Credential Verified")
            st.json(data)

            st.session_state.verified_result = data
            st.session_state.verified_credID = credID

            ok2, report = call_api("GET", f"verify-hash/{credID}")
            if ok2:
                st.info(f"Hash match: {report.get('isHashValid')}")
                st.code(json.dumps(report, indent=2))
            else:
                st.error("Hash check failed")

        else:
            st.error("Verification failed")
            st.write(data)
            st.session_state.verified_result = None
            st.session_state.verified_credID = ""

# ---------------- Download button (OUTSIDE form) ----------------
if st.session_state.verified_result:
    st.download_button(
        "⬇️ Download Verification Report",
        data=json.dumps(st.session_state.verified_result, indent=2),
        file_name=f"{st.session_state.verified_credID}_verification.json",
        mime="application/json",
        use_container_width=True
    )

