"""
Streamlit UI for Health Canada Medical Device Regulatory Agent.
Connects to Vercel API backend.
"""

import requests
import streamlit as st

# Configuration
API_BASE_URL = "https://health-canada-meddev-agent.vercel.app"

# Page configuration
st.set_page_config(
    page_title="Health Canada MedDev Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "classification_result" not in st.session_state:
    st.session_state.classification_result = None
if "pathway_result" not in st.session_state:
    st.session_state.pathway_result = None


def main():
    """Main application entry point."""
    st.title("🏥 Health Canada Medical Device Regulatory Agent")
    st.markdown("*AI-powered assistant for navigating Canadian medical device regulations*")

    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Select a tool:",
            [
                "🔬 Device Classification",
                "🗺️ Regulatory Pathway",
                "ℹ️ About",
            ],
        )

        st.divider()
        st.markdown("### Quick Links")
        st.markdown("- [Health Canada Medical Devices](https://www.canada.ca/en/health-canada/services/drugs-health-products/medical-devices.html)")
        st.markdown("- [MDALL Database](https://health-products.canada.ca/mdall-limh/)")
        st.markdown("- [Fee Schedule](https://www.canada.ca/en/health-canada/services/drugs-health-products/medical-devices/fees.html)")

        st.divider()
        st.markdown("### API Status")
        try:
            resp = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if resp.status_code == 200:
                st.success("✅ API Online")
            else:
                st.error("❌ API Error")
                except Exception:
                    st.error("❌ API Offline")

    # Route to appropriate page
    if page == "🔬 Device Classification":
        render_classification_page()
    elif page == "🗺️ Regulatory Pathway":
        render_pathway_page()
    elif page == "ℹ️ About":
        render_about_page()


def render_classification_page():
    """Render the device classification interface."""
    st.header("🔬 Device Classification")

    st.markdown("""
    Enter your device information to determine its Health Canada classification.
    The classification determines regulatory requirements, review timelines, and fees.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Device Information")
        device_name = st.text_input("Device Name", placeholder="e.g., CardioMonitor Pro")
        device_description = st.text_area(
            "Device Description",
            placeholder="Describe what the device does and how it works...",
            height=100,
        )
        intended_use = st.text_area(
            "Intended Use",
            placeholder="Describe the intended use, indications, and target population...",
            height=100,
        )
        manufacturer = st.text_input("Manufacturer Name", placeholder="Your company name")

    with col2:
        st.subheader("Device Characteristics")
        is_software = st.checkbox("Software as Medical Device (SaMD)")
        is_implantable = st.checkbox("Implantable Device")
        is_active = st.checkbox("Active (Powered) Device")

        contact_duration = None
        if is_implantable:
            contact_duration = st.selectbox(
                "Contact Duration",
                ["short-term", "long-term"],
                format_func=lambda x: x.replace("-", " ").title(),
            )

        healthcare_situation = None
        significance = None
        uses_ml = False

        if is_software:
            st.subheader("SaMD Classification")
            healthcare_situation = st.selectbox(
                "Healthcare Situation",
                ["non_serious", "serious", "critical"],
                format_func=lambda x: x.replace("_", " ").title(),
            )
            significance = st.selectbox(
                "Significance of Information",
                ["inform", "drive", "diagnose", "treat"],
                format_func=lambda x: x.title(),
            )
            uses_ml = st.checkbox("Uses Machine Learning/AI")

    if st.button("🔍 Classify Device", type="primary"):
        if not all([device_name, device_description, intended_use, manufacturer]):
            st.error("Please fill in all required fields")
        else:
            with st.spinner("Classifying device..."):
                try:
                    # Build request
                    request_data = {
                        "device_info": {
                            "name": device_name,
                            "description": device_description,
                            "intended_use": intended_use,
                            "manufacturer_name": manufacturer,
                            "is_software": is_software,
                            "is_implantable": is_implantable,
                            "is_active": is_active,
                            "contact_duration": contact_duration,
                        }
                    }

                    if is_software and healthcare_situation and significance:
                        request_data["samd_info"] = {
                            "healthcare_situation": healthcare_situation,
                            "significance": significance,
                            "uses_ml": uses_ml,
                        }

                    # Call API
                    response = requests.post(
                        f"{API_BASE_URL}/api/v1/classify",
                        json=request_data,
                        timeout=30,
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.classification_result = result

                        # Display results
                        st.success("Classification Complete!")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Device Class", f"Class {result['device_class']}")
                        with col2:
                            st.metric("Risk Level", result['risk_level'])
                        with col3:
                            st.metric("Confidence", f"{result['confidence']*100:.0f}%")

                        st.subheader("Classification Rationale")
                        st.info(result['rationale'])

                        if result.get('warnings'):
                            st.subheader("⚠️ Warnings")
                            for warning in result['warnings']:
                                st.warning(warning)

                        # Show next steps
                        st.subheader("Next Steps")
                        st.markdown(f"""
                        Based on **Class {result['device_class']}** classification:
                        1. Go to **Regulatory Pathway** to see required steps
                        2. Review fee requirements
                        3. Prepare documentation
                        """)
                    else:
                        st.error(f"API Error: {response.text}")

                except Exception as e:
                    st.error(f"Error: {str(e)}")


def render_pathway_page():
    """Render the regulatory pathway interface."""
    st.header("🗺️ Regulatory Pathway")

    st.markdown("""
    Get a step-by-step regulatory pathway with timelines and fees
    based on your device classification.
    """)

    col1, col2 = st.columns(2)

    with col1:
        device_class = st.selectbox(
            "Device Class",
            ["I", "II", "III", "IV"],
            index=2,
        )

    with col2:
        is_software = st.checkbox("Software Device", value=True)
        has_mdel = st.checkbox("Already have MDEL", value=False)

    if st.button("📋 Get Pathway", type="primary"):
        with st.spinner("Generating pathway..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/v1/pathway",
                    json={
                        "device_class": device_class,
                        "is_software": is_software,
                        "has_mdel": has_mdel,
                    },
                    timeout=30,
                )

                if response.status_code == 200:
                    result = response.json()
                    st.session_state.pathway_result = result

                    st.success("Pathway Generated!")

                    # Fee summary
                    st.subheader("💰 Fee Summary (2024 CAD)")
                    fees = result['fees']

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("MDEL Fee", f"${fees['mdel_fee']:,.0f}")
                    with col2:
                        st.metric("MDL Fee", f"${fees['mdl_fee']:,.0f}")
                    with col3:
                        st.metric("Annual Fee", f"${fees['annual_fee']:,.0f}")
                    with col4:
                        st.metric("Total", f"${fees['total']:,.0f}", delta=None)

                    # Timeline
                    st.subheader("⏱️ Timeline")
                    st.info(f"Estimated: **{result['timeline_days_min']} - {result['timeline_days_max']} days**")

                    # Steps
                    st.subheader("📝 Regulatory Steps")
                    for i, step in enumerate(result['steps'], 1):
                        with st.expander(f"Step {i}: {step['name']}", expanded=True):
                            st.write(step['description'])
                            if step.get('duration_days'):
                                st.caption(f"⏱️ Duration: ~{step['duration_days']} days")

                else:
                    st.error(f"API Error: {response.text}")

            except Exception as e:
                st.error(f"Error: {str(e)}")


def render_about_page():
    """Render the about page."""
    st.header("ℹ️ About This Tool")

    st.markdown("""
    ### Health Canada Medical Device Regulatory Agent

    This AI-powered tool helps medical device manufacturers navigate Health Canada's
    regulatory requirements for bringing devices to the Canadian market.

    #### Features

    - **Device Classification**: Determine your device class (I-IV) using Health Canada rules
      and the IMDRF SaMD framework
    - **Regulatory Pathway**: Get step-by-step guidance with timelines and fees
    - **2024 Fee Schedule**: Up-to-date Health Canada fee information

    #### Classification Framework

    | Class | Risk Level | MDL Required | Review Time |
    |-------|------------|--------------|-------------|
    | I | Lowest | No | N/A |
    | II | Low-Moderate | Yes | 15 days |
    | III | Moderate-High | Yes | 75 days |
    | IV | Highest | Yes | 90 days |

    #### SaMD Classification (IMDRF N12)

    For Software as Medical Device, classification is based on:
    - **Healthcare Situation**: Critical, Serious, or Non-serious
    - **Significance**: Treat, Diagnose, Drive, or Inform

    #### Disclaimer

    This tool provides guidance based on Health Canada regulations and guidance documents.
    It is not a substitute for professional regulatory advice. Always verify requirements
    with Health Canada and consult qualified regulatory professionals for official submissions.

    ---

    **API**: [health-canada-meddev-agent.vercel.app](https://health-canada-meddev-agent.vercel.app)

    **Source**: [GitHub](https://github.com/rbhatti-ai/health-canada-meddev-agent)
    """)


if __name__ == "__main__":
    main()
