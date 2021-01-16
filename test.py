from CommentScraper import CommentScraper

testURl = ["https://theintercept.com/2021/01/15/deconstructed-jayapal-capitol-escape/", "https://www.washingtonpost.com/politics/capitol-police-intelligence-warning/2021/01/15/c8b50744-5742-11eb-a08b-f1381ef3d207_story.html", "https://www.seattletimes.com/seattle-news/politics/former-gubernatorial-candidate-loren-culp-drops-election-fraud-lawsuit-after-washington-state-threatens-legal-sanctions/"]#, "https://www.nytimes.com/2021/01/14/opinion/trump-evangelicals.html"]

scraper = CommentScraper()
for url in testURl:
    scraper.load_comments(url, 'data')