import pytest
import os
from unittest.mock import patch
from io import StringIO
from main import main, filter_data, aggregate_data

SAMPLE_CSV_CONTENT = """name,brand,price,rating
iphone 15 pro,apple,999,4.9
galaxy s23 ultra,samsung,1199,4.8
redmi note 12,xiaomi,199,4.6
poco x5 pro,xiaomi,299,4.4
old phone,apple,50,3.5
"""

@pytest.fixture
def sample_csv_file(tmp_path):
    file_path = tmp_path / "products.csv"
    file_path.write_text(SAMPLE_CSV_CONTENT)
    return str(file_path)

@pytest.fixture
def mock_stdout():
    with patch('sys.stdout', new_callable=StringIO) as mock_output:
        yield mock_output

def test_filter_data_no_condition():
    header = ["name", "brand", "price", "rating"]
    data = [
        ["iphone 15 pro", "apple", "999", "4.9"],
        ["galaxy s23 ultra", "samsung", "1199", "4.8"],
    ]
    filtered = filter_data(data, header, None)
    assert filtered == data

def test_filter_data_numeric_equality():
    header = ["name", "brand", "price", "rating"]
    data = [
        ["iphone 15 pro", "apple", "999", "4.9"],
        ["galaxy s23 ultra", "samsung", "1199", "4.8"],
    ]
    filtered = filter_data(data, header, "rating=4.9")
    assert filtered == [["iphone 15 pro", "apple", "999", "4.9"]]

def test_filter_data_numeric_greater_than():
    header = ["name", "brand", "price", "rating"]
    data = [
        ["iphone 15 pro", "apple", "999", "4.9"],
        ["galaxy s23 ultra", "samsung", "1199", "4.8"],
        ["old phone", "apple", "50", "3.5"]
    ]
    filtered = filter_data(data, header, "rating>4.7")
    assert filtered == [
        ["iphone 15 pro", "apple", "999", "4.9"],
        ["galaxy s23 ultra", "samsung", "1199", "4.8"],
    ]

def test_filter_data_numeric_less_than():
    header = ["name", "brand", "price", "rating"]
    data = [
        ["iphone 15 pro", "apple", "999", "4.9"],
        ["galaxy s23 ultra", "samsung", "1199", "4.8"],
        ["old phone", "apple", "50", "3.5"]
    ]
    filtered = filter_data(data, header, "price<100")
    assert filtered == [["old phone", "apple", "50", "3.5"]]

def test_filter_data_string_equality():
    header = ["name", "brand", "price", "rating"]
    data = [
        ["iphone 15 pro", "apple", "999", "4.9"],
        ["galaxy s23 ultra", "samsung", "1199", "4.8"],
    ]
    filtered = filter_data(data, header, "brand=apple")
    assert filtered == [["iphone 15 pro", "apple", "999", "4.9"]]

def test_filter_data_no_match():
    header = ["name", "brand", "price", "rating"]
    data = [
        ["iphone 15 pro", "apple", "999", "4.9"],
    ]
    filtered = filter_data(data, header, "brand=microsoft")
    assert filtered == []

def test_aggregate_data_avg():
    header = ["name", "brand", "price", "rating"]
    data = [
        ["iphone 15 pro", "apple", "999", "4.9"],
        ["galaxy s23 ultra", "samsung", "1199", "4.8"],
        ["redmi note 12", "xiaomi", "199", "4.6"],
        ["poco x5 pro", "xiaomi", "299", "4.4"],
    ]
    result = aggregate_data(data, header, "rating=avg")
    expected_avg = (4.9 + 4.8 + 4.6 + 4.4) / 4
    assert result == {'avg': pytest.approx(expected_avg)}

def test_aggregate_data_min():
    header = ["name", "brand", "price", "rating"]
    data = [
        ["iphone 15 pro", "apple", "999", "4.9"],
        ["galaxy s23 ultra", "samsung", "1199", "4.8"],
        ["redmi note 12", "xiaomi", "199", "4.6"],
        ["poco x5 pro", "xiaomi", "299", "4.4"],
    ]
    result = aggregate_data(data, header, "price=min")
    assert result == {'min': 199.0}

def test_aggregate_data_max():
    header = ["name", "brand", "price", "rating"]
    data = [
        ["iphone 15 pro", "apple", "999", "4.9"],
        ["galaxy s23 ultra", "samsung", "1199", "4.8"],
        ["redmi note 12", "xiaomi", "199", "4.6"],
        ["poco x5 pro", "xiaomi", "299", "4.4"],
    ]
    result = aggregate_data(data, header, "price=max")
    assert result == {'max': 1199.0}

def test_aggregate_data_empty_data():
    header = ["name", "brand", "price", "rating"]
    data = []
    result = aggregate_data(data, header, "rating=avg")
    assert result == {'avg': 'N/A'}

def test_aggregate_data_invalid_column():
    header = ["name", "brand", "price", "rating"]
    data = [
        ["iphone 15 pro", "apple", "999", "4.9"],
    ]
    result = aggregate_data(data, header, "nonexistent=avg")
    assert result is None

def test_aggregate_data_non_numeric_column(mock_stdout):
    header = ["name", "brand", "price", "rating"]
    data = [
        ["iphone 15 pro", "apple", "999", "4.9"],
        ["galaxy s23 ultra", "samsung", "abc", "4.8"],
    ]
    result = aggregate_data(data, header, "price=avg")
    assert result == {'avg': 999.0}
    assert "Warning: Non-numeric value 'abc' in column 'price'. Skipping for aggregation." in mock_stdout.getvalue()


def test_main_display_all(sample_csv_file, mock_stdout):
    with patch('sys.argv', ['main.py', sample_csv_file]):
        main()
        output = mock_stdout.getvalue()
        assert "| name             | brand   | price | rating |" in output
        assert "| iphone 15 pro  | apple   | 999   | 4.9    |" in output
        assert "| redmi note 12  | xiaomi  | 199   | 4.6    |" in output

def test_main_filter_and_display(sample_csv_file, mock_stdout):
    with patch('sys.argv', ['main.py', sample_csv_file, '--where', 'brand=apple']):
        main()
        output = mock_stdout.getvalue()
        assert "| name            | brand | price | rating |" in output
        assert "| iphone 15 pro | apple | 999   | 4.9    |" in output
        assert "| old phone     | apple | 50    | 3.5    |" in output
        assert "galaxy s23 ultra" not in output

def test_main_filter_numeric_and_display(sample_csv_file, mock_stdout):
    with patch('sys.argv', ['main.py', sample_csv_file, '--where', 'rating>4.7']):
        main()
        output = mock_stdout.getvalue()
        assert "| name             | brand   | price | rating |" in output
        assert "| iphone 15 pro  | apple   | 999   | 4.9    |" in output
        assert "| galaxy s23 ultra | samsung | 1199  | 4.8    |" in output
        assert "redmi note 12" not in output

def test_main_aggregate_avg(sample_csv_file, mock_stdout):
    with patch('sys.argv', ['main.py', sample_csv_file, '--aggregate', 'rating=avg']):
        main()
        output = mock_stdout.getvalue()
        expected_avg = (4.9 + 4.8 + 4.6 + 4.4 + 3.5) / 5
        assert f"| avg |" in output
        assert f"{expected_avg:.2f}" in output

def test_main_filter_and_aggregate_min(sample_csv_file, mock_stdout):
    with patch('sys.argv', ['main.py', sample_csv_file, '--where', 'brand=xiaomi', '--aggregate', 'rating=min']):
        main()
        output = mock_stdout.getvalue()
        assert "| min |" in output
        assert "| 4.4 |" in output
        assert "4.6" not in output

def test_main_file_not_found(mock_stdout):
    with patch('sys.argv', ['main.py', 'non_existent_file.csv']):
        main()
        output = mock_stdout.getvalue()
        assert "Error: File not found at 'non_existent_file.csv'." in output

def test_main_no_data_after_filter(sample_csv_file, mock_stdout):
    with patch('sys.argv', ['main.py', sample_csv_file, '--where', 'brand=microsoft']):
        main()
        output = mock_stdout.getvalue()
        assert "No data found after filtering." in output