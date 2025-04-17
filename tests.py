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

from utils import clean_title

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

    download_path = tmp_path / "rss_urls.pdf"

    mock_scraper.download_pdf(download_path)

    mock_get.assert_called_once_with(
        "https://about.fb.com/wp-content/uploads/2016/05/rss-urls-1.pdf", timeout=10
    )
    assert download_path.exists()


@patch("pypdf.PdfReader")
def test_extract_urls(mock_pdf_reader, mock_scraper, tmp_path):
    """
    Test that extract_urls correctly extracts unique RSS URLs from a PDF.
    """
    pdf_path = tmp_path / "rss_urls.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%EOF")

    mock_reader = MagicMock()
    mock_reader.pages = [
        MagicMock(
            extract_text=lambda: (
                "https://example.com/rss1\n"
                "https://example.com/rss2\n"
                "https://example.com/rss1"
            )
        ),
    ]
    mock_pdf_reader.return_value = mock_reader

    os.chdir(tmp_path)  # Ensure working directory is tmp_path
    mock_scraper.extract_urls()

    expected_urls = {"https://example.com/rss1", "https://example.com/rss2"}
    assert set(mock_scraper.urls) == expected_urls
    assert len(mock_scraper.urls) == 2

    mock_pdf_reader.assert_called_once()


@patch("requests.get")
@pytest.mark.parametrize(
    "rss_content,expected_titles",
    [
        # l1 - basic rss to test core functionality
        (
            """
        <rss><channel>
            <item><title>Title 1</title></item>
            <item><title>Title 2</title></item>
        </channel></rss>
        """,
            ["Title 1", "Title 2"],
        ),
        # l2 - rss with special characters
        (
            """
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
                    <title></title>
                </item>
            </channel>
        </rss>
        """,
            [
                "Climate & Change: New Findings",
                "Tech Update — AI + Humanity?",
                "Economic Outlook 2025",
            ],
        ),
    ],
)
def test_verify_extract_titles(mock_get, mock_scraper, rss_content, expected_titles):
    """Test title extraction across different RSS feed complexities"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/rss+xml"}
    mock_response.content = rss_content
    mock_get.return_value = mock_response

    url, titles = mock_scraper.verify_and_extract_titles("https://example.com/rss")

    assert url == "https://example.com/rss"
    assert titles == expected_titles
    assert len(titles) == len(expected_titles)  # Redundant but explicit


@pytest.mark.parametrize(
    "raw,expected",
    [
        (
            "<b>Breaking News:</b> Market <i>rises</i> sharply",
            "Breaking News: Market rises sharply",
        ),
        ("   Multiple    spaces   here   ", "Multiple spaces here"),
        ("<p>Economy â\x80\x93 Outlook 2025</p>", "Economy – Outlook 2025"),
        ("💰 Economic Outlook 2025", "Economic Outlook 2025"),
        ("", ""),
    ],
)
def test_clean_title(raw, expected):
    cleaned = clean_title(raw)
    print(f"Cleaned: {cleaned}")
    assert clean_title(raw) == expected
