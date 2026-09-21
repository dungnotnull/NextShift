"""Core state: DynamoDB tables + SNS topic for inbound WhatsApp."""
from aws_cdk import Stack
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_sns as sns
from constructs import Construct


class CoreStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        def table(name: str, partition: str, sort: str | None = None,
                  gsi: list | None = None, ttl: str | None = None):
            # aws-cdk-lib >= 2.270 dropped the global_secondary_indexes ctor kwarg;
            # GSIs are attached post-construction via add_global_secondary_index.
            t = dynamodb.Table(
                self, name, table_name=f"nextshift-{name}",
                partition_key=dynamodb.Attribute(name=partition,
                                                 type=dynamodb.AttributeType.STRING),
                sort_key=(dynamodb.Attribute(name=sort, type=dynamodb.AttributeType.STRING)
                          if sort else None),
                billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
                time_to_live_attribute=ttl,
            )
            for props in (gsi or []):
                t.add_global_secondary_index(
                    index_name=props["index_name"],
                    partition_key=dynamodb.Attribute(
                        name=props["partition"],
                        type=dynamodb.AttributeType.STRING))
            return t

        self.workers = table("workers", "worker_id",
                             gsi=[{"index_name": "phone-index", "partition": "phone"}])
        self.roles = table("roles", "role_id", sort="company_id",
                           gsi=[{"index_name": "company-index", "partition": "company_id"}])
        self.pathways = table("pathways", "worker_id", sort="pathway_id")
        self.progress = table("progress", "worker_id", sort="lesson_id")
        self.consent = table("consent", "phone")
        self.events = table("events", "worker_id", sort="ts", ttl="expiration_date")

        self.inbound_whatsapp = sns.Topic(
            self, "inbound-whatsapp", topic_name="nextshift-inbound-whatsapp")

        # SES identity is verified manually in console (runbook Task 14).
