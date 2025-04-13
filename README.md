# RSS Scraper

### (3a) What is a unit test? Write a pseudo-code for a unit-test for the rss feed scraper (just rough, doesn’t need to be super deep). Think about the library you’re using, the naming conventions, and also ease of use/speed

A unit test verifies core functionality in a codebase, making sure it works as expected, often by comparing the functionality's output with our expectations for it. 

I defined a full test suite in `tests.py`, but here is quick pseudo-code for the actual RSS parsing + cleaning component 

I would run it across two complexities of RSS feeds, one that's linear and straightforward, and one that's more complex with special characters, nesting etc. If the first complexity level fails, it immediately shows that core parsing itself is broken. If the second fails, one should look deeper into the pre-processing and cleaning steps. 

### (3b) What data checks can you do upon first extraction to ensure your data is sane? What do 2 of these checks look like?

1. Check that the length of the title is of reasonable length. Often parsers can cut-off strings, resulting in single-world titles. While there can be single-word titles, the distribution of this data shows that it is not common. 

2. Per-feed checks - If some fields past the pre-processing step (which checks that the website indeed leads to XML data), but returned only 1 title or none at all, it's probably worth looking into, as that link might have malformed data. Titles shouldn't be near-identical as well.

### (3c) What are the limitations of the data that you have extracted? Are there any glaring biases upon first glance?

It's a 2016 list of RSS feeds, so most of the links are dead and end up failing my first check, that verifies if the link actually leads to RSS data. 

### (3d) What stats/ML models can you use to extract information from the titles?

Since the feeds return data around a similar time range, one can quickly visualise the common "topics" across the extracted titles using topic modelling. I implemented rudimentary topic modelling using BERTopic. 

Other forms of textual analysis include:
1. Keyword extraction - either through TF-IDF
2. Sentiment analysis - group titles into different tones / sentiments
3. Named Entity Recognition (NER) - news items often have a subject that they refer to / are centered around. NER can identify the main entities discussed in the day's news.

### Other Features of This Tool

1. I implementated multi-threading to speed up the scraping + parsing process.
2. 4 tests are available in `tests.py`, which test the core functionality of the tool. It can be run using `pytest tests.py`.
3. Post-pipeline data checks are implemented