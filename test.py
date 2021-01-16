from CommentScraper import CommentScraper

testURl = ["https://www.washingtonpost.com/national-security/terror-watchlist-capitol-riot-fbi/2021/01/14/07412814-55f7-11eb-a931-5b162d0d033d_story.html", "https://www.seattletimes.com/seattle-news/politics/former-gubernatorial-candidate-loren-culp-drops-election-fraud-lawsuit-after-washington-state-threatens-legal-sanctions/", "https://theintercept.com/2021/01/15/deconstructed-jayapal-capitol-escape/", "https://www.nytimes.com/2021/01/14/opinion/trump-evangelicals.html"]

scraper = CommentScraper()
for url in testURl:
    scraper.load_comments(url, 'data')