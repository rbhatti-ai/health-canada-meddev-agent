# Knowledge Base Documentation

This document provides a comprehensive overview of all regulatory knowledge sources ingested into the Health Canada Medical Device Regulatory Agent.

## Data Sources Overview

| Source | Documents | Chunks | Description |
|--------|-----------|--------|-------------|
| Health Canada Regulations | 1 | 575 | Core Medical Devices Regulations (SOR/98-282) |
| Guidance Documents | 25+ | 1,375 | Official Health Canada guidance |
| ISO Standards | 2 | 56 | ISO 13485 and related standards |
| Application Forms | 5 | 32 | Health Canada forms (F201, F202, FRM series) |
| Submission Checklists | 7 | 12 | Class-specific submission checklists |
| Process Flowcharts | 4 | 5 | Visual timeline guides |

**Total: 52 documents, 2,093 searchable chunks**

---

## 1. Core Regulations

### Medical Devices Regulations (SOR/98-282)
- **File**: `HC_MedicalDevicesRegulations_SOR-98-282_2025-01-14.pdf`
- **Category**: `regulation`
- **Chunks**: 575
- **Key Content**:
  - Part 1: Interpretation and Application
  - Part 2: Device Classification (Schedule 1 Rules)
  - Part 3: MDEL Requirements
  - Part 4: MDL Application Requirements
  - Part 5: Labelling Requirements
  - Part 6: Post-Market Requirements
  - Schedule 1: Classification Rules

---

## 2. Guidance Documents

### Device Classification
| Document | Purpose |
|----------|---------|
| `HC_SaMD_DefinitionClassification_2019-12-18.pdf` | SaMD classification using IMDRF framework |
| `HC_SaMD_Classification_Examples_2022-11-15.pdf` | Real-world SaMD classification examples |
| `HC_Guidance for determining medical device application type.pdf` | New vs. amendment application decision |

### MDEL (Establishment Licensing)
| Document | Purpose |
|----------|---------|
| `Guidance on medical device establishment licensing (GUI-0016).pdf` | Complete MDEL requirements |
| `Fees for the Review of MDEL Applications.pdf` | MDEL fee schedule |

### MDL (Device Licensing)
| Document | Purpose |
|----------|---------|
| `Guidance on managing applications for medical device licences Feb 2026.pdf` | MDL application process |
| `HC_Guidance Document- How to Complete MDL Application.pdf` | Step-by-step MDL guidance |
| `Guidance Document_ Fees for MDL Applications.pdf` | MDL fee schedule |
| `Guidance Document_ MDL Renewal and Annual Fees.pdf` | Annual right-to-sell fees |

### Quality Management Systems
| Document | Purpose |
|----------|---------|
| `GD210- ISO 13485 QMS Audits.pdf` | QMS audit requirements |
| `GD211- Content of QMS Audit Reports.pdf` | Audit report format |
| `GD207- Content of ISO 13485 Certificates.pdf` | Certificate requirements |
| `MDSAP Auditing Organizations Requirements.pdf` | MDSAP program details |
| `Notice_ Transition to ISO 13485:2016.pdf` | ISO 13485 version requirements |

### Clinical Evidence
| Document | Purpose |
|----------|---------|
| `HC_Guidance on clinical evidence requirements.pdf` | Clinical data requirements by class |

### Cybersecurity
| Document | Purpose |
|----------|---------|
| `Pre-market Requirements for Medical Device Cybersecurity.pdf` | Cybersecurity submission requirements |
| `HC_PreMarket_Cybersecurity_2019-06-26.pdf` | SBOM and security controls |

### Machine Learning / AI
| Document | Purpose |
|----------|---------|
| `HC_Pre-market guidance for ML-enabled medical devices 2025.pdf` | PCCP, validation for ML devices |

### Submission Format
| Document | Purpose |
|----------|---------|
| `Health Canada adapted IMDRF ToC guide.pdf` | IMDRF Table of Contents structure |
| Supporting DOCX files | File naming, bookmarking, granularity rules |

---

## 3. Standards

### ISO 13485:2016
- **File**: `ISO_13485_2016_MedicalDevicesQMS.pdf`
- **Content**: Quality management system requirements for medical devices
- **Key Sections**:
  - Section 4: Quality Management System
  - Section 5: Management Responsibility
  - Section 6: Resource Management
  - Section 7: Product Realization
  - Section 8: Measurement, Analysis, Improvement

### Quality Systems Overview
- **File**: `Quality Systems ISO 13485 - Canada.ca.pdf`
- **Content**: Health Canada's interpretation of ISO 13485 requirements

---

## 4. Forms

| Form | Purpose | Classes |
|------|---------|---------|
| FRM-0292 | MDEL Application | All |
| FRM-0077 | MDL Application - Class II | II |
| FRM-0078 | MDL Application - Class III | III |
| FRM-0079 | MDL Application - Class IV | IV |
| F201 | Manufacturer Registration Status Change | All |
| F202 | QMS Certificate Filing | II-IV |

---

## 5. Submission Checklists

Located in `/data/raw/checklists/`:

| Checklist | Purpose |
|-----------|---------|
| `Checklist_PreSubmission_Client_Readiness.pdf` | Pre-engagement readiness assessment |
| `Checklist_MDEL_Application_Completeness.pdf` | MDEL application completeness |
| `Checklist_MDL_Submission_ClassII.pdf` | Class II MDL requirements |
| `Checklist_MDL_Submission_ClassIII.pdf` | Class III MDL requirements |
| `Checklist_MDL_Submission_ClassIV.pdf` | Class IV MDL requirements |
| `Checklist_PostMarket_Compliance.pdf` | Post-market obligations |

---

## 6. Process Flowcharts

Located in `/data/raw/flowcharts/`:

| Flowchart | Timeline |
|-----------|----------|
| `Flowchart_MDEL_Process_120Day_Breakdown.pdf` | MDEL: 4-8 weeks typical |
| `Flowchart_ClassII_MDL_15Day_Timeline.pdf` | Class II: 15 calendar days |
| `Flowchart_ClassIII_MDL_75Day_Timeline.pdf` | Class III: 75 calendar days |
| `Flowchart_ClassIV_MDL_90Day_Timeline.pdf` | Class IV: 90 calendar days |

---

## Document Categories in Vector Store

The RAG system categorizes documents for filtered retrieval:

| Category | Description | Use Case |
|----------|-------------|----------|
| `regulation` | Core laws (SOR/98-282) | Legal requirements queries |
| `guidance` | Health Canada guidance docs | How-to and process queries |
| `standard` | ISO standards | QMS requirement queries |
| `form` | Application forms | Form-specific queries |
| `checklist` | Submission checklists | Completeness checks |
| `flowchart` | Process timelines | Timeline queries |

---

## Search Examples

### Find Classification Rules
```python
results = retrieve(query="SaMD classification healthcare situation", filter_category="guidance")
```

### Find Fee Information
```python
results = retrieve(query="MDL application fee Class III", filter_category="guidance")
```

### Find QMS Requirements
```python
results = retrieve(query="ISO 13485 design control", filter_category="standard")
```

### Find Checklist Items
```python
results = retrieve(query="Class IV MDL submission requirements", filter_category="checklist")
```

---

## Keeping Knowledge Current

### Update Process
1. Download new guidance from Health Canada website
2. Place PDFs in `/data/raw/` (organize by type)
3. Run ingestion: `meddev-agent ingest data/raw/`
4. Update this document

### Key Health Canada URLs
- [Medical Devices Overview](https://www.canada.ca/en/health-canada/services/drugs-health-products/medical-devices.html)
- [Guidance Documents](https://www.canada.ca/en/health-canada/services/drugs-health-products/medical-devices/application-information/guidance-documents.html)
- [Fee Schedule](https://www.canada.ca/en/health-canada/services/drugs-health-products/medical-devices/fees.html)
- [MDALL Database](https://health-products.canada.ca/mdall-limh/)

---

## Version History

| Date | Change |
|------|--------|
| 2025-02-05 | Initial knowledge base created with 52 documents, 2,093 chunks |
