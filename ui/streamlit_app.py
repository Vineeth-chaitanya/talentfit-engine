import os
import requests
import streamlit as st

API_URL = os.getenv("TALENTFIT_API_URL", "http://localhost:8000")

st.set_page_config(page_title="TalentFit Engine", layout="wide")
st.title("TalentFit Engine")
st.caption("Explainable resume-to-job matching with structured extraction, hybrid scoring, and grounded suggestions.")

uploaded = st.file_uploader("Upload resume", type=["pdf", "docx", "txt"])
resume_text = st.text_area("Or paste resume text", height=220)
job_description = st.text_area("Paste job description", height=260)

if st.button("Analyze Fit", type="primary"):
    if not job_description.strip() or (not uploaded and not resume_text.strip()):
        st.error("Please provide a resume and job description.")
    else:
        files = {"file": (uploaded.name, uploaded.getvalue(), uploaded.type)} if uploaded else None
        data = {"job_description": job_description, "resume_text": resume_text}
        with st.spinner("Analyzing..."):
            res = requests.post(f"{API_URL}/analyze", data=data, files=files, timeout=120)
        if not res.ok:
            st.error(res.text)
        else:
            payload = res.json()
            match = payload["match"]
            st.metric("Overall Fit Score", f"{match['final_score']}/100")
            st.subheader("Score Breakdown")
            st.bar_chart(match["score_breakdown"])
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Matched Skills")
                st.write(match["matched_skills"] or "None")
                st.subheader("Evidence Snippets")
                for e in match["strongest_evidence_snippets"]:
                    st.markdown(f"**{e['skill']}** — `{e['section']}`")
                    st.write(e["snippet"])
            with c2:
                st.subheader("Missing Required Skills")
                st.write(match["missing_required_skills"] or "None")
                st.subheader("Missing Preferred Skills")
                st.write(match["missing_preferred_skills"] or "None")
                st.subheader("Risk Flags")
                st.write(match["risk_flags"] or "None")
            st.subheader("Fit Report")
            st.text(payload["fit_report"])
            st.subheader("Grounded Suggestions")
            for s in payload["suggestions"]:
                st.markdown(f"- **{s['suggestion']}**  ")
                st.caption(f"Reason: {s['reason']} | Requirement: {s['related_requirement']}")
                st.code(s["evidence"])
            with st.expander("Raw JSON"):
                st.json(payload)
