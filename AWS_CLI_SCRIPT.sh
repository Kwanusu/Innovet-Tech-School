#!/bin/bash
BUCKET_NAME="innovet-terraform-state-$(date +%s)" # Unique name
REGION="us-east-1"

# Create S3 Bucket for State
aws s3api create-bucket --bucket $BUCKET_NAME --region $REGION

# Create DynamoDB Table for State Locking
aws dynamodb create-table \
    --table-name terraform-lock-table \
    --attribute-definitions AttributeName=LockID,AttributeType=S    \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

echo "Update your backend.tf with this bucket name: $BUCKET_NAME"
