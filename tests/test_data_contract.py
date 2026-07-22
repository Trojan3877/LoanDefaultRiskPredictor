import pytest

from src.data_loader import DataLoader
from tests.helpers import loan_frame


def test_valid_dataframe_contract():
    loaded = next(iter(DataLoader.from_df(loan_frame())))
    assert len(loaded) == 80


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda frame: frame.drop(columns=["dti"]), "Missing columns"),
        (lambda frame: frame.assign(defaulted=3), "binary"),
        (lambda frame: frame.assign(annual_inc=-1), "outside"),
        (lambda frame: frame.assign(loan_id=1), "Duplicate"),
        (lambda frame: frame.assign(dti=None), "Missing required"),
    ],
)
def test_invalid_cohorts_fail_closed(mutation, message):
    with pytest.raises(ValueError, match=message):
        next(iter(DataLoader.from_df(mutation(loan_frame()))))


def test_remote_uri_policy_and_s3_parsing(monkeypatch):
    with pytest.raises(ValueError, match="HTTPS"):
        DataLoader.from_uri("http://example.com/loans.csv")
    monkeypatch.setenv("ALLOWED_DATA_HOSTS", "data.example.com")
    with pytest.raises(ValueError, match="allowlisted"):
        DataLoader.from_uri("https://example.com/loans.csv")
    loader = DataLoader.from_uri("s3://governed-bucket/cohorts/loans.csv")
    assert loader._reader.bucket == "governed-bucket"
    assert loader._reader.key == "cohorts/loans.csv"
