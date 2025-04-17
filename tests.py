"""
PyTest Fixtures to evaluate the robustness of the RSS scraper.

Core functionality is tested:
1. Downloading the PDF
2. Extracting URLs from the PDF
3. Extracting titles from an RSS feed
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app import RSSScraper
from app import RSSScraper
import requests
import pypdf
import json
import os

PDF_URL = "https://about.fb.com/wp-content/uploads/2016/05/rss-urls-1.pdf"


@pytest.fixture
def mock_scraper():
    """
    Fixture to create an RSS Scraper instance
    """
    return RSSScraper(pdf_url=PDF_URL)


@patch("requests.get")
def test_download_pdf(mock_get, mock_scraper, tmp_path):
    """
    Test the download PDF method
    """
    mock_response = Mock()
    mock_response.content = b"PDF content"
    mock_get.return_value = mock_response

    mock_scraper.download_pdf()

    mock_get.assert_called_once_with(
        "https://about.fb.com/wp-content/uploads/2016/05/rss-urls-1.pdf", timeout=10
    )
    assert os.path.exists("rss_urls.pdf")


@patch("pypdf.PdfReader")
def test_extract_urls(mock_pdf_reader, mock_scraper):
    mock_reader = MagicMock()
    mock_reader.pages = [
        MagicMock(
            extract_text=lambda: "https://example.com/rss1\nhttps://example.com/rss2\nhttps://example.com/rss1"
        ),
    ]
    mock_pdf_reader.return_value = mock_reader

    mock_scraper.download_pdf()
    mock_scraper.extract_urls()

    assert len(mock_scraper.urls) == 2
    assert "https://example.com/rss1" in mock_scraper.urls
    assert "https://example.com/rss2" in mock_scraper.urls


@patch("requests.get")
def test_verify_extract_titles_level_1(mock_get, mock_scraper):
    """
    Test the title extraction from an RSS feed.
    """
    # first for a straightforward case <- this makes sure that the core function works
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/rss+xml"}
    mock_response.content = """
    <rss><channel>
        <item><title>Title 1</title></item>
        <item><title>Title 2</title></item>
    </channel></rss>
    """
    mock_get.return_value = mock_response

    url, titles = mock_scraper.verify_and_extract_titles("https://example.com/rss")
    assert url == "https://example.com/rss"
    assert len(titles) == 2
    assert titles == ["Title 1", "Title 2"]


@patch("requests.get")
def test_verify_extract_titles_level_2(mock_get, mock_scraper):
    """
    Test more advanced pre-processing logic for parsing and title extraction.
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/rss+xml"}
    # now for a more complex RSS feed, which is more messy
    # here, I particularly want to test the robustness of the function
    mock_response.content = """
    <?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0" 
            xmlns:dc="http://purl.org/dc/elements/1.1/"
            xmlns:content="http://purl.org/rss/1.0/modules/content/">
            <channel>
                <item>
                    <title><![CDATA[Climate & Change: New Findings]]></title>
                    <dc:creator>John Doe</dc:creator>
                    <content:encoded><![CDATA[<p>Complex <b>HTML</b> content</p>]]></content:encoded>
                </item>
                <item>
                    <title>Tech Update â\x80\x94 AI + Humanity?</title>
                </item>
                <item>
                    <title>💰 Economic Outlook 2025</title>
                </item>
                <item>
                    <title></title>  <!-- Empty title -->
                </item>
            </channel>
        </rss>
    """
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/rss+xml"}
    mock_get.return_value = mock_response
    url, titles = mock_scraper.verify_and_extract_titles("https://example.com/rss")
    assert url == "https://example.com/rss"
    assert len(titles) == 3
    print(titles)
    assert titles == [
        "Climate & Change: New Findings",
        "Tech Update — AI + Humanity?",
        "Economic Outlook 2025",
    ]
