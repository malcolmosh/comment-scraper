import json
from CommentScraper import NewYorkTimes

nyt = NewYorkTimes()
with open("nyt.json", encoding='utf-8') as input:
    data = json.load(input)
    nyt.restore_structure(data)
    with open("nyt-mod.json", 'w', encoding='utf-8') as output:
        json.dump(data, output, indent=4)

