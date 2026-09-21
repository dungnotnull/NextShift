# NextShift

NextShift turns AI displacement into internal advancement for frontline workers — an agentic career companion on the phone they already own.

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg) ![Hackathon](https://img.shields.io/badge/AWS%20CDS-Agentic%20AI%20Hackathon-orange.svg)

## The Problem

The WEF Future of Jobs Report 2025 projects 92M jobs displaced and 170M new roles created by 2030 — the real problem is the transition gap in between, and Frey & Osborne estimated 47% of US jobs are at risk of automation. Frontline workers (~80% of the global workforce) have no corporate email, no laptop, and no LMS access; messaging apps are their only digital channel. Meanwhile, enterprises automating operations face responsible-automation pressure: layoff costs of 50–200% of annual salary per replacement, lost institutional knowledge, and reputational risk. NextShift closes the gap by converting displacement into internal advancement, delivered entirely over WhatsApp, SMS, RCS, and email.

## How It Works (the Maria story)

1. **HR uploads** an Automation Impact Map (affected roles + emerging internal roles) on the HR dashboard; workers are ingested into DynamoDB.
2. Maria receives an **SMS invite** (AWS EUM) with an opt-in link — no smartphone app required.
3. She continues on **WhatsApp** (AWS End User Messaging Social): a conversational skills audit plus a short adaptability/anxiety profiling.
4. The agent matches her skills against internal roles and proposes a **pathway** — Maria: Robot Fleet Operator at a 50% match, with transferable skills highlighted.
5. **Daily 2-minute micro-lessons** on WhatsApp with spaced repetition and retrieval practice; wrong answers get an explanation and a rescheduled repeat.
6. On milestone: a **SES email** with transcript + certificate + one-tap internal application, and an **RCS card** for interview scheduling.

All channels share one **AgentCore Memory** (one session per worker) — the conversation picks up exactly where it left off, cross-channel.

## Architecture

```
HR Dashboard (Next.js) ──► API Gateway ──► hr-api Lambda ──► DynamoDB
                                                │ invite
                                                ▼
Worker phone ◄──SMS── EUM (pinpoint-sms-voice-v2) ◄── invite Lambda
Worker phone ◄──► WhatsApp (EUM Social / socialmessaging) ──SNS──► webhook Lambda
                                                                       │
                                                     bedrock-agentcore invoke_agent_runtime
                                                                       ▼
                                              AgentCore Runtime (Strands agent, Nova Lite)
                                              ├── 6 tools: match_role, get_progress, next_lesson,
                                              │   submit_answer, enroll_pathway, escalate_human
                                              ├── AgentCore Memory (cross-channel, per worker)
                                              └── Guardrails (crisis + no-promises constitution)
EventBridge (14:00 UTC daily) ──► dispatcher Lambda ──► WhatsApp/SMS lessons
                                                   └──► SES milestone email + RCS card
```

See [docs/architecture.md](docs/architecture.md) for resource names and per-component details.

## Research Foundation (28 sources)

### A. Labor economics

| # | Source | Applied to |
|---|---|---|
| 1 | WEF Future of Jobs Report 2025 (92M displaced / 170M created) | Opening numbers for description & video |
| 2 | Frey & Osborne (2017), The Future of Employment — 47% US jobs at risk | Problem statement |
| 3 | Acemoglu & Restrepo (2019), Automation and New Tasks (JEP) — reinstatement effect | Core thesis: internal mobility converts displacement into job creation |
| 4 | McKinsey Global Institute (2017), Jobs Lost, Jobs Gained — 375M must switch | Scale of problem |
| 5 | Arntz, Gregory & Zierahn (2016, OECD) — task-level automation risk ~9% | Skill-decomposition design: many tasks remain transferable |

### B. Career-transition psychology

| # | Source | Applied to |
|---|---|---|
| 6 | Savickas & Porfeli (2012), Career Adapt-Abilities Scale (concern, control, curiosity, confidence) | Conversational profiling instrument; agent intervenes on weakest dimension |
| 7 | Wang & Wang (2022), AI Anxiety Scale (4 dimensions; predicts motivated learning) | Detect job-replacement anxiety early; adapt agent tone (reassure vs. push) |
| 8 | Deci & Ryan (2000), Self-Determination Theory | Conversation design: worker chooses pathway (autonomy), sees progress (competence), connects with peers (relatedness) |
| 9 | Dweck (2006), Growth Mindset | Message framing: "skills are buildable", never "you lack X" |
| 10 | Prochaska & DiClemente (1983), Transtheoretical Model | Journey state machine: precontemplation → contemplation → preparation → action; different nudges per stage |
| 11 | Fogg (2009), Behavior Model B=MAP | Message timing rules; lessons engineered to be tiny (easy) |
| 12 | Thaler & Sunstein (2008), Nudge | Smart defaults in rich cards ("today's 2-min lesson" one tap) |

### C. Learning science

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

### E. Agent engineering

| # | Source | Applied to |
|---|---|---|
| 23 | Lewis et al. (2020), Retrieval-Augmented Generation | Role/skill retrieval into agent context |
| 24 | Yao et al. (2023), ReAct | Agent loop: reason → act (tools: match-role, get-progress, enroll-pathway) |
| 25 | Packer et al. (2023), MemGPT | Memory tiers: core profile vs. archived conversation history |
| 26 | Bai et al. (2022), Constitutional AI | Guardrail policy for a vulnerable population: no job guarantees, no legal advice, crisis escalation to humans |

### F. Official documentation

| # | Source | Applied to |
|---|---|---|
| 27 | Amazon Bedrock AgentCore docs (Runtime, Memory, Identity) | Agent orchestration, cross-channel memory, per-worker authZ |
| 28 | AWS EUM Social / EUM (SMS, RCS) / SES docs; Meta WhatsApp Business Platform (24h window, templates, opt-in); AWS Well-Architected | Multi-CDS usage, Meta policy compliance (WhatsApp prize eligibility), reproducible architecture |

## Tech Stack

Python 3.12 with the Strands SDK, running on Amazon Bedrock AgentCore (Runtime and Memory) powered by Amazon Nova Lite. Communications use AWS End User Messaging Social (WhatsApp), End User Messaging SMS/RCS, and Amazon SES, backed by DynamoDB, EventBridge, and API Gateway, all provisioned with AWS CDK. The HR dashboard is a Next.js app.

## Getting Started

Full deployment steps are in [docs/runbook.md](docs/runbook.md). Summary:

1. Console prerequisites (start early — approvals take days): link a WhatsApp Business Account in EUM Social, approve the `nextshift_invite` template, create an SMS phone pool, verify an SES identity, enable Nova Lite model access.
2. `cd infra && npx aws-cdk deploy nextshift-core nextshift-messaging` — note the `ApiUrl` output.
3. Create the agent memory: `python scripts/create_memory.py` (stores `/nextshift/memory-id` in SSM).
4. Deploy the agent: `agentcore deploy src/nextshift/agent/entrypoint.py`, then redeploy messaging with `AGENT_RUNTIME_ARN`, `WA_PHONE_ID`, `SMS_POOL_ID`, `SES_FROM`.
5. Seed and smoke: `python scripts/seed.py`, invoke `nextshift-dispatcher`, text "hi" to the WhatsApp test number.

Frontend:

```bash
cd frontend && npm install
NEXT_PUBLIC_API_URL=<ApiUrl from cdk outputs> npm run build
npm start
```

## Safety

- **Guardrails:** a constitution-inspired policy — the agent never promises employment, never gives legal or financial advice.
- **Crisis escalation:** crisis keywords trigger immediate escalation to the 988 lifeline and an HR-facing human queue.
- **Consent & compliance:** WhatsApp opt-in before any messaging; template messages outside the 24-hour window (Meta policy).
- **Data minimization:** only what the pathway needs; no PII in LLM prompts beyond first name and role; DynamoDB encryption at rest.

## Demo Video

The 3-minute recording follows the script in [docs/demo-script.md](docs/demo-script.md) — the Maria story from impact map to milestone email.

## License

MIT — see [LICENSE](LICENSE).
