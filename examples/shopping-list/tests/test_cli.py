import pytest

from shoplist import cli


@pytest.fixture
def served(monkeypatch):
    """Replace the blocking server with a recorder of what would be served."""
    calls = []
    monkeypatch.setattr(cli, "serve", lambda api, host, port, out: calls.append((api, host, port)))
    return calls


def test_first_start_adds_the_sample_dishes(tmp_path, served):
    assert cli.main(["--data", str(tmp_path / "list.json"), "--port", "9000"]) == 0
    api, host, port = served[0]
    assert (host, port) == ("127.0.0.1", 9000)
    assert [dish["name"] for dish in api.dishes.dishes()] == ["Gemüsecurry", "Pfannkuchen", "Spaghetti Bolognese"]


def test_samples_are_added_only_once(tmp_path, served):
    data = str(tmp_path / "list.json")
    cli.main(["--data", data])
    cli.main(["--data", data])
    assert len(served[1][0].dishes.dishes()) == 3


def test_no_samples_flag_starts_empty(tmp_path, served):
    cli.main(["--data", str(tmp_path / "list.json"), "--no-samples"])
    assert served[0][0].dishes.dishes() == []
