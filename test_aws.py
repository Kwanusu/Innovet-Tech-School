import boto3
import os

def test_connection():
    try:
        # This looks at the environment variables you set in PowerShell
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"Success! Authenticated as: {identity['Arn']}")
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    test_connection()