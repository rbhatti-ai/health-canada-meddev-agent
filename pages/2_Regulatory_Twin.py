"""
Regulatory Twin Management — Sprint 10B.

Manages the regulatory digital twin:
- Device version CRUD
- Claim/hazard/control/test management
- Evidence upload + linking
- Attestation workflow
- IP classification
"""

from __future__ import annotations

from uuid import uuid4

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Regulatory Twin - Health Canada MedDev",
    page_icon="🔄",
    layout="wide",
)


def get_mock_device_data() -> dict:
    """Get mock device data for demonstration."""
    return {
        "id": str(uuid4()),
        "name": "CardioMonitor Pro",
        "version": "2.1.0",
        "device_class": "III",
        "intended_use": "Continuous cardiac monitoring for adult patients",
        "status": "development",
        "claims": [
            {"id": str(uuid4()), "text": "Non-invasive cardiac monitoring", "status": "verified"},
            {"id": str(uuid4()), "text": "Real-time arrhythmia detection", "status": "pending"},
            {"id": str(uuid4()), "text": "Battery life > 24 hours", "status": "verified"},
        ],
        "hazards": [
            {
                "id": str(uuid4()),
                "description": "Electrical shock",
                "severity": "critical",
                "mitigated": True,
            },
            {
                "id": str(uuid4()),
                "description": "Battery overheating",
                "severity": "major",
                "mitigated": False,
            },
            {
                "id": str(uuid4()),
                "description": "Incorrect reading display",
                "severity": "major",
                "mitigated": True,
            },
        ],
        "controls": [
            {
                "id": str(uuid4()),
                "description": "Isolation barrier",
                "hazard": "Electrical shock",
                "verified": True,
            },
            {
                "id": str(uuid4()),
                "description": "Display validation algorithm",
                "hazard": "Incorrect reading display",
                "verified": True,
            },
        ],
        "evidence": [
            {
                "id": str(uuid4()),
                "title": "Biocompatibility Test Report",
                "type": "test_report",
                "status": "accepted",
            },
            {
                "id": str(uuid4()),
                "title": "Clinical Study NCT12345",
                "type": "clinical_study",
                "status": "accepted",
            },
            {
                "id": str(uuid4()),
                "title": "Software Validation Protocol",
                "type": "validation",
                "status": "draft",
            },
        ],
    }


def render_claims_tab(data: dict) -> None:
    """Render the claims management tab."""
    st.subheader("📝 Claims")
    st.markdown("*Claims are statements about device performance that require evidence support.*")

    # Add new claim
    with st.expander("➕ Add New Claim"):
        new_claim = st.text_input("Claim Text")
        _claim_type = st.selectbox("Claim Type", ["performance", "safety", "clinical"])
        if st.button("Add Claim"):
            st.success(f"Claim added: {new_claim}")

    # List claims
    for claim in data["claims"]:
        status_icon = "✅" if claim["status"] == "verified" else "⏳"
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"{status_icon} {claim['text']}")
            with col2:
                st.caption(claim["status"])
            with col3:
                st.button("Edit", key=f"edit_{claim['id']}")


def render_hazards_tab(data: dict) -> None:
    """Render the hazards management tab."""
    st.subheader("⚠️ Hazards")
    st.markdown("*Hazards are potential sources of harm that require risk controls.*")

    # Add new hazard
    with st.expander("➕ Add New Hazard"):
        new_hazard = st.text_input("Hazard Description")
        _severity = st.selectbox("Severity", ["critical", "major", "minor"])
        _probability = st.selectbox(
            "Probability", ["frequent", "probable", "occasional", "remote", "improbable"]
        )
        if st.button("Add Hazard"):
            st.success(f"Hazard added: {new_hazard}")

    # List hazards
    severity_colors = {"critical": "🔴", "major": "🟠", "minor": "🟡"}

    for hazard in data["hazards"]:
        color = severity_colors.get(hazard["severity"], "⚪")
        mitigated = "✅ Mitigated" if hazard["mitigated"] else "❌ Unmitigated"

        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown(f"{color} {hazard['description']}")
            with col2:
                st.caption(hazard["severity"])
            with col3:
                st.caption(mitigated)
            with col4:
                st.button("Link Control", key=f"link_{hazard['id']}")


def render_controls_tab(data: dict) -> None:
    """Render the controls management tab."""
    st.subheader("🛡️ Risk Controls")
    st.markdown("*Controls are measures that reduce or eliminate hazards.*")

    # Add new control
    with st.expander("➕ Add New Control"):
        new_control = st.text_input("Control Description")
        _control_type = st.selectbox("Control Type", ["design", "protective", "informational"])
        _linked_hazard = st.selectbox(
            "Linked Hazard",
            [h["description"] for h in data["hazards"]],
        )
        if st.button("Add Control"):
            st.success(f"Control added: {new_control}")

    # List controls
    for control in data["controls"]:
        verified = "✅" if control["verified"] else "⏳"
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown(f"{verified} {control['description']}")
            with col2:
                st.caption(f"→ {control['hazard']}")
            with col3:
                st.caption("Verified" if control["verified"] else "Pending")
            with col4:
                st.button("Verify", key=f"verify_{control['id']}")


def render_evidence_tab(data: dict) -> None:
    """Render the evidence management tab."""
    st.subheader("📎 Evidence Items")
    st.markdown("*Evidence supports claims and verifies controls.*")

    # Upload evidence
    with st.expander("📤 Upload Evidence"):
        uploaded_file = st.file_uploader("Choose file")
        evidence_title = st.text_input("Evidence Title")
        _evidence_type = st.selectbox(
            "Evidence Type",
            ["test_report", "clinical_study", "literature", "validation", "verification"],
        )
        _confidentiality = st.selectbox(
            "Confidentiality Level",
            ["public", "confidential_submission", "trade_secret", "patent_pending"],
        )
        if st.button("Upload"):
            if uploaded_file and evidence_title:
                st.success(f"Evidence uploaded: {evidence_title}")
            else:
                st.error("Please provide a file and title")

    # List evidence
    status_icons = {"accepted": "✅", "draft": "📝", "rejected": "❌", "pending": "⏳"}

    for evidence in data["evidence"]:
        icon = status_icons.get(evidence["status"], "⚪")
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown(f"{icon} {evidence['title']}")
            with col2:
                st.caption(evidence["type"])
            with col3:
                st.caption(evidence["status"])
            with col4:
                st.button("Link", key=f"link_ev_{evidence['id']}")


def render_attestation_tab(data: dict) -> None:
    """Render the attestation workflow tab."""
    st.subheader("✍️ Attestation Workflow")
    st.markdown("*Attestations provide human sign-off on AI-generated or critical artifacts.*")

    # Pending attestations
    st.markdown("### Pending Attestations")

    pending_items = [
        {
            "artifact": "Risk Analysis Report v2.1",
            "type": "ai_generated",
            "requested_by": "System",
            "requested_at": "2026-02-07 14:30",
        },
        {
            "artifact": "Clinical Summary",
            "type": "critical_document",
            "requested_by": "QA Manager",
            "requested_at": "2026-02-07 10:15",
        },
    ]

    for item in pending_items:
        with st.expander(f"📋 {item['artifact']}", expanded=True):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Type:** {item['type'].replace('_', ' ').title()}")
                st.markdown(f"**Requested by:** {item['requested_by']}")
                st.markdown(f"**Requested at:** {item['requested_at']}")
            with col2:
                attestation_type = st.selectbox(
                    "Attestation Type",
                    ["reviewed", "approved", "verified", "rejected"],
                    key=f"attest_{item['artifact']}",
                )
                _notes = st.text_area("Notes", key=f"notes_{item['artifact']}")
                if st.button("Submit Attestation", key=f"submit_{item['artifact']}"):
                    st.success(f"Attestation submitted: {attestation_type}")

    # Completed attestations
    st.markdown("### Completed Attestations")
    st.info("3 attestations completed in the last 7 days")


def main():
    """Main regulatory twin management page."""
    st.title("🔄 Regulatory Twin Management")
    st.markdown("*Manage your device's digital regulatory twin*")

    # Device selector
    col1, col2 = st.columns([2, 1])
    with col1:
        _selected_device = st.selectbox(
            "Select Device Version",
            ["CardioMonitor Pro v2.1.0", "CardioMonitor Pro v2.0.0 (archived)"],
        )
    with col2:
        st.button("➕ New Version")

    # Get mock data
    data = get_mock_device_data()

    # Device info summary
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Device Class", data["device_class"])
    with col2:
        st.metric("Claims", len(data["claims"]))
    with col3:
        st.metric("Hazards", len(data["hazards"]))
    with col4:
        st.metric("Evidence Items", len(data["evidence"]))

    st.divider()

    # Tabs for different aspects
    tabs = st.tabs(["📝 Claims", "⚠️ Hazards", "🛡️ Controls", "📎 Evidence", "✍️ Attestations"])

    with tabs[0]:
        render_claims_tab(data)

    with tabs[1]:
        render_hazards_tab(data)

    with tabs[2]:
        render_controls_tab(data)

    with tabs[3]:
        render_evidence_tab(data)

    with tabs[4]:
        render_attestation_tab(data)


if __name__ == "__main__":
    main()
