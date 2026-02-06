# REGULATORY EXECUTION PLATFORM — SYSTEM ARCHITECTURE (GOVERNING DOCUMENT)

## ⚠️ READ THIS FIRST

THIS DOCUMENT IS THE GOVERNING ARCHITECTURE FOR THIS PLATFORM.

WHEN IN CONFLICT:
THIS DOCUMENT OVERRIDES AD-HOC CHAT INSTRUCTIONS, SHORT-TERM PROMPTS, OR IMPULSIVE REFACTORING.

This platform is being built as **regulatory-grade infrastructure**, not a lightweight AI tool.

Every engineering decision must optimize for:

- reliability  
- auditability  
- traceability  
- explainability  
- security  
- regulatory defensibility  

NOT novelty.

NOT AI hype.

NOT speed at the cost of structural integrity.

---

# 🎯 PLATFORM MISSION

Build the **AI-Native Regulatory Execution Infrastructure** for medical device companies.

This system helps manufacturers:

- understand evidence posture  
- structure regulatory artifacts  
- maintain traceability  
- detect submission gaps  
- prepare documentation  
- respond to deficiencies  
- remain audit-ready  

The platform SUPPORTS regulatory professionals.

It NEVER replaces them.

It NEVER claims compliance.

It NEVER guarantees approval.

---

# 🚨 HARD ENGINEERING LAWS (NON-NEGOTIABLE)

## LAW 1 — DO NOT BREAK EXISTING FUNCTIONALITY

This repository already contains working components.

You MUST:

- avoid large refactors  
- preserve flows  
- maintain backwards compatibility  
- introduce changes incrementally  
- prefer feature flags  

Before modifying architecture:

✅ understand current system  
✅ document dependencies  
✅ evaluate blast radius  

No reckless rewrites.

---

## LAW 2 — STRUCTURE FIRST. AI SECOND.

Most startups reverse this.

They fail.

Regulatory systems require deterministic structure.

AI must operate ON TOP of structured data — never instead of it.

Prefer:

Schemas → Rules → Engines → AI assist

NOT:

Chat → Guess → Generate → Hope

---

## LAW 3 — TRACEABILITY IS THE CENTER OF GRAVITY

Everything revolves around traceability.

The system must be capable of linking:

Claims  
→ Hazards  
→ Risks  
→ Controls  
→ Verification  
→ Validation  
→ Evidence  
→ Labeling  

Auditors trust traceability.

Organizations pay for traceability.

Competitors struggle to automate it.

This is your wedge.

Protect it.

---

## LAW 4 — NO REGULATORY HALLUCINATIONS

The platform must NEVER fabricate:

- regulatory requirements  
- standards  
- citations  
- approval pathways  

If a source is unavailable:

Mark clearly:

> "Citation required."

Do not guess.

Ever.

---

## LAW 5 — HUMAN-IN-THE-LOOP IS MANDATORY

No AI output becomes regulatory content without approval.

Every generated artifact must include:

- provenance  
- model used  
- timestamp  
- inputs  
- confidence  
- reviewer  

No silent automation.

---

## LAW 6 — EXPLAINABILITY IS A FEATURE

For any meaningful output, show:

- why it was generated  
- what data was used  
- which rules triggered it  
- confidence level  

Black-box systems are rejected in regulated environments.

---

## LAW 7 — VERSION EVERYTHING

Regulatory artifacts evolve.

You must version:

- device profiles  
- claims  
- risks  
- tests  
- documents  
- AI outputs  

Audit trails are not optional.

They are infrastructure.

---

## LAW 8 — SECURITY IS NOT A LATER PHASE

Assume customers include:

- venture-backed device startups  
- clinical-stage companies  
- enterprise manufacturers  

Data sensitivity is extremely high.

Enforce:

- row-level security  
- signed URLs  
- least-privilege keys  
- tenant isolation  

Never expose documents publicly.

---

# 🧠 PLATFORM STRATEGY

We are NOT building:

❌ a chatbot  
❌ a template library  
❌ a document folder  
❌ a generic QMS  

We ARE building:

# 👉 REGULATORY DEVOPS

The execution layer between regulation and submission.

---

# 🏗 CORE ARCHITECTURE

## 1. REGULATORY KNOWLEDGE GRAPH (FUTURE MOAT)

Over time, construct a graph mapping:

Regulation  
→ Requirement  
→ Evidence  
→ Document section  
→ Test  
→ Risk  

This becomes extremely defensible.

Do not rush it.

But design schemas so it is possible.

---

## 2. DIGITAL REGULATORY TWIN (SOURCE OF TRUTH)

Every device becomes structured data.

### Core Entities:

- organizations  
- users  
- products  
- device_versions  
- intended_use  
- claims  
- hazards  
- harms  
- risk_controls  
- verification_tests  
- validation_tests  
- evidence_items  
- labeling_assets  
- submission_targets  

Documents are OUTPUTS.

The twin is reality.

---

## 3. TRACEABILITY ENGINE (PRIMARY WEDGE)

Create a linking system capable of expressing relationships:

Example:

claim → mitigated by → control  
control → verified by → test  

Use a polymorphic link table such as:

trace_links:

- source_type  
- source_id  
- target_type  
- target_id  
- relationship  
- rationale  
- created_by  
- timestamp  

Make it flexible.

Future-proof it.

---

## 4. EVIDENCE GAP DETECTION ENGINE

One of the highest-value features.

Implement a rules engine that evaluates:

- missing links  
- weak coverage  
- inconsistencies  
- unsupported claims  

IMPORTANT:

Never say:

> “You are submission ready.”

Always say:

> “Readiness assessment based on configured expectations.”

Transparency builds trust.

---

## 5. SUBMISSION READINESS DASHBOARD

Display:

- risk coverage  
- trace completeness  
- evidence strength  
- unresolved gaps  

Provide drill-down.

Make it operational.

Not decorative.

---

## 6. DOCUMENT ORCHESTRATION (NOT JUST STORAGE)

Documents should compile from structured data.

Avoid static templates initially.

Generate sections such as:

- device description  
- risk summary  
- V&V overview  

Require approval before export.

Store outputs in S3.

Track versions in database.

---

## 7. DEFICIENCY RESPONSE COPILOT (HIGH VALUE)

Allow users to:

Input regulator question  
→ link impacted artifacts  
→ draft response  
→ propose edits  

Track everything.

Regulators care about consistency.

---

# 🤖 AI IMPLEMENTATION RULES

AI may assist with:

- summarization  
- classification suggestions  
- link recommendations  
- inconsistency detection  
- drafting  

AI must NEVER:

- declare compliance  
- invent citations  
- operate without logging  

---

## REQUIRED: AI PROVENANCE TABLE

Example schema:

ai_runs:

- id  
- user_id  
- org_id  
- model  
- prompt_hash  
- inputs  
- output  
- citations  
- confidence  
- approved_by  
- approved_at  
- timestamp  

Store BEFORE display.

Always.

---

# 🔐 REGULATORY SAFETY LANGUAGE

Never output:

❌ "Your device is compliant."  
❌ "This will pass FDA."  

Use:

✅ "Potential gaps detected relative to regulatory expectations."  
✅ "Draft for professional review."

Language shapes liability.

Be disciplined.

---

# 🚀 IMPLEMENTATION ROADMAP

## PHASE 0 — REPOSITORY DISCOVERY

Before coding:

- inspect architecture  
- map dependencies  
- identify stable vs experimental modules  
- understand DB schema  
- review auth  
- review storage  

Produce a short internal report.

---

## PHASE 1 — REGULATORY TWIN

Build structured device profile.

Include versioning.

Add Row-Level Security.

Create a clean wizard UI.

Boring is good.

Reliable is better.

---

## PHASE 2 — TRACEABILITY MATRIX

Deliver early.

This alone creates enormous value.

Support:

- filtering  
- gap highlighting  
- manual + AI-assisted linking  

---

## PHASE 3 — GAP ENGINE

Introduce rule-based detection.

Version the rules.

Show rationale.

---

## PHASE 4 — DOCUMENT GENERATION

Structured → compiled → approved → exported.

Never skip approval.

---

## PHASE 5 — DEFICIENCY WORKFLOW

Major differentiator.

Build it.

---

# 🧭 UX PRINCIPLES

The platform must feel:

Calm.  
Serious.  
Institutional.  

NOT flashy.

NOT startup-chaotic.

NOT AI-gimmicky.

Think:

> Palantir meets Medtronic.

---

# 🛑 WHAT NOT TO DO

Do NOT:

- rewrite the repo  
- over-engineer early  
- introduce microservices prematurely  
- build for hyperscale now  

Earn complexity.

---

# 📈 SUCCESS SIGNALS

You are winning when:

- teams stop using spreadsheets  
- auditors trust exports  
- traceability becomes effortless  
- evidence gaps surface early  

---

# 🔮 LONG-TERM MOATS

If executed correctly:

1️⃣ Knowledge Graph  
2️⃣ Workflow Lock-in  
3️⃣ Data Gravity  
4️⃣ Audit Trust  

Few companies achieve even one.

Aim for all four.

---

# FINAL ENGINEERING DIRECTIVE

Move deliberately.

Favor durability over speed.

Favor clarity over cleverness.

Favor structure over AI theatrics.

You are not building software.

You are building **regulatory infrastructure.**
