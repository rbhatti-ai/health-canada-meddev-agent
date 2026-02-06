# Health Canada Medical Device Regulatory Agent

AI-powered assistant for navigating Health Canada medical device regulatory requirements.

## Features

- **Device Classification**: Determine device class (I-IV) using Health Canada rules and IMDRF SaMD framework
- **Regulatory Pathway**: Get step-by-step guidance with timelines and fees
- **Checklist Generation**: Dynamic checklists based on device classification
- **Document Search**: RAG-powered search of Health Canada guidance documents
- **Interactive Chat**: Conversational interface for regulatory questions

## Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key (for embeddings)
- Anthropic API key (for chat, optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/health-canada-meddev-agent.git
cd health-canada-meddev-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Usage

#### Command Line Interface

```bash
# Classify a device
meddev-agent classify \
  --name "CardioMonitor Pro" \
  --desc "AI-powered cardiac monitoring software" \
  --use "Continuous ECG monitoring for arrhythmia detection" \
  --software \
  --manufacturer "MedTech Inc"

# Get regulatory pathway
meddev-agent pathway --class III --software

# Start interactive chat
meddev-agent chat

# Ingest regulatory documents
meddev-agent ingest /path/to/documents

# Start API server
meddev-agent serve

# Launch Streamlit UI
meddev-agent ui
```

#### Python API

```python
from src.core.models import DeviceInfo, SaMDInfo, HealthcareSituation, SaMDCategory
from src.core.classification import classify_device
from src.core.pathway import get_pathway
from src.core.checklist import generate_checklist

# Classify a SaMD device
device = DeviceInfo(
    name="DiagnosticAI",
    description="ML-powered skin lesion analysis",
    intended_use="Assist dermatologists in melanoma screening",
    manufacturer_name="SkinTech",
    is_software=True,
)

samd = SaMDInfo(
    healthcare_situation=HealthcareSituation.SERIOUS,
    significance=SaMDCategory.DIAGNOSE,
    uses_ml=True,
)

result = classify_device(device, samd)
print(f"Device Class: {result.device_class.value}")  # Class III
print(f"Rationale: {result.rationale}")

# Get regulatory pathway
pathway = get_pathway(result, device, has_mdel=False)
print(f"Timeline: {pathway.timeline.total_days_min}-{pathway.timeline.total_days_max} days")
print(f"Total Fees: ${pathway.fees.total:,.0f} CAD")

# Generate checklist
checklist = generate_checklist(result, device)
print(f"Checklist items: {checklist.total_items}")
```

#### REST API

```bash
# Start the server
uvicorn src.api.main:app --reload

# Classify device
curl -X POST http://localhost:8000/api/v1/classify \
  -H "Content-Type: application/json" \
  -d '{
    "device_info": {
      "name": "TestDevice",
      "description": "A test device",
      "intended_use": "Testing",
      "manufacturer_name": "Test Inc",
      "is_software": true
    },
    "samd_info": {
      "healthcare_situation": "serious",
      "significance": "diagnose",
      "uses_ml": true
    }
  }'

# Get pathway
curl -X POST http://localhost:8000/api/v1/pathway \
  -H "Content-Type: application/json" \
  -d '{"device_class": "III", "is_software": true}'
```

### Docker

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access services
# API: http://localhost:8000
# UI: http://localhost:8501
```

## Knowledge Base

The agent is pre-loaded with **52 official Health Canada documents** comprising **2,093 searchable chunks**:

| Category | Documents | Description |
|----------|-----------|-------------|
| Regulations | 1 | Medical Devices Regulations (SOR/98-282) |
| Guidance | 25+ | Official Health Canada guidance documents |
| Standards | 2 | ISO 13485 and QMS requirements |
| Forms | 5 | Application forms (MDEL, MDL) |
| Checklists | 7 | Class-specific submission checklists |
| Flowcharts | 4 | Process timeline visualizations |

See [docs/KNOWLEDGE_BASE.md](docs/KNOWLEDGE_BASE.md) for detailed documentation of all sources.

## Project Structure

```
health-canada-meddev-agent/
├── src/
│   ├── core/              # Core business logic
│   │   ├── models.py      # Domain models
│   │   ├── classification.py  # Device classification engine
│   │   ├── pathway.py     # Regulatory pathway advisor
│   │   └── checklist.py   # Checklist management
│   ├── ingestion/         # Document processing
│   │   ├── loader.py      # Multi-format document loader
│   │   ├── chunker.py     # Semantic text chunking
│   │   ├── embedder.py    # Embedding generation
│   │   └── pipeline.py    # Ingestion orchestration
│   ├── retrieval/         # RAG components
│   │   ├── vectorstore.py # ChromaDB integration
│   │   ├── retriever.py   # Hybrid retrieval
│   │   └── reranker.py    # Result reranking
│   ├── agents/            # Agent orchestration
│   │   ├── tools.py       # LangChain tools
│   │   └── regulatory_agent.py  # Main agent
│   ├── api/               # FastAPI REST API
│   │   └── main.py
│   ├── ui/                # Streamlit interface
│   │   └── app.py
│   └── cli.py             # Command-line interface
├── configs/               # Configuration
│   └── settings.py
├── data/
│   ├── raw/               # Source documents
│   │   ├── checklists/    # Submission checklists (PDF)
│   │   └── flowcharts/    # Process flowcharts (PDF)
│   ├── processed/         # Processed chunks
│   └── vectorstore/       # ChromaDB with 2,093 embedded chunks
├── scripts/
│   └── ingest_documents.py  # Document ingestion script
├── tests/                 # Test suite
├── docs/
│   ├── ARCHITECTURE.md    # System architecture
│   └── KNOWLEDGE_BASE.md  # Data source documentation
├── pyproject.toml         # Project configuration
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Device Classification

### Health Canada Device Classes

| Class | Risk Level | MDL Required | Review Time | Example |
|-------|------------|--------------|-------------|---------|
| I | Lowest | No | N/A | Tongue depressors |
| II | Low-Moderate | Yes | 15 days | Blood pressure monitors |
| III | Moderate-High | Yes | 75 days | Insulin pumps |
| IV | Highest | Yes | 90 days | Pacemakers |

### SaMD Classification (IMDRF Framework)

The agent uses the IMDRF N12 classification matrix:

|  | Treat/Diagnose | Drive | Inform |
|--|----------------|-------|--------|
| **Critical** | Class IV | Class III | Class II |
| **Serious** | Class IV/III | Class II | Class II |
| **Non-serious** | Class III | Class II | Class I |

## Current Health Canada Fees (2024)

| Fee Type | Amount (CAD) |
|----------|--------------|
| MDEL Application | $4,590 |
| MDL Class II | $468 |
| MDL Class III | $7,658 |
| MDL Class IV | $23,130 |
| Annual Fee (Class III) | $831 |
| Annual Fee (Class IV) | $1,662 |

*Fees subject to change. Verify with Health Canada.*

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src/

# Format code
black src/

# Type checking
mypy src/
```

## License

MIT License - see LICENSE file for details.

## Disclaimer

This tool provides guidance based on Health Canada regulations and guidance documents. It is not a substitute for professional regulatory advice. Always verify requirements with Health Canada and consult qualified regulatory professionals for official submissions.
