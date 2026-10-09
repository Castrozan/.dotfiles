import os
from pathlib import Path
import tempfile

import pytest

from private_session_process_fixture import PrivateSessionFixture


@pytest.fixture
def private_session():
    if os.name != "posix":
        pytest.skip("private session process ownership requires POSIX")
    with tempfile.TemporaryDirectory(prefix="cs-") as directory:
        session = PrivateSessionFixture(Path(directory))
        try:
            yield session
        finally:
            session.close()
