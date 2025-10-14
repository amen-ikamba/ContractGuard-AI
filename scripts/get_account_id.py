#!/usr/bin/env python3
"""Quick script to get AWS Account ID"""
import os
import sys
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set credentials
os.environ['AWS_ACCESS_KEY_ID'] = os.getenv('AWS_ACCESS_KEY_ID', '').strip('"')
os.environ['AWS_SECRET_ACCESS_KEY'] = os.getenv('AWS_SECRET_ACCESS_KEY', '').strip('"')
os.environ['AWS_DEFAULT_REGION'] = os.getenv('AWS_REGION', 'us-east-2')

try:
    # Get caller identity
    sts = boto3.client('sts')
    identity = sts.get_caller_identity()

    print(f"\n✓ AWS Connection Successful!")
    print(f"Account ID: {identity['Account']}")
    print(f"User ARN: {identity['Arn']}")
    print(f"User ID: {identity['UserId']}")
    print(f"\nUpdate your .env file with:")
    print(f"AWS_ACCOUNT_ID={identity['Account']}")

except Exception as e:
    print(f"\n✗ Error connecting to AWS: {e}")
    print("\nPlease check:")
    print("1. Your AWS_ACCESS_KEY_ID is correct")
    print("2. Your AWS_SECRET_ACCESS_KEY is correct")
    print("3. Your credentials have the necessary permissions")
    sys.exit(1)
