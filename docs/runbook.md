# NextShift Runbook

## One-time console prerequisites (START EARLY - approvals take days)
1. AWS End User Messaging Social: link a WhatsApp Business Account (WABA), register a phone number -> note its Phone Number ID (WA_PHONE_ID). In the EUM Social console, set the inbound message destination to the SNS topic `nextshift-inbound-whatsapp` (created by CDK).
2. Create and approve a WhatsApp template named `nextshift_invite` (category UTILITY, language en_US) in the Meta Business Manager tied to the WABA.
3. AWS End User Messaging (SMS): create a phone pool -> note pool ID (SMS_POOL_ID). For RCS: register an RCS agent -> note its ARN (RCS_AGENT_ARN); optional.
4. Amazon SES: verify the sending identity (SES_FROM). While in sandbox, also verify the recipient address used for the milestone email (or request sandbox exit). Update dispatcher _send_milestone recipient if you want a real inbox.
5. Bedrock model access: enable Amazon Nova Lite in us-east-1 (Bedrock console -> Model access).
6. AWS credentials configured locally (`aws configure`) with rights for CDK deploy + AgentCore + DynamoDB + SSM.

## Deploy steps
```bash
cd infra && source .venv/Scripts/activate
export AWS_DEFAULT_REGION=us-east-1
npx aws-cdk deploy nextshift-core nextshift-messaging
# Note the ApiUrl output.

# Create memory + deploy the agent
cd ../backend && source .venv/Scripts/activate
pip install "bedrock-agentcore[cli]"
python scripts/create_memory.py           # stores /nextshift/memory-id in SSM
MEMORY_ID=$(aws ssm get-parameter --name /nextshift/memory-id --query Parameter.Value --output text)
agentcore deploy src/nextshift/agent/entrypoint.py   # note the returned Agent Runtime ARN
```
Set env vars and redeploy messaging with real values:
```bash
cd ../infra
AGENT_RUNTIME_ARN=<arn> WA_PHONE_ID=<id> SMS_POOL_ID=<pool> SES_FROM=<email> \
  [RCS_AGENT_ARN=<arn>] [WA_DISPLAY_NUMBER=<display>] \
  npx aws-cdk deploy nextshift-messaging
```
The agent entrypoint also needs MEMORY_ID and BEDROCK_MODEL_ID: configure them in the AgentCore runtime environment when deploying (agentcore CLI prompts / runtime settings), default model us.amazon.nova-lite-v1:0.

## Seed + operate
```bash
cd ../backend && source .venv/Scripts/activate
python scripts/seed.py
aws lambda invoke --function-name nextshift-dispatcher --payload '{}' /tmp/dispatch.json && cat /tmp/dispatch.json
# Expected before any enrollment: {"lessons_sent": 0, "milestones": 0}
```
Daily lessons run via EventBridge at 14:00 UTC.

## End-to-end smoke (after WABA test number is live)
1. Text "hi" to the WhatsApp test number -> expect agent reply (SNS -> webhook -> AgentCore -> WhatsApp). If no reply: check nextshift-webhook logs first.
2. Capture ONE real inbound SNS event from CloudWatch logs and verify parse_whatsapp_sns_event handles it (add a fixture if the shape differs — planned in Task 8 Step 5).
3. HR dashboard: POST /impact-map with seed CSV, POST /invite, GET /workers.

## Demo worker journey (3-min script)
1. POST /impact-map  2. POST /invite (SMS)  3. worker replies on WhatsApp
4. agent profiles + match_role (Maria: Robot Fleet Operator 50%) + enroll_pathway
5. daily lesson -> submit_answer via chat  6. milestone email + RCS card.

## Frontend
```bash
cd frontend && npm install
NEXT_PUBLIC_API_URL=<ApiUrl from cdk outputs> npm run build
npm start
```
