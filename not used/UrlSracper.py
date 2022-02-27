# import sys, requests, json, os, argparse, random, time, mysql.connector, hashlib, dateutil.parser
# from requests.models import Response
# from utility import Message, base_header
# from requests import HTTPError
# from bs4 import BeautifulSoup
# from mysql.connector import errorcode
# from urllib.parse import urlparse

# class UrlScraper(Message):
#     def __init__(self, DBHost='localhost', DBPort=3306, DBName='mysql', DBUser='mysql', DBPassword='mysql', updateInterval=120, batchSize=15, outputPath=None) -> None:
#         super().__init__()
#         self.DBCon = None
#         try:
#             self.DBCon = mysql.connector.connect(host=DBHost, port=DBPort, database=DBName, user=DBUser, password=DBPassword)
#             self.DBCon.autocommit = True
#             self.dbCursor = self.DBCon.cursor()
#         except mysql.connector.Error as err:
#             self.error(repr(err))
#             exit()
#         self.updateInterval = updateInterval
#         self.batchSize = batchSize
#         self.outputPath = outputPath
    
#     def __date_url_hash__(self, date: str, url: str) -> str:
#         """Generate a global identifier using the date and the last 8 character of the md5 hash string of the url.

#         Args:
#             date (str): published data.
#             url (str): article url

#         Returns:
#             str: identifier in the format of "yyyy-mm-dd-xxxxxxxx".
#         """
#         return dateutil.parser.parse(date).strftime('%Y-%m-%d-') + hashlib.md5(url.encode('utf-8')).hexdigest()[-1:-9:-1]

#     def __request_page_source__(self, url:str) -> str:
#         """Request HTML source of the input url.

#         Args:
#             url (str): target url.

#         Returns:
#             str: source codes or None.
#         """

#         headers = base_header()
#         headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
#         headers['Accept-Encoding'] = 'identity'
#         try:
#             response = requests.get(url, headers = headers)
#             response.raise_for_status()
#         except Exception as e:
#             self.error("Failed to request HTML source codes from {}: \n{}".format(url, repr(e)))
#             return None

#         return response.content.decode(encoding=response.encoding)

#     def add_url(self, url:str) -> bool:
#         """Add a url to the queue.

#         Args:
#             url (str): an article url to be added.

#         Returns:
#             bool: add success or not.
#         """
#         try:
#             self.dbCursor.execute("INSERT INTO url_queue(url, status) VALUES (%s, %s)", (url, -2))
#         except mysql.connector.IntegrityError as err:
#             return False
#         return True
    
#     def update_url(self, url: str, title: str = None, publishedTime: str=None, topic: str=None, category: str=None) -> int:
#         """Update info of a url.

#         Args:
#             url (str): url to be updated.
#             title (str): article title.
#             publishedTime ([str], optional): published time of the article  . Defaults to None.
#             topic ([str], optional): topic of the article. Defaults to None.

#         Returns:
#             int: number of updated rows.
#         """
#         publishedTime = dateutil.parser.parse(publishedTime).strftime('%Y-%m-%d %H:%M:%S')
#         self.dbCursor.execute("UPDATE url_queue SET status = %(status)s, date_hash = %(date_hash)s, host = %(host)s, title = %(title)s, topic = %(topic)s, category = %(category)s, published_time = %(published_time)s WHERE url = %(url)s;", {'url': url, 'status': 0, 'title': title, 'published_time': publishedTime, 'topic': topic, 'category': category, 'host': urlparse(url).hostname, 'date_hash': self.__date_url_hash__(publishedTime, url)})
#         return self.dbCursor.rowcount

#     def find_url(self, url:str) -> bool:
#         """Find url in the queue.

#         Args:
#             url (str): url to find.

#         Returns:
#             bool: find url or not.
#         """
#         self.dbCursor.execute('SELECT 1 FROM url_queue WHERE url = (%s);', (url,))
#         return len(self.dbCursor.fetchall()) > 0

#     def bootstrap(self) -> None:
#         """Initiate the scraping process, insert all currently available url from the source to the queue.
#         """
#         pass

#     def update(self) -> None:
#         """Retrieve new urls from the source since last visit.
#         """
#         pass

#     def main_routine(self) -> None:
#         """The main routine of the url scraping process.
#         """
#         self.info('Start the boostrap process...')
#         self.bootstrap()
#         self.info('The boostrape process is finished.')
#         while 1:
#             self.info('I am going to sleep for {} minute(s) before next update.'.format(self.updateInterval))
#             cnt = self.updateInterval
#             while cnt > 0:
#                 self.debug('Sleeping, wake up in {} minutes.'.format(cnt))
#                 time.sleep(60)
#                 cnt -= 1
#             self.info('Start the update process...')
#             self.update()
#             self.info('The update process is finished.')

# class WashingtonPostUrlScraper(UrlScraper):
#     def __init__(self, DBHost='localhost', DBPort=3306, DBName='mysql', DBUser='mysql', DBPassword='mysql', updateInterval=120, outputPath=None) -> None:
#         super().__init__(DBHost=DBHost, DBPort=DBPort, DBName=DBName, DBUser=DBUser, DBPassword=DBPassword, updateInterval=updateInterval, outputPath=outputPath)
#         self.API_ENDPOINT = "https://www.washingtonpost.com/pb/api/v2/render/feature/section/story-list?content_origin=prism-query&url=prism://prism.query/site-articles-only,/{section}&offset={offset}&limit={limit}"
#         self.sections = ['politics', 'opinions', 'technology', 'world', 'sports', 'business', 'national']

#     def __process_url__(self, url: str, topic: str = None, category: str = None) -> bool:
#         if self.add_url(url):
#             source = self.__request_page_source__(url)
#             publishedTime = None
#             title = None
#             if source:
#                 soup = BeautifulSoup(source, "lxml")
#                 publishedTime = soup.select_one('meta[property="article:published_time"]')
#                 if publishedTime:
#                     publishedTime = publishedTime['content']
#                 else:
#                     self.warn('Cannot find published time for {}'.format(url))
#                     publishedTime = '0001-01-01 00:00:00'

#                 title = soup.select_one('head title')
#                 if title:
#                     title = str(title.string).split(' - ')[0]
#                 else:
#                     self.warn('Cannot find title for {}'.format(url))
#                     #title = 'unknown'
#                 if self.update_url(url, title=title, publishedTime=publishedTime, topic=topic, category=category):
#                     output = self.__date_url_hash__(publishedTime, url) + '.html'
#                     if self.outputPath:
#                         output = os.path.join(self.outputPath, output)
#                     with open(output, 'w+', encoding='utf-8') as f:
#                         f.write(source)
#             self.info('Processed {}'.format(url))
#             return True
#         else:
#             self.info('{} already exists, skipping.'.format(url))
#             return False

#     def bootstrap(self) -> None:
#         super().bootstrap()

#         headers = base_header()
#         headers['Accept'] = '*/*'
#         headers['X-Requested-With'] = "XMLHttpRequest"
#         for section in self.sections:
#             for offset in range(10000-self.batchSize, -1, -self.batchSize):
#                 requestURL = self.API_ENDPOINT.format(section=section, offset=offset, limit=self.batchSize)
#                 try:
#                     response = requests.get(requestURL, headers=headers)
#                     response.raise_for_status()
#                     response = response.json()
#                 except Exception as e:
#                     self.error("Failed to complete the boostrap process: \n{}".format(repr(e)))
#                     exit()
#                 soup = BeautifulSoup('<html><body>{}</body></html>'.format(response['rendering']), "lxml")
#                 for a in soup.select('div[class="story-headline"] > h2 > a'):
#                     url = a['href']
#                     self.__process_url__(url, category=section)
        
#     def update(self) -> None:
#         super().update()

#         headers = base_header()
#         headers['Accept'] = '*/*'
#         headers['X-Requested-With'] = "XMLHttpRequest"
#         for section in self.sections:
#             #for offset in range(0, 0, self.batchSize):
#             requestURL = self.API_ENDPOINT.format(section=section, offset=0, limit=self.batchSize)
#             try:
#                 response = requests.get(requestURL, headers=headers)
#                 response.raise_for_status()
#                 response = response.json()
#             except Exception as e:
#                 self.error("Failed to retrieve part of urls from the Washington Post: {}\n{}".format( repr(e)))
#                 continue
#             soup = BeautifulSoup('<html><body>{}</body></html>'.format(response['rendering']), "lxml")
#             for a in soup.select('div[class="story-headline"] > h2 > a'):
#                 url = a['href']
#                 self.__process_url__(url, category=section)
#             self.info('Update finished for section {} in Washington Post.'.format(section))


# if __name__ == '__main__':
#     wsp = WashingtonPostUrlScraper(updateInterval=30, DBHost='localhost', DBName='comment-crawler', DBUser='root', DBPassword='root', outputPath='D:/request-based-comment-crawler/page')
#     wsp.main_routine()


