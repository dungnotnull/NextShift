# NextShift — Design Spec

**Hackathon:** AWS Communication Developer Services (CDS) Agentic AI Partner Hackathon
**Deadline:** 2026-10-28 (submission 1:00pm PDT per Devpost listing)
**Date:** 2026-09-21
**Status:** Approved by team

---

## 1. One-line Pitch

NextShift is an AI career companion that turns "AI displacement" into "internal advancement" for frontline workers — warehouse, retail, manufacturing, logistics — delivered entirely over the phone they already own (WhatsApp, SMS, RCS) plus email, with AWS CDS as the communications backbone and Amazon Bedrock AgentCore as the agentic brain.

## 2. Problem

- WEF Future of Jobs Report 2025: 92M jobs displaced, 170M new roles by 2030. The transition gap is the problem — not the net number.
- Frontline workers (~80% of the global workforce) have no corporate email, no laptop, no LMS access. Messaging apps are their only channel.
- Enterprises automating operations face a "responsible automation" problem: layoff costs (50–200% of annual salary per replacement, SHRM), lost institutional knowledge, and reputational/legal risk.
- Current corporate messaging usage (OTP, notifications, scripted chatbots) is one-way and rigid — exactly what the hackathon asks teams to move beyond.

## 3. Who Pays / Who Benefits (B2B2C)

| Actor | Role | Benefit |
|---|---|---|
| Enterprise (HR/L&D) | Buyer | Retention (internal movers are 40% more likely to stay 3+ years, LinkedIn 2024; 5.4 vs 2.9 yr tenure), lower replacement cost, responsible-automation story |
| Frontline worker | End user | Personalized reskilling pathway, delivered on their own phone, ending in an internal job application |
| AWS Partner | Vendor | Repeatable offering, AWS Marketplace listing, applicable across retail/logistics/manufacturing customers |

## 4. Core User Journey (demo storyline)

1. HR uploads an **Automation Impact Map** (affected roles + emerging internal roles) on the HR Dashboard.
2. Worker receives **SMS invite** (AWS EUM) with opt-in link — no smartphone app required.
3. Worker continues on **WhatsApp** (AWS End User Messaging Social): conversational skills audit + short adaptability/AI-anxiety profiling.
4. Agent matches skills against new internal roles via RAG over O*NET/ESCO + internal job data → proposes a personalized **pathway**.
5. Daily **2-minute micro-lessons** on WhatsApp with spaced repetition and retrieval practice; agent tracks progress.
6. On milestone: **email via SES** delivers learning transcript + certificate + one-tap internal job application.
7. **RCS** rich card for interview scheduling; **SMS fallback** where rich channels are unavailable.
8. All channels share **AgentCore Memory** — conversation picks up where it left off, cross-channel.

Demo persona: "Maria, 45, 12 years warehouse associate → robot fleet operator in 8 weeks."

## 5. Research Foundation (28 sources, each mapped to a feature)

### A. Labor economics — underpins Impact (20% of score)

| # | Source | Applied to |
|---|---|---|
| 1 | WEF Future of Jobs Report 2025 (92M displaced / 170M created) | Opening numbers for description & video |
| 2 | Frey & Osborne (2017), The Future of Employment — 47% US jobs at risk | Problem statement |
| 3 | Acemoglu & Restrepo (2019), Automation and New Tasks (JEP) — reinstatement effect | Core thesis: internal mobility converts displacement into job creation |
| 4 | McKinsey Global Institute (2017), Jobs Lost, Jobs Gained — 375M must switch | Scale of problem |
| 5 | Arntz, Gregory & Zierahn (2016, OECD) — task-level automation risk ~9% | Skill-decomposition design: many tasks remain transferable |

### B. Career-transition psychology — shapes agent behavior

| # | Source | Applied to |
|---|---|---|
| 6 | Savickas & Porfeli (2012), Career Adapt-Abilities Scale (concern, control, curiosity, confidence) | Conversational profiling instrument; agent intervenes on weakest dimension |
| 7 | Wang & Wang (2022), AI Anxiety Scale (4 dimensions; predicts motivated learning) | Detect job-replacement anxiety early; adapt agent tone (reassure vs. push) |
| 8 | Deci & Ryan (2000), Self-Determination Theory | Conversation design: worker chooses pathway (autonomy), sees progress (competence), connects with peers (relatedness) |
| 9 | Dweck (2006), Growth Mindset | Message framing: "skills are buildable", never "you lack X" |
| 10 | Prochaska & DiClemente (1983), Transtheoretical Model | Journey state machine: precontemplation → contemplation → preparation → action; different nudges per stage |
| 11 | Fogg (2009), Behavior Model B=MAP | Message timing rules; lessons engineered to be tiny (easy) |
| 12 | Thaler & Sunstein (2008), Nudge | Smart defaults in rich cards ("today's 2-min lesson" one tap) |

### C. Learning science — micro-learning engine

| # | Source | Applied to |
|---|---|---|
| 13 | Knowles (1980), Andragogy | Problem-centered lessons tied to shop-floor scenarios |
| 14 | Cepeda et al. (2006), spacing-effect meta-analysis | Spaced schedule: 1d → 3d → 7d repeats |
| 15 | Roediger & Karpicke (2006), testing effect | Micro-lessons are recall questions, not slides |
| 16 | Dunlosky et al. (2013), learning-techniques review | Only high-utility techniques used (retrieval + distributed practice) |
| 17 | Ericsson et al. (1993), deliberate practice | Targeted exercises on weak skills with immediate agent feedback |
| 18 | Castleman & Page (2015), Summer Nudging RCT | Direct RCT evidence that personalized texting improves education outcomes for vulnerable populations — the channel thesis |

### D. Skills data & business case

| # | Source | Applied to |
|---|---|---|
| 19 | O*NET (US Dept. of Labor) | Primary skills/occupation knowledge base for RAG |
| 20 | ESCO (European Commission) | Global/EU skills taxonomy complement |
| 21 | LinkedIn Economic Graph (2024) internal-mobility data | Buyer ROI: retention +40%, tenure 5.4 vs 2.9 yrs |
| 22 | SHRM / Work Institute turnover-cost research | Business-case slide numbers |

### E. Agent engineering — Technical Execution (40% of score)

| # | Source | Applied to |
|---|---|---|
| 23 | Lewis et al. (2020), Retrieval-Augmented Generation | Role/skill retrieval into agent context |
| 24 | Yao et al. (2023), ReAct | Agent loop: reason → act (tools: match-role, get-progress, enroll-pathway) |
| 25 | Packer et al. (2023), MemGPT | Memory tiers: core profile vs. archived conversation history |
| 26 | Bai et al. (2022), Constitutional AI | Guardrail policy for a vulnerable population: no job guarantees, no legal advice, crisis escalation to humans |

### F. Official documentation (eligibility + architecture)

| # | Source | Applied to |
|---|---|---|
| 27 | Amazon Bedrock AgentCore docs (Runtime, Memory, Identity) | Agent orchestration, cross-channel memory, per-worker authZ |
| 28 | AWS EUM Social / EUM (SMS, RCS) / SES docs; Meta WhatsApp Business Platform (24h window, templates, opt-in); AWS Well-Architected | Multi-CDS usage, Meta policy compliance (WhatsApp prize eligibility), reproducible architecture |

## 6. Architecture

```
HR Dashboard (Next.js, S3 + CloudFront)
   │  upload Automation Impact Map
   ▼
Amazon API Gateway ──► AWS Lambda ──► Amazon DynamoDB
                                        (workers, pathways, progress)
WhatsApp ◄────► AWS EUM Social ───────► Bedrock AgentCore Runtime
SMS / RCS ◄───► AWS EUM                       │
Email ◄──────── Amazon SES                    ├── AgentCore Memory (cross-channel state)
                                               ├── AgentCore Identity (worker-scoped credentials)
                                               └── Bedrock LLM (Nova Micro/Lite default, Claude for complex turns)
                                                      └── Role/skill retrieval: DynamoDB lookup grounded in O*NET/ESCO-style
                                                         skill data (RAG via Amazon OpenSearch reserved as stretch goal)
Amazon EventBridge Scheduler ──► daily micro-lesson + milestone + check-in triggers
CloudWatch (observability) + Bedrock guardrails (safety)
Everything deployed via AWS CDK (reproducibility criterion)
```

### Component responsibilities

- **Inbound webhook (API Gateway + Lambda):** receives WhatsApp/SMS/RCS events; normalizes to a channel-agnostic message envelope with worker ID.
- **AgentCore Runtime:** the brain. Tools: `match-role`, `get-progress`, `next-lesson`, `enroll-pathway`, `escalate-human`.
- **AgentCore Memory:** stores worker profile (core memory) and full cross-channel history (archive). Every channel reads/writes the same memory — the "continue where you left off" requirement.
- **AgentCore Identity:** scoped, short-lived credentials when the agent calls internal systems on the worker's behalf.
- **EventBridge Scheduler:** daily lesson dispatch, milestone detection, re-engagement nudges (Fogg/TTM-informed cadence).
- **SES:** milestone transcripts, certificates, long-form learning plans (email is the archive channel).
- **DynamoDB:** worker registry, pathway definitions, lesson progress, event log.
- **OpenSearch (stretch goal):** MVP matches roles via structured DynamoDB lookups over O*NET/ESCO-style skill data; vector search is a documented extension if time permits.

## 7. Feature Scope (build for demo)

In scope:
1. HR Dashboard: upload impact map (CSV), worker list, progress heatmap.
2. SMS invite + opt-in flow.
3. WhatsApp conversational profiling: skills audit + a questionnaire of at most 10 items derived from CAAS and AIAS dimensions.
4. Pathway matching (RAG) with 3 target roles seeded.
5. Daily micro-lesson flow with spaced repetition and retrieval questions.
6. Milestone email with certificate + internal application link.
7. RCS scheduling card + SMS fallback.
8. Cross-channel memory continuity.
9. Guardrails: refusal policy, anxiety-aware tone, human-escalation keyword detection.

Out of scope (explicitly):
- Real WABA production approval (use test number for demo; document production steps).
- Multi-language (English only; i18n hooks in place).
- Real payroll/HRIS integrations (mock data).
- Voice channel.

## 8. Safety & Compliance

- WhatsApp opt-in before any messaging; template messages for re-engagement outside the 24h window (Meta policy).
- Guardrail policy (Constitutional AI-inspired): never promise employment, never give legal/financial advice, escalate crisis keywords to a human queue immediately.
- Worker data minimization: only what the pathway needs; DynamoDB encryption at rest; no PII in LLM prompts beyond first name/role.

## 9. Judging-Criteria Mapping

| Criterion | Weight | How NextShift scores |
|---|---|---|
| Technical Execution | 40% | 3 CDS services + AgentCore + Bedrock + CDK IaC; RAG; cross-channel memory; reproducible |
| Potential Value/Impact | 20% | 92M-worker transition gap; buyer ROI with cited numbers; Marketplace-ready offering |
| Demo Presentation | 20% | Emotional end-to-end agentic story (Maria) crossing 4 channels in 3 minutes |
| Creativity | 10% | Only entry framed around frontline workers + responsible automation; evidence-based behavioral design |
| Functionality | 10% | Live working WhatsApp loop; fallback channels; scalable serverless design |

## 10. Key Risks

| Risk | Mitigation |
|---|---|
| WABA approval delay | Register early; demo on WhatsApp test number; RCS/SMS flow as backup |
| $50 AWS credit limit | Nova Micro/Lite for routine turns; Claude only where needed |
| 5-week runway | One fictional company, 3 roles, 2 pathways — depth over breadth |
| Sentiment-heavy domain | Guardrails + human escalation path built in from day 1 |

## 11. Deliverables Checklist (per Devpost)

- [ ] Repository (GitHub, MIT license) with all source + README run instructions
- [ ] Architecture diagram
- [ ] Text description (with research citations from Section 5)
- [ ] ~3-minute demo video (Maria storyline)
- [ ] Deployed URL or interaction instructions
- [ ] ACE opportunity ID with campaign code "AWS CDS Agentic AI Hackathon -Sept. 2026."
- [ ] WhatsApp usage description (for Meta Best-of-WhatsApp prize)
