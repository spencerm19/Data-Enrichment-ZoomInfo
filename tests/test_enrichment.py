import pytest
from enrichment import enrich_data, EnrichmentError

def test_enrich_data_with_valid_file(sample_csv, mock_zoominfo_response):
    result = enrich_data(str(sample_csv))
    assert 'output_file' in result
    assert 'records_processed' in result
    assert 'total_records' in result
    assert result['total_records'] == 3

def test_enrich_data_with_invalid_file():
    with pytest.raises(EnrichmentError):
        enrich_data("nonexistent_file.csv")

def test_enrich_data_with_empty_file(tmp_path, mock_zoominfo_response):
    empty_file = tmp_path / "empty.csv"
    empty_file.write_text("company_name\n")
    result = enrich_data(str(empty_file))
    assert result['total_records'] == 0 