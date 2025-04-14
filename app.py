"""
RSS Scraper

Sidharrth Nagappan (c) 2025
"""

from collections import defaultdict
import json
import re
import requests
import feedparser
from concurrent.futures import ThreadPoolExecutor, as_completed
import pypdf
from tqdm import tqdm

import logging

from utils import clean_title
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer


logging.basicConfig(level=logging.WARNING)


class RSSScraper:
    """
    Full pipeline for scraping RSS feeds based on data stored in a PDF file.

    Implements all the required pre-processing and error handling.
    """

    def __init__(self, pdf_url):
        self.pdf_url = pdf_url
        self.rss_content = defaultdict(list)
        self.urls = []

    def download_pdf(self, download_path: str) -> None:
        """
        STEP 1:
        Download the PDF file from the RSS URL and save it locally for analysis.
        """
        response = requests.get(self.pdf_url, timeout=10)
        response.raise_for_status()
        with open(download_path, "wb") as f:
            f.write(response.content)

    def extract_urls(self) -> None:
        """
        STEP 2:
        Extract URLs from the downloaded PDF file.
        """
        with open("rss_urls.pdf", "rb") as f:
            reader = pypdf.PdfReader(f)
            text = "".join(page.extract_text() for page in reader.pages)

        # Use regex to find all URLs in the text, including http and https
        urls = re.findall(r"(https?://[^\s]+)", text)
        self.urls.extend(list(set(urls)))

    def verify_and_extract_titles(self, url: str, num_titles: int = 5) -> tuple:
        """
        Verify if a URL is a valid RSS feed and extract titles if valid.

        Args:
            url (str): The URL to verify.
            num_titles (int, optional): Number of titles to extract. Defaults to 5.
        """
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                content_type = response.headers.get("Content-Type", "")
                if "xml" in content_type or "rss" in content_type:
                    feed = feedparser.parse(response.content)
                    titles = [
                        clean_title(entry.title)
                        for entry in feed.entries[:num_titles]
                        if entry.title
                    ]
                    logging.debug("Extracted titles from %s: %s", url, titles)
                    return url, titles
            return url, []
        except requests.exceptions.RequestException as e:
            logging.debug("Error processing %s: %s", url, e)
            return url, []

    def extract_data(self, num_threads: int = 10) -> None:
        """
        Check the authenticity of URLs and extract data using parallel processing.

        Args:
            num_threads (int, optional): Number of threads for parallel processing. Defaults to 10.
        """
        num_valid_urls = 0
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            future_to_url = {
                executor.submit(self.verify_and_extract_titles, url): url
                for url in self.urls
            }
            for future in tqdm(
                as_completed(future_to_url),
                total=len(future_to_url),
                desc="Processing URLs",
            ):
                url, titles = future.result()
                if titles:
                    logging.info("Valid RSS Feed: %s", url)
                    self.rss_content[url] = titles
                    num_valid_urls += 1
                else:
                    logging.debug("Invalid RSS Feed: %s", url)

        # print out the statistics
        logging.info("Total valid URLs: %d", num_valid_urls)
        logging.info("Total URLs processed: %d", len(self.urls))
        logging.info(
            "Percentage of valid URLs: %.2f%%", (num_valid_urls / len(self.urls)) * 100
        )

    def run_data_check(self) -> None:
        """
        Run sanity checks to ensure the data is valid, sane and coherent. Two rudimentary checks are:
        1. Making sure that titles are not too short and are within a reasonable length.
        2. If a feed has less than 2 titles, it may be worth looking into the link manually to see if that URL is malformed OR
        if there is an edge case the script doesn't account for.

        More complex checks such as comparing the similarity of titles can be added here later.
        """
        # Check for empty titles
        for url, titles in self.rss_content.items():
            # No titles at all
            if not titles:
                logging.warning("Empty titles found for URL: %s", url)
                continue

            # Check for titles that are too short or too long
            for title in titles:
                if len(title) < 10:
                    logging.warning(
                        "Title length issue for URL: %s, Title: %s", url, title
                    )

            # Very little titles picked up from that RSS feed
            if len(titles) < 3:
                logging.warning(
                    "Less than 3 titles found for URL: %s, Titles: %s", url, titles
                )
                continue
        logging.info("Data sanity checks completed.")

    def topic_modelling(
        self,
        num_topics: int = 5,
        topic_analysis_file_name: str = "topic_analysis.json",
        topic_bar_chart_file_name: str = "topic_visualization.html",
    ) -> None:
        """
        Run topic modelling on the extracted titles to get the key events of the day, using BERTopic.

        Note: There are more powerful ways to do this, but plain BERT is a good place to start.
        """
        titles = [title for titles in self.rss_content.values() for title in titles]
        titles = list(set(titles))

        # use the count vectorizer to remove the stopwords
        vectorizer_model = CountVectorizer(stop_words="english")
        topic_model = BERTopic(
            verbose=True, nr_topics=num_topics, vectorizer_model=vectorizer_model
        )

        topics, probabilities = topic_model.fit_transform(titles)

        topic_info = topic_model.get_topic_info()

        topics_with_titles = {}
        for topic in topic_info["Topic"].unique():
            if topic != -1:  # Exclude outliers
                topic_titles = [titles[i] for i, t in enumerate(topics) if t == topic]
                topic_keywords = topic_model.get_topic(topic)
                topics_with_titles[f"Topic {topic}"] = {
                    "keywords": [kw[0] for kw in topic_keywords],
                    "titles": topic_titles,
                }

        # Save the topic information to a JSON file
        with open(topic_analysis_file_name, "w", encoding="utf-8") as f:
            json.dump(topics_with_titles, f, ensure_ascii=False, indent=4)
        logging.info("Topic modelling results saved to %s", topic_analysis_file_name)

        # Print out the statistics
        logging.info("Total unique titles: %d", len(titles))
        logging.info("Total topics found: %d", len(topics_with_titles))

        # save the visualization to a file
        topic_model.visualize_barchart().write_html(topic_bar_chart_file_name)
        logging.info("Topic visualization saved to topic_visualization.html")

    def save_to_file(self, filename: str = "rss_data.json") -> None:
        """
        Save the extracted titles from each URL to a JSON file.

        Args:
            filename (str, optional): JSON filename to save extracted titles to. Defaults to "rss_data.json".
        """
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.rss_content, f, ensure_ascii=False, indent=4)
        logging.info("Data saved to %s", filename)


if __name__ == "__main__":

    scraper = RSSScraper(
        pdf_url="https://about.fb.com/wp-content/uploads/2016/05/rss-urls-1.pdf"
    )
    # Step 1: Download the PDF
    scraper.download_pdf(download_path="rss_urls.pdf")
    # Step 2: Extract URLs from the PDF
    scraper.extract_urls()
    # Step 3: Verify and extract titles from the URLs
    scraper.extract_data(num_threads=10)
    # Step 4: Save the extracted data to a JSON file
    scraper.save_to_file(filename="./artifacts/rss_data.json")
    # Step 5: Run sanity checks on the data
    scraper.run_data_check()
    # Step 6: Perform topic modelling on the extracted titles
    scraper.topic_modelling(
        num_topics=10,
        topic_analysis_file_name="./artifacts/topic_analysis.json",
        topic_bar_chart_file_name="./artifacts/topic_visualization.html",
    )
