"""
Streamlit UI for the Health Canada Medical Device Regulatory Agent.

Provides an interactive web interface for:
- Device classification
- Pathway visualization
- Checklist management
- Document search
- Chat interface
"""

import streamlit as st
from typing import Optional

# Page configuration
st.set_page_config(
    page_title="Health Canada MedDev Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "classification_result" not in st.session_state:
    st.session_state.classification_result = None
if "pathway_result" not in st.session_state:
    st.session_state.pathway_result = None
if "checklist" not in st.session_state:
    st.session_state.checklist = None


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
                "💬 Chat Assistant",
                "🔬 Device Classification",
                "🗺️ Regulatory Pathway",
                "✅ Checklist Generator",
                "🔍 Document Search",
            ],
        )

        st.divider()
        st.markdown("### Quick Links")
        st.markdown("- [Health Canada Medical Devices](https://www.canada.ca/en/health-canada/services/drugs-health-products/medical-devices.html)")
        st.markdown("- [MDALL Database](https://health-products.canada.ca/mdall-limh/)")
        st.markdown("- [Fee Schedule](https://www.canada.ca/en/health-canada/services/drugs-health-products/medical-devices/fees.html)")

    # Route to appropriate page
    if page == "💬 Chat Assistant":
        render_chat_page()
    elif page == "🔬 Device Classification":
        render_classification_page()
    elif page == "🗺️ Regulatory Pathway":
        render_pathway_page()
    elif page == "✅ Checklist Generator":
        render_checklist_page()
    elif page == "🔍 Document Search":
        render_search_page()


def render_chat_page():
    """Render the chat interface."""
    st.header("💬 Chat with Regulatory Assistant")

    st.markdown("""
    Ask me anything about Health Canada medical device regulations:
    - Device classification questions
    - Regulatory pathway guidance
    - Documentation requirements
    - Fee information
    - Specific regulation queries
    """)

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about medical device regulations..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    from src.agents.regulatory_agent import SimpleRegulatoryAgent

                    if "agent" not in st.session_state:
                        st.session_state.agent = SimpleRegulatoryAgent()

                    response = st.session_state.agent.chat(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.messages = []
        if "agent" in st.session_state:
            st.session_state.agent.reset()
        st.rerun()


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
        is_ivd = st.checkbox("In-Vitro Diagnostic (IVD)")
        is_implantable = st.checkbox("Implantable Device")
        is_active = st.checkbox("Active (Powered) Device")

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

    if st.button("Classify Device", type="primary"):
        if not all([device_name, device_description, intended_use, manufacturer]):
            st.error("Please fill in all required fields")
        else:
            with st.spinner("Classifying device..."):
                try:
                    from src.core.models import DeviceInfo, SaMDInfo, HealthcareSituation, SaMDCategory
                    from src.core.classification import classify_device

                    device_info = DeviceInfo(
                        name=device_name,
                        description=device_description,
                        intended_use=intended_use,
                        manufacturer_name=manufacturer,
                        is_software=is_software,
                        is_ivd=is_ivd,
                        is_implantable=is_implantable,
                        is_active=is_active,
                    )

                    samd_info = None
                    if is_software:
                        situation_map = {
                            "critical": HealthcareSituation.CRITICAL,
                            "serious": HealthcareSituation.SERIOUS,
                            "non_serious": HealthcareSituation.NON_SERIOUS,
                        }
                        significance_map = {
                            "treat": SaMDCategory.TREAT,
                            "diagnose": SaMDCategory.DIAGNOSE,
                            "drive": SaMDCategory.DRIVE,
                            "inform": SaMDCategory.INFORM,
                        }
                        samd_info = SaMDInfo(
                            healthcare_situation=situation_map[healthcare_situation],
                            significance=significance_map[significance],
                            uses_ml=uses_ml,
                        )

                    result = classify_device(device_info, samd_info)
                    st.session_state.classification_result = result

                    # Display results
                    st.success("Classification Complete!")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Device Class", f"Class {result.device_class.value}")
                    with col2:
                        st.metric("Risk Level", result.device_class.risk_level)
                    with col3:
                        st.metric("Review Days", f"{result.device_class.review_days} days")

                    st.subheader("Classification Rationale")
                    st.markdown(result.rationale)

                    if result.warnings:
                        st.warning("**Warnings:**\n" + "\n".join(f"- {w}" for w in result.warnings))

                    st.subheader("Regulatory References")
                    for ref in result.references:
                        st.markdown(f"- {ref}")

                except Exception as e:
                    st.error(f"Classification failed: {str(e)}")


def render_pathway_page():
    """Render the regulatory pathway interface."""
    st.header("🗺️ Regulatory Pathway")

    st.markdown("""
    Generate a complete regulatory pathway with steps, timeline, and fees.
    """)

    col1, col2 = st.columns(2)

    with col1:
        device_class = st.selectbox(
            "Device Class",
            ["II", "III", "IV"],
            help="Class I devices don't require MDL",
        )
        is_software = st.checkbox("Software Device")

    with col2:
        has_mdel = st.checkbox("Already have MDEL")
        has_qms = st.checkbox("Already have ISO 13485 certification")

    if st.button("Generate Pathway", type="primary"):
        with st.spinner("Generating pathway..."):
            try:
                from src.core.models import DeviceClass, DeviceInfo, ClassificationResult
                from src.core.pathway import get_pathway

                class_map = {
                    "II": DeviceClass.CLASS_II,
                    "III": DeviceClass.CLASS_III,
                    "IV": DeviceClass.CLASS_IV,
                }

                classification = ClassificationResult(
                    device_class=class_map[device_class],
                    rationale="User selection",
                    is_samd=is_software,
                )

                device_info = DeviceInfo(
                    name="Device",
                    description="Pathway device",
                    intended_use="Pathway calculation",
                    is_software=is_software,
                    manufacturer_name="Manufacturer",
                )

                pathway = get_pathway(classification, device_info, has_mdel, has_qms)
                st.session_state.pathway_result = pathway

                # Display summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Steps", len(pathway.steps))
                with col2:
                    st.metric("Timeline", f"{pathway.timeline.total_days_min}-{pathway.timeline.total_days_max} days")
                with col3:
                    st.metric("Total Fees", f"${pathway.fees.total:,.0f} CAD")

                # Display steps
                st.subheader("Pathway Steps")
                for step in pathway.steps:
                    with st.expander(f"**Step {step.step_number}: {step.name}**"):
                        st.markdown(step.description)
                        if step.estimated_duration_days:
                            st.info(f"Duration: ~{step.estimated_duration_days} days")
                        if step.fees:
                            st.info(f"Fee: ${step.fees:,.0f} CAD")
                        if step.documents_required:
                            st.markdown("**Documents Required:**")
                            for doc in step.documents_required:
                                st.markdown(f"- {doc}")
                        if step.forms:
                            st.markdown(f"**Forms:** {', '.join(step.forms)}")

                # Fee breakdown
                st.subheader("Fee Breakdown")
                fee_data = {
                    "Fee Type": ["MDEL Application", "MDL Application", "Annual Fee", "Total"],
                    "Amount (CAD)": [
                        f"${pathway.fees.mdel_fee:,.0f}",
                        f"${pathway.fees.mdl_fee:,.0f}",
                        f"${pathway.fees.annual_fee:,.0f}",
                        f"**${pathway.fees.total:,.0f}**",
                    ],
                }
                st.table(fee_data)

            except Exception as e:
                st.error(f"Failed to generate pathway: {str(e)}")


def render_checklist_page():
    """Render the checklist generator interface."""
    st.header("✅ Regulatory Checklist")

    st.markdown("""
    Generate a comprehensive checklist for your regulatory submission.
    """)

    col1, col2 = st.columns(2)

    with col1:
        device_class = st.selectbox(
            "Device Class",
            ["I", "II", "III", "IV"],
            index=1,
        )
        device_name = st.text_input("Device Name")
        device_description = st.text_area("Device Description", height=100)

    with col2:
        intended_use = st.text_area("Intended Use", height=100)
        is_software = st.checkbox("Software Device (SaMD)")
        include_optional = st.checkbox("Include Optional Items", value=True)

    if st.button("Generate Checklist", type="primary"):
        if not device_name:
            st.error("Please enter a device name")
        else:
            with st.spinner("Generating checklist..."):
                try:
                    from src.core.models import DeviceClass, DeviceInfo, ClassificationResult
                    from src.core.checklist import generate_checklist

                    class_map = {
                        "I": DeviceClass.CLASS_I,
                        "II": DeviceClass.CLASS_II,
                        "III": DeviceClass.CLASS_III,
                        "IV": DeviceClass.CLASS_IV,
                    }

                    classification = ClassificationResult(
                        device_class=class_map[device_class],
                        rationale="User selection",
                        is_samd=is_software,
                    )

                    device_info = DeviceInfo(
                        name=device_name,
                        description=device_description or "Device",
                        intended_use=intended_use or "General use",
                        is_software=is_software,
                        manufacturer_name="Manufacturer",
                    )

                    checklist = generate_checklist(classification, device_info, include_optional)
                    st.session_state.checklist = checklist

                    # Display checklist
                    st.success(f"Generated checklist with {checklist.total_items} items")

                    # Group by category
                    categories = {}
                    for item in checklist.items:
                        if item.category not in categories:
                            categories[item.category] = []
                        categories[item.category].append(item)

                    for category, items in categories.items():
                        st.subheader(f"📁 {category}")
                        for item in items:
                            required_badge = "🔴 Required" if item.required else "🟡 Optional"
                            with st.expander(f"{item.title} ({required_badge})"):
                                st.markdown(item.description)
                                if item.guidance_reference:
                                    st.info(f"Reference: {item.guidance_reference}")
                                if item.form_number:
                                    st.info(f"Form: {item.form_number}")

                    # Export button
                    from src.core.checklist import checklist_manager
                    md_export = checklist_manager.export_checklist(checklist, "markdown")
                    st.download_button(
                        "📥 Download Checklist (Markdown)",
                        md_export,
                        file_name="regulatory_checklist.md",
                        mime="text/markdown",
                    )

                except Exception as e:
                    st.error(f"Failed to generate checklist: {str(e)}")


def render_search_page():
    """Render the document search interface."""
    st.header("🔍 Document Search")

    st.markdown("""
    Search Health Canada regulatory documents and guidance.
    """)

    query = st.text_input("Search Query", placeholder="e.g., SaMD classification requirements")

    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox(
            "Filter by Category",
            [None, "regulation", "guidance", "standard", "form"],
            format_func=lambda x: "All Categories" if x is None else x.title(),
        )
    with col2:
        top_k = st.slider("Number of Results", 1, 10, 5)

    if st.button("Search", type="primary"):
        if not query:
            st.error("Please enter a search query")
        else:
            with st.spinner("Searching..."):
                try:
                    from src.retrieval.retriever import retrieve

                    results = retrieve(
                        query=query,
                        top_k=top_k,
                        filter_category=category,
                    )

                    if not results:
                        st.warning("No results found. Try a different query or ingest documents first.")
                    else:
                        st.success(f"Found {len(results)} results")

                        for i, result in enumerate(results, 1):
                            with st.expander(f"**Result {i}** (Score: {result.score:.2f})"):
                                st.markdown(result.content)
                                st.caption(f"Source: {result.source}")

                except Exception as e:
                    st.error(f"Search failed: {str(e)}")


if __name__ == "__main__":
    main()
