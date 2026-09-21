"""Create the AgentCore Memory resource once; store id in SSM.
Run: python scripts/create_memory.py (requires AWS credentials)"""
import boto3

from bedrock_agentcore.memory import MemoryClient

ssm = boto3.client("ssm")

client = MemoryClient(region_name="us-east-1")
memory = client.create_memory_and_wait(
    name="nextshift-worker-memory",
    description="Cross-channel worker profiles and conversation history",
    strategies=[
        {"semanticMemoryStrategy": {
            "name": "FactExtractor",
            "namespaceTemplates": ["/facts/{actorId}/"]}},
        {"userPreferenceMemoryStrategy": {
            "name": "PreferenceLearner",
            "namespaceTemplates": ["/preferences/{actorId}/"]}},
    ],
)
ssm.put_parameter(Name="/nextshift/memory-id",
                  Value=memory["id"], Type="String", Overwrite=True)
print(f"Memory created: {memory['id']}")
