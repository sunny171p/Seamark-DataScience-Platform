# ==
# conftest.py
# Shared pytest fixtures for the Seamark test suite
# ==
#
# Every test in this folder needs to know where the project root is
# so it can find raw_data/, cleaned_data/ and outputs/ regardless of
# which folder pytest happens to be invoked from. This file works
# that out once and hands it to every test as the `project_root`
# fixture.

from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def project_root():
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def raw_data_dir(project_root):
    return project_root / "Stage1_Analytics" / "raw_data"


@pytest.fixture(scope="session")
def cleaned_data_dir(project_root):
    return project_root / "Stage1_Analytics" / "cleaned_data"


@pytest.fixture(scope="session")
def outputs_dir(project_root):
    return project_root / "outputs"
