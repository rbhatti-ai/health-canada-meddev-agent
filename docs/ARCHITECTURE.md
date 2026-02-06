# Health Canada Medical Device Regulatory Agent - Architecture

## 1. System Overview

An AI-powered regulatory compliance assistant that helps medical device manufacturers navigate Health Canada's regulatory requirements, from device classification through market authorization.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE LAYER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  CLI Interface  │  Web API (FastAPI)  │  Streamlit Dashboard  │  Slack Bot  │
└────────┬────────┴──────────┬──────────┴───────────┬───────────┴──────┬──────┘
         │                   │                      │                  │
         └───────────────────┴──────────┬───────────┴──────────────────┘
                                        │
┌───────────────────────────────────────▼─────────────────────────────────────┐
│                           ORCHESTRATION LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Agent Controller  │  Session Manager  │  Conversation Memory  │  Router    │
└────────┬───────────┴─────────┬─────────┴───────────┬───────────┴─────┬──────┘
         │                     │                     │                 │
         └─────────────────────┴──────────┬──────────┴─────────────────┘
                                          │
┌─────────────────────────────────────────▼───────────────────────────────────┐
│                           CORE AGENT MODULES                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐           │
│  │ Classification   │  │ Pathway          │  │ Documentation    │           │
│  │ Engine           │  │ Advisor          │  │ Generator        │           │
│  │                  │  │                  │  │                  │           │
│  │ - SaMD Rules     │  │ - MDEL/MDL Flow  │  │ - IMDRF ToC      │           │
│  │ - Risk Classes   │  │ - Timeline Calc  │  │ - Form Filler    │           │
│  │ - IVD Detection  │  │ - Fee Calculator │  │ - Checklist Gen  │           │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘           │
│           │                     │                     │                      │
│  ┌────────▼─────────┐  ┌────────▼─────────┐  ┌────────▼─────────┐           │
│  │ Compliance       │  │ Timeline         │  │ Gap Analysis     │           │
│  │ Checker          │  │ Tracker          │  │ Engine           │           │
│  │                  │  │                  │  │                  │           │
│  │ - ISO 13485      │  │ - Milestone Mgmt │  │ - Missing Docs   │           │
│  │ - Cybersecurity  │  │ - Deadline Alerts│  │ - Risk Assessment│           │
│  │ - Clinical Reqs  │  │ - Progress View  │  │ - Recommendations│           │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────▼───────────────────────────────────┐
│                           RAG & RETRIEVAL LAYER                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        Query Engine                                   │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │ Query       │→ │ Embedding   │→ │ Vector      │→ │ Reranker    │  │   │
│  │  │ Preprocessor│  │ Generator   │  │ Search      │  │ (Cohere)    │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        Document Store                                 │   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │   │
│  │  │ ChromaDB        │  │ Document        │  │ Metadata        │       │   │
│  │  │ Vector Store    │  │ Cache           │  │ Index           │       │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘       │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────▼───────────────────────────────────┐
│                           DATA INGESTION LAYER                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ PDF         │  │ DOCX        │  │ Markdown    │  │ Web         │         │
│  │ Processor   │  │ Processor   │  │ Processor   │  │ Scraper     │         │
│  │ (PyMuPDF)   │  │ (python-docx│  │             │  │ (HC Website)│         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                │                 │
│         └────────────────┴────────┬───────┴────────────────┘                 │
│                                   │                                          │
│                          ┌────────▼────────┐                                 │
│                          │ Text Chunker    │                                 │
│                          │ & Cleaner       │                                 │
│                          │                 │                                 │
│                          │ - Semantic Split│                                 │
│                          │ - Table Extract │                                 │
│                          │ - Metadata Tag  │                                 │
│                          └────────┬────────┘                                 │
│                                   │                                          │
│                          ┌────────▼────────┐                                 │
│                          │ Embedding       │                                 │
│                          │ Generator       │                                 │
│                          │ (OpenAI/Cohere) │                                 │
│                          └─────────────────┘                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
┌─────────────────────────────────────────▼───────────────────────────────────┐
│                           KNOWLEDGE BASE                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Regulatory Documents                                                 │    │
│  │ ├── 01_Core_Law_Regulations/     (Medical Devices Regulations)       │    │
│  │ ├── 02_Guidance_Documents/       (Health Canada Guidance)            │    │
│  │ ├── 03_Standards/                (ISO 13485, IEC 62304)              │    │
│  │ ├── 04_Process_Flows/            (MDL/MDEL Flowcharts)               │    │
│  │ └── 05_Forms/                    (Application Forms)                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ Structured Data                                                      │    │
│  │ ├── classification_rules.json    (SaMD/Device Classification)        │    │
│  │ ├── fee_schedule.json            (Current HC Fees)                   │    │
│  │ ├── timelines.json               (Processing Times by Class)         │    │
│  │ ├── checklists.json              (Application Checklists)            │    │
│  │ └── imdrf_toc_template.json      (IMDRF Table of Contents)           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. Technology Stack

### Core Framework
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Language | Python 3.11+ | Rich ML/AI ecosystem |
| LLM Framework | LangChain + LangGraph | Agent orchestration, tool use |
| LLM Provider | Anthropic Claude / OpenAI GPT-4 | High-quality reasoning |
| Vector DB | ChromaDB (local) / Pinecone (prod) | Efficient similarity search |
| Embeddings | OpenAI text-embedding-3-small | Cost-effective, high quality |

### Data Processing
| Component | Technology | Rationale |
|-----------|------------|-----------|
| PDF Extraction | PyMuPDF (fitz) | Fast, accurate text extraction |
| DOCX Processing | python-docx | Native Word document support |
| Text Chunking | LangChain RecursiveCharacterTextSplitter | Semantic-aware chunking |
| OCR (if needed) | Tesseract / AWS Textract | Scanned document support |

### API & Interface
| Component | Technology | Rationale |
|-----------|------------|-----------|
| REST API | FastAPI | Async, auto-docs, type hints |
| Web UI | Streamlit | Rapid prototyping, easy deployment |
| CLI | Typer | Modern CLI with type hints |
| Task Queue | Celery + Redis | Background document processing |

### Infrastructure
| Component | Technology | Rationale |
|-----------|------------|-----------|
| Containerization | Docker | Consistent environments |
| Orchestration | Docker Compose | Multi-service coordination |
| Database | PostgreSQL | User data, sessions, audit logs |
| Cache | Redis | Session state, API caching |

## 3. Core Agent Modules

### 3.1 Classification Engine
Determines device class (I, II, III, IV) based on Health Canada rules.

```python
class ClassificationEngine:
    """
    Implements Health Canada SOR/98-282 Schedule 1 Rules
    and SaMD classification framework (IMDRF N12)
    """

    def classify_device(self, device_info: DeviceInfo) -> ClassificationResult:
        # Rule-based + LLM-assisted classification
        pass

    def classify_samd(self, samd_info: SaMDInfo) -> SaMDClassification:
        # IMDRF SaMD classification matrix
        # Significance of information × Healthcare situation
        pass

    def get_classification_rationale(self) -> str:
        # Explainable AI - cite specific regulations
        pass
```

**Classification Decision Tree:**
```
Device Input
    │
    ├─► Is it Software as Medical Device (SaMD)?
    │       │
    │       ├─► YES → Apply IMDRF SaMD Framework
    │       │           │
    │       │           ├─► Healthcare Situation (Critical/Serious/Non-serious)
    │       │           └─► Information Significance (Treat/Diagnose/Drive/Inform)
    │       │           └─► → Class I, II, III, or IV
    │       │
    │       └─► NO → Apply Schedule 1 Rules
    │                   │
    │                   ├─► Rule 1-4: Non-invasive devices
    │                   ├─► Rule 5-8: Invasive devices
    │                   ├─► Rule 9-12: Active devices
    │                   └─► Rule 13-16: Special rules (IVD, etc.)
    │
    └─► Output: Device Class + Regulatory Pathway
```

### 3.2 Pathway Advisor
Guides users through the correct regulatory pathway.

```python
class PathwayAdvisor:
    """
    Determines MDEL vs MDL requirements and sequences
    """

    def get_pathway(self, classification: ClassificationResult) -> RegulatoryPathway:
        # Returns complete pathway with steps
        pass

    def calculate_timeline(self, pathway: RegulatoryPathway) -> Timeline:
        # Class II: 15 days, Class III: 75 days, Class IV: 90 days
        pass

    def calculate_fees(self, pathway: RegulatoryPathway) -> FeeBreakdown:
        # Current Health Canada fee schedule
        pass
```

### 3.3 Documentation Generator
Assists with documentation preparation.

```python
class DocumentationGenerator:
    """
    Generates document templates and validates completeness
    """

    def generate_imdrf_toc(self, device_info: DeviceInfo) -> IMDRFTableOfContents:
        # Health Canada adapted IMDRF ToC structure
        pass

    def validate_submission(self, documents: List[Document]) -> ValidationResult:
        # Check completeness against requirements
        pass

    def generate_checklist(self, classification: ClassificationResult) -> Checklist:
        # Dynamic checklist based on device type
        pass
```

### 3.4 Compliance Checker
Validates compliance with standards and regulations.

```python
class ComplianceChecker:
    """
    Checks compliance with ISO 13485, IEC 62304, cybersecurity requirements
    """

    def check_qms_requirements(self, qms_info: QMSInfo) -> ComplianceReport:
        # ISO 13485:2016 compliance check
        pass

    def check_cybersecurity(self, device_info: DeviceInfo) -> CybersecurityReport:
        # IEC 62304, SBOM requirements
        pass

    def check_clinical_evidence(self, clinical_data: ClinicalData) -> ClinicalReport:
        # Clinical evidence requirements per class
        pass
```

## 4. Data Flow

### 4.1 Document Ingestion Pipeline

```
Raw Documents (PDF/DOCX/MD)
         │
         ▼
┌─────────────────────┐
│ Document Loader     │
│ - Extract text      │
│ - Extract tables    │
│ - Extract metadata  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Text Preprocessor   │
│ - Clean whitespace  │
│ - Normalize unicode │
│ - Remove headers    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Semantic Chunker    │
│ - Split by section  │
│ - Overlap chunks    │
│ - Preserve context  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Metadata Tagger     │
│ - Document type     │
│ - Regulation ref    │
│ - Device class      │
│ - Effective date    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Embedding Generator │
│ - OpenAI embeddings │
│ - Batch processing  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Vector Store        │
│ - ChromaDB insert   │
│ - Index metadata    │
└─────────────────────┘
```

### 4.2 Query Processing Pipeline

```
User Query
     │
     ▼
┌─────────────────────┐
│ Intent Classifier   │
│ - Classification?   │
│ - Pathway?          │
│ - Documentation?    │
│ - General question? │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Query Rewriter      │
│ - Add context       │
│ - Regulatory terms  │
│ - Expand acronyms   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Hybrid Retrieval    │
│ - Vector search     │
│ - Keyword search    │
│ - Metadata filter   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Reranker            │
│ - Cross-encoder     │
│ - Relevance scoring │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Context Builder     │
│ - Top-k chunks      │
│ - Source citations  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ LLM Response Gen    │
│ - Claude/GPT-4      │
│ - Structured output │
│ - Citations         │
└─────────────────────┘
```

## 5. Agent Architecture (LangGraph)

```python
from langgraph.graph import StateGraph, END

# Define agent state
class AgentState(TypedDict):
    messages: List[Message]
    device_info: Optional[DeviceInfo]
    classification: Optional[ClassificationResult]
    pathway: Optional[RegulatoryPathway]
    checklist: Optional[Checklist]
    retrieved_context: List[Document]

# Build the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("router", route_query)
workflow.add_node("classifier", classify_device)
workflow.add_node("pathway_advisor", advise_pathway)
workflow.add_node("doc_generator", generate_documents)
workflow.add_node("retriever", retrieve_context)
workflow.add_node("responder", generate_response)

# Add edges
workflow.add_conditional_edges(
    "router",
    determine_next_step,
    {
        "classify": "classifier",
        "pathway": "pathway_advisor",
        "document": "doc_generator",
        "general": "retriever"
    }
)
workflow.add_edge("classifier", "pathway_advisor")
workflow.add_edge("pathway_advisor", "responder")
workflow.add_edge("doc_generator", "responder")
workflow.add_edge("retriever", "responder")
workflow.add_edge("responder", END)

# Compile
agent = workflow.compile()
```

## 6. Security & Compliance

### Data Protection
- All PHI/PII encrypted at rest (AES-256)
- TLS 1.3 for data in transit
- No retention of sensitive device details beyond session
- Audit logging for all queries

### Access Control
- Role-based access (Admin, Reviewer, User)
- API key authentication
- Rate limiting per user/organization

### Compliance
- SOC 2 Type II ready architecture
- PIPEDA compliant data handling
- Audit trail for regulatory submissions

## 7. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         PRODUCTION                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Load        │  │ API         │  │ API         │              │
│  │ Balancer    │─▶│ Server 1    │  │ Server 2    │              │
│  │ (nginx)     │  │ (FastAPI)   │  │ (FastAPI)   │              │
│  └─────────────┘  └──────┬──────┘  └──────┬──────┘              │
│                          │                │                      │
│                          └────────┬───────┘                      │
│                                   │                              │
│  ┌─────────────┐  ┌───────────────▼───────────────┐             │
│  │ Redis       │  │ PostgreSQL                    │             │
│  │ (Cache)     │  │ (Primary + Replica)           │             │
│  └─────────────┘  └───────────────────────────────┘             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐                               │
│  │ Pinecone    │  │ S3          │                               │
│  │ (Vectors)   │  │ (Documents) │                               │
│  └─────────────┘  └─────────────┘                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 8. API Design

### REST Endpoints

```
POST /api/v1/classify
  - Input: DeviceInfo JSON
  - Output: ClassificationResult

POST /api/v1/pathway
  - Input: ClassificationResult
  - Output: RegulatoryPathway with timeline

POST /api/v1/checklist
  - Input: DeviceInfo + Classification
  - Output: Dynamic checklist

POST /api/v1/chat
  - Input: Message + ConversationHistory
  - Output: AssistantResponse with citations

POST /api/v1/documents/ingest
  - Input: PDF/DOCX file
  - Output: Ingestion status

GET /api/v1/documents/search
  - Input: Query string + filters
  - Output: Relevant document chunks
```

## 9. Monitoring & Observability

- **Metrics**: Prometheus + Grafana
- **Logging**: Structured JSON logs → ELK Stack
- **Tracing**: OpenTelemetry for request tracing
- **Alerts**: PagerDuty integration for critical issues

## 10. Future Enhancements

1. **Multi-jurisdiction support** (FDA, EU MDR, TGA)
2. **Automated form filling** with OCR validation
3. **Real-time regulatory updates** from Health Canada RSS
4. **Collaborative workspace** for submission teams
5. **Integration with MDALL** (Medical Devices Active Licence Listing)
