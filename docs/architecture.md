# NextShift Architecture

Serverless, event-driven architecture on AWS. All resources are provisioned with AWS CDK (two stacks: `nextshift-core` for state, `nextshift-messaging` for compute and messaging).

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

## Resources (as defined in infra/)

| Resource | Name / Value |
|---|---|
| DynamoDB tables | `nextshift-workers`, `nextshift-roles`, `nextshift-pathways`, `nextshift-progress`, `nextshift-consent`, `nextshift-events` |
| SNS topic (inbound WhatsApp) | `nextshift-inbound-whatsapp` |
| Lambda functions | `nextshift-hr-api`, `nextshift-invite`, `nextshift-webhook`, `nextshift-dispatcher` |
| EventBridge rule | `nextshift-daily-lessons` (cron 0 14 * * ? *, UTC) |
| API Gateway (HTTP API) | `GET /workers`, `POST /impact-map`, `POST /invite` (base URL in the `ApiUrl` CDK output) |
| AgentCore Memory | ID stored in SSM parameter `/nextshift/memory-id` (created by `backend/scripts/create_memory.py`) |
| Agent runtime | Deployed via `agentcore deploy` from `backend/src/nextshift/agent/entrypoint.py`; ARN passed to the messaging stack as `AGENT_RUNTIME_ARN` |

## Components

**HR Dashboard (Next.js).** Static frontend for HR staff. Uploads the Automation Impact Map CSV, lists workers, and sends SMS invites. Calls the HTTP API using the `ApiUrl` CDK output.

**API Gateway (HTTP API, apigatewayv2).** Three routes (`/workers`, `/impact-map`, `/invite`) proxying to the `hr-api` Lambda.

**hr-api Lambda.** Implements the HR routes: parses the impact map CSV into worker/role records in DynamoDB, and asynchronously invokes the `invite` Lambda.

**invite Lambda.** Sends the SMS invite through AWS End User Messaging (pinpoint-sms-voice-v2) using the configured phone pool, with the WhatsApp display number as an opt-in alternative.

**webhook Lambda.** Subscribed to the `nextshift-inbound-whatsapp` SNS topic. Normalizes inbound WhatsApp events into a channel-agnostic envelope, resolves the worker by phone, and invokes the agent via `bedrock-agentcore invoke_agent_runtime`. Replies are sent back over EUM Social (WhatsApp) or SMS.

**AgentCore Runtime (Strands agent, Amazon Nova Lite).** The brain. Exposes six tools: `match_role`, `get_progress`, `next_lesson`, `submit_answer`, `enroll_pathway`, `escalate_human`. Role matching is a structured skill-gap lookup over the `nextshift-roles` table (Arntz-style task decomposition); lessons follow a spaced-repetition schedule (1d/3d/7d).

**AgentCore Memory.** One memory per worker, shared across SMS, WhatsApp, and email — the conversation continues where it left off regardless of channel. Memory ID is kept in SSM `/nextshift/memory-id`.

**Guardrails.** A constitution enforced in the agent: never promise employment, no legal/financial advice, crisis keywords escalate to 988 plus an HR-facing human queue.

**dispatcher Lambda + EventBridge.** `nextshift-daily-lessons` fires at 14:00 UTC daily. The dispatcher sends due micro-lessons over WhatsApp (SMS fallback) and, on pathway milestones, the SES certificate email and the RCS interview-scheduling card.

**DynamoDB.** Six on-demand tables: workers (with phone GSI), roles (company GSI), pathways, progress, consent, events (TTL).
