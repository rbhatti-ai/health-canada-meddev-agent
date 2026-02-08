"""
Clinical Evidence Portfolio — Sprint 10C.

Displays clinical evidence data:
- Clinical studies list with hierarchy scores
- Predicate comparison matrix
- Evidence strength visualization
"""

from __future__ import annotations

from uuid import uuid4

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Clinical Evidence - Health Canada MedDev",
    page_icon="🔬",
    layout="wide",
)

# Evidence hierarchy scores (per GUI-0102)
EVIDENCE_HIERARCHY = {
    "randomized_controlled_trial": 1.0,
    "prospective_cohort": 0.85,
    "retrospective_cohort": 0.70,
    "case_control": 0.55,
    "case_series": 0.40,
    "case_report": 0.25,
    "expert_opinion": 0.15,
    "literature_review": 0.15,
    "registry_data": 0.60,
}

# Class thresholds (per GUI-0102)
CLASS_THRESHOLDS = {
    "I": 0.0,
    "II": 0.40,
    "III": 0.60,
    "IV": 0.85,
}


def get_mock_clinical_data() -> dict:
    """Get mock clinical evidence data for demonstration."""
    return {
        "device_name": "CardioMonitor Pro",
        "device_class": "III",
        "portfolio": {
            "total_studies": 5,
            "weighted_quality_score": 0.68,
            "studies": [
                {
                    "id": str(uuid4()),
                    "title": "Multicenter RCT for CardioMonitor Pro",
                    "study_type": "randomized_controlled_trial",
                    "sample_size": 250,
                    "primary_outcome_met": True,
                    "peer_reviewed": True,
                    "quality_score": 0.92,
                    "status": "completed",
                },
                {
                    "id": str(uuid4()),
                    "title": "Prospective Cohort Study - Real-World Use",
                    "study_type": "prospective_cohort",
                    "sample_size": 500,
                    "primary_outcome_met": True,
                    "peer_reviewed": True,
                    "quality_score": 0.78,
                    "status": "completed",
                },
                {
                    "id": str(uuid4()),
                    "title": "Post-Market Registry Analysis",
                    "study_type": "registry_data",
                    "sample_size": 1200,
                    "primary_outcome_met": True,
                    "peer_reviewed": False,
                    "quality_score": 0.55,
                    "status": "completed",
                },
                {
                    "id": str(uuid4()),
                    "title": "Case Series - Complex Patients",
                    "study_type": "case_series",
                    "sample_size": 25,
                    "primary_outcome_met": True,
                    "peer_reviewed": True,
                    "quality_score": 0.45,
                    "status": "completed",
                },
                {
                    "id": str(uuid4()),
                    "title": "Expert Opinion - Device Selection",
                    "study_type": "expert_opinion",
                    "sample_size": None,
                    "primary_outcome_met": None,
                    "peer_reviewed": True,
                    "quality_score": 0.15,
                    "status": "published",
                },
            ],
        },
        "predicates": [
            {
                "id": str(uuid4()),
                "predicate_name": "HeartWatch 2000",
                "predicate_manufacturer": "CardioTech Inc.",
                "mdl_number": "MDL-12345",
                "intended_use_equivalent": True,
                "technological_equivalent": True,
                "equivalence_conclusion": "substantially_equivalent",
                "differences": [],
            },
            {
                "id": str(uuid4()),
                "predicate_name": "CardioSense Pro",
                "predicate_manufacturer": "MedDevices Co.",
                "mdl_number": "MDL-67890",
                "intended_use_equivalent": True,
                "technological_equivalent": False,
                "equivalence_conclusion": "substantially_equivalent_with_data",
                "differences": ["Uses different sensor technology", "Improved battery system"],
            },
        ],
    }


def render_evidence_hierarchy():
    """Display the evidence hierarchy reference."""
    st.markdown("### 📊 Evidence Hierarchy (GUI-0102)")
    st.markdown("*Higher scores indicate stronger evidence per Health Canada guidelines.*")

    # Display as table
    st.markdown(
        """
    | Study Type | Quality Score | Description |
    |------------|---------------|-------------|
    | Randomized Controlled Trial | 1.00 | Gold standard, prospective, randomized |
    | Prospective Cohort | 0.85 | Prospective observation, no randomization |
    | Retrospective Cohort | 0.70 | Historical data analysis |
    | Registry Data | 0.60 | Real-world evidence from registries |
    | Case-Control | 0.55 | Comparison of cases vs controls |
    | Case Series | 0.40 | Collection of individual cases |
    | Case Report | 0.25 | Single case description |
    | Literature Review | 0.15 | Summary of existing literature |
    | Expert Opinion | 0.15 | Professional judgment |
    """
    )


def render_portfolio_summary(data: dict):
    """Render the evidence portfolio summary."""
    portfolio = data["portfolio"]
    device_class = data["device_class"]
    threshold = CLASS_THRESHOLDS[device_class]

    st.subheader("📈 Portfolio Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Studies", portfolio["total_studies"])

    with col2:
        score = portfolio["weighted_quality_score"]
        delta = (
            f"+{(score - threshold) * 100:.0f}% above threshold"
            if score >= threshold
            else f"{(score - threshold) * 100:.0f}% below threshold"
        )
        st.metric("Weighted Score", f"{score * 100:.0f}%", delta=delta)

    with col3:
        st.metric("Class Threshold", f"{threshold * 100:.0f}%")
        st.caption(f"For Class {device_class}")

    with col4:
        if score >= threshold:
            st.success("✅ Meets Threshold")
        else:
            st.error("❌ Below Threshold")

    # Progress bar
    st.markdown(f"**Evidence Strength vs Class {device_class} Threshold**")
    st.progress(min(score / max(threshold, 0.01), 1.0) if threshold > 0 else 1.0)


def render_studies_list(data: dict):
    """Render the list of clinical studies."""
    studies = data["portfolio"]["studies"]

    st.subheader("📋 Clinical Studies")

    for study in studies:
        hierarchy_score = EVIDENCE_HIERARCHY.get(study["study_type"], 0)
        quality = study["quality_score"]

        # Determine color based on score
        if quality >= 0.7:
            color = "🟢"
        elif quality >= 0.4:
            color = "🟡"
        else:
            color = "🔴"

        with st.expander(f"{color} {study['title']}", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Study Type:** {study['study_type'].replace('_', ' ').title()}")
                st.markdown(f"**Hierarchy Score:** {hierarchy_score:.2f}")
                st.markdown(f"**Quality Score:** {quality:.2f}")
                if study["sample_size"]:
                    st.markdown(f"**Sample Size:** {study['sample_size']}")

            with col2:
                st.markdown(f"**Status:** {study['status'].title()}")
                st.markdown(f"**Peer Reviewed:** {'Yes' if study['peer_reviewed'] else 'No'}")
                if study["primary_outcome_met"] is not None:
                    outcome = "✅ Met" if study["primary_outcome_met"] else "❌ Not Met"
                    st.markdown(f"**Primary Outcome:** {outcome}")

            st.progress(quality)
            st.caption(f"Quality: {quality * 100:.0f}%")


def render_predicate_comparison(data: dict):
    """Render predicate device comparison matrix."""
    predicates = data["predicates"]

    st.subheader("🔍 Predicate Device Comparison")
    st.markdown(
        "*Per SOR/98-282 s.32(4), Class II/III devices must demonstrate substantial equivalence.*"
    )

    if not predicates:
        st.info("No predicate devices identified. Add a predicate for comparison.")
        return

    for predicate in predicates:
        conclusion = predicate["equivalence_conclusion"]
        if conclusion == "substantially_equivalent":
            status = "✅ Substantially Equivalent"
        elif conclusion == "substantially_equivalent_with_data":
            status = "⚠️ Equivalent with Supporting Data"
        else:
            status = "❌ Not Equivalent"

        with st.expander(f"{status}: {predicate['predicate_name']}", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Predicate Device:** {predicate['predicate_name']}")
                st.markdown(f"**Manufacturer:** {predicate['predicate_manufacturer']}")
                st.markdown(f"**MDL Number:** {predicate['mdl_number']}")

            with col2:
                st.markdown("**Comparison Matrix**")
                intended_use = "✅" if predicate["intended_use_equivalent"] else "❌"
                tech = "✅" if predicate["technological_equivalent"] else "⚠️"
                st.markdown(f"- Intended Use: {intended_use}")
                st.markdown(f"- Technological: {tech}")

            if predicate["differences"]:
                st.markdown("**Technological Differences:**")
                for diff in predicate["differences"]:
                    st.markdown(f"- {diff}")
                st.warning(
                    "Differences require supporting data per SOR/98-282 s.32(4)(b). "
                    "Ensure clinical or bench data addresses each difference."
                )

            st.code("[SOR/98-282, s.32(4)]", language=None)


def main():
    """Main clinical evidence page."""
    st.title("🔬 Clinical Evidence Portfolio")
    st.markdown("*Manage clinical studies and predicate comparisons for regulatory submission*")

    # Get mock data
    data = get_mock_clinical_data()

    # Device info
    col1, col2 = st.columns([2, 1])
    with col1:
        st.selectbox(
            "Select Device",
            [f"{data['device_name']} (Class {data['device_class']})"],
        )
    with col2:
        st.button("➕ Add Clinical Study")

    st.divider()

    # Tabs
    tabs = st.tabs(["📈 Portfolio Summary", "📋 Studies", "🔍 Predicates", "📊 Reference"])

    with tabs[0]:
        render_portfolio_summary(data)
        st.divider()
        st.markdown("### 📊 Evidence Distribution")
        # Show study type distribution
        type_counts: dict[str, int] = {}
        for study in data["portfolio"]["studies"]:
            stype = study["study_type"].replace("_", " ").title()
            type_counts[stype] = type_counts.get(stype, 0) + 1

        for stype, count in type_counts.items():
            st.markdown(f"**{stype}:** {count}")

    with tabs[1]:
        render_studies_list(data)

    with tabs[2]:
        render_predicate_comparison(data)

    with tabs[3]:
        render_evidence_hierarchy()
        st.divider()
        st.markdown("### 📋 Class Evidence Thresholds")
        st.markdown(
            """
        | Device Class | Minimum Score | Clinical Data Required |
        |--------------|---------------|------------------------|
        | Class I | 0% | Not required |
        | Class II | 40% | Generally required |
        | Class III | 60% | Required [GUI-0102] |
        | Class IV | 85% | Extensive data required |
        """
        )
        st.info(
            "Thresholds are based on Health Canada guidance. "
            "Actual requirements may vary based on device type and intended use."
        )


if __name__ == "__main__":
    main()
