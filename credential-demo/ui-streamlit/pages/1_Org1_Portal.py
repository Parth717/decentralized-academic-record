import json
import time
import requests
import streamlit as st
import hashlib
import pandas as pd

st.set_page_config(page_title="Org1 Portal", page_icon="🏫", layout="wide")

# ------------- Sidebar Settings -------------
st.sidebar.title("⚙️ Settings")
API = st.sidebar.text_input("Gateway API URL", "http://localhost:3000")
TIMEOUT = st.sidebar.number_input("HTTP Timeout (sec)", min_value=5, max_value=60, value=15)

def call_api(method, path, json_payload=None):
    url = f"{API.rstrip('/')}/{path.lstrip('/')}"
    t0 = time.time()
    try:
        resp = requests.request(method, url, json=json_payload, timeout=TIMEOUT)
        sec = time.time() - t0
        if resp.ok:
            try:
                return True, resp.json(), sec
            except:
                return True, resp.text, sec
        else:
            try:
                return False, resp.json(), sec
            except:
                return False, resp.text, sec
    except Exception as e:
        return False, str(e), time.time() - t0

st.title("🏫 Org1 Portal – University Dashboard")
st.caption("Issue → Share → Revoke → History")

tab_issue, tab_share, tab_revoke, tab_history = st.tabs(
    ["📄 Issue", "🔗 Share", "⛔ Revoke", "🕘 History"]
)

# -------------------------------- ISSUE --------------------------------
with tab_issue:
    st.subheader("Issue Credential")

    # Session state storage for issued result
    if "issued_result" not in st.session_state:
        st.session_state.issued_result = None
        st.session_state.issued_credID = ""

    def canonical_string(cid, sid, sname, uni, deg, gpa, idate):
        return f"{cid}|{sid}|{sname}|{uni}|{deg}|{gpa}|{idate}"

    with st.form("issue_form"):
        c1, c2, c3 = st.columns([1, 1, 1])

        with c1:
            credID = st.text_input("Credential ID", "CRED3001")
            studentID = st.text_input("Student ID", "S-301")
            gpa = st.text_input("GPA", "8.8")

        with c2:
            studentName = st.text_input("Student Name", "Asha Patel")
            degree = st.text_input("Degree", "B.Tech")
            issueDate = st.text_input("Issue Date", "2025-10-01")

        with c3:
            university = st.text_input("University", "UniA")

        # Hash preview
        preview = canonical_string(
            credID.strip(), studentID.strip(), studentName.strip(),
            university.strip(), degree.strip(), gpa.strip(), issueDate.strip()
        )
        preview_hash = hashlib.sha256(preview.encode()).hexdigest()
        st.caption("Auto-computed SHA-256 Hash")
        st.code(preview_hash)

        submit = st.form_submit_button("🚀 Issue")

        if submit:
            payload = {
                "credID": credID,
                "studentID": studentID,
                "studentName": studentName,
                "university": university,
                "degree": degree,
                "gpa": gpa,
                "issueDate": issueDate
            }
            ok, data, sec = call_api("POST", "/issue", payload)
            if ok:
                st.success(f"Issued successfully in {sec:.2f}s")
                st.json(data)

                # Save issued result for download
                st.session_state.issued_result = data
                st.session_state.issued_credID = credID

            else:
                st.error("Issue failed")
                st.write(data)
                st.session_state.issued_result = None
                st.session_state.issued_credID = ""
                submit = False

    # ---------- DOWNLOAD BUTTON OUTSIDE FORM ----------
    if st.session_state.issued_result:
        st.download_button(
            "⬇️ Download Issued Credential JSON",
            data=json.dumps(st.session_state.issued_result, indent=2),
            file_name=f"{st.session_state.issued_credID}_issued.json",
            mime="application/json",
            use_container_width=True
        )

# ------------------------------- SHARE --------------------------------
with tab_share:
    st.subheader("Share Credential")

    with st.form("share_form"):
        credID = st.text_input("Credential ID", "CRED3001")
        submit = st.form_submit_button("🔗 Share to Org2")

        if submit:
            ok, data, sec = call_api("POST", "/share", {"credID": credID})
            if ok:
                st.success(f"Shared to Org2 in {sec:.2f}s")
                st.json(data)
            else:
                st.error("Share failed")
                st.write(data)

# ------------------------------ REVOKE --------------------------------
with tab_revoke:
    st.subheader("Revoke Credential")

    with st.form("revoke_form"):
        credID = st.text_input("Credential ID", "CRED3001")
        submit = st.form_submit_button("⛔ Revoke")

        if submit:
            ok, data, sec = call_api("POST", "/revoke", {"credID": credID})
            if ok:
                st.success(f"Revoked in {sec:.2f}s")
                st.json(data)
            else:
                st.error("Revoke failed")
                st.write(data)

# ------------------------------ HISTORY -------------------------------
with tab_history:
    st.subheader("Credential History (Public Audit)")

    with st.form("history_form"):
        cid = st.text_input("Credential ID", "CRED3001")
        submit = st.form_submit_button("📜 Fetch History")

        if submit:
            ok, data, sec = call_api("GET", f"/history/{cid}")
            if ok:
                st.success(f"Loaded {len(data)} events • {sec:.2f}s")
                if isinstance(data, list) and len(data):
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No history yet.")
            else:
                st.error("Failed to fetch history")
                st.write(data)
