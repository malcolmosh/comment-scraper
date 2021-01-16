# Comment Scrapper
This tool load user comments from a url. Given a url of an articles Web page, user comments are requested from the hosting server and saved in json file. Only the following websites are supported:

[New York Times](https://www.nytimes.com)

[Washington Post](https://www.washingtonpost.com)

[Seattle Times](https://www.seattletimes.com)

[The Intercept](https://theintercept.com)

[Deseret News](https://www.deseret.com)

[NU](https://www.nu.nl)

All the websites above except for the New York Times manage user comments using the [Coral Platform](https://github.com/coralproject/talk), so the program adapts a basic comments request routine (see the `CoralByPost` class) to each website. It should be quite straight forward to add more websites -- only need to find the API endpoints of the target Coral server, and the unique ID of the target article, which is usually the article url, or some post id store in the target Web page somewhere. 

## Usages
To load comments from a target article url, use the command `python3 CommentScrapper.py --url some-url`. By default, the result is saved under current directory in a path mapped to the path of the url. To save the output to a particular path, use the `--filepath` option, and to name the output file, use the `--filename` option.

