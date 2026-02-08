"""
Readiness Dashboard — Sprint 10A.

Displays regulatory readiness status:
- Risk coverage visualization
- Trace completeness display
- Evidence strength indicators
- Gap findings with citations
- Readiness score with breakdown
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Readiness Dashboard - Health Canada MedDev",
    page_icon="📊",
    layout="wide",
)


def get_mock_readiness_data() -> dict[str, Any]:
    """Get mock readiness data for demonstration.

    In production, this would call the actual services.
    """
    return {
        "device_version_id": str(uuid4()),
        "device_name": "CardioMonitor Pro",
        "device_class": "III",
        "overall_score": 0.72,
        "risk_coverage": {
            "total_hazards": 15,
            "mitigated_hazards": 12,
            "coverage_score": 0.80,
        },
        "trace_completeness": {
            "total_claims": 8,
            "fully_traced": 6,
            "completeness_score": 0.75,
        },
        "evidence_strength": {
            "total_evidence": 12,
            "strong_evidence": 8,
            "strength_score": 0.67,
        },
        "gap_findings": [
            {
                "rule_id": "GAP-001",
                "severity": "major",
                "description": "Hazard 'Battery overheating' has no control measure.",
                "citation": "[ISO 14971:2019, 7.1]",
                "entity_type": "hazard",
            },
            {
                "rule_id": "GAP-002",
                "severity": "critical",
                "description": "Control 'Temperature sensor' lacks verification evidence.",
                "citation": "[ISO 14971:2019, 7.2]",
                "entity_type": "control",
            },
            {
                "rule_id": "GAP-014",
                "severity": "major",
                "description": "Clinical evidence strength (0.55) below Class III threshold (0.60).",
                "citation": "[GUI-0102, Section 4.1]",
                "entity_type": "device_version",
            },
        ],
        "category_scores": {
            "completeness": 0.85,
            "consistency": 0.70,
            "evidence_strength": 0.65,
            "verification": 0.68,
        },
    }


def render_score_gauge(score: float, label: str) -> None:
    """Render a score as a progress bar with color coding."""
    if score >= 0.8:
        status = "Strong"
    elif score >= 0.6:
        status = "Moderate"
    else:
        status = "Needs Work"

    st.metric(label, f"{score * 100:.0f}%", delta=status)
    st.progress(score)


def render_gap_findings(findings: list[dict]) -> None:
    """Render gap findings with citations."""
    severity_colors = {
        "critical": "🔴",
        "major": "🟠",
        "minor": "🟡",
        "info": "🔵",
    }

    for finding in findings:
        severity = finding.get("severity", "info")
        color = severity_colors.get(severity, "⚪")

        with st.expander(
            f"{color} {finding['rule_id']}: {finding['description'][:50]}...",
            expanded=severity == "critical",
        ):
            st.markdown(f"**Severity:** {severity.title()}")
            st.markdown(f"**Description:** {finding['description']}")
            st.markdown(f"**Entity Type:** {finding.get('entity_type', 'N/A')}")
            st.code(finding.get("citation", "No citation"), language=None)

            if severity in ("critical", "major"):
                st.warning("This finding requires attention before submission.")


def main():
    """Main readiness dashboard page."""
    st.title("📊 Regulatory Readiness Dashboard")
    st.markdown("*Monitor your device's regulatory submission readiness*")

    # Device selector (mock)
    col1, col2 = st.columns([2, 1])
    with col1:
        _device_name = st.selectbox(
            "Select Device",
            ["CardioMonitor Pro (Class III)", "DiagnosticAI (Class II)", "SimpleGauge (Class I)"],
        )
    with col2:
        st.button("🔄 Refresh Data")

    st.divider()

    # Get data
    data = get_mock_readiness_data()

    # Overall readiness score
    st.subheader("Overall Readiness Score")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        render_score_gauge(data["overall_score"], "Overall")

    with col2:
        render_score_gauge(data["risk_coverage"]["coverage_score"], "Risk Coverage")

    with col3:
        render_score_gauge(data["trace_completeness"]["completeness_score"], "Traceability")

    with col4:
        render_score_gauge(data["evidence_strength"]["strength_score"], "Evidence")

    with col5:
        st.metric("Device Class", data["device_class"])
        st.caption("Higher classes require stronger evidence")

    st.divider()

    # Two-column layout for details
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 Risk Management Coverage")
        st.markdown(
            f"""
        | Metric | Value |
        |--------|-------|
        | Total Hazards | {data['risk_coverage']['total_hazards']} |
        | Mitigated | {data['risk_coverage']['mitigated_hazards']} |
        | Unmitigated | {data['risk_coverage']['total_hazards'] - data['risk_coverage']['mitigated_hazards']} |
        """
        )

        st.subheader("🔗 Trace Completeness")
        st.markdown(
            f"""
        | Metric | Value |
        |--------|-------|
        | Total Claims | {data['trace_completeness']['total_claims']} |
        | Fully Traced | {data['trace_completeness']['fully_traced']} |
        | Incomplete | {data['trace_completeness']['total_claims'] - data['trace_completeness']['fully_traced']} |
        """
        )

    with col2:
        st.subheader("📊 Category Breakdown")
        for category, score in data["category_scores"].items():
            st.markdown(f"**{category.replace('_', ' ').title()}**")
            st.progress(score)
            st.caption(f"{score * 100:.0f}%")

    st.divider()

    # Gap Findings
    st.subheader("⚠️ Gap Findings")
    st.markdown(
        "*Findings are generated by the Gap Detection Engine using deterministic rules. "
        "Each finding cites its regulatory source.*"
    )

    # Filter by severity
    severity_filter = st.multiselect(
        "Filter by Severity",
        ["critical", "major", "minor", "info"],
        default=["critical", "major"],
    )

    filtered_findings = [f for f in data["gap_findings"] if f["severity"] in severity_filter]

    if filtered_findings:
        render_gap_findings(filtered_findings)
    else:
        st.success("No findings match the selected filters.")

    st.divider()

    # Submission readiness advice
    st.subheader("📝 Submission Guidance")

    overall = data["overall_score"]
    if overall >= 0.8:
        st.success(
            "**Potential readiness for regulatory review.** "
            "Address any remaining findings and consult with a regulatory professional."
        )
    elif overall >= 0.6:
        st.warning(
            "**Additional work may be needed.** "
            "Review critical and major findings. Strengthen evidence and traceability."
        )
    else:
        st.error(
            "**Significant gaps detected.** "
            "Address critical findings before proceeding. "
            "Consider a comprehensive gap analysis with regulatory support."
        )

    # Regulatory-safe language reminder
    st.info(
        "**Note:** This dashboard provides readiness indicators for internal use. "
        "It does not guarantee regulatory approval. Always consult qualified regulatory "
        "professionals for official submissions. [Per CLAUDE.md regulatory language safety]"
    )


if __name__ == "__main__":
    main()
