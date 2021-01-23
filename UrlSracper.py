import sys, requests, json, os, argparse, random, time, mysql.connector, hashlib, dateutil.parser
from requests.models import Response
from utility import Message, base_header
from requests import HTTPError
from bs4 import BeautifulSoup

class UrlScraper(Message):
    def __init__(self, DBHost='localhost', DBName='mysql', DBUserName='mysql', DBPassword='mysql', updateInterval=120, batchSize=15, outputPath=None) -> None:
        super().__init__()
        self.DBCon = None
        try:
            self.DBCon = mysql.connector.connect(host=DBHost, database=DBName, user=DBUserName, password=DBPassword)
            self.DBCon.autocommit(True)
        except mysql.connector.Error as err:
            self.error(repr(err))
            exit()
        self.updateInterval = updateInterval
        self.batchSize = batchSize
        self.outputPath = outputPath
    def __date_url_hash(self, date: str, url: str) -> str:
        """Generate a global identifier using the date and the last 8 character of the md5 hash string of the url.

        Args:
            date (str): published data.
            url (str): article url

        Returns:
            str: identifier in the format of "yyyy-mm-dd-xxxxxxxx".
        """
        return dateutil.parser.parse(date).strftime('%y-%m-%d-') + hashlib.md5(url.encode('utf-8')).hexdigest()[-1:-9:-1]

    def __request_page_source__(self, url:str) -> str:
        """Request HTML source of the input url.

        Args:
            url (str): target url.

        Returns:
            str: source codes or None.
        """

        headers = base_header()
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        headers['Accept-Encoding'] = 'identity'
        response = requests.get(url, headers = headers)
        try:
            response.raise_for_status()
        except HTTPError as e:
            self.error("Failed to request HTML source codes from {}: \n{}".format(url, repr(e)))
            return None

        return response.content.decode(encoding=response.encoding)

    def add_url(self, url:str, title: str, key: str, publishedTime: str=None, topic: str=None) -> bool:
        """Add a url to the queue.

        Args:
            url (str): an article url to be added.
            title (str): article title.
            key (str): a global uniform identifier for the url.
            publishedTime ([str], optional): published time of the article  . Defaults to None.
            topic ([str], optional): topic of the article. Defaults to None.

        Returns:
            bool: add success or not.
        """
        pass

    def find_url(self, url:str) -> bool:
        """Find url in the queue.

        Args:
            url (str): url to find.

        Returns:
            bool: find url or not.
        """
        pass

    def bootstrap(self) -> None:
        """Initiate the scraping process, insert all currently available url from the source to the queue.
        """
        pass

    def update(self) -> None:
        """Retrieve new urls from the source since last visit.
        """
        pass

    def main_routine(self) -> None:
        """The main routine of the url scraping process.
        """
        self.info('Start the boostrap process...')
        self.bootstrap()
        self.info('The boostrape process is finished.')
        while 1:
            self.info('I am going to sleep for {} minute(s) before next update.'.format(self.updateInterval))
            cnt = self.updateInterval
            while cnt > 0:
                self.debug('Sleeping, wake up in {} minutes.'.format(cnt))
                time.sleep(60)
                cnt -= 1
            self.info('Start the update process...')
            self.update()
            self.info('The update process is finished.')

class WashingtonPostUrlScraper(UrlScraper):
    def __init__(self, DBHost, DBName, DBUserName, DBPassword, updateInterval) -> None:
        super().__init__(DBHost=DBHost, DBName=DBName, DBUserName=DBUserName, DBPassword=DBPassword, updateInterval=updateInterval)
        self.API_ENDPOINT = "https://www.washingtonpost.com/pb/api/v2/render/feature/section/story-list?content_origin=prism-query&url=prism://prism.query/site-articles-only,/{section}&offset={offset}&limit={limit}"
        self.sections = ['politics', 'opinions', 'technology', 'world', 'sports', 'business', 'national']

    def bootstrap(self) -> None:
        super().bootstrap()

        headers = base_header()
        headers['Accept'] = '*/*'
        headers['X-Requested-With'] = "XMLHttpRequest"
        for section in self.sections:
            for offset in range(10000-self.batchSize, -1, -self.batchSize):
                requestURL = self.API_ENDPOINT.format(section=section, offset=offset, limit=self.batchSize)
                response = requests.get(requestURL, headers=headers)
                try:
                    response.raise_for_status()
                    response = response.json()
                except HTTPError as e:
                    self.error("Failed to complete the boostrap process: \n{}".format(repr(e)))
                    exit()
                soup = BeautifulSoup(markup='<html><body>{}</body></html>'.format(response['rendering']))
                for a in soup.select('div[class="story-headline"] > h2 > a'):
                    url = a['href']
                    title = str(a.string)
                    if not self.find_url(url):
                        source = self.__request_page_source__(url)
                        publishedTime = None
                        if source:
                            soup = BeautifulSoup(markup=source)
                            publishedTime = soup.select_one('meta[property="article:published_time"]')['content']
                        if self.add_url(url, title, publishedTime=publishedTime):
                            output = self.__date_url_hash(publishedTime, url) + '.html'
                            if self.outputPath:
                                output += os.path.join(self.outputPath, output)
                            with open(output, 'w+', encoding='utf-8') as f:
                                f.write(source)
                    else:
                        self.info('{} already exists, skipping.'.format(url))
        
    def update(self) -> None:
        super().update()

        headers = base_header()
        headers['Accept'] = '*/*'
        headers['X-Requested-With'] = "XMLHttpRequest"
        for section in self.sections:
            for offset in range(0, 101-self.batchSize, self.batchSize):
                requestURL = self.API_ENDPOINT.format(section=section, offset=offset, limit=self.batchSize)
                response = requests.get(requestURL, headers=headers)
                try:
                    response.raise_for_status()
                    response = response.json()
                except HTTPError as e:
                    self.error("Failed to get comments for article: {}\n{}".format(self.targetUrl, repr(e)))
                    return
                soup = BeautifulSoup(markup='<html><body>{}</body></html>'.format(response['rendering']))
                for a in soup.select('div[class="story-headline"] > h2 > a'):
                    url = a['href']
                    title = str(a.string)
                    if not self.find_url(url):
                        source = self.__request_page_source__(url)
                        publishedTime = None
                        if source:
                            soup = BeautifulSoup(markup=source)
                            publishedTime = soup.select_one('meta[property="article:published_time"]')['content']
                        if self.add_url(url, title, publishedTime=publishedTime):
                            output = self.__date_url_hash(publishedTime, url) + '.html'
                            if self.outputPath:
                                output += os.path.join(self.outputPath, output)
                            with open(output, 'w+', encoding='utf-8') as f:
                                f.write(source)
                    else:
                        # match a url already exists, which means we have added all the news urls since last sleep.
                        break
            self.info('Update finished for section {} in Washington Post.'.format(section))





