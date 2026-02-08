# MASTER SPRINT PLAN v3 — Rigour Medtech Regulatory Platform

> **Revised:** 2026-02-07 22:00 MST (Mountain Time — Edmonton)
> **Revision reason:** Strategic expansion for senior regulatory professionals (cardiologist-entrepreneur profile). Adds citation infrastructure, IP protection, design controls, clinical evidence hierarchy, predicate analysis. Maintains strict Health Canada grounding.
> **Previous version:** MASTER_SPRINT_PLAN_v2.md (Sprint 4 fully complete)
> **Governing doc:** `docs/architecture/REGULATORY_EXECUTION_PLATFORM_ARCHITECTURE.md`
> **Repo:** rbhatti-ai/health-canada-meddev-agent (private, GitHub)
> **Tests at v3 creation:** 921 passing

---

## TARGET CLIENT PROFILE

**Senior Cardiologist-Entrepreneur:**
- 20 years medical education experience
- Research and IP protection expertise
- QMS (ISO 13485) proficiency
- Building cardiac medical devices (likely Class III/IV or SaMD)
- Parallel regulatory strategy (Health Canada → FDA → EU MDR)

**What this profile demands:**
1. **Every output cites regulations** — SOR/98-282 sections, GUI document numbers, ISO standards
2. **IP protection** — Trade secrets tracked, confidentiality classification
3. **Clinical evidence hierarchy** — RCT > cohort > case series
4. **Design control traceability** — Full ISO 13485 Section 7.3
5. **Predicate device analysis** — Substantial equivalence for Class II/III
6. **No AI hallucination** — System NEVER invents regulatory requirements

---

## CURRENT STATE (as of 2026-02-07 22:00 MST)

### Completed Sprints (ALL 4 SPRINTS DONE)

| Sprint | Commit | Tests | What Was Delivered |
|--------|--------|-------|--------------------|
| 1 | f19051c | 410 | 10 DB tables, Pydantic models, TwinRepository |
| 2 | 6f8853f | 549 | TraceabilityEngine, EvidenceIngestion, Attestation, 13 API endpoints |
| 3a | c541059 | 627 | GapDetectionEngine, 12 rules (GAP-001 to GAP-012) |
| 3b | 43f9038 | 699 | ReadinessAssessment, penalty scoring, language safety |
| 3c | 810b002 | 732 | Gap/Readiness API endpoints (4 new) |
| 4A | 3912245 | 780 | 13 LangGraph agent tools, REGULATORY_TWIN_TOOLS |
| 4B | (prev) | 847 | 6 system prompts, 6 structured schemas, AI provenance |
| 4C | fb3ba0d | 888 | Agent orchestration: LangGraph StateGraph, 4 workflows |
| **4D** | **172b35c** | **921** | **33 agent integration tests: workflows, provenance, error handling** |

### Current Capabilities

- Device classification (Health Canada + IMDRF SaMD)
- Regulatory pathway advisor (timelines, fees)
- Checklist generation
- RAG search (52 Health Canada docs, 2,093 chunks)
- Traceability engine (9 link types)
- Evidence ingestion + orphan detection
- Attestation service (human sign-off)
- Gap detection (12 deterministic rules)
- Readiness assessment (0.0–1.0 scoring)
- 18 agent tools (13 new + 5 original)
- 6 system prompts + 6 structured output schemas
- 4 named workflows (full_analysis, risk_assessment, evidence_review, submission_readiness)
- Language safety (14 forbidden words)
- AI provenance logging

### Gaps vs. Target Profile

| Need | Current State | Priority |
|------|---------------|----------|
| Mandatory citations | Guidance refs exist, not systematic | **P0 — CRITICAL** |
| IP/Confidentiality | Not implemented | **P0 — CRITICAL** |
| Design controls (ISO 13485 7.3) | Not implemented | **P1 — HIGH** |
| Clinical evidence hierarchy | Basic evidence_type, no scoring | **P1 — HIGH** |
| Predicate device analysis | Not implemented | **P1 — HIGH** |
| Labeling compliance checker | Existence check only (GAP-009) | **P2 — MEDIUM** |
| Post-market planning | Not implemented | **P2 — MEDIUM** |
| Streamlit Dashboard | Not implemented | **P2 — MEDIUM** |

---

## STRATEGIC DECISION: SPRINT ORDERING

**Why Citation Infrastructure before UI:**
1. Every output in the UI should display citations
2. Building UI without citations = rebuilding UI later
3. A regulatory professional won't trust outputs without citations
4. Citations are foundational; other features depend on them

**Revised Sprint Order:**
- Sprint 5: **Citation Infrastructure** (P0) — Foundation for everything
- Sprint 6: **IP Protection** (P0) — Before UI exposes any data
- Sprint 7: **Clinical Evidence + Predicate** (P1) — Core for Class III/IV
- Sprint 8: **Design Controls** (P1) — ISO 13485 7.3 traceability
- Sprint 9: **Labeling + Post-Market** (P2) — Compliance modules
- Sprint 10: **Streamlit Dashboard** (P2) — UI with all features

---

## SPRINT 5 — CITATION INFRASTRUCTURE (P0)

**Status:** NOT STARTED
**Goal:** Every substantive output includes mandatory regulatory citations.
**Why P0:** A regulatory professional will not use a system that doesn't cite sources.

### 5A: Regulatory Reference Registry (~30 tests)

**File:** `src/core/regulatory_references.py`

```python
ReferenceType = Literal["regulation", "guidance", "standard", "form", "internal"]


class RegulatoryReference(BaseModel):
    """A structured citation to a regulatory source."""

    id: str  # "SOR-98-282-S32" or "GUI-0098-4.3"
    reference_type: ReferenceType
    document_id: str  # "SOR/98-282" or "GUI-0098"
    section: str | None = None  # "Section 32(2)(c)" or "4.3"
    schedule: str | None = None  # "Schedule 1, Rule 11"
    title: str  # Human-readable title
    url: str | None = None  # Health Canada URL
    effective_date: date | None = None


class RegulatoryReferenceRegistry:
    """
    Registry of Health Canada regulatory references.
    Pre-populated from KNOWLEDGE_BASE.md documents.
    """

    def get_reference(self, document_id: str, section: str = None) -> RegulatoryReference | None
    def search(self, query: str) -> list[RegulatoryReference]
    def get_by_topic(self, topic: str) -> list[RegulatoryReference]
    def get_classification_rules(self) -> list[RegulatoryReference]  # Schedule 1
    def get_labeling_requirements(self) -> list[RegulatoryReference]  # Part 5
    def get_clinical_requirements(self, device_class: str) -> list[RegulatoryReference]
    def format_citation(self, ref: RegulatoryReference) -> str  # "[SOR/98-282, s.32(2)(c)]"


# Pre-populated registry (50+ entries)
REGULATION_REFERENCES: dict[str, RegulatoryReference] = {
    "SOR-98-282": RegulatoryReference(
        id="SOR-98-282",
        reference_type="regulation",
        document_id="SOR/98-282",
        title="Medical Devices Regulations",
        url="https://laws-lois.justice.gc.ca/eng/regulations/SOR-98-282/",
    ),
    # ... 50+ more entries from KNOWLEDGE_BASE.md
}
```

**Pre-populated References (from KNOWLEDGE_BASE.md):**

| ID | Document | Type |
|----|----------|------|
| SOR-98-282 | Medical Devices Regulations | regulation |
| GUI-0016 | MDEL Guidance | guidance |
| GUI-0098 | How to Complete MDL Application | guidance |
| GUI-0102 | Clinical Evidence Requirements | guidance |
| GUI-0123 | SaMD Pre-market Guidance | guidance |
| ISO-13485-2016 | Medical Device QMS | standard |
| ISO-14971-2019 | Risk Management | standard |
| IEC-62304-2006 | Medical Device Software | standard |
| FRM-0292 | MDEL Application | form |
| FRM-0077 | Class II MDL | form |
| FRM-0078 | Class III MDL | form |
| FRM-0079 | Class IV MDL | form |

### 5B: Citation-Enabled Gap Findings (~25 tests)

**File:** `src/core/gap_engine.py` (modify GapFinding)

```python
class GapFinding(BaseModel):
    # ... existing fields ...

    # NEW: Citation fields (at least one required for non-info)
    regulation_section: str | None = None    # "SOR/98-282, s.32(2)(c)"
    guidance_document: str | None = None     # "GUI-0098, Section 4.3"
    iso_reference: str | None = None         # "ISO 13485:2016, 7.3.4"
    schedule_rule: str | None = None         # "Schedule 1, Rule 11"
    form_reference: str | None = None        # "FRM-0078, Section B"
    citation_text: str | None = None         # Full formatted citation

    @model_validator(mode="after")
    def validate_citation_present(self) -> "GapFinding":
        """Non-info findings require at least one citation."""
        if self.severity != "info":
            has_citation = any([
                self.regulation_section,
                self.guidance_document,
                self.iso_reference,
            ])
            if not has_citation:
                # Warning, not error — allows gradual migration
                pass  # Log warning for now
        return self
```

**Update all 12 gap rules with citations:**

| Rule | Primary Citation | Secondary Citation |
|------|------------------|-------------------|
| GAP-001 | ISO 14971:2019, 7.1 | SOR/98-282, s.10.1 |
| GAP-002 | ISO 14971:2019, 7.2 | ISO 13485:2016, 7.3.6 |
| GAP-003 | SOR/98-282, s.32(4) | — |
| GAP-004 | SOR/98-282, s.32(2)(a) | — |
| GAP-005 | GUI-0102, Section 3.2 | — |
| GAP-006 | ISO 13485:2016, 7.3.6 | — |
| GAP-007 | SOR/98-282, s.26 | — |
| GAP-008 | Platform policy | — |
| GAP-009 | SOR/98-282, Part 5 | GUI-0015 |
| GAP-010 | ISO 14971:2019, 6.1-6.4 | — |
| GAP-011 | GUI-0098, Section 5.1 | — |
| GAP-012 | GUI-0102, Section 4.1 | SOR/98-282, s.32(2)(c) |

### 5C: Citation in Agent Outputs (~15 tests)

**File:** `src/agents/prompts.py` (update all 6 prompts)

Add to each system prompt:

```
CITATION REQUIREMENT:
Every substantive statement must cite its source.

FORMAT: "[Statement]. [Citation]"

EXAMPLES:
- "Class III devices require clinical evidence. [SOR/98-282, s.32(2)(c)]"
- "Risk controls must be verified. [ISO 14971:2019, 7.2]"

IF NO CITATION AVAILABLE:
- "[Statement]. [Citation required — verify with Health Canada]"

FORBIDDEN:
- Substantive claims without citations
- Invented regulation sections
- Made-up guidance document numbers
```

### 5D: Tests

**Files:**
- `tests/unit/test_regulatory_references.py` — Registry tests (~30)
- `tests/unit/test_gap_citations.py` — Citation validation (~25)
- `tests/unit/test_prompt_citations.py` — Agent citation behavior (~15)

**Sprint 5 Exit Criteria:**
- [ ] RegulatoryReferenceRegistry with 50+ pre-loaded references
- [ ] All 12 gap rules have mandatory citations
- [ ] All 6 agent prompts require citations
- [ ] ~991 total tests passing (921 + 70)
- [ ] Checkpoint created with MST timestamp

---

## SPRINT 6 — IP PROTECTION & CONFIDENTIALITY (P0)

**Status:** NOT STARTED
**Goal:** Classify evidence and artifacts by confidentiality level.
**Why P0:** An IP expert will not use a system that doesn't protect trade secrets.

### 6A: Confidentiality Classification (~35 tests)

**File:** `src/core/confidentiality.py`

```python
ConfidentialityLevel = Literal[
    "public",                    # Can appear in any document
    "confidential_submission",   # Redacted from public portions
    "trade_secret",              # Never disclosed, summarized only
    "patent_pending",            # Can reference patent application
]


class ConfidentialityTag(RegulatoryTwinBase):
    """IP protection classification for an entity."""

    id: UUID | None = None
    organization_id: UUID
    entity_type: str  # "evidence_item", "artifact", "claim"
    entity_id: UUID
    level: ConfidentialityLevel
    patent_application_number: str | None = None
    trade_secret_attestation: bool = False
    disclosure_restrictions: list[str] = []
    summary_for_public_use: str | None = None
    classified_by: UUID | None = None
    classified_at: datetime | None = None


class ConfidentialityService:
    """Manages IP protection classifications."""

    def classify(self, entity_type: str, entity_id: UUID, level: ConfidentialityLevel, **kwargs) -> ConfidentialityTag
    def get_classification(self, entity_type: str, entity_id: UUID) -> ConfidentialityTag | None
    def get_trade_secrets(self, organization_id: UUID) -> list[ConfidentialityTag]
    def get_patent_pending(self, organization_id: UUID) -> list[ConfidentialityTag]
    def get_unclassified(self, organization_id: UUID) -> list[tuple[str, UUID]]
```

### 6B: CBI Request Generator (~20 tests)

Per SOR/98-282, Section 43.2:

```python
class CBIItem(BaseModel):
    """Single item in CBI request."""
    entity_type: str
    entity_id: UUID
    description: str  # What is CBI
    justification: str  # Why it's CBI
    harm_if_disclosed: str  # Competitive harm
    page_references: list[str] = []


class CBIRequest(BaseModel):
    """Confidential Business Information request."""
    organization_id: UUID
    submission_reference: str
    items: list[CBIItem]
    attestation_text: str
    attested_by: UUID
    attested_at: datetime


def generate_cbi_request_template(items: list[CBIItem]) -> str:
    """Generate CBI request document for Health Canada."""
```

### 6C: Gap Rule for Unclassified Assets (~10 tests)

```python
# GAP-013: Unclassified sensitive assets
GapRuleDefinition(
    id="GAP-013",
    name="Unclassified sensitive assets",
    description="Evidence items with no confidentiality classification",
    severity="minor",
    category="consistency",
    version=1,
)
```

### 6D: Agent Tool for IP (~10 tests)

```python
@tool
def classify_confidentiality(
    entity_type: str,
    entity_id: str,
    level: str,
    patent_number: str | None = None,
) -> str:
    """Classify an entity's confidentiality level for IP protection."""

@tool
def get_ip_inventory(organization_id: str) -> str:
    """Get summary of IP assets (trade secrets, patents pending)."""
```

**Sprint 6 Exit Criteria:**
- [ ] ConfidentialityService with 4 levels
- [ ] CBIRequest generator
- [ ] GAP-013 rule
- [ ] 2 new agent tools
- [ ] ~1,066 total tests passing (991 + 75)
- [ ] Checkpoint created with MST timestamp

---

## SPRINT 7 — CLINICAL EVIDENCE + PREDICATE (P1)

**Status:** NOT STARTED
**Goal:** Clinical evidence hierarchy scoring + predicate device comparison.
**Why P1:** Core for Class III/IV cardiac devices.

### 7A: Clinical Evidence Model (~50 tests)

**File:** `src/core/clinical_evidence.py`

```python
ClinicalStudyType = Literal[
    "randomized_controlled_trial",    # Score: 1.0
    "prospective_cohort",             # Score: 0.85
    "retrospective_cohort",           # Score: 0.70
    "case_control",                   # Score: 0.55
    "case_series",                    # Score: 0.40
    "case_report",                    # Score: 0.25
    "expert_opinion",                 # Score: 0.15
    "literature_review",              # Score: 0.15
    "registry_data",                  # Score: 0.60
]

EVIDENCE_HIERARCHY_SCORE: dict[ClinicalStudyType, float] = {
    "randomized_controlled_trial": 1.0,
    "prospective_cohort": 0.85,
    # ...
}


class ClinicalEvidence(RegulatoryTwinBase):
    """Structured clinical study data (GUI-0102 aligned)."""

    id: UUID | None = None
    organization_id: UUID
    device_version_id: UUID

    # Identification
    study_type: ClinicalStudyType
    study_id: str | None = None  # NCT number, ethics approval
    title: str

    # Design
    blinding: Literal["open", "single_blind", "double_blind", "triple_blind"] | None = None
    control_type: Literal["placebo", "active", "sham", "no_control"] | None = None

    # Population
    inclusion_criteria: list[str] = []
    exclusion_criteria: list[str] = []
    sample_size: int | None = None

    # Endpoints
    primary_endpoint: str | None = None
    secondary_endpoints: list[str] = []

    # Results
    results_summary: str | None = None
    primary_outcome_met: bool | None = None
    adverse_events_summary: str | None = None

    # Quality
    peer_reviewed: bool = False
    publication_reference: str | None = None
    quality_score: float | None = None  # Calculated

    # Regulatory
    hc_guidance_alignment: str | None = None  # "GUI-0102, Section 3.1"
    evidence_item_id: UUID | None = None


class ClinicalEvidenceService:
    def create(self, evidence: ClinicalEvidence) -> ClinicalEvidence
    def calculate_quality_score(self, evidence: ClinicalEvidence) -> float
    def get_portfolio(self, device_version_id: UUID) -> ClinicalEvidencePortfolio
    def assess_package(self, device_version_id: UUID, device_class: str) -> ClinicalPackageAssessment
```

### 7B: Predicate Device Model (~40 tests)

**File:** `src/core/predicate_analysis.py`

```python
class PredicateDevice(RegulatoryTwinBase):
    """Predicate device for substantial equivalence."""

    id: UUID | None = None
    organization_id: UUID
    device_version_id: UUID  # Subject device

    # Predicate identification
    predicate_name: str
    predicate_manufacturer: str
    mdl_number: str | None = None  # Health Canada MDL
    mdall_id: str | None = None  # MDALL database
    device_class: str

    # Comparison (SOR/98-282, s.32(4))
    intended_use_comparison: str
    intended_use_equivalent: bool
    technological_characteristics: str
    technological_equivalent: bool
    technological_differences: list[str] = []
    performance_comparison: str
    performance_equivalent: bool

    # Conclusion
    equivalence_conclusion: Literal[
        "substantially_equivalent",
        "substantially_equivalent_with_data",
        "not_equivalent",
        "requires_additional_analysis",
    ]
    additional_data_required: list[str] = []

    # Citation
    regulation_reference: str = "SOR/98-282, s.32(4)"


class PredicateAnalysisService:
    def create_predicate(self, predicate: PredicateDevice) -> PredicateDevice
    def generate_comparison_matrix(self, device_version_id: UUID, predicate_id: UUID) -> PredicateComparisonMatrix
```

### 7C: Clinical/Predicate Gap Rules (~25 tests)

```python
# GAP-014: Insufficient clinical evidence strength
GapRuleDefinition(
    id="GAP-014",
    name="Insufficient clinical evidence strength",
    description="Clinical evidence below threshold for device class",
    severity="critical",
    category="evidence_strength",
    guidance_document="GUI-0102, Section 4.1",
)

# GAP-015: No predicate identified (Class II/III)
GapRuleDefinition(
    id="GAP-015",
    name="No predicate device identified",
    description="Class II/III device with no predicate comparison",
    severity="major",
    category="completeness",
    regulation_section="SOR/98-282, s.32(4)",
)

# GAP-016: Technological differences unaddressed
GapRuleDefinition(
    id="GAP-016",
    name="Technological differences unaddressed",
    description="Predicate has differences without supporting data",
    severity="critical",
    category="evidence_strength",
    regulation_section="SOR/98-282, s.32(4)(b)",
)
```

**Sprint 7 Exit Criteria:**
- [ ] ClinicalEvidence model with hierarchy scoring
- [ ] PredicateDevice model with comparison
- [ ] GAP-014, GAP-015, GAP-016 rules
- [ ] ~1,181 total tests passing (1,066 + 115)
- [ ] Checkpoint created with MST timestamp

---

## SPRINT 8 — DESIGN CONTROLS (P1)

**Status:** NOT STARTED
**Goal:** Full ISO 13485 Section 7.3 design control traceability.

### 8A: Design Control Entities (~50 tests)

**File:** `src/core/design_controls.py`

```python
class DesignInput(RegulatoryTwinBase):
    """User need driving design (ISO 13485 7.3.2)."""
    id: UUID | None = None
    organization_id: UUID
    device_version_id: UUID
    source: Literal["user_need", "clinical_feedback", "regulatory", "standard", "competitive"]
    priority: Literal["essential", "desired", "nice_to_have"]
    description: str
    acceptance_criteria: str | None = None
    regulatory_reference: str | None = None  # "SOR/98-282, s.XX"


class DesignOutput(RegulatoryTwinBase):
    """Specification meeting input (ISO 13485 7.3.3)."""
    id: UUID | None = None
    organization_id: UUID
    device_version_id: UUID
    design_input_id: UUID
    output_type: Literal["specification", "drawing", "procedure", "software_requirement"]
    title: str
    specification: str
    acceptance_criteria: str
    status: Literal["draft", "reviewed", "approved", "released"] = "draft"


class DesignReview(RegulatoryTwinBase):
    """Formal review record (ISO 13485 7.3.5)."""
    id: UUID | None = None
    organization_id: UUID
    device_version_id: UUID
    phase: Literal["concept", "feasibility", "development", "verification", "validation", "transfer"]
    review_date: date
    participants: list[str] = []
    findings: list[str] = []
    action_items: list[str] = []
    decision: Literal["proceed", "proceed_with_conditions", "repeat", "stop"]
```

### 8B: Design Control Trace Links (~20 tests)

Add to VALID_RELATIONSHIPS:

```python
"design_input": [("drives", "design_output")],
"design_output": [
    ("verified_by", "verification_test"),
    ("validated_by", "validation_test"),
    ("satisfies", "design_input"),
],
"design_review": [("reviews", "design_output")],
```

### 8C: Design Control Gap Rules (~20 tests)

```python
# GAP-017: Unmet design inputs
# GAP-018: Unverified design outputs
# GAP-019: Missing design review
```

**Sprint 8 Exit Criteria:**
- [ ] DesignInput, DesignOutput, DesignReview models
- [ ] Design control trace links
- [ ] GAP-017, GAP-018, GAP-019 rules
- [ ] ~1,271 total tests passing (1,181 + 90)
- [ ] Checkpoint created with MST timestamp

---

## SPRINT 9 — LABELING + POST-MARKET (P2)

**Status:** NOT STARTED
**Goal:** Labeling compliance checker + post-market planning.

### 9A: Labeling Compliance (~40 tests)

**File:** `src/core/labeling_compliance.py`

30+ labeling requirements from SOR/98-282 Part 5:
- Device label requirements (s.21)
- IFU requirements (s.22)
- Packaging requirements (s.23)
- Bilingual requirements

### 9B: Post-Market Planning (~30 tests)

**File:** `src/core/post_market.py`

- PostMarketPlan model
- Mandatory problem reporting timelines
- PMCF planning

**Sprint 9 Exit Criteria:**
- [ ] LabelingComplianceReport with 30+ requirements
- [ ] PostMarketPlan model
- [ ] ~1,341 total tests passing (1,271 + 70)
- [ ] Checkpoint created with MST timestamp

---

## SPRINT 10 — STREAMLIT DASHBOARD (P2)

**Status:** NOT STARTED
**Goal:** Operational dashboard with ALL features from Sprints 5-9.

### 10A: Readiness Dashboard

- Risk coverage visualization
- Trace completeness display
- Evidence strength indicators
- Gap findings with **citations displayed**
- Readiness score with breakdown

### 10B: Regulatory Twin Management

- Device version CRUD
- Claim/hazard/control/test management
- Evidence upload + linking
- Attestation workflow
- **IP classification UI**

### 10C: Clinical Evidence Portfolio

- Clinical studies list with hierarchy scores
- Predicate comparison matrix
- Evidence strength visualization

### 10D: Agent Chat Interface

- Conversational agent in Streamlit
- Tool execution visible
- AI provenance display
- **Citations in responses**

**Sprint 10 Exit Criteria:**
- [ ] Full operational dashboard
- [ ] All new features integrated
- [ ] ~1,391 total tests passing (1,341 + 50)
- [ ] Checkpoint created with MST timestamp

---

## CUMULATIVE MILESTONE TRACKER

| Metric | S4D ✅ | S5 | S6 | S7 | S8 | S9 | S10 |
|--------|--------|----|----|----|----|----|----|
| Tests | 921 | ~991 | ~1,066 | ~1,181 | ~1,271 | ~1,341 | ~1,391 |
| Gap rules | 12 | 12 | 13 | 16 | 19 | 19 | 19 |
| Entity models | 10 | 11 | 13 | 15 | 18 | 20 | 20 |
| Agent tools | 18 | 18 | 20 | 22 | 24 | 24 | 24 |
| Citations indexed | 0 | 50+ | 50+ | 60+ | 70+ | 80+ | 80+ |
| Workflows | 4 | 4 | 4 | 4 | 4 | 4 | 4 |

---

## NEW DB TABLES REQUIRED

| Sprint | Table | Purpose |
|--------|-------|---------|
| 5 | regulatory_references | Citation registry |
| 6 | confidentiality_tags | IP classification |
| 6 | cbi_requests | CBI request records |
| 7 | clinical_evidence | Clinical study data |
| 7 | predicate_devices | Substantial equivalence |
| 8 | design_inputs | ISO 13485 7.3.2 |
| 8 | design_outputs | ISO 13485 7.3.3 |
| 8 | design_reviews | ISO 13485 7.3.5 |
| 9 | labeling_checks | Compliance records |
| 9 | post_market_plans | Surveillance planning |

---

## DEFERRED FEATURES (Phase 4-5)

| Feature | Reason |
|---------|--------|
| Document Orchestration | Needs all structure layers |
| Deficiency Response Copilot | Needs all prior layers |
| Regulatory Knowledge Graph | "Do not rush it" per architecture |
| Multi-jurisdiction dashboard | Needs core features first |
| Literature automation | External API integration |
| CAPA integration | Lower priority QMS feature |

---

## CRITICAL API PATTERNS (UNCHANGED)

1. **TwinRepository** — Generic methods ONLY
2. **TraceLink** — Pydantic model, use `.attr` not `.get()`
3. **Logger:** `from src.utils.logging import get_logger`
4. **ruff B017:** No `pytest.raises(Exception)`
5. **ruff B904:** Always `raise ... from e`
6. **ruff modern style:** `list[str]`, `dict[str, Any]`, `str | None`
7. **Regulatory-safe language:** NEVER "compliant", "ready", "will pass"
8. **AI provenance:** Every AI output → ai_runs table
9. **ToolNode mocks:** Must also mock `_build_graph`
10. **Unused variables:** ruff F841 catches these

---

## INSTRUCTIONS FOR FUTURE AI SESSIONS

1. **READ THIS FILE FIRST.** It supersedes v2.
2. **Citation-first:** Every new feature must include regulatory citations.
3. **No hallucination:** Never invent regulation sections or guidance documents.
4. **Test rigorously:** ~70-90 tests per sprint.
5. **Language safety:** All outputs use regulatory-safe language.
6. **MST timestamps:** All checkpoints use Mountain Time (Edmonton).
7. **Additive changes:** Don't break existing functionality.
8. **Governing doc:** `docs/architecture/REGULATORY_EXECUTION_PLATFORM_ARCHITECTURE.md`
9. **venv:** Always `source venv/bin/activate`
10. **User's name is Raj.** Simple, conversational language.

---

## CHANGE LOG

| Date (MST) | Change |
|------------|--------|
| 2026-02-07 19:45 | v2 created — corrected sprint ordering |
| 2026-02-07 22:00 | **v3 created** — Strategic expansion for cardiologist-entrepreneur. Added citation infrastructure (P0), IP protection (P0), clinical evidence (P1), predicate analysis (P1), design controls (P1), labeling/post-market (P2). Streamlit moved to Sprint 10. |

---

*End of master sprint plan v3*
