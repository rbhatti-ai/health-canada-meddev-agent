# CLAUDE.md — AGENT OPERATING DIRECTIVE

## READ THIS FIRST — MANDATORY

Before making ANY architectural, schema, AI, workflow, or infrastructure decisions, you MUST read:

👉 `/docs/architecture/REGULATORY_EXECUTION_PLATFORM_ARCHITECTURE.md`

That document is the governing constitution of this platform.

If a chat instruction conflicts with the architecture document:

**THE ARCHITECTURE DOCUMENT WINS.**

No exceptions.

---

# PLATFORM IDENTITY

This system is being built as:

## 👉 Regulatory Execution Infrastructure

NOT a chatbot.  
NOT a template generator.  
NOT an AI gimmick.

Optimize for:

- auditability  
- traceability  
- explainability  
- regulatory defensibility  
- security  

Over speed.

Over cleverness.

Over novelty.

---

# PRIMARY ENGINEERING DIRECTIVES

## 1. DO NOT BREAK EXISTING FUNCTIONALITY

Before modifying code:

- Understand dependencies  
- Evaluate blast radius  
- Prefer additive changes  
- Use feature flags when appropriate  

Avoid sweeping refactors.

---

## 2. STRUCTURE FIRST. AI SECOND.

AI operates ON structured data.

Never the reverse.

Prefer:

Schemas → Rules → Engines → AI Assist

Avoid:

Chat → Guess → Generate.

---

## 3. TRACEABILITY IS THE PRODUCT WEDGE

When uncertain what to prioritize, favor systems that strengthen:

Claim → Risk → Control → Verification → Evidence linking.

Auditors trust traceability.

Customers pay for traceability.

Protect it.

---

## 4. NEVER FABRICATE REGULATORY INFORMATION

Do NOT invent:

- requirements  
- standards  
- pathways  
- citations  

If unsure:

Label clearly:

> "Citation required."

---

## 5. HUMAN-IN-THE-LOOP IS REQUIRED

No AI-generated regulatory artifact is final without human approval.

Always store:

- provenance  
- inputs  
- outputs  
- model  
- timestamp  
- reviewer  

---

## 6. EXPLAINABILITY IS A FEATURE

Every meaningful output should answer:

- Why was this generated?
- What triggered it?
- What data was used?
- What is the confidence level?

No black boxes.

---

## 7. VERSION EVERYTHING

Regulatory systems require historical reconstruction.

Prefer immutable records + version pointers.

Audit trails are infrastructure — not enhancements.

---

## 8. SECURITY IS NON-NEGOTIABLE

Assume enterprise customers.

Enforce:

- tenant isolation  
- row-level security  
- least-privilege access  
- signed URLs  

Never expose sensitive artifacts publicly.

---

# IMPLEMENTATION PRIORITY ORDER

When planning work, bias toward:

1️⃣ Regulatory Twin  
2️⃣ Traceability Engine  
3️⃣ Evidence Gap Detection  
4️⃣ Readiness Dashboard  
5️⃣ Document Orchestration  
6️⃣ Deficiency Workflows  

Avoid premature complexity.

Earn scale.

---

# LANGUAGE SAFETY (VERY IMPORTANT)

Never output:

❌ "You are compliant."  
❌ "This will pass FDA."  

Always prefer:

✅ "Potential gaps detected relative to regulatory expectations."  
✅ "Draft for professional review."

---

# WHEN STARTING ANY MAJOR TASK

First:

✅ Inspect the repository  
✅ Understand current architecture  
✅ Identify risks  
✅ Propose a plan  

THEN implement.

Not the reverse.

---

# ENGINEERING PHILOSOPHY

Move deliberately.

Favor durability over speed.  
Favor clarity over cleverness.  
Favor structure over AI theatrics.

You are not building software.

You are building **regulatory infrastructure.**
