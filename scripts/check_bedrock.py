#!/usr/bin/env python3
"""Check Bedrock access and model availability"""
import os
import sys
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set credentials
os.environ['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID', '').strip('"')
os.environ['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY', '').strip('"')
region = os.getenv('AWS_REGION', 'us-east-2')
os.environ['AWS_DEFAULT_REGION'] = region

print(f"Checking Bedrock access in region: {region}\n")

try:
    # Check Bedrock access
    bedrock = boto3.client('bedrock', region_name=region)

    print("✓ Bedrock service is accessible!")

    # List foundation models
    try:
        response = bedrock.list_foundation_models()
        models = response.get('modelSummaries', [])

        print(f"\n✓ Found {len(models)} foundation models available")

        # Check for Claude models
        claude_models = [m for m in models if 'claude' in m['modelId'].lower()]

        if claude_models:
            print(f"✓ Found {len(claude_models)} Claude models:")
            for model in claude_models:
                print(f"  - {model['modelId']}")

            # Check for the specific model we need
            target_model = "anthropic.claude-3-5-sonnet-20241022-v2:0"
            if any(target_model in m['modelId'] for m in claude_models):
                print(f"\n✓ Target model is available: {target_model}")
            else:
                print(f"\n⚠ Target model not found: {target_model}")
                print("Available Claude 3.5 Sonnet models:")
                sonnet_models = [m for m in claude_models if 'sonnet' in m['modelId'].lower()]
                for model in sonnet_models:
                    print(f"  - {model['modelId']}")
        else:
            print("\n⚠ No Claude models found.")
            print("You may need to request model access:")
            print(f"  https://console.aws.amazon.com/bedrock/home?region={region}#/modelaccess")

    except Exception as e:
        print(f"\n⚠ Could not list models: {e}")
        print("\nYou may need to:")
        print("1. Enable Bedrock in your region")
        print("2. Request model access for Claude 3.5 Sonnet")
        print(f"   Visit: https://console.aws.amazon.com/bedrock/home?region={region}#/modelaccess")

except Exception as e:
    print(f"✗ Error accessing Bedrock: {e}")
    print("\nPossible issues:")
    print("1. Bedrock may not be available in your region")
    print("2. Your IAM user may need additional permissions")
    print("3. You may need to enable Bedrock in the AWS Console")
    sys.exit(1)
