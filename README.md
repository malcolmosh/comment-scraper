# Comment Scrapper
This tool scrapes user comments. Given a url of an articles Web page, user comments are requested from the comments hosting server and saved in json file. Only the following websites/commenting platforms are supported:
- **Platform**:
  - [OpenWeb](https://www.openweb.com/) (formerly name Spot.IM)
  - [Coral](https://github.com/coralproject/talk)
    - A basic comments request routine is provided (see the [`CoralByPost`](https://github.com/ZhijiaCHEN/comment-scraper/blob/a1722c9770156082d3f66726b65a78bd88be8c4a/CommentScraper.py#L81) class). This basic routine needs to be tailored for each target website that manages comments on Coral. To implement the solution for a particular website, you will need to find the API endpoints of the target Coral server, and article identifier for the website, which is usually the article url, or some post id stored in each article page somewhere. Then you can subclass [`CoralByPost`](https://github.com/ZhijiaCHEN/comment-scraper/blob/a1722c9770156082d3f66726b65a78bd88be8c4a/CommentScraper.py#L81) and instruct the [comments request routine](https://github.com/ZhijiaCHEN/comment-scraper/blob/a1722c9770156082d3f66726b65a78bd88be8c4a/CommentScraper.py#L133) to extract the article identifier from the HTML source codes.
    - You may reference to the example solutions of the following websites:
      - [Washington Post](https://www.washingtonpost.com)
      - [Seattle Times](https://www.seattletimes.com)
      - [The Intercept](https://theintercept.com)
      - [Deseret News](https://www.deseret.com)
      - [NU](https://www.nu.nl)
- **Websites**
    - [New York Times](https://www.nytimes.com)

## Usages
To load comments from a target article url, use the command `python3 CommentScrapper.py --url some-url`. By default, the result is saved under current directory in a path mapped to the path of the url. To save the output to a particular path, use the `--filepath` option, and to name the output file, use the `--filename` option.

