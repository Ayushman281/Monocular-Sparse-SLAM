import os
import platform
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def pytest_sessionstart(session):
    if (os.getenv("EXECUTION_TARGET") not in {"aws", "lightning"} or platform.system() != "Linux"
            or "microsoft" in platform.release().lower()):
        raise pytest.UsageError("Tests may run only in the authorized hosted runtime, never on the development PC.")
