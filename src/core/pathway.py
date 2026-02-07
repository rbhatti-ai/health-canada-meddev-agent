"""
Regulatory Pathway Advisor

Determines the correct regulatory pathway and generates timelines,
fee calculations, and step-by-step guidance for Health Canada submissions.
"""

from datetime import date, timedelta

from src.core.models import (
    ClassificationResult,
    DeviceClass,
    DeviceInfo,
    FeeBreakdown,
    PathwayStep,
    RegulatoryPathway,
    Timeline,
)

# Health Canada Fee Schedule (as of April 2024)
# Reference: https://www.canada.ca/en/health-canada/services/drugs-health-products/medical-devices/fees
FEES_2024 = {
    "mdel_application": 4590,  # MDEL new application
    "mdel_amendment": 384,  # MDEL amendment
    "mdl_class_ii": 468,  # MDL Class II
    "mdl_class_iii": 7658,  # MDL Class III
    "mdl_class_iv": 23130,  # MDL Class IV
    "mdl_amendment_admin": 384,  # Administrative amendment
    "mdl_amendment_significant": 7658,  # Significant change
    "annual_right_to_sell_ii": 0,  # No annual fee Class II
    "annual_right_to_sell_iii": 831,  # Annual fee Class III
    "annual_right_to_sell_iv": 1662,  # Annual fee Class IV
}

# Review timelines in calendar days
REVIEW_TIMELINES = {
    DeviceClass.CLASS_I: {"min": 0, "max": 0},  # No MDL required
    DeviceClass.CLASS_II: {"min": 15, "max": 30},
    DeviceClass.CLASS_III: {"min": 75, "max": 120},
    DeviceClass.CLASS_IV: {"min": 90, "max": 180},
}

# MDEL processing time
MDEL_TIMELINE = {"min": 30, "max": 60}  # 4-8 weeks


class PathwayAdvisor:
    """
    Regulatory pathway advisor for Health Canada medical device submissions.

    Provides:
    - Complete pathway determination
    - Step-by-step guidance
    - Timeline calculations
    - Fee estimates
    """

    def get_pathway(
        self,
        classification: ClassificationResult,
        device_info: DeviceInfo,
        has_mdel: bool = False,
        has_qms_certificate: bool = False,
    ) -> RegulatoryPathway:
        """
        Determine the complete regulatory pathway for a device.

        Args:
            classification: Device classification result
            device_info: Device information
            has_mdel: Whether manufacturer already has MDEL
            has_qms_certificate: Whether manufacturer has ISO 13485 certificate

        Returns:
            Complete regulatory pathway with steps, timeline, and fees
        """
        device_class = classification.device_class
        steps = []
        step_num = 1
        total_days_min = 0
        total_days_max = 0

        # Step 1: MDEL (if not already held)
        if not has_mdel:
            steps.append(
                PathwayStep(
                    step_number=step_num,
                    name="Obtain Medical Device Establishment Licence (MDEL)",
                    description=(
                        "Apply for MDEL using form FRM-0292. Required for any entity that "
                        "imports or sells medical devices in Canada. MDEL must be obtained "
                        "BEFORE applying for MDL."
                    ),
                    required=True,
                    estimated_duration_days=45,
                    dependencies=[],
                    documents_required=[
                        "Completed FRM-0292 form",
                        "Quality Management System procedures (if applicable)",
                        "Site Master File (for Class II-IV distributors)",
                        "Canadian importer information",
                    ],
                    forms=["FRM-0292"],
                    fees=FEES_2024["mdel_application"],
                )
            )
            total_days_min += MDEL_TIMELINE["min"]
            total_days_max += MDEL_TIMELINE["max"]
            step_num += 1

        # Step 2: QMS Certificate (for Class II-IV)
        if device_class != DeviceClass.CLASS_I and not has_qms_certificate:
            steps.append(
                PathwayStep(
                    step_number=step_num,
                    name="Obtain ISO 13485 QMS Certificate",
                    description=(
                        "Obtain quality management system certification to ISO 13485:2016 "
                        "from a Health Canada recognized registrar. Certificate must cover "
                        "the device types being licensed."
                    ),
                    required=True,
                    estimated_duration_days=90,  # Can be done in parallel
                    dependencies=[],
                    documents_required=[
                        "ISO 13485:2016 QMS implementation",
                        "MDSAP audit (recommended)",
                        "Design and development procedures",
                        "Risk management file (ISO 14971)",
                    ],
                    forms=[],
                    fees=None,  # Third-party cost, varies
                )
            )
            step_num += 1

        # Step 3: Clinical Evidence (for Class III-IV and some Class II)
        if device_class in [DeviceClass.CLASS_III, DeviceClass.CLASS_IV]:
            steps.append(
                PathwayStep(
                    step_number=step_num,
                    name="Prepare Clinical Evidence",
                    description=(
                        "Compile clinical evidence demonstrating safety and effectiveness. "
                        "May include clinical trials, literature reviews, predicate device "
                        "comparisons, or real-world evidence."
                    ),
                    required=True,
                    estimated_duration_days=180,  # Highly variable
                    dependencies=[],
                    documents_required=[
                        "Clinical evaluation report",
                        "Clinical investigation data (if applicable)",
                        "Literature review",
                        "Risk-benefit analysis",
                    ],
                    forms=[],
                    fees=None,
                )
            )
            step_num += 1

        # Step 4: Cybersecurity (for software devices)
        if device_info.is_software:
            steps.append(
                PathwayStep(
                    step_number=step_num,
                    name="Cybersecurity Documentation",
                    description=(
                        "Prepare cybersecurity documentation per Health Canada guidance. "
                        "Includes threat modeling, security controls, and SBOM."
                    ),
                    required=True,
                    estimated_duration_days=30,
                    dependencies=[],
                    documents_required=[
                        "Cybersecurity risk assessment",
                        "Software Bill of Materials (SBOM)",
                        "IEC 62304 software lifecycle documentation",
                        "Vulnerability management plan",
                    ],
                    forms=[],
                    fees=None,
                )
            )
            step_num += 1

        # Step 5: MDL Application (for Class II-IV)
        if device_class.requires_mdl:
            mdl_fee = self._get_mdl_fee(device_class)
            form_name = self._get_mdl_form(device_class)

            steps.append(
                PathwayStep(
                    step_number=step_num,
                    name=f"Submit MDL Application (Class {device_class.value})",
                    description=(
                        f"Submit Medical Device Licence application for Class {device_class.value} "
                        f"device. Standard review time is {device_class.review_days} calendar days. "
                        "Application must follow IMDRF Table of Contents format."
                    ),
                    required=True,
                    estimated_duration_days=device_class.review_days,
                    dependencies=[s.step_number for s in steps],  # Depends on all previous
                    documents_required=[
                        "Completed application form",
                        "Device description and specifications",
                        "Intended use statement",
                        "Manufacturing information",
                        "Quality system certificate",
                        "Labelling (including IFU)",
                        "Risk analysis (ISO 14971)",
                        "Biocompatibility (if applicable)",
                        "Sterilization validation (if applicable)",
                        "Clinical evidence",
                    ],
                    forms=[form_name],
                    fees=mdl_fee,
                )
            )
            review_times = REVIEW_TIMELINES[device_class]
            total_days_min += review_times["min"]
            total_days_max += review_times["max"]
            step_num += 1

        # Calculate fees
        fees = self._calculate_fees(device_class, has_mdel)

        # Build timeline
        timeline = Timeline(
            total_days_min=total_days_min,
            total_days_max=total_days_max,
            critical_path=[step.name for step in steps if step.required],
            start_date=date.today(),
            target_completion=date.today() + timedelta(days=total_days_max),
            milestones=self._generate_milestones(steps, date.today()),
        )

        # Determine special requirements
        special_requirements = self._get_special_requirements(
            device_class, device_info, classification
        )

        return RegulatoryPathway(
            pathway_name=f"Class {device_class.value} MDL Pathway",
            device_class=device_class,
            requires_mdel=not has_mdel,
            requires_mdl=device_class.requires_mdl,
            steps=steps,
            timeline=timeline,
            fees=fees,
            special_requirements=special_requirements,
        )

    def _get_mdl_fee(self, device_class: DeviceClass) -> float:
        """Get MDL application fee for device class."""
        fee_map = {
            DeviceClass.CLASS_II: FEES_2024["mdl_class_ii"],
            DeviceClass.CLASS_III: FEES_2024["mdl_class_iii"],
            DeviceClass.CLASS_IV: FEES_2024["mdl_class_iv"],
        }
        return fee_map.get(device_class, 0)

    def _get_mdl_form(self, device_class: DeviceClass) -> str:
        """Get appropriate MDL application form."""
        if device_class == DeviceClass.CLASS_II:
            return "FRM-0077 (Class II)"
        elif device_class == DeviceClass.CLASS_III:
            return "FRM-0078 (Class III)"
        else:
            return "FRM-0079 (Class IV)"

    def _calculate_fees(
        self,
        device_class: DeviceClass,
        has_mdel: bool,
    ) -> FeeBreakdown:
        """Calculate total regulatory fees."""

        mdel_fee = 0 if has_mdel else FEES_2024["mdel_application"]
        mdl_fee = self._get_mdl_fee(device_class)

        annual_fee_map = {
            DeviceClass.CLASS_I: 0,
            DeviceClass.CLASS_II: FEES_2024["annual_right_to_sell_ii"],
            DeviceClass.CLASS_III: FEES_2024["annual_right_to_sell_iii"],
            DeviceClass.CLASS_IV: FEES_2024["annual_right_to_sell_iv"],
        }
        annual_fee = annual_fee_map.get(device_class, 0)

        total = mdel_fee + mdl_fee

        notes = []
        if mdel_fee > 0:
            notes.append("MDEL fee is one-time; renewal is automatic if compliant")
        if annual_fee > 0:
            notes.append(f"Annual right-to-sell fee of ${annual_fee:,.2f} CAD applies")
        notes.append("Fees subject to change; verify current fee schedule with Health Canada")

        return FeeBreakdown(
            mdel_fee=mdel_fee,
            mdl_fee=mdl_fee,
            annual_fee=annual_fee,
            amendment_fees=0,
            total=total,
            currency="CAD",
            fee_schedule_date="2024-04-01",
            notes=notes,
        )

    def _generate_milestones(
        self,
        steps: list[PathwayStep],
        start_date: date,
    ) -> dict:
        """Generate milestone dates based on steps."""
        milestones = {}
        current_date = start_date

        for step in steps:
            if step.estimated_duration_days:
                milestone_date = current_date + timedelta(days=step.estimated_duration_days)
                milestones[step.name] = milestone_date
                # Only advance date for sequential steps
                if step.required:
                    current_date = milestone_date

        return milestones

    def _get_special_requirements(
        self,
        device_class: DeviceClass,
        device_info: DeviceInfo,
        classification: ClassificationResult,
    ) -> list[str]:
        """Determine special requirements based on device characteristics."""
        requirements = []

        if device_info.is_software and classification.is_samd:
            requirements.append(
                "SaMD-specific documentation required per Health Canada SaMD guidance"
            )

        if device_info.is_software and "ml" in device_info.description.lower():
            requirements.append(
                "Machine learning devices may require Predetermined Change Control Plan (PCCP)"
            )

        if device_info.is_ivd:
            requirements.append("IVD-specific requirements apply (analytical/clinical performance)")

        if device_info.is_implantable:
            requirements.append("Biocompatibility testing per ISO 10993 required")

        if device_class == DeviceClass.CLASS_IV:
            requirements.append("Pre-submission meeting with Health Canada recommended")

        return requirements


# Singleton instance
pathway_advisor = PathwayAdvisor()


def get_pathway(
    classification: ClassificationResult,
    device_info: DeviceInfo,
    has_mdel: bool = False,
    has_qms_certificate: bool = False,
) -> RegulatoryPathway:
    """Convenience function to get regulatory pathway."""
    return pathway_advisor.get_pathway(classification, device_info, has_mdel, has_qms_certificate)
