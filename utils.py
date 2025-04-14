import re


def fix_encoding_issues(text):
    """
    Fixes encoding issues such as invalid characters caused by incorrect decoding (e.g., â\x80\x99).
    
    Args:
        text (str): The input text with potential encoding issues.
    
    Returns:
        str: The text with encoding issues fixed.
    """
    try:
        # Fix misinterpreted UTF-8 as Latin-1 by re-encoding and decoding properly
        return text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        # Return original text if re-encoding fails <- sometimes happens
        return text


def replace_problematic_sequences(text):
    """
    Replaces problematic sequences like â\x80\x99 with their correct characters.
    
    Args:
        text (str): The input text containing problematic sequences.
    
    Returns:
        str: The cleaned text with problematic sequences replaced.
    """
    # this is sort of a brute force way of doing it for common encodings found in the files
    # commonly found characters that should be replaced with interpretable alternatives
    replacements = {
        "â\x80\x99": "’",   
        "â\x80\x9c": "“",
        "â\x80\x9d": "”",
        "â\x80\x93": "–",
        "â\x80\x94": "—",
        "â\x80¦": "…",
    }

    for sequence, replacement in replacements.items():
        text = text.replace(sequence, replacement)
    return text


def remove_html_tags(text):
    """
    Removes HTML tags from the input text using a regular expression.
    
    Args:
        text (str): The text containing HTML tags.
    
    Returns:
        str: The text with HTML tags removed.
    """
    return re.sub(r"<[^>]+>", "", text)


def remove_unwanted_characters(text):
    """
    Removes unwanted characters while keeping essential punctuation like apostrophes, hyphens, quotes and ampersands.
    
    Args:
        text (str): The input text containing unwanted characters.
    
    Returns:
        str: The cleaned text with unwanted characters removed.
    """
    return re.sub(r"[^\w\s'-“”’&]", "", text)


def normalize_whitespace(text):
    """
    Normalizes whitespace by replacing multiple spaces with a single space and stripping leading/trailing spaces.

    Args:
        text (str): The input text with irregular spacing.

    Returns:
        str: The cleaned text with normalized whitespace.
    """
    return re.sub(r"\s+", " ", text).strip()


def clean_title(title):
    """
    Cleans an individual title by removing HTML tags, fixing encoding issues, replacing problematic sequences,
    removing unwanted characters, and normalizing whitespace.

    Args:
        title (str): The raw title to clean.

    Returns:
        str: The cleaned title.
    """
    title = remove_html_tags(title)
    title = fix_encoding_issues(title)
    title = replace_problematic_sequences(title)
    title = remove_unwanted_characters(title)
    title = normalize_whitespace(title)

    return title
