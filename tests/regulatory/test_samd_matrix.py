"""
Tests for IMDRF SaMD Classification Matrix accuracy.

Verifies that the implementation matches the official IMDRF N12
SaMD classification framework.

Reference: IMDRF/SaMD WG/N12FINAL:2014 - "Software as a Medical Device":
Possible Framework for Risk Categorization and Corresponding Considerations
"""

import pytest

from src.core.classification import SAMD_CLASSIFICATION_MATRIX
from src.core.models import DeviceClass, HealthcareSituation, SaMDCategory


@pytest.mark.regulatory
class TestIMDRFMatrix:
    """
    Test the complete IMDRF N12 classification matrix.

    Matrix Structure:
                    | Treat/Diagnose | Drive | Inform
    Critical        |     IV         |  III  |   II
    Serious         |   IV/III       |   II  |   II
    Non-serious     |     III        |   II  |    I
    """

    # Row 1: Critical Healthcare Situation
    def test_critical_treat_class_iv(self):
        """Critical + Treat = Class IV."""
        key = (HealthcareSituation.CRITICAL, SaMDCategory.TREAT)
        assert SAMD_CLASSIFICATION_MATRIX[key] == DeviceClass.CLASS_IV

    def test_critical_diagnose_class_iv(self):
        """Critical + Diagnose = Class IV."""
        key = (HealthcareSituation.CRITICAL, SaMDCategory.DIAGNOSE)
        assert SAMD_CLASSIFICATION_MATRIX[key] == DeviceClass.CLASS_IV

    def test_critical_drive_class_iii(self):
        """Critical + Drive = Class III."""
        key = (HealthcareSituation.CRITICAL, SaMDCategory.DRIVE)
        assert SAMD_CLASSIFICATION_MATRIX[key] == DeviceClass.CLASS_III

    def test_critical_inform_class_ii(self):
        """Critical + Inform = Class II."""
        key = (HealthcareSituation.CRITICAL, SaMDCategory.INFORM)
        assert SAMD_CLASSIFICATION_MATRIX[key] == DeviceClass.CLASS_II

    # Row 2: Serious Healthcare Situation
    def test_serious_treat_class_iv(self):
        """Serious + Treat = Class IV."""
        key = (HealthcareSituation.SERIOUS, SaMDCategory.TREAT)
        assert SAMD_CLASSIFICATION_MATRIX[key] == DeviceClass.CLASS_IV

    def test_serious_diagnose_class_iii(self):
        """Serious + Diagnose = Class III."""
        key = (HealthcareSituation.SERIOUS, SaMDCategory.DIAGNOSE)
        assert SAMD_CLASSIFICATION_MATRIX[key] == DeviceClass.CLASS_III

    def test_serious_drive_class_ii(self):
        """Serious + Drive = Class II."""
        key = (HealthcareSituation.SERIOUS, SaMDCategory.DRIVE)
        assert SAMD_CLASSIFICATION_MATRIX[key] == DeviceClass.CLASS_II

    def test_serious_inform_class_ii(self):
        """Serious + Inform = Class II."""
        key = (HealthcareSituation.SERIOUS, SaMDCategory.INFORM)
        assert SAMD_CLASSIFICATION_MATRIX[key] == DeviceClass.CLASS_II

    # Row 3: Non-Serious Healthcare Situation
    def test_non_serious_treat_class_iii(self):
        """Non-Serious + Treat = Class III."""
        key = (HealthcareSituation.NON_SERIOUS, SaMDCategory.TREAT)
        assert SAMD_CLASSIFICATION_MATRIX[key] == DeviceClass.CLASS_III

    def test_non_serious_diagnose_class_ii(self):
        """Non-Serious + Diagnose = Class II."""
        key = (HealthcareSituation.NON_SERIOUS, SaMDCategory.DIAGNOSE)
        assert SAMD_CLASSIFICATION_MATRIX[key] == DeviceClass.CLASS_II

    def test_non_serious_drive_class_ii(self):
        """Non-Serious + Drive = Class II."""
        key = (HealthcareSituation.NON_SERIOUS, SaMDCategory.DRIVE)
        assert SAMD_CLASSIFICATION_MATRIX[key] == DeviceClass.CLASS_II

    def test_non_serious_inform_class_i(self):
        """Non-Serious + Inform = Class I (lowest)."""
        key = (HealthcareSituation.NON_SERIOUS, SaMDCategory.INFORM)
        assert SAMD_CLASSIFICATION_MATRIX[key] == DeviceClass.CLASS_I


@pytest.mark.regulatory
class TestMatrixCompleteness:
    """Verify the matrix covers all combinations."""

    def test_all_combinations_exist(self):
        """Matrix should have all 12 combinations (3 situations x 4 categories)."""
        expected_count = len(HealthcareSituation) * len(SaMDCategory)
        assert len(SAMD_CLASSIFICATION_MATRIX) == expected_count

    def test_all_healthcare_situations_covered(self):
        """All healthcare situations should be represented."""
        situations_in_matrix = {key[0] for key in SAMD_CLASSIFICATION_MATRIX}
        all_situations = set(HealthcareSituation)
        assert situations_in_matrix == all_situations

    def test_all_samd_categories_covered(self):
        """All SaMD categories should be represented."""
        categories_in_matrix = {key[1] for key in SAMD_CLASSIFICATION_MATRIX}
        all_categories = set(SaMDCategory)
        assert categories_in_matrix == all_categories


@pytest.mark.regulatory
class TestMatrixLogic:
    """Verify the matrix follows expected regulatory logic."""

    def test_critical_never_class_i(self):
        """Critical situations should never result in Class I."""
        for key, value in SAMD_CLASSIFICATION_MATRIX.items():
            situation, _ = key
            if situation == HealthcareSituation.CRITICAL:
                assert value != DeviceClass.CLASS_I

    def test_treat_never_class_i_or_ii(self):
        """Treat significance should never result in Class I or II."""
        for key, value in SAMD_CLASSIFICATION_MATRIX.items():
            _, category = key
            if category == SaMDCategory.TREAT:
                assert value not in [DeviceClass.CLASS_I, DeviceClass.CLASS_II]

    def test_inform_never_class_iv(self):
        """Inform significance should never result in Class IV."""
        for key, value in SAMD_CLASSIFICATION_MATRIX.items():
            _, category = key
            if category == SaMDCategory.INFORM:
                assert value != DeviceClass.CLASS_IV

    def test_class_i_only_lowest_risk(self):
        """Class I should only occur for Non-Serious + Inform."""
        class_i_keys = [
            k for k, v in SAMD_CLASSIFICATION_MATRIX.items() if v == DeviceClass.CLASS_I
        ]
        assert len(class_i_keys) == 1
        assert class_i_keys[0] == (HealthcareSituation.NON_SERIOUS, SaMDCategory.INFORM)
