"""Lambda functions, EventBridge schedule, API Gateway for the HR dashboard."""
import os
from pathlib import Path

from aws_cdk import CfnOutput, Duration, Stack
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_integrations as apigwv2_integrations
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_sns_subscriptions as sns_subs
from constructs import Construct

from nextshift.stack_core import CoreStack

BACKEND_SRC = Path(__file__).parents[2] / "backend" / "src"


def fn(scope, name: str, handler: str, env: dict, timeout: int = 60) -> lambda_.Function:
    return lambda_.Function(
        scope, name, function_name=f"nextshift-{name}",
        runtime=lambda_.Runtime.PYTHON_3_12,
        handler=handler,
        code=lambda_.Code.from_asset(
            str(BACKEND_SRC),
            exclude=["**/__pycache__", "nextshift.egg-info", "nextshift.egg-info/**"]),
        memory_size=512,
        timeout=Duration.seconds(timeout),
        log_retention=logs.RetentionDays.ONE_WEEK,
        environment=env,
    )


class MessagingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str,
                 core: CoreStack, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        env_common = {
            "WORKERS_TABLE": core.workers.table_name,
            "ROLES_TABLE": core.roles.table_name,
            "PATHWAYS_TABLE": core.pathways.table_name,
            "PROGRESS_TABLE": core.progress.table_name,
            "CONSENT_TABLE": core.consent.table_name,
            "EVENTS_TABLE": core.events.table_name,
        }

        webhook = fn(self, "webhook", "nextshift.handlers.webhook_whatsapp.handler",
                     {**env_common,
                      "WA_PHONE_ID": os.environ.get("WA_PHONE_ID", ""),
                      "AGENT_RUNTIME_ARN": os.environ.get("AGENT_RUNTIME_ARN", "")},
                     timeout=120)
        core.inbound_whatsapp.add_subscription(sns_subs.LambdaSubscription(webhook))

        invite = fn(self, "invite", "nextshift.handlers.invite.handler",
                    {**env_common,
                     "SMS_POOL_ID": os.environ.get("SMS_POOL_ID", ""),
                     "WA_DISPLAY_NUMBER": os.environ.get("WA_DISPLAY_NUMBER", "")})

        dispatcher = fn(self, "dispatcher", "nextshift.handlers.dispatcher.handler",
                        {**env_common,
                         "WA_PHONE_ID": os.environ.get("WA_PHONE_ID", ""),
                         "SMS_POOL_ID": os.environ.get("SMS_POOL_ID", ""),
                         "RCS_AGENT_ARN": os.environ.get("RCS_AGENT_ARN", ""),
                         "SES_FROM": os.environ.get("SES_FROM", "")},
                        timeout=120)

        events.Rule(
            self, "daily-lessons",
            schedule=events.Schedule.cron(minute="0", hour="14"),  # 09:00 US Eastern approx
            targets=[targets.LambdaFunction(dispatcher)])

        hr_api = fn(self, "hr-api", "nextshift.handlers.hr_api.handler",
                    {**env_common, "COMPANY_ID": "velocity",
                     "INVITE_FUNCTION": invite.function_name})

        api = apigwv2.HttpApi(self, "hr-http-api")
        api.add_routes(
            path="/workers", methods=[apigwv2.HttpMethod.GET],
            integration=apigwv2_integrations.HttpLambdaIntegration("workers", hr_api))
        api.add_routes(
            path="/impact-map", methods=[apigwv2.HttpMethod.POST],
            integration=apigwv2_integrations.HttpLambdaIntegration("impact", hr_api))
        api.add_routes(
            path="/invite", methods=[apigwv2.HttpMethod.POST],
            integration=apigwv2_integrations.HttpLambdaIntegration("invite", hr_api))

        for t in (core.workers, core.roles, core.pathways,
                  core.progress, core.consent, core.events):
            t.grant_read_write_data(webhook)
            t.grant_read_write_data(dispatcher)
            t.grant_read_write_data(hr_api)
        core.inbound_whatsapp.grant_publish(webhook)
        invite.grant_invoke(hr_api)

        self.api_url = api.url
        CfnOutput(self, "ApiUrl", value=api.url,
                  description="HR dashboard HTTP API base URL")
