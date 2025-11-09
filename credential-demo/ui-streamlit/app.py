import json, requests, streamlit as st

API = "http://localhost:3000"

st.set_page_config(page_title="Blockchain Credential Demo", page_icon="🎓", layout="centered")
st.title("🎓 Blockchain Credential System (Streamlit)")

tab_issue, tab_share, tab_verify, tab_revoke = st.tabs(["Issue", "Share", "Verify", "Revoke"])

with tab_issue:
    st.subheader("Issue Credential (University / Org1)")
    credID = st.text_input("Credential ID", "CRED3001")
    studentID = st.text_input("Student ID", "S-301")
    studentName = st.text_input("Student Name", "Asha Patel")
    university = st.text_input("University", "UniA")
    degree = st.text_input("Degree", "B.Tech")
    gpa = st.text_input("GPA", "8.8")
    issueDate = st.text_input("Issue Date (YYYY-MM-DD)", "2025-10-01")
    hashv = st.text_input("Optional Hash", "hash123")

    if st.button("Issue"):
        try:
            r = requests.post(f"{API}/issue", json={
                "credID": credID, "studentID": studentID, "studentName": studentName,
                "university": university, "degree": degree, "gpa": gpa,
                "issueDate": issueDate, "hash": hashv
            }, timeout=15)
            if r.ok:
                st.success(f"Issued {credID}")
            else:
                st.error(r.text)
        except Exception as e:
            st.error(str(e))

with tab_share:
    st.subheader("Share Credential (Student identity)")
    credID2 = st.text_input("Credential ID to Share", "CRED3001", key="share_cred")
    targetMSP = st.text_input("Target MSP", "Org2MSP")
    if st.button("Share with Employer"):
        try:
            r = requests.post(f"{API}/share", json={"credID": credID2, "targetMSP": targetMSP}, timeout=15)
            if r.ok:
                st.success("Shared!")
            else:
                st.error(r.text)

        except Exception as e:
            st.error(str(e))

with tab_verify:
    st.subheader("Verify Credential (Employer / Org2)")
    credID3 = st.text_input("Credential ID to Verify", "CRED3001", key="verify_cred")
    if st.button("Verify"):
        try:
            r = requests.get(f"{API}/verify/{credID3}", timeout=15)
            if r.ok:
                st.code(json.dumps(r.json(), indent=2))
                st.success("Verified and fetched private data.")
            else:
                st.error(r.text)
        except Exception as e:
            st.error(str(e))

with tab_revoke:
    st.subheader("Revoke Credential (University / Org1)")
    credID4 = st.text_input("Credential ID to Revoke", "CRED3001", key="revoke_cred")
    if st.button("Revoke"):
        try:
            r = requests.post(f"{API}/revoke", json={"credID": credID4}, timeout=15)
            if r.ok:
                st.success("Revoked!")
            else:
                st.error(r.text)

        except Exception as e:
            st.error(str(e))
