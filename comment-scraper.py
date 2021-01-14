import sys, requests, json, os, argparse
from requests import HTTPError
from urllib.parse import urlparse

SUPPORTED_WEBSITES = ['www.nytimes.com', 'www.washingtonpost.com', 'www.seattletimes.com']

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

    def load_comments(self, articleURL):
        self.headers["Referer"] = articleURL
        commentsURL = "https://www.nytimes.com/svc/community/V3/requestHandler?url={articleURL}&method=get&commentSequence=0&offset=0&includeReplies=true&sort=oldest&cmd=GetCommentsAll&limit=-1".format(articleURL=articleURL)

        response = requests.get(commentsURL, headers = self.headers)
        try:
            response.raise_for_status()
        except HTTPError as e:
            self.error("Failed to get comments for article: {}\n{}".format(articleURL, repr(e)))
            return
        
        comments = response.json()
        parentComments = comments['results']['comments']
        replyCnt = 0
        for cmt in parentComments:
            # by default, only 3 replies are returned
            if cmt["replyCount"] > 3:
                replies = self._get_reply_comments(articleURL, cmt['commentSequence'], 0, cmt["replyCount"])
                if replies:
                    cmt['replies'] = replies
                    replyCnt += (len(replies) - 3)
        comments['results']['totalCommentsReturned'] += replyCnt
        comments['results']['totalReplyCommentsReturned'] += replyCnt
        
        return comments
    
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
    def __init__(self, batchSize = 500) -> None:
        self.API_ENDPOINT = "https://www.washingtonpost.com/talk/api/v1/graph/ql"
        self.LIMIT = str(batchSize)
    def error(self, msg):
        print(msg)

    @staticmethod
    def __build_request_headers(url):
        headers = \
        {
            "Host": "www.washingtonpost.com",\
            "Accept": "*/*",\
            "Accept-Language": "en-US,en;q=0.5",\
            "Accept-Encoding":"gzip, deflate, br",\
            "Content-Type": "application/json",\
            "Origin": "https://www.washingtonpost.com",\
            "Referer": url,\
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"
        }
        return headers

    @staticmethod
    def __load_initial_request_payload(limit):
        with open('WSPinitPayload.json', encoding='utf-8') as f:
            s = f.read().replace('__LIMIT__', limit)
            ret = json.loads(s)
            return ret

    @staticmethod
    def __load_request_more_payload(limit):
        with open('WPSLoadMorePayload.json', encoding='utf-8') as f:
            s = f.read().replace('__LIMIT__', limit)
            ret = json.loads(s)
            return ret

    # def __build_initial_request_headers(self, url):
    #     header = self.__request_headers_base()
    #     header['Referer'] = url
    #     return header

    def __build_initial_request_payload(self, url):
        payload = self.__load_initial_request_payload(self.LIMIT)
        payload['variables']['assetUrl'] = url
        return json.dumps(payload)

    def __build_request_more_payload(self, limit, cursor, parentID, assetID):
        payload = self.__load_request_more_payload(self.LIMIT)
        #payload['variables']['limit'] = limit
        payload['variables']['cursor'] = cursor
        payload['variables']['parent_id'] = parentID
        payload['variables']['asset_id'] = assetID
        return json.dumps(payload)

    def load_comments(self, articleURL):
        parsedUrl = urlparse(articleURL)
        articleURL = '{}://{}{}'.format(parsedUrl.scheme, parsedUrl.netloc, parsedUrl.path)
        # request initial comments
        response = requests.post(self.API_ENDPOINT, headers = self.__build_request_headers(articleURL), data = self.__build_initial_request_payload(articleURL))
        try:
            response.raise_for_status()
            data = response.json()
        except HTTPError as e:
            self.error("Failed to get comments for article: {}\n{}".format(articleURL, repr(e)))
            return
    
        assetID = data['data']['asset']['id']
        comments = data['data']['asset']['comments']

        # dfs each comment and load all replies as needed.
        def load_replies(assetID, parentNode, parentID):
            hasNextPage = parentNode['hasNextPage']
            cursor = parentNode['endCursor']
            while hasNextPage:
                response = requests.post(self.API_ENDPOINT, headers = self.__build_request_headers(articleURL), data = self.__build_request_more_payload(self.LIMIT, cursor, parentID, assetID))
                try:
                    response.raise_for_status()
                    replies = response.json()
                except HTTPError as e:
                    self.error("Failed to get part of comments for article: {}\n{}".format(articleURL, repr(e)))
                    break
                parentNode['nodes'] += replies['data']['comments']['nodes']
                hasNextPage = replies['data']['comments']['hasNextPage']
                cursor = replies['data']['comments']['endCursor']

            for cmt in parentNode['nodes']:
                # if cmt['id'] not in seen:
                #     seen.add(cmt['id'])
                #     commentCnt += 1
                # else:
                #     print('comment {} is visited before'.format(cmt['id']))
                if cmt['replyCount'] > 0:
                    load_replies(assetID, cmt['replies'], cmt['id'])
        load_replies(assetID, comments, None)

        return data

class SeattleTimes:
    def __init__(self, batchSize = 500) -> None:
        self.API_ENDPOINT = "https://seattletimes.talk.coralproject.net/api/v1/graph/ql"
        self.LIMIT = str(batchSize)
    def error(self, msg):
        print(msg)

    @staticmethod
    def __build_request_headers(url):
        headers = \
        {
            "Host": "seattletimes.talk.coralproject.net",\
            "Accept": "*/*",\
            "Accept-Language": "en-US,en;q=0.5",\
            "Accept-Encoding":"gzip, deflate, br",\
            "Content-Type": "application/json",\
            "Origin": "https://seattletimes.talk.coralproject.net",\
            "Referer": url,\
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"
        }
        return headers

    @staticmethod
    def __load_initial_request_payload(limit):
        with open('SeattleTimesInitPayload.json', encoding='utf-8') as f:
            s = f.read().replace('__LIMIT__', limit)
            ret = json.loads(s)
            return ret

    @staticmethod
    def __load_request_more_payload(limit):
        with open('WPSLoadMorePayload.json', encoding='utf-8') as f:
            s = f.read().replace('__LIMIT__', limit)
            ret = json.loads(s)
            return ret

    # def __build_initial_request_headers(self, url):
    #     header = self.__request_headers_base()
    #     header['Referer'] = url
    #     return header

    def __build_initial_request_payload(self, url):
        payload = self.__load_initial_request_payload(self.LIMIT)
        payload['variables']['assetUrl'] = url
        return json.dumps(payload)

    def __build_request_more_payload(self, limit, cursor, parentID, assetID):
        payload = self.__load_request_more_payload(self.LIMIT)
        #payload['variables']['limit'] = limit
        payload['variables']['cursor'] = cursor
        payload['variables']['parent_id'] = parentID
        payload['variables']['asset_id'] = assetID
        return json.dumps(payload)

    def load_comments(self, articleURL):
        parsedUrl = urlparse(articleURL)
        articleURL = '{}://{}{}'.format(parsedUrl.scheme, parsedUrl.netloc, parsedUrl.path)
        # request initial comments
        headers = self.__build_request_headers(articleURL)
        data = self.__build_initial_request_payload(articleURL)
        response = requests.post(self.API_ENDPOINT, headers = headers, data = data)
        try:
            response.raise_for_status()
            data = response.json()
        except HTTPError as e:
            self.error("Failed to get comments for article: {}\n{}".format(articleURL, repr(e)))
            return
    
        assetID = data['data']['asset']['id']
        comments = data['data']['asset']['comments']

        # dfs each comment and load all replies as needed.
        def load_replies(assetID, parentNode, parentID):
            hasNextPage = parentNode['hasNextPage']
            cursor = parentNode['endCursor']
            while hasNextPage:
                response = requests.post(self.API_ENDPOINT, headers = self.__build_request_headers(articleURL), data = self.__build_request_more_payload(self.LIMIT, cursor, parentID, assetID))
                try:
                    response.raise_for_status()
                    replies = response.json()
                except HTTPError as e:
                    self.error("Failed to get part of comments for article: {}\n{}".format(articleURL, repr(e)))
                    break
                parentNode['nodes'] += replies['data']['comments']['nodes']
                hasNextPage = replies['data']['comments']['hasNextPage']
                cursor = replies['data']['comments']['endCursor']

            for cmt in parentNode['nodes']:
                # if cmt['id'] not in seen:
                #     seen.add(cmt['id'])
                #     commentCnt += 1
                # else:
                #     print('comment {} is visited before'.format(cmt['id']))
                if cmt['replyCount'] > 0:
                    load_replies(assetID, cmt['replies'], cmt['id'])
        load_replies(assetID, comments, None)

        return data

class CommentScraper:
    def __init__(self) -> None:
        self.scraper = {'www.washingtonpost.com': WashingtonPost(), 'www.seattletimes.com': SeattleTimes(), 'www.nytimes.com': NewYorkTimes()}
    
    def load_comments(self, articleURL, output):
        comments = self.scraper[parsedUrl.netloc].load_comments(articleURL)
        if comments:
            if not os.path.exists(os.path.dirname(output)):
                try:
                    os.makedirs(os.path.dirname(output))
                except Exception as e:
                    print(repr(e))
                    return
            with open(output, 'w+', encoding='utf-8') as f:
                json.dump(comments, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape comments from the input article URL. Only articles from the following websites are supported:\n{}\n{}'.format('New York Times', 'Washington Post'))
    parser.add_argument('articleURL', type=str, help='An article url from supported websites.')
    parser.add_argument('--filename', type=str, help='The output file name for the comments json file. If not given, the url path is used.')
    parser.add_argument('--filepath', type=str, help='The output file path for the comments json file, default to current directory.')
    
    args = parser.parse_args()
    parsedUrl = urlparse(args.articleURL)
    if parsedUrl.netloc not in SUPPORTED_WEBSITES:
        print(parsedUrl.netloc, ' is not supported.')
        exit()
    if args.filename:
        filename = args.filename
        if args.filepath:
            output = os.path.join(args.filepath, filename)
        else:
            output = os.path.join('.', filename)
    else:
        urlPath = parsedUrl.path.split('/')
        if urlPath[-1] == '':
            urlPath.pop()
        if urlPath[0] == '':
            del urlPath[0]

        filename = urlPath.pop().split('.')
        if len(filename) > 1:
            filename.pop()
        filename = '.'.join(filename) + '.json'
        if args.filepath:
            output = os.path.join(args.filepath, parsedUrl.netloc, *urlPath, filename)
        else:
            output = os.path.join('.', parsedUrl.netloc, *urlPath, filename)

    scraper = CommentScraper()
    scraper.load_comments(args.articleURL, output)
    exit()
