import sys, requests, json
from requests import HTTPError
class NYTimesComments:
    def __init__(self) -> None:
        self.headers = \
        {
            "Host": "www.nytimes.com",\
            "Accept": "*/*",\
            "Accept-Language": "en-US,en;q=0.5",\
            "Accept-Encoding":"gzip, deflate, br",\
            "Connection":"close",\
            "Cookie": "nyt-gdpr=0",\
            "Referer": "https://www.nytimes.com",\
            "TE":"Trailers",\
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"
        }
    def error(self, msg):
        print(msg)

    def get_parent_comments(self, articleURL):
        self.headers["Referer"] = articleURL
        commentsURL = "https://www.nytimes.com/svc/community/V3/requestHandler?url={articleURL}&method=get&commentSequence=0&offset=0&includeReplies=true&sort=oldest&cmd=GetCommentsAll&limit=-1".format(articleURL=articleURL)

        response = requests.get(commentsURL, headers = self.headers)
        try:
            response.raise_for_status()
        except HTTPError as e:
            self.error("Failed to get comments for article: {}\n{}".format(articleURL, repr(e)))
            return
        
        data = response.json()
        parentComments = data['results']['comments']
        replyCnt = 0
        for cmt in parentComments:
            # by default, only 3 replies are returned
            if cmt["replyCount"] > 3:
                replies = self._get_reply_comments(articleURL, cmt['commentSequence'], 0, cmt["replyCount"])
                if replies:
                    cmt['replies'] = replies
                    replyCnt += (len(replies) - 3)
        data['results']['totalCommentsReturned'] += replyCnt
        data['results']['totalReplyCommentsReturned'] += replyCnt
        
        outFile = articleURL.split('/')[-1].split('.')[0]+'.json'
        with open(outFile, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    def _get_reply_comments(self, articleURL, commentSequence, offset, limit):
        commentsURL = "https://www.nytimes.com/svc/community/V3/requestHandler?url={articleURL}&method=get&commentSequence={commentSequence}&offset={offset}&limit={limit}&cmd=GetRepliesBySequence".format(articleURL=articleURL, commentSequence=commentSequence, offset=offset, limit=limit)

        response = requests.get(commentsURL, headers = self.headers)
        try:
            response.raise_for_status()
        except HTTPError as e:
            self.error("Failed to get reply comments for for comment {} of article: {}\n{}".format(commentSequence, articleURL, repr(e)))
            return None
        return response.json()['results']['comments'][0]['replies']

if __name__ == "__main__":
    worker = NYTimesComments()
    articleURL = sys.argv[1]
    worker.get_parent_comments(articleURL)
