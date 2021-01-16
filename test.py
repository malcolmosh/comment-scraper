from CommentScraper import CommentScraper

testURl = ["https://www.nu.nl/politiek/6100724/kabinet-treedt-af-vanwege-vernietigend-rapport-over-toeslagenaffaire.html#coral_talk_wrapper", "https://www.deseret.com/utah/2021/1/14/22228950/coronavirus-vaccine-delays-local-health-departments-doing-best-covid-19-older-residents-vaccinated", "https://theintercept.com/2021/01/15/deconstructed-jayapal-capitol-escape/", "https://www.washingtonpost.com/politics/capitol-police-intelligence-warning/2021/01/15/c8b50744-5742-11eb-a08b-f1381ef3d207_story.html", "https://www.seattletimes.com/seattle-news/politics/former-gubernatorial-candidate-loren-culp-drops-election-fraud-lawsuit-after-washington-state-threatens-legal-sanctions/"]#, "https://www.nytimes.com/2021/01/14/opinion/trump-evangelicals.html"]

scraper = CommentScraper()
for url in testURl:
    scraper.load_comments(url, 'data')
