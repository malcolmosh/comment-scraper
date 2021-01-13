import sys, requests, json, os
from requests import HTTPError
#from jsonObj import washingtonPostInitialRequestPayload, washingtonPostLoadMoreRequestPayload, testHeader, testData, payloadTest
class NewYorkTimes:
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

class WashingtonPost:
    def __init__(self) -> None:
        self.API_ENDPOINT = "https://www.washingtonpost.com/talk/api/v1/graph/ql"

    def error(self, msg):
        print(msg)

    @staticmethod
    def __load_initial_request_headers():
        headers = \
        {
            "Host": "www.washingtonpost.com",\
            "Accept": "*/*",\
            "Accept-Language": "en-US,en;q=0.5",\
            "Accept-Encoding":"gzip, deflate, br",\
            "Content-Type": "application/json",\
            "Origin": "https://www.washingtonpost.com",\
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"
        }
        return headers

    @staticmethod
    def __load_initial_request_payload():
        with open('WSPinitPayload.json', encoding='utf-8') as f:
            return json.load(f)

    def __build_initial_request_headers(self, url):
        header = self.__load_initial_request_headers()
        header['Referer'] = url
        return header

    def __build_initial_request_payload(self, url):
        payload = self.__load_initial_request_payload()
        payload['variables']['assetUrl'] = url
        return json.dumps(payload)

    def get_article_comments(self, articleURL):
        # request asset id and comment number
        response = requests.post(self.API_ENDPOINT, headers = self.__build_initial_request_headers(articleURL), data = self.__build_initial_request_payload(url))
        try:
            response.raise_for_status()
        except HTTPError as e:
            self.error("Failed to get comments for article: {}\n{}".format(articleURL, repr(e)))
            return
        
        response = response.json()
        assetID = response['data']['asset']['id']
        cmtCnt = response['data']['asset']['totalCommentCount']
        print(assetID, cmtCnt)
    
    def _get_reply_comments(self, articleURL, commentSequence, offset, limit):
        commentsURL = "https://www.washingtonpost.com/talk/api/v1/graph/ql"
        response = requests.get(commentsURL, headers = self.headers)
        try:
            response.raise_for_status()
        except HTTPError as e:
            self.error("Failed to get reply comments for for comment {} of article: {}\n{}".format(commentSequence, articleURL, repr(e)))
            return None
        return response.json()['results']['comments'][0]['replies']

if __name__ == "__main__":
    url = "https://www.washingtonpost.com/opinions/2021/01/11/hillary-clinton-impeach-trump-capitol-white-supremacy/"
    wsp = WashingtonPost()
    wsp.get_article_comments(url)
