"""Test-wide environment defaults (no AWS credentials or network needed)."""
import os

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
