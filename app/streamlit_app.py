from __future__ import annotations

import sys
from pathlib import Path

# Make `src/` importable when run via `streamlit run app/streamlit_app.py`.
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from ai_job_advisor.config import get_settings  # noqa: E402
from ai_job_advisor.models.schemas import ProfileType, UserProfile  # noqa: E402
from ai_job_advisor.services.pipeline import JobAdvisorService  # noqa: E402

st.set_page_config(page_title="AI Job Advisor", page_icon="🧭", layout="wide")


@st.cache_resource(show_spinner=False)
def get_service() -> JobAdvisorService:
    return JobAdvisorService(get_settings())


@st.cache_data(show_spinner="Aggregating jobs from sources…")
def load_jobs(query: str, location: str):
    service = get_service()
    jobs = service.ingest(query, location)
    return jobs


def sidebar_profile() -> tuple[UserProfile, str, str]:
    st.sidebar.header("👤 Your profile")
    profile_label = st.sidebar.selectbox(
        "I am a…",
        ["Student", "Graduating Soon", "Non-Student"],
    )
    profile_map = {
        "Student": ProfileType.STUDENT,
        "Graduating Soon": ProfileType.GRADUATING_SOON,
        "Non-Student": ProfileType.NON_STUDENT,
    }
    skills_raw = st.sidebar.text_area(
        "Skills (comma-separated)",
        value="Python, SQL, machine learning",
        help="e.g. Python, SQL, React, communication",
    )
    education = st.sidebar.text_input("Education", value="BSc Computer Science")
    location = st.sidebar.text_input("Location", value="Ljubljana")
    industries_raw = st.sidebar.text_input("Preferred industries", value="Technology")

    st.sidebar.header("🔎 Job search")
    query = st.sidebar.text_input("Search query", value="data")
    search_location = st.sidebar.text_input("Search location", value="Ljubljana")

    user = UserProfile(
        user_id="streamlit-user",
        profile_type=profile_map[profile_label],
        skills=[s.strip() for s in skills_raw.split(",") if s.strip()],
        education=education,
        location=location,
        preferred_industries=[s.strip() for s in industries_raw.split(",") if s.strip()],
    )
    return user, query, search_location


def render_recommendations(service, user, jobs):
    st.subheader("🎯 Recommended jobs")
    recs = service.recommend(user, jobs, top_k=10)
    if not recs:
        st.info("No jobs found. Try a broader search.")
        return
    for rec in recs:
        with st.container(border=True):
            cols = st.columns([3, 1])
            with cols[0]:
                st.markdown(f"**{rec.job.title}** — {rec.job.company}")
                meta = " · ".join(p for p in [rec.job.location, rec.job.industry, f"source: {rec.job.source}"] if p)
                st.caption(meta)
                if rec.matched_skills:
                    st.markdown("✅ Matched: " + ", ".join(f"`{s}`" for s in rec.matched_skills))
                if rec.missing_skills:
                    st.markdown("➕ To learn: " + ", ".join(f"`{s}`" for s in rec.missing_skills[:6]))
                if rec.job.url:
                    st.markdown(f"[View posting]({rec.job.url})")
            with cols[1]:
                st.metric("Match", f"{rec.match_score * 100:.0f}%")
                st.caption(f"semantic {rec.semantic_score:.2f} · skills {rec.skill_similarity:.2f}")


def render_skill_gap(service, user, jobs):
    st.subheader("🪜 Skill-gap analysis (vs. the live market)")
    report = service.skill_gap(user, jobs)
    c1, c2 = st.columns([1, 2])
    with c1:
        st.metric("Market readiness", f"{report.readiness_score * 100:.0f}%")
        st.progress(report.readiness_score)
        st.caption(f"You already have {len(report.matched_skills)} in-demand skills.")
    with c2:
        if report.missing_skills:
            df = pd.DataFrame(
                [
                    {"Skill": i.skill, "Market demand": i.market_demand, "Priority": round(i.priority, 2)}
                    for i in report.missing_skills[:12]
                ]
            )
            st.markdown("**Learning priorities** (ranked by demand × gap)")
            st.dataframe(df, hide_index=True, use_container_width=True)
        else:
            st.success("No skill gaps detected against the current market!")


def render_coverage(service, jobs):
    st.subheader("📊 Market-coverage analytics")
    report = service.market_coverage(jobs)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total jobs", report.total_jobs)
    c2.metric("Hidden market", f"{report.hidden_market_pct:.0f}%",
              help="Share from non-mainstream sources a single board would miss")
    c3.metric("Student-friendly", report.student_jobs)
    c4.metric("Other roles", report.non_student_jobs)

    c5, c6 = st.columns(2)
    with c5:
        st.markdown("**Jobs by source**")
        st.bar_chart(pd.Series(report.jobs_by_source, name="jobs"))
    with c6:
        st.markdown("**Student vs non-student**")
        st.bar_chart(
            pd.Series(
                {"Student-friendly": report.student_jobs, "Other": report.non_student_jobs},
                name="jobs",
            )
        )


def render_trends(service, jobs):
    st.subheader("📈 Skill-demand trends")
    report = service.market_coverage(jobs)
    if report.most_requested_skills:
        df = pd.DataFrame(report.most_requested_skills, columns=["Skill", "Demand"]).set_index("Skill")
        st.bar_chart(df)
    else:
        st.info("No skills extracted yet.")


def main() -> None:
    st.title("🧭 AI Job Advisor")
    st.caption(
        "Aggregates jobs from multiple sources and recommends them with AI and "
        "graph-based reasoning — for students, graduates and early-career professionals."
    )

    service = get_service()
    user, query, search_location = sidebar_profile()
    jobs = load_jobs(query, search_location)

    tab1, tab2, tab3, tab4 = st.tabs(
        ["🎯 Recommendations", "🪜 Skill Gap", "📊 Coverage", "📈 Skill Trends"]
    )
    with tab1:
        render_recommendations(service, user, jobs)
    with tab2:
        render_skill_gap(service, user, jobs)
    with tab3:
        render_coverage(service, jobs)
    with tab4:
        render_trends(service, jobs)

    with st.sidebar:
        st.divider()
        st.caption(
            f"Embedding backend: `{get_settings().embedding_backend}` · "
            f"Sample data: `{get_settings().use_sample_provider}`"
        )


if __name__ == "__main__":
    main()
