"""
Device Classification Engine

Implements Health Canada medical device classification rules based on:
- Medical Devices Regulations SOR/98-282 Schedule 1
- IMDRF SaMD Classification Framework (N12)
- Health Canada SaMD guidance documents
"""

from typing import Optional, Tuple

from src.core.models import (
    DeviceClass,
    DeviceInfo,
    SaMDInfo,
    SaMDCategory,
    HealthcareSituation,
    ClassificationResult,
)


# IMDRF SaMD Classification Matrix
# Rows: Healthcare Situation (Critical, Serious, Non-serious)
# Cols: Significance (Treat/Diagnose, Drive, Inform)
SAMD_CLASSIFICATION_MATRIX = {
    (HealthcareSituation.CRITICAL, SaMDCategory.TREAT): DeviceClass.CLASS_IV,
    (HealthcareSituation.CRITICAL, SaMDCategory.DIAGNOSE): DeviceClass.CLASS_IV,
    (HealthcareSituation.CRITICAL, SaMDCategory.DRIVE): DeviceClass.CLASS_III,
    (HealthcareSituation.CRITICAL, SaMDCategory.INFORM): DeviceClass.CLASS_II,
    (HealthcareSituation.SERIOUS, SaMDCategory.TREAT): DeviceClass.CLASS_IV,
    (HealthcareSituation.SERIOUS, SaMDCategory.DIAGNOSE): DeviceClass.CLASS_III,
    (HealthcareSituation.SERIOUS, SaMDCategory.DRIVE): DeviceClass.CLASS_II,
    (HealthcareSituation.SERIOUS, SaMDCategory.INFORM): DeviceClass.CLASS_II,
    (HealthcareSituation.NON_SERIOUS, SaMDCategory.TREAT): DeviceClass.CLASS_III,
    (HealthcareSituation.NON_SERIOUS, SaMDCategory.DIAGNOSE): DeviceClass.CLASS_II,
    (HealthcareSituation.NON_SERIOUS, SaMDCategory.DRIVE): DeviceClass.CLASS_II,
    (HealthcareSituation.NON_SERIOUS, SaMDCategory.INFORM): DeviceClass.CLASS_I,
}


class ClassificationEngine:
    """
    Medical device classification engine implementing Health Canada rules.

    This engine determines the device class (I, II, III, or IV) based on:
    1. Device characteristics (invasiveness, duration, active/passive)
    2. Intended use and target population
    3. For SaMD: IMDRF classification framework
    """

    def classify_device(
        self,
        device_info: DeviceInfo,
        samd_info: Optional[SaMDInfo] = None,
    ) -> ClassificationResult:
        """
        Classify a medical device according to Health Canada regulations.

        Args:
            device_info: Basic device information
            samd_info: Additional SaMD information (required if device_info.is_software=True)

        Returns:
            ClassificationResult with device class and rationale
        """
        # Check if SaMD classification applies
        if device_info.is_software:
            if samd_info is None:
                return ClassificationResult(
                    device_class=DeviceClass.CLASS_II,  # Default conservative
                    classification_rules=["SaMD Classification Required"],
                    rationale="Device is software-based. Additional SaMD information needed for precise classification.",
                    is_samd=True,
                    confidence=0.5,
                    warnings=["Please provide SaMD-specific information for accurate classification"],
                )
            return self._classify_samd(device_info, samd_info)

        # Non-software device classification using Schedule 1 rules
        return self._classify_traditional_device(device_info)

    def _classify_samd(
        self,
        device_info: DeviceInfo,
        samd_info: SaMDInfo,
    ) -> ClassificationResult:
        """Classify Software as Medical Device using IMDRF framework."""

        # Look up classification in matrix
        key = (samd_info.healthcare_situation, samd_info.significance)
        device_class = SAMD_CLASSIFICATION_MATRIX.get(key, DeviceClass.CLASS_II)

        # Build rationale
        rationale_parts = [
            f"SaMD Classification based on IMDRF N12 framework:",
            f"- Healthcare situation: {samd_info.healthcare_situation.value}",
            f"- Significance of information: {samd_info.significance.value}",
            f"- Matrix result: Class {device_class.value}",
        ]

        warnings = []
        references = [
            "IMDRF/SaMD WG/N12FINAL:2014",
            "Health Canada: Software as a Medical Device (SaMD): Definition and Classification",
        ]

        # Check for ML/AI considerations
        if samd_info.uses_ml:
            if not samd_info.is_locked:
                warnings.append(
                    "Adaptive/learning ML algorithms may require Predetermined Change Control Plan (PCCP)"
                )
                references.append(
                    "Health Canada: Pre-market guidance for machine learning-enabled medical devices"
                )
            rationale_parts.append(
                f"- ML-enabled: Yes ({'Adaptive' if not samd_info.is_locked else 'Locked algorithm'})"
            )

        # Clinical validation note
        if samd_info.clinical_validation_patients:
            rationale_parts.append(
                f"- Clinical validation: {samd_info.clinical_validation_patients} patients"
            )
            if samd_info.clinical_validation_patients < 100:
                warnings.append(
                    "Clinical validation sample size may be insufficient for Class III/IV devices"
                )

        return ClassificationResult(
            device_class=device_class,
            classification_rules=[
                f"IMDRF SaMD Matrix: {samd_info.healthcare_situation.value} x {samd_info.significance.value}"
            ],
            rationale="\n".join(rationale_parts),
            is_samd=True,
            samd_category=f"{samd_info.significance.value}/{samd_info.healthcare_situation.value}",
            confidence=0.9,
            warnings=warnings,
            references=references,
        )

    def _classify_traditional_device(
        self,
        device_info: DeviceInfo,
    ) -> ClassificationResult:
        """
        Classify non-software medical device using Schedule 1 rules.

        This implements a simplified rule-based classification. In production,
        this would be augmented with LLM-based reasoning for complex cases.
        """

        rules_applied = []
        rationale_parts = []
        warnings = []
        references = ["Medical Devices Regulations SOR/98-282, Schedule 1"]

        # IVD devices have specific rules
        if device_info.is_ivd:
            device_class, ivd_rules, ivd_rationale = self._classify_ivd(device_info)
            rules_applied.extend(ivd_rules)
            rationale_parts.append(ivd_rationale)
            return ClassificationResult(
                device_class=device_class,
                classification_rules=rules_applied,
                rationale="\n".join(rationale_parts),
                is_samd=False,
                confidence=0.85,
                warnings=warnings,
                references=references,
            )

        # Class IV: Highest risk - implantables, life-sustaining
        if device_info.is_implantable:
            if device_info.contact_duration == "long-term":
                rules_applied.append("Schedule 1, Rule 8 (Long-term implantable)")
                rationale_parts.append("Long-term implantable device - highest risk category")
                return ClassificationResult(
                    device_class=DeviceClass.CLASS_IV,
                    classification_rules=rules_applied,
                    rationale="\n".join(rationale_parts),
                    is_samd=False,
                    confidence=0.9,
                    references=references,
                )

        # Class III: Moderate-high risk
        if device_info.is_implantable or device_info.invasive_type == "surgical":
            rules_applied.append("Schedule 1, Rule 7 (Surgically invasive, short-term)")
            rationale_parts.append("Surgically invasive device - moderate-high risk")
            return ClassificationResult(
                device_class=DeviceClass.CLASS_III,
                classification_rules=rules_applied,
                rationale="\n".join(rationale_parts),
                is_samd=False,
                confidence=0.85,
                references=references,
            )

        # Class II: Low-moderate risk - most active devices, body orifice invasive
        if device_info.is_active or device_info.invasive_type == "body orifice":
            rules_applied.append("Schedule 1, Rule 9-11 (Active devices)")
            rationale_parts.append("Active or body orifice invasive device - low-moderate risk")
            return ClassificationResult(
                device_class=DeviceClass.CLASS_II,
                classification_rules=rules_applied,
                rationale="\n".join(rationale_parts),
                is_samd=False,
                confidence=0.8,
                warnings=["Classification may vary based on specific intended use"],
                references=references,
            )

        # Class I: Lowest risk - non-invasive, non-active
        rules_applied.append("Schedule 1, Rule 1-4 (Non-invasive devices)")
        rationale_parts.append("Non-invasive, non-active device - lowest risk category")

        return ClassificationResult(
            device_class=DeviceClass.CLASS_I,
            classification_rules=rules_applied,
            rationale="\n".join(rationale_parts),
            is_samd=False,
            confidence=0.75,
            warnings=["Verify classification against specific Schedule 1 rules for your device type"],
            references=references,
        )

    def _classify_ivd(
        self,
        device_info: DeviceInfo,
    ) -> Tuple[DeviceClass, list, str]:
        """Classify In-Vitro Diagnostic devices."""

        # Simplified IVD classification
        # In production, this would check specific analytes, specimen types, etc.

        intended_use_lower = device_info.intended_use.lower()

        # Class IV IVDs: Blood screening, high-risk transmissible diseases
        if any(term in intended_use_lower for term in ["hiv", "hepatitis", "blood screening", "transfusion"]):
            return (
                DeviceClass.CLASS_IV,
                ["Schedule 1, Rule 15 (High-risk IVD)"],
                "IVD for blood screening or high-risk transmissible disease detection",
            )

        # Class III IVDs: Moderate risk diagnostics
        if any(term in intended_use_lower for term in ["cancer", "genetic", "prenatal", "companion diagnostic"]):
            return (
                DeviceClass.CLASS_III,
                ["Schedule 1, Rule 14 (Moderate-risk IVD)"],
                "IVD for cancer, genetic, or prenatal testing",
            )

        # Class II IVDs: Low-moderate risk
        if any(term in intended_use_lower for term in ["glucose", "cholesterol", "self-testing"]):
            return (
                DeviceClass.CLASS_II,
                ["Schedule 1, Rule 13 (Self-testing IVD)"],
                "IVD for self-testing or common analytes",
            )

        # Default Class II for unspecified IVDs
        return (
            DeviceClass.CLASS_II,
            ["Schedule 1, Rule 13 (General IVD)"],
            "General in-vitro diagnostic device",
        )


# Singleton instance for convenience
classification_engine = ClassificationEngine()


def classify_device(
    device_info: DeviceInfo,
    samd_info: Optional[SaMDInfo] = None,
) -> ClassificationResult:
    """Convenience function for device classification."""
    return classification_engine.classify_device(device_info, samd_info)
