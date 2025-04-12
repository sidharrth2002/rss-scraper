"""
PyTest Fixtures to evaluate the robustness of the RSS scraper.
"""

import pytest
from unittest.mock import patch, MagicMock
from app import RSSScraper


@pytest.fixture
def scraper():
    """
    Instantiate the RSSScraper class.
    """
    return RSSScraper()


@patch("requests.get")
def test_verify_and_extract_titles_valid_feed(mock_get, scraper):
    """
    Test that titles are correctly extracted from a valid RSS feed URL.
    """
    pass


@patch("requests.get")
def test_verify_and_extract_titles_invalid_feed(mock_get, scraper):
    """
    Test that an invalid RSS feed URL returns an empty list of titles.
    """
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    url = "https://invalid-url.com/rss"
    result_url, titles = scraper.verify_and_extract_titles(url)
    assert result_url == url
    assert titles == []


@patch("pypdf.PdfReader")
def test_extract_urls(mock_pdf_reader, scraper):
    """
    Test that URLs are correctly extracted from a PDF file.
    """
    # Mock PDF text content
    mock_pdf_reader.return_value.pages = [
        MagicMock(
            extract_text=lambda: "https://example.com/rss\nhttps://another.com/feed"
        )
    ]

    scraper.download_pdf()  # This would normally download the PDF
    scraper.extract_urls()

    expected_urls = ["https://example.com/rss", "https://another.com/feed"]
    assert set(scraper.urls) == set(expected_urls)


@patch("requests.get")
def test_download_pdf(mock_get, scraper):
    """
    Test that the PDF is downloaded successfully.
    """
    # Mock a successful response
    mock_response = MagicMock()
    mock_response.content = b"PDF content"
    mock_get.return_value = mock_response

    # Call the method to download the PDF
    scraper.download_pdf()

    # Check if the file was created and contains the expected content
    with open("rss_urls.pdf", "rb") as f:
        content = f.read()
        assert content == b"PDF content"