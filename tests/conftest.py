"""Shared pytest fixtures for the PyiTOL test suite."""

from pathlib import Path

import pytest

# Test data directory
DATA_DIR = Path(__file__).parent / "data"

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"
IQ_TREE_NEWICK = "((A:0.1,B:0.2)90:0.3,(C:0.4,D:0.5)85:0.6);"
NEXUS_TREE = """#NEXUS
begin trees;
    tree tree1 = ((A,B),(C,D));
end;
"""
TAXONOMY_TSV = "id\tKingdom\tPhylum\tcount\tvalue\nA\tBacteria\tProteobacteria\t10\t0.5\nB\tBacteria\tProteobacteria\t20\t0.8\nC\tArchaea\tEuryarchaeota\t15\t0.3\nD\tArchaea\tEuryarchaeota\t25\t0.6\n"  # noqa: E501
TAXONOMY_SIMPLE_TSV = "id\tKingdom\nA\tBacteria\nB\tBacteria\nC\tArchaea\nD\tArchaea\n"


@pytest.fixture
def tree_file(tmp_path):
    p = tmp_path / "test.nwk"
    p.write_text(SIMPLE_NEWICK)
    return str(p)


@pytest.fixture
def iqtree_file(tmp_path):
    p = tmp_path / "test.treefile"
    p.write_text(IQ_TREE_NEWICK)
    return str(p)


@pytest.fixture
def nexus_file(tmp_path):
    p = tmp_path / "test.nex"
    p.write_text(NEXUS_TREE)
    return str(p)


@pytest.fixture
def taxonomy_file(tmp_path):
    p = tmp_path / "test.tsv"
    p.write_text(TAXONOMY_TSV)
    return str(p)


@pytest.fixture
def simple_taxonomy_file(tmp_path):
    p = tmp_path / "simple.tsv"
    p.write_text(TAXONOMY_SIMPLE_TSV)
    return str(p)


@pytest.fixture
def api_key_file(tmp_path):
    p = tmp_path / ".itolapi.key"
    p.write_text("test-api-key-12345")
    return str(p)


@pytest.fixture
def data_dir():
    """Return the path to the test data directory."""
    return DATA_DIR


@pytest.fixture
def sample_tree_path():
    """Return the path to the sample tree file in tests/data/."""
    return str(DATA_DIR / "4taxa_tree.nwk")


@pytest.fixture
def sample_taxonomy_path():
    """Return the path to the sample taxonomy file in tests/data/."""
    return str(DATA_DIR / "4taxa_taxonomy.csv")
