import sys, requests, json, os, argparse
from requests import HTTPError
from urllib.parse import urlparse
import functools
from bs4 import BeautifulSoup

def base_header():
    headers = \
    {
        "Accept-Language": "en-US,en;q=0.5",\
        "Accept-Encoding":"gzip, deflate, br",\
        "Connection":"close",\
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0"
    }
    return headers

class __SolutionSkeleton__():
    def __init__(self) -> None:
        self.headers = base_header()
        self.headers["Content-Type"] = "application/json"
        self.headers["Accept"] = "*/*"

    def request_routine(self, url):
        # comment request routine, return the json object of comments
        raise NotImplementedError

    def error(self, msg):
        print('Error: \n', msg)
    
    def warn(self, msg):
        print('Warn: \n', msg)

    def info(self, msg):
        print('Info: \n', msg)

class NewYorkTimes(__SolutionSkeleton__):
    def __init__(self) -> None:
        super().__init__()
        self.headers["Host"] = "www.nytimes.com"

    def request_routine(self, articleURL):
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
                replies = self.__get_reply_comments__(articleURL, cmt['commentSequence'], 0, cmt["replyCount"])
                if replies:
                    cmt['replies'] = replies
                    replyCnt += (len(replies) - 3)
        comments['results']['totalCommentsReturned'] += replyCnt
        comments['results']['totalReplyCommentsReturned'] += replyCnt
        
        return comments
    
    def __get_reply_comments__(self, articleURL, commentSequence, offset, limit):
        commentsURL = "https://www.nytimes.com/svc/community/V3/requestHandler?url={articleURL}&method=get&commentSequence={commentSequence}&offset={offset}&limit={limit}&cmd=GetRepliesBySequence".format(articleURL=articleURL, commentSequence=commentSequence, offset=offset, limit=limit)

        response = requests.get(commentsURL, headers = self.headers)
        try:
            response.raise_for_status()
        except HTTPError as e:
            self.error("Failed to get reply comments for for comment {} of article: {}\n{}".format(commentSequence, articleURL, repr(e)))
            return None
        return response.json()['results']['comments'][0]['replies']

class CoralByGet(__SolutionSkeleton__):
    pass

class CoralByPost(__SolutionSkeleton__):
    def __init__(self, endpoint, batchSize = 500) -> None:
        super().__init__()
        self.LIMIT = batchSize
        self.API_ENDPOINT = endpoint

        parsedUrl = urlparse(endpoint)
        self.headers["Host"] = parsedUrl.netloc
        self.headers["Origin"] = "{}://{}".format(parsedUrl.scheme, parsedUrl.netloc)

    @staticmethod
    def __load_initial_query__():
        with open('coral-initial-query.txt', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    def __load_more_query__():
        with open('coral-load-more-query.txt', encoding='utf-8') as f:
            return f.read()

    def __build_initial_request_payload__(self, url):
        query = self.__load_initial_query__().replace('__LIMIT__', str(self.LIMIT))
        payload = {
            "query": query,
            "variables": {
                "assetId": "",
                "assetUrl": url,
                "commentId": "",
                "hasComment": False,
                "excludeIgnored": False,
                "sortBy": "CREATED_AT",
                "sortOrder": "ASC"
            }
        }
        return json.dumps(payload)

    def __build_request_more_payload__(self, cursor, parentID, assetID):
        query = self.__load_more_query__().replace('__LIMIT__', str(self.LIMIT))
        payload = {
            "query": query,
            "variables": {
                "limit": self.LIMIT,
                "cursor": cursor,
                "parent_id": parentID,
                "asset_id": assetID,
                "sortOrder": "ASC",
                "sortBy": "CREATED_AT",
                "excludeIgnored": False
            }
        }
        return json.dumps(payload)

    def request_routine(self, articleURL):
        #self.headers["Referer"] = articleURL
        # parsedUrl = urlparse(articleURL)
        # articleURL = '{}://{}{}'.format(parsedUrl.scheme, parsedUrl.netloc, parsedUrl.path)
        # request initial comments
        payload = self.__build_initial_request_payload__(articleURL)
        response = requests.post(self.API_ENDPOINT, headers = self.headers, data = payload)
        try:
            response.raise_for_status()
            data = response.json()
        except HTTPError as e:
            self.error("Failed to get comments for article: {}\n{}".format(articleURL, repr(e)))
            return
    
        assetID = data['data']['asset']['id']
        comments = data['data']['asset']['comments']

        cnt = 0
        requestCnt = 1
        # dfs each comment and load all replies as needed.
        def load_replies(assetID, parentNode, parentID):
            nonlocal cnt, requestCnt
            hasNextPage = parentNode['hasNextPage']
            cursor = parentNode['endCursor']
            while hasNextPage:
                requestCnt += 1
                response = requests.post(self.API_ENDPOINT, headers = self.headers, data = self.__build_request_more_payload__(cursor, parentID, assetID))
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
                cnt += 1
                if 'replies' in cmt:
                    load_replies(assetID, cmt['replies'], cmt['id'])
        load_replies(assetID, comments, None)
        self.info('{} comments loaded, {} requests made for article {}'.format(cnt, requestCnt,articleURL))
        return data

class WashingtonPost(CoralByPost):
    def __init__(self, batchSize=500) -> None:
        super().__init__("https://www.washingtonpost.com/talk/api/v1/graph/ql", batchSize=batchSize)
        self.headers["Origin"] = "https://www.washingtonpost.com"

class SeattleTimes(CoralByPost):
    def __init__(self, batchSize=500) -> None:
        super().__init__("https://seattletimes.talk.coralproject.net/api/v1/graph/ql", batchSize=batchSize)

class TheIntercept(CoralByPost):
    def __init__(self, batchSize=500) -> None:
        super().__init__("https://talk.theintercept.com/api/v1/graph/ql", batchSize=batchSize)
    
    def request_routine(self, articleURL):
        headers = base_header()
        headers["Host"] = "theintercept.com"
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        response = requests.get(articleURL, headers =headers)
        s = response.content.decode(response.encoding)
        idx = s.find('post_id')
        if idx == -1:
            self.error('Cannot find post id in {}.'.format(articleURL))
            return
        postID = []
        while not s[idx].isdigit():
            idx += 1
        while idx < len(s) and s[idx].isdigit():
            postID.append(s[idx])
            idx += 1
        postID = ''.join(postID)

        return super().request_routine("https://theintercept.com/?p={}".format(postID))

class DeseretNews(CoralByPost):
    def __init__(self, batchSize=500) -> None:
        super().__init__("https://deseretnews.talk.coralproject.net/api/v1/graph/ql", batchSize=batchSize)

class NUnl(CoralByPost):
    def __init__(self, batchSize=500) -> None:
        super().__init__("https://talk.nu.nl/api/v1/graph/ql", batchSize=batchSize)
    
    def request_routine(self, articleURL):
        try:
            postID = articleURL.split('/')[4]
        except Exception as e:
            self.error('Unrecognized patter for url from NU.nl.')
            return

        return super().request_routine("https://www.nu.nl/artikel/{}/redirect.html".format(postID))

SOLUTION_MAP = {'www.washingtonpost.com': WashingtonPost(), 'www.seattletimes.com': SeattleTimes(), 'www.nytimes.com': NewYorkTimes(), 'theintercept.com': TheIntercept(), 'www.deseret.com': DeseretNews(), 'www.nu.nl': NUnl()}

class CommentScraper:
    def __init__(self) -> None:
        pass
    
    def __get_solution__(self, host):
        return SOLUTION_MAP.get(host, None)

    def __build_output__(self, parsedUrl, filepath, filename):
        if filename:
            if filepath:
                output = os.path.join(filepath, filename)
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
            if filepath:
                output = os.path.join(filepath, parsedUrl.netloc, *urlPath, filename)
            else:
                output = os.path.join('.', parsedUrl.netloc, *urlPath, filename)
        return output

    def load_comments(self, articleURL, filepath=None, filename=None):
        parsedUrl = urlparse(articleURL)
        articleURL = '{}://{}{}'.format(parsedUrl.scheme, parsedUrl.netloc, parsedUrl.path)
        output = self.__build_output__(parsedUrl, filepath, filename)

        sol = self.__get_solution__(parsedUrl.netloc)
        if sol:
            comments = sol.request_routine(articleURL)
            if comments:
                if not os.path.exists(os.path.dirname(output)):
                    try:
                        os.makedirs(os.path.dirname(output))
                    except Exception as e:
                        print(repr(e))
                        return
                with open(output, 'w+', encoding='utf-8') as f:
                    json.dump(comments, f, ensure_ascii=False, indent=4)
        else:
            print(parsedUrl.netloc, ' is not supported.')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape comments from the input article URL.')
    parser.add_argument('-url', '--url', type=str, help='An article url from supported websites.')
    parser.add_argument('--filename', type=str, help='The output file name for the comments json file. If not given, the url path is used.')
    parser.add_argument('--filepath', type=str, help='The output file path for the comments json file, default to current directory.')
    parser.add_argument('-l', '--list', action='store_true', help='List supported websites.')
    
    args = parser.parse_args()
    if args.list:
        print('\n'.join(SOLUTION_MAP))
    if args.url:
        scraper = CommentScraper()
        scraper.load_comments(args.url, filepath=args.filepath, filename=args.filename)
    exit()
