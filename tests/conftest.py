"""
Pytest configuration for volatility harvesting tests.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables BEFORE importing app
os.environ["TESTING"] = "true"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "secret"
os.environ["JWT_SECRET_KEY"] = "test_secret_key_for_testing_only"
os.environ["API_KEY"] = "test_api_key"
os.environ["SECRET_KEY"] = "test_secret_key"
