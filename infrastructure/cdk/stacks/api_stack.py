"""
API Stack: API Gateway and related resources
"""

from aws_cdk import (
    Stack,
    aws_apigateway as apigw,
    aws_lambda as lambda_,
    CfnOutput
)
from constructs import Construct


class APIStack(Stack):
    """API Gateway resources for ContractGuard"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        lambda_functions: dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ==================== API Gateway ====================

        # Create REST API
        self.api = apigw.RestApi(
            self, "ContractGuardAPI",
            rest_api_name="ContractGuard API",
            description="API for ContractGuard AI contract analysis",
            deploy_options=apigw.StageOptions(
                stage_name="prod",
                throttling_rate_limit=100,
                throttling_burst_limit=200,
                metrics_enabled=True
            ),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        # API Key for access control
        self.api_key = apigw.ApiKey(
            self, "ContractGuardAPIKey",
            api_key_name="ContractGuard-APIKey"
        )

        # Usage plan
        usage_plan = self.api.add_usage_plan(
            "ContractGuardUsagePlan",
            name="Standard",
            throttle=apigw.ThrottleSettings(
                rate_limit=100,
                burst_limit=200
            ),
            quota=apigw.QuotaSettings(
                limit=10000,
                period=apigw.Period.MONTH
            )
        )

        usage_plan.add_api_key(self.api_key)
        usage_plan.add_api_stage(
            stage=self.api.deployment_stage
        )

        # ==================== API Resources ====================

        # Health check endpoint
        health = self.api.root.add_resource("health")
        health.add_method(
            "GET",
            apigw.MockIntegration(
                integration_responses=[
                    apigw.IntegrationResponse(
                        status_code="200",
                        response_templates={
                            "application/json": '{"status": "healthy", "service": "ContractGuard API"}'
                        }
                    )
                ],
                passthrough_behavior=apigw.PassthroughBehavior.NEVER,
                request_templates={
                    "application/json": '{"statusCode": 200}'
                }
            ),
            method_responses=[
                apigw.MethodResponse(status_code="200")
            ]
        )

        # Contracts resource
        contracts = self.api.root.add_resource("contracts")

        # POST /contracts/upload
        upload = contracts.add_resource("upload")
        upload.add_method(
            "POST",
            apigw.LambdaIntegration(lambda_functions['contract_parser']),
            api_key_required=True
        )

        # GET /contracts/{contractId}
        contract = contracts.add_resource("{contractId}")
        contract.add_method(
            "GET",
            apigw.LambdaIntegration(lambda_functions['contract_parser']),
            api_key_required=True
        )

        # POST /contracts/{contractId}/analyze
        analyze = contract.add_resource("analyze")
        analyze.add_method(
            "POST",
            apigw.LambdaIntegration(lambda_functions['risk_analyzer']),
            api_key_required=True
        )

        # POST /contracts/{contractId}/recommend
        recommend = contract.add_resource("recommend")
        recommend.add_method(
            "POST",
            apigw.LambdaIntegration(lambda_functions['clause_recommender']),
            api_key_required=True
        )

        # POST /contracts/{contractId}/negotiate
        negotiate = contract.add_resource("negotiate")
        negotiate.add_method(
            "POST",
            apigw.LambdaIntegration(lambda_functions['negotiation_strategist']),
            api_key_required=True
        )

        # POST /contracts/{contractId}/redline
        redline = contract.add_resource("redline")
        redline.add_method(
            "POST",
            apigw.LambdaIntegration(lambda_functions['redline_creator']),
            api_key_required=True
        )

        # POST /contracts/{contractId}/email
        email = contract.add_resource("email")
        email.add_method(
            "POST",
            apigw.LambdaIntegration(lambda_functions['email_generator']),
            api_key_required=True
        )

        # ==================== Outputs ====================

        CfnOutput(
            self, "APIEndpoint",
            value=self.api.url,
            description="API Gateway endpoint URL"
        )

        CfnOutput(
            self, "APIKeyId",
            value=self.api_key.key_id,
            description="API Key ID"
        )
