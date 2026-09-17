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

    def test_postgres_database_connection(self):
        dotenv_path = Path(__file__).resolve().parents[1] / ".env"
        if not dotenv_path.exists():
            self.skipTest(".env is not present")

        from dotenv import load_dotenv

        load_dotenv(dotenv_path=dotenv_path, override=True)
        database_url = os.environ.get("POSTGRES_DATABASE_URL", "")
        if not database_url or "your-" in database_url or "database_name" in database_url:
            self.skipTest("POSTGRES_DATABASE_URL is not configured")
        psycopg_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)

        try:
            import psycopg  # type: ignore[import-not-found]
        except ImportError:
            self.skipTest("psycopg is not installed")

        try:
            with psycopg.connect(psycopg_url, connect_timeout=5) as connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    self.assertEqual(cursor.fetchone(), (1,))
                    print("PostgreSQL connection successful.")
        except psycopg.OperationalError as exc:
            self.fail(f"Could not connect to PostgreSQL: {exc}")


if __name__ == "__main__":
    unittest.main()
