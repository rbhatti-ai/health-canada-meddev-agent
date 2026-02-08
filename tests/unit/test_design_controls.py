"""
Unit tests for Design Controls — ISO 13485 Section 7.3.

Tests for:
- DesignInput model (7.3.2)
- DesignOutput model (7.3.3)
- DesignReview model (7.3.5)
- DesignVerification model (7.3.6)
- DesignValidation model (7.3.7)
- DesignChange model (7.3.9)
- DesignControlService operations

Citation: [ISO 13485:2016, 7.3]
"""

from datetime import date, datetime
from uuid import uuid4

import pytest

from src.core.design_controls import (
    DesignChange,
    DesignControlService,
    DesignHistoryRecord,
    DesignInput,
    DesignOutput,
    DesignReview,
    DesignValidation,
    DesignVerification,
    get_design_control_service,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def org_id():
    """Generate test organization ID."""
    return uuid4()


@pytest.fixture
def device_version_id():
    """Generate test device version ID."""
    return uuid4()


@pytest.fixture
def design_service():
    """Fresh DesignControlService instance."""
    return DesignControlService()


# =============================================================================
# DesignInput Model Tests
# =============================================================================


@pytest.mark.unit
class TestDesignInputModel:
    """Tests for DesignInput Pydantic model."""

    def test_create_minimal_input(self, org_id, device_version_id):
        """DesignInput with required fields should be valid."""
        input_data = DesignInput(
            organization_id=org_id,
            device_version_id=device_version_id,
            source="user_need",
            title="Easy to use interface",
            description="Users require an intuitive interface",
        )
        assert input_data.source == "user_need"
        assert input_data.priority == "essential"  # default
        assert input_data.status == "active"  # default

    def test_input_with_all_fields(self, org_id, device_version_id):
        """DesignInput with all optional fields."""
        input_data = DesignInput(
            id=uuid4(),
            organization_id=org_id,
            device_version_id=device_version_id,
            source="regulatory",
            priority="essential",
            input_type="safety",
            title="Electrical safety",
            description="Device must meet IEC 60601-1",
            rationale="Required for CE marking",
            acceptance_criteria="Pass IEC 60601-1 testing",
            regulatory_reference="SOR-98-282-S10",
            standard_reference="IEC-60601-1",
            source_document="DOC-001",
            version=2,
            metadata={"category": "safety"},
        )
        assert input_data.priority == "essential"
        assert input_data.regulatory_reference == "SOR-98-282-S10"
        assert input_data.metadata["category"] == "safety"

    def test_input_source_types(self, org_id, device_version_id):
        """All valid source types should be accepted."""
        sources = [
            "user_need",
            "clinical_feedback",
            "regulatory",
            "standard",
            "competitive",
            "risk_analysis",
        ]
        for source in sources:
            input_data = DesignInput(
                organization_id=org_id,
                device_version_id=device_version_id,
                source=source,
                title="Test",
                description="Test",
            )
            assert input_data.source == source

    def test_input_priority_types(self, org_id, device_version_id):
        """All valid priority levels should be accepted."""
        priorities = ["essential", "desired", "nice_to_have"]
        for priority in priorities:
            input_data = DesignInput(
                organization_id=org_id,
                device_version_id=device_version_id,
                source="user_need",
                priority=priority,
                title="Test",
                description="Test",
            )
            assert input_data.priority == priority


# =============================================================================
# DesignOutput Model Tests
# =============================================================================


@pytest.mark.unit
class TestDesignOutputModel:
    """Tests for DesignOutput Pydantic model."""

    def test_create_minimal_output(self, org_id, device_version_id):
        """DesignOutput with required fields should be valid."""
        output = DesignOutput(
            organization_id=org_id,
            device_version_id=device_version_id,
            output_type="specification",
            title="Interface Specification",
            specification="UI shall have max 3 clicks to any function",
            acceptance_criteria="Verify click count in usability testing",
        )
        assert output.output_type == "specification"
        assert output.status == "draft"  # default

    def test_output_with_linked_input(self, org_id, device_version_id):
        """DesignOutput can link to a design input."""
        input_id = uuid4()
        output = DesignOutput(
            organization_id=org_id,
            device_version_id=device_version_id,
            design_input_id=input_id,
            output_type="specification",
            title="Test Spec",
            specification="Test content",
            acceptance_criteria="Test criteria",
        )
        assert output.design_input_id == input_id

    def test_output_type_values(self, org_id, device_version_id):
        """All valid output types should be accepted."""
        types = [
            "specification",
            "drawing",
            "procedure",
            "software_requirement",
            "test_method",
            "manufacturing_spec",
        ]
        for output_type in types:
            output = DesignOutput(
                organization_id=org_id,
                device_version_id=device_version_id,
                output_type=output_type,
                title="Test",
                specification="Test",
                acceptance_criteria="Test",
            )
            assert output.output_type == output_type

    def test_output_status_values(self, org_id, device_version_id):
        """All valid status values should be accepted."""
        statuses = ["draft", "reviewed", "approved", "released"]
        for status in statuses:
            output = DesignOutput(
                organization_id=org_id,
                device_version_id=device_version_id,
                output_type="specification",
                status=status,
                title="Test",
                specification="Test",
                acceptance_criteria="Test",
            )
            assert output.status == status

    def test_output_with_approval(self, org_id, device_version_id):
        """DesignOutput can have approval information."""
        output = DesignOutput(
            organization_id=org_id,
            device_version_id=device_version_id,
            output_type="specification",
            status="approved",
            title="Test",
            specification="Test",
            acceptance_criteria="Test",
            approved_by="John Doe",
            approved_at=datetime.utcnow(),
        )
        assert output.approved_by == "John Doe"
        assert output.approved_at is not None


# =============================================================================
# DesignReview Model Tests
# =============================================================================


@pytest.mark.unit
class TestDesignReviewModel:
    """Tests for DesignReview Pydantic model."""

    def test_create_minimal_review(self, org_id, device_version_id):
        """DesignReview with required fields should be valid."""
        review = DesignReview(
            organization_id=org_id,
            device_version_id=device_version_id,
            phase="development",
            review_date=date.today(),
            review_title="Development Review",
            decision="proceed",
        )
        assert review.phase == "development"
        assert review.decision == "proceed"

    def test_review_with_participants(self, org_id, device_version_id):
        """DesignReview can have multiple participants."""
        review = DesignReview(
            organization_id=org_id,
            device_version_id=device_version_id,
            phase="verification",
            review_date=date.today(),
            review_title="Verification Review",
            participants=["Alice", "Bob", "Charlie"],
            chairperson="Alice",
            decision="proceed",
        )
        assert len(review.participants) == 3
        assert review.chairperson == "Alice"

    def test_review_with_findings(self, org_id, device_version_id):
        """DesignReview can have findings and action items."""
        review = DesignReview(
            organization_id=org_id,
            device_version_id=device_version_id,
            phase="development",
            review_date=date.today(),
            review_title="Dev Review",
            findings=["Minor issue in spec A", "Clarification needed for B"],
            action_items=["Update spec A", "Clarify B with team"],
            decision="proceed_with_conditions",
            conditions=["Complete action items by next review"],
        )
        assert len(review.findings) == 2
        assert len(review.action_items) == 2
        assert review.decision == "proceed_with_conditions"

    def test_review_phase_values(self, org_id, device_version_id):
        """All valid design phases should be accepted."""
        phases = [
            "concept",
            "feasibility",
            "development",
            "verification",
            "validation",
            "transfer",
            "post_market",
        ]
        for phase in phases:
            review = DesignReview(
                organization_id=org_id,
                device_version_id=device_version_id,
                phase=phase,
                review_date=date.today(),
                review_title="Test Review",
                decision="proceed",
            )
            assert review.phase == phase

    def test_review_decision_values(self, org_id, device_version_id):
        """All valid decision values should be accepted."""
        decisions = ["proceed", "proceed_with_conditions", "repeat", "stop"]
        for decision in decisions:
            review = DesignReview(
                organization_id=org_id,
                device_version_id=device_version_id,
                phase="development",
                review_date=date.today(),
                review_title="Test Review",
                decision=decision,
            )
            assert review.decision == decision


# =============================================================================
# DesignVerification Model Tests
# =============================================================================


@pytest.mark.unit
class TestDesignVerificationModel:
    """Tests for DesignVerification Pydantic model."""

    def test_create_minimal_verification(self, org_id, device_version_id):
        """DesignVerification with required fields should be valid."""
        output_id = uuid4()
        verification = DesignVerification(
            organization_id=org_id,
            device_version_id=device_version_id,
            design_output_id=output_id,
            method="test",
            title="Button response test",
            description="Verify button responds within 100ms",
            acceptance_criteria="Response < 100ms",
            result="pass",
            actual_results="Average response: 45ms",
        )
        assert verification.method == "test"
        assert verification.result == "pass"

    def test_verification_methods(self, org_id, device_version_id):
        """All valid verification methods should be accepted."""
        methods = ["inspection", "analysis", "test", "demonstration"]
        output_id = uuid4()
        for method in methods:
            verification = DesignVerification(
                organization_id=org_id,
                device_version_id=device_version_id,
                design_output_id=output_id,
                method=method,
                title="Test",
                description="Test",
                acceptance_criteria="Test",
                result="pass",
                actual_results="Test",
            )
            assert verification.method == method

    def test_verification_results(self, org_id, device_version_id):
        """All valid result values should be accepted."""
        results = ["pass", "fail", "conditional"]
        output_id = uuid4()
        for result in results:
            verification = DesignVerification(
                organization_id=org_id,
                device_version_id=device_version_id,
                design_output_id=output_id,
                method="test",
                title="Test",
                description="Test",
                acceptance_criteria="Test",
                result=result,
                actual_results="Test",
            )
            assert verification.result == result

    def test_verification_with_deviations(self, org_id, device_version_id):
        """Verification can have deviations and still pass."""
        verification = DesignVerification(
            organization_id=org_id,
            device_version_id=device_version_id,
            design_output_id=uuid4(),
            method="test",
            title="Test",
            description="Test",
            acceptance_criteria="Test",
            result="pass",
            actual_results="Test",
            deviations=["Minor deviation noted"],
            pass_with_deviation=True,
        )
        assert len(verification.deviations) == 1
        assert verification.pass_with_deviation is True


# =============================================================================
# DesignValidation Model Tests
# =============================================================================


@pytest.mark.unit
class TestDesignValidationModel:
    """Tests for DesignValidation Pydantic model."""

    def test_create_minimal_validation(self, org_id, device_version_id):
        """DesignValidation with required fields should be valid."""
        validation = DesignValidation(
            organization_id=org_id,
            device_version_id=device_version_id,
            validation_type="usability",
            title="Usability Validation",
            description="Validate device is easy to use",
            acceptance_criteria="90% task completion rate",
            result="pass",
            actual_results="95% task completion achieved",
            conclusions="Device meets usability requirements",
        )
        assert validation.validation_type == "usability"
        assert validation.result == "pass"

    def test_validation_types(self, org_id, device_version_id):
        """All valid validation types should be accepted."""
        types = ["clinical", "usability", "simulated_use", "field"]
        for val_type in types:
            validation = DesignValidation(
                organization_id=org_id,
                device_version_id=device_version_id,
                validation_type=val_type,
                title="Test",
                description="Test",
                acceptance_criteria="Test",
                result="pass",
                actual_results="Test",
                conclusions="Test",
            )
            assert validation.validation_type == val_type

    def test_validation_with_sample_info(self, org_id, device_version_id):
        """Validation can include sample information."""
        validation = DesignValidation(
            organization_id=org_id,
            device_version_id=device_version_id,
            validation_type="clinical",
            title="Clinical Validation",
            description="Clinical trial",
            acceptance_criteria="Primary endpoint met",
            sample_description="Production representative units",
            sample_size=50,
            lot_batch_number="LOT-2026-001",
            result="pass",
            actual_results="All endpoints met",
            conclusions="Clinical validation successful",
        )
        assert validation.sample_size == 50
        assert validation.lot_batch_number == "LOT-2026-001"


# =============================================================================
# DesignChange Model Tests
# =============================================================================


@pytest.mark.unit
class TestDesignChangeModel:
    """Tests for DesignChange Pydantic model."""

    def test_create_minimal_change(self, org_id, device_version_id):
        """DesignChange with required fields should be valid."""
        change = DesignChange(
            organization_id=org_id,
            device_version_id=device_version_id,
            change_number="DCN-001",
            title="Update material specification",
            description="Change housing material from ABS to PC",
            rationale="Improved durability required",
            change_type="major",
            impact_assessment="Material change requires biocompatibility testing",
        )
        assert change.change_type == "major"
        assert change.status == "proposed"  # default

    def test_change_type_values(self, org_id, device_version_id):
        """All valid change types should be accepted."""
        types = ["major", "minor", "administrative"]
        for change_type in types:
            change = DesignChange(
                organization_id=org_id,
                device_version_id=device_version_id,
                change_number="DCN-001",
                title="Test",
                description="Test",
                rationale="Test",
                change_type=change_type,
                impact_assessment="Test",
            )
            assert change.change_type == change_type

    def test_change_with_regulatory_impact(self, org_id, device_version_id):
        """Change can specify regulatory impact."""
        change = DesignChange(
            organization_id=org_id,
            device_version_id=device_version_id,
            change_number="DCN-002",
            title="Major design change",
            description="Complete redesign",
            rationale="Customer feedback",
            change_type="major",
            impact_assessment="Significant impact",
            risk_impact="Re-evaluate risk analysis",
            regulatory_impact="Amendment submission required",
            verification_required=True,
            validation_required=True,
        )
        assert change.regulatory_impact == "Amendment submission required"
        assert change.validation_required is True


# =============================================================================
# DesignHistoryRecord Model Tests
# =============================================================================


@pytest.mark.unit
class TestDesignHistoryRecordModel:
    """Tests for DesignHistoryRecord Pydantic model."""

    def test_create_history_record(self, org_id, device_version_id):
        """DesignHistoryRecord with required fields should be valid."""
        record = DesignHistoryRecord(
            organization_id=org_id,
            device_version_id=device_version_id,
            record_type="input",
            record_id=uuid4(),
            record_date=date.today(),
            title="User need: Easy operation",
            summary="Captured user need for easy operation",
        )
        assert record.record_type == "input"
        assert record.status == "active"

    def test_history_record_types(self, org_id, device_version_id):
        """All valid record types should be accepted."""
        types = ["input", "output", "review", "verification", "validation", "change", "transfer"]
        for record_type in types:
            record = DesignHistoryRecord(
                organization_id=org_id,
                device_version_id=device_version_id,
                record_type=record_type,
                record_id=uuid4(),
                record_date=date.today(),
                title="Test",
                summary="Test",
            )
            assert record.record_type == record_type


# =============================================================================
# DesignControlService Tests
# =============================================================================


@pytest.mark.unit
class TestDesignControlServiceInputs:
    """Tests for DesignControlService input operations."""

    def test_create_input(self, design_service, org_id, device_version_id):
        """Service should create design input and assign ID."""
        input_data = DesignInput(
            organization_id=org_id,
            device_version_id=device_version_id,
            source="user_need",
            title="Test input",
            description="Test description",
        )
        created = design_service.create_input(input_data)
        assert created.id is not None
        assert created.created_at is not None

    def test_get_input(self, design_service, org_id, device_version_id):
        """Service should retrieve input by ID."""
        input_data = DesignInput(
            organization_id=org_id,
            device_version_id=device_version_id,
            source="regulatory",
            title="Test",
            description="Test",
        )
        created = design_service.create_input(input_data)
        retrieved = design_service.get_input(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_list_inputs(self, design_service, org_id, device_version_id):
        """Service should list all inputs for device version."""
        for i in range(3):
            input_data = DesignInput(
                organization_id=org_id,
                device_version_id=device_version_id,
                source="user_need",
                title=f"Input {i}",
                description="Test",
            )
            design_service.create_input(input_data)

        inputs = design_service.list_inputs(device_version_id)
        assert len(inputs) == 3

    def test_get_inputs_by_source(self, design_service, org_id, device_version_id):
        """Service should filter inputs by source."""
        design_service.create_input(
            DesignInput(
                organization_id=org_id,
                device_version_id=device_version_id,
                source="regulatory",
                title="Regulatory 1",
                description="Test",
            )
        )
        design_service.create_input(
            DesignInput(
                organization_id=org_id,
                device_version_id=device_version_id,
                source="user_need",
                title="User need 1",
                description="Test",
            )
        )
        design_service.create_input(
            DesignInput(
                organization_id=org_id,
                device_version_id=device_version_id,
                source="regulatory",
                title="Regulatory 2",
                description="Test",
            )
        )

        regulatory_inputs = design_service.get_inputs_by_source(device_version_id, "regulatory")
        assert len(regulatory_inputs) == 2

    def test_get_essential_inputs(self, design_service, org_id, device_version_id):
        """Service should filter essential priority inputs."""
        design_service.create_input(
            DesignInput(
                organization_id=org_id,
                device_version_id=device_version_id,
                source="user_need",
                priority="essential",
                title="Essential",
                description="Test",
            )
        )
        design_service.create_input(
            DesignInput(
                organization_id=org_id,
                device_version_id=device_version_id,
                source="user_need",
                priority="nice_to_have",
                title="Nice to have",
                description="Test",
            )
        )

        essential = design_service.get_essential_inputs(device_version_id)
        assert len(essential) == 1
        assert essential[0].title == "Essential"


@pytest.mark.unit
class TestDesignControlServiceOutputs:
    """Tests for DesignControlService output operations."""

    def test_create_output(self, design_service, org_id, device_version_id):
        """Service should create design output and assign ID."""
        output = DesignOutput(
            organization_id=org_id,
            device_version_id=device_version_id,
            output_type="specification",
            title="Test spec",
            specification="Test content",
            acceptance_criteria="Test criteria",
        )
        created = design_service.create_output(output)
        assert created.id is not None
        assert created.created_at is not None

    def test_get_outputs_for_input(self, design_service, org_id, device_version_id):
        """Service should get outputs linked to a specific input."""
        input_id = uuid4()
        design_service.create_output(
            DesignOutput(
                organization_id=org_id,
                device_version_id=device_version_id,
                design_input_id=input_id,
                output_type="specification",
                title="Spec 1",
                specification="Test",
                acceptance_criteria="Test",
            )
        )
        design_service.create_output(
            DesignOutput(
                organization_id=org_id,
                device_version_id=device_version_id,
                design_input_id=input_id,
                output_type="drawing",
                title="Drawing 1",
                specification="Test",
                acceptance_criteria="Test",
            )
        )
        design_service.create_output(
            DesignOutput(
                organization_id=org_id,
                device_version_id=device_version_id,
                design_input_id=uuid4(),  # Different input
                output_type="procedure",
                title="Procedure 1",
                specification="Test",
                acceptance_criteria="Test",
            )
        )

        outputs = design_service.get_outputs_for_input(input_id)
        assert len(outputs) == 2

    def test_get_approved_outputs(self, design_service, org_id, device_version_id):
        """Service should get only approved/released outputs."""
        design_service.create_output(
            DesignOutput(
                organization_id=org_id,
                device_version_id=device_version_id,
                output_type="specification",
                status="approved",
                title="Approved",
                specification="Test",
                acceptance_criteria="Test",
            )
        )
        design_service.create_output(
            DesignOutput(
                organization_id=org_id,
                device_version_id=device_version_id,
                output_type="specification",
                status="draft",
                title="Draft",
                specification="Test",
                acceptance_criteria="Test",
            )
        )
        design_service.create_output(
            DesignOutput(
                organization_id=org_id,
                device_version_id=device_version_id,
                output_type="specification",
                status="released",
                title="Released",
                specification="Test",
                acceptance_criteria="Test",
            )
        )

        approved = design_service.get_approved_outputs(device_version_id)
        assert len(approved) == 2


@pytest.mark.unit
class TestDesignControlServiceReviews:
    """Tests for DesignControlService review operations."""

    def test_create_review(self, design_service, org_id, device_version_id):
        """Service should create design review."""
        review = DesignReview(
            organization_id=org_id,
            device_version_id=device_version_id,
            phase="development",
            review_date=date.today(),
            review_title="Dev Review",
            decision="proceed",
        )
        created = design_service.create_review(review)
        assert created.id is not None

    def test_get_reviews_by_phase(self, design_service, org_id, device_version_id):
        """Service should filter reviews by phase."""
        design_service.create_review(
            DesignReview(
                organization_id=org_id,
                device_version_id=device_version_id,
                phase="development",
                review_date=date.today(),
                review_title="Dev 1",
                decision="proceed",
            )
        )
        design_service.create_review(
            DesignReview(
                organization_id=org_id,
                device_version_id=device_version_id,
                phase="verification",
                review_date=date.today(),
                review_title="Ver 1",
                decision="proceed",
            )
        )

        dev_reviews = design_service.get_reviews_by_phase(device_version_id, "development")
        assert len(dev_reviews) == 1

    def test_get_latest_review(self, design_service, org_id, device_version_id):
        """Service should get most recent review."""
        design_service.create_review(
            DesignReview(
                organization_id=org_id,
                device_version_id=device_version_id,
                phase="concept",
                review_date=date(2026, 1, 1),
                review_title="Concept",
                decision="proceed",
            )
        )
        design_service.create_review(
            DesignReview(
                organization_id=org_id,
                device_version_id=device_version_id,
                phase="development",
                review_date=date(2026, 2, 1),
                review_title="Development",
                decision="proceed",
            )
        )

        latest = design_service.get_latest_review(device_version_id)
        assert latest is not None
        assert latest.phase == "development"


@pytest.mark.unit
class TestDesignControlServiceVerification:
    """Tests for DesignControlService verification operations."""

    def test_create_verification(self, design_service, org_id, device_version_id):
        """Service should create verification record."""
        verification = DesignVerification(
            organization_id=org_id,
            device_version_id=device_version_id,
            design_output_id=uuid4(),
            method="test",
            title="Test",
            description="Test",
            acceptance_criteria="Test",
            result="pass",
            actual_results="Test",
        )
        created = design_service.create_verification(verification)
        assert created.id is not None

    def test_get_verifications_for_output(self, design_service, org_id, device_version_id):
        """Service should get verifications for a specific output."""
        output_id = uuid4()
        design_service.create_verification(
            DesignVerification(
                organization_id=org_id,
                device_version_id=device_version_id,
                design_output_id=output_id,
                method="test",
                title="Test 1",
                description="Test",
                acceptance_criteria="Test",
                result="pass",
                actual_results="Test",
            )
        )
        design_service.create_verification(
            DesignVerification(
                organization_id=org_id,
                device_version_id=device_version_id,
                design_output_id=output_id,
                method="inspection",
                title="Test 2",
                description="Test",
                acceptance_criteria="Test",
                result="pass",
                actual_results="Test",
            )
        )

        verifications = design_service.get_verifications_for_output(output_id)
        assert len(verifications) == 2


@pytest.mark.unit
class TestDesignControlServiceValidation:
    """Tests for DesignControlService validation operations."""

    def test_create_validation(self, design_service, org_id, device_version_id):
        """Service should create validation record."""
        validation = DesignValidation(
            organization_id=org_id,
            device_version_id=device_version_id,
            validation_type="usability",
            title="Usability",
            description="Test",
            acceptance_criteria="Test",
            result="pass",
            actual_results="Test",
            conclusions="Test",
        )
        created = design_service.create_validation(validation)
        assert created.id is not None

    def test_get_validations_by_type(self, design_service, org_id, device_version_id):
        """Service should filter validations by type."""
        design_service.create_validation(
            DesignValidation(
                organization_id=org_id,
                device_version_id=device_version_id,
                validation_type="clinical",
                title="Clinical 1",
                description="Test",
                acceptance_criteria="Test",
                result="pass",
                actual_results="Test",
                conclusions="Test",
            )
        )
        design_service.create_validation(
            DesignValidation(
                organization_id=org_id,
                device_version_id=device_version_id,
                validation_type="usability",
                title="Usability 1",
                description="Test",
                acceptance_criteria="Test",
                result="pass",
                actual_results="Test",
                conclusions="Test",
            )
        )

        clinical = design_service.get_validations_by_type(device_version_id, "clinical")
        assert len(clinical) == 1


@pytest.mark.unit
class TestDesignControlServiceChanges:
    """Tests for DesignControlService change operations."""

    def test_create_change(self, design_service, org_id, device_version_id):
        """Service should create design change record."""
        change = DesignChange(
            organization_id=org_id,
            device_version_id=device_version_id,
            change_number="DCN-001",
            title="Test change",
            description="Test",
            rationale="Test",
            change_type="minor",
            impact_assessment="Test",
        )
        created = design_service.create_change(change)
        assert created.id is not None

    def test_get_pending_changes(self, design_service, org_id, device_version_id):
        """Service should get changes awaiting approval."""
        design_service.create_change(
            DesignChange(
                organization_id=org_id,
                device_version_id=device_version_id,
                change_number="DCN-001",
                title="Proposed",
                description="Test",
                rationale="Test",
                change_type="minor",
                impact_assessment="Test",
                status="proposed",
            )
        )
        design_service.create_change(
            DesignChange(
                organization_id=org_id,
                device_version_id=device_version_id,
                change_number="DCN-002",
                title="Approved",
                description="Test",
                rationale="Test",
                change_type="minor",
                impact_assessment="Test",
                status="approved",
            )
        )

        pending = design_service.get_pending_changes(device_version_id)
        assert len(pending) == 1
        assert pending[0].title == "Proposed"


# =============================================================================
# Analysis Method Tests
# =============================================================================


@pytest.mark.unit
class TestDesignControlServiceAnalysis:
    """Tests for DesignControlService analysis methods."""

    def test_get_unmet_inputs(self, design_service, org_id, device_version_id):
        """Service should identify inputs with no outputs."""
        # Create inputs
        input1 = design_service.create_input(
            DesignInput(
                organization_id=org_id,
                device_version_id=device_version_id,
                source="user_need",
                title="Input 1",
                description="Test",
            )
        )
        input2 = design_service.create_input(
            DesignInput(
                organization_id=org_id,
                device_version_id=device_version_id,
                source="user_need",
                title="Input 2",
                description="Test",
            )
        )

        # Create output for input1 only
        design_service.create_output(
            DesignOutput(
                organization_id=org_id,
                device_version_id=device_version_id,
                design_input_id=input1.id,
                output_type="specification",
                title="Spec 1",
                specification="Test",
                acceptance_criteria="Test",
            )
        )

        unmet = design_service.get_unmet_inputs(device_version_id)
        assert len(unmet) == 1
        assert unmet[0].id == input2.id

    def test_get_unverified_outputs(self, design_service, org_id, device_version_id):
        """Service should identify outputs without passing verification."""
        # Create outputs
        output1 = design_service.create_output(
            DesignOutput(
                organization_id=org_id,
                device_version_id=device_version_id,
                output_type="specification",
                title="Output 1",
                specification="Test",
                acceptance_criteria="Test",
            )
        )
        output2 = design_service.create_output(
            DesignOutput(
                organization_id=org_id,
                device_version_id=device_version_id,
                output_type="specification",
                title="Output 2",
                specification="Test",
                acceptance_criteria="Test",
            )
        )

        # Create passing verification for output1 only
        design_service.create_verification(
            DesignVerification(
                organization_id=org_id,
                device_version_id=device_version_id,
                design_output_id=output1.id,
                method="test",
                title="Test",
                description="Test",
                acceptance_criteria="Test",
                result="pass",
                actual_results="Test",
            )
        )

        unverified = design_service.get_unverified_outputs(device_version_id)
        assert len(unverified) == 1
        assert unverified[0].id == output2.id

    def test_get_phases_without_review(self, design_service, org_id, device_version_id):
        """Service should identify phases missing reviews."""
        # Create review for development only
        design_service.create_review(
            DesignReview(
                organization_id=org_id,
                device_version_id=device_version_id,
                phase="development",
                review_date=date.today(),
                review_title="Dev Review",
                decision="proceed",
            )
        )

        missing = design_service.get_phases_without_review(device_version_id)
        assert "development" not in missing
        assert "concept" in missing
        assert "verification" in missing

    def test_calculate_design_completeness(self, design_service, org_id, device_version_id):
        """Service should calculate completeness metrics."""
        # Create 2 inputs
        input1 = design_service.create_input(
            DesignInput(
                organization_id=org_id,
                device_version_id=device_version_id,
                source="user_need",
                title="Input 1",
                description="Test",
            )
        )
        design_service.create_input(
            DesignInput(
                organization_id=org_id,
                device_version_id=device_version_id,
                source="user_need",
                title="Input 2",
                description="Test",
            )
        )

        # Create 1 output meeting 1 input
        output1 = design_service.create_output(
            DesignOutput(
                organization_id=org_id,
                device_version_id=device_version_id,
                design_input_id=input1.id,
                output_type="specification",
                title="Spec 1",
                specification="Test",
                acceptance_criteria="Test",
            )
        )

        # Create verification for output
        design_service.create_verification(
            DesignVerification(
                organization_id=org_id,
                device_version_id=device_version_id,
                design_output_id=output1.id,
                method="test",
                title="Test",
                description="Test",
                acceptance_criteria="Test",
                result="pass",
                actual_results="Test",
            )
        )

        metrics = design_service.calculate_design_completeness(device_version_id)
        assert metrics["inputs"]["total"] == 2
        assert metrics["inputs"]["met"] == 1
        assert metrics["inputs"]["unmet"] == 1
        assert metrics["outputs"]["total"] == 1
        assert metrics["outputs"]["verified"] == 1


# =============================================================================
# Singleton Tests
# =============================================================================


@pytest.mark.unit
class TestDesignControlServiceSingleton:
    """Tests for singleton access."""

    def test_get_design_control_service_returns_instance(self):
        """get_design_control_service should return DesignControlService."""
        service = get_design_control_service()
        assert isinstance(service, DesignControlService)

    def test_singleton_returns_same_instance(self):
        """Multiple calls should return same instance."""
        service1 = get_design_control_service()
        service2 = get_design_control_service()
        assert service1 is service2
