import os
import unittest
from pathlib import Path
from unittest.mock import patch


class EnvironmentTests(unittest.TestCase):
    def test_google_api_key_is_loaded_from_dotenv(self):
        dotenv_path = Path(__file__).resolve().parents[1] / ".env"
        if not dotenv_path.exists():
            self.skipTest(".env is not present")

        with patch.dict(os.environ, {"GOOGLE_API_KEY": ""}, clear=False):
            from agent import llm

            llm.load_dotenv(dotenv_path=dotenv_path, override=True)
            self.assertTrue(os.environ.get("GOOGLE_API_KEY"))


if __name__ == "__main__":
    unittest.main()
