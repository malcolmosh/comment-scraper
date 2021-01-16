import requests, json
headers = \
{
    "Accept": "*/*",\
    "Accept-Language": "en-US,en;q=0.5",\
    "Accept-Encoding":"gzip, deflate, br",\
    "Content-Type": "application/json",\
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:81.0) Gecko/20100101 Firefox/81.0"
}

data = json.loads('{"query":"query GetComments($url: String!) { asset(url: $url) { title url comments { nodes { body user { username } } } }}","variables":{"url":"http://localhost:3000/"},"operationName":"GetComments"}')

data['variables']['url'] = 'https://theintercept.com/2021/01/14/dustin-higgs-federal-executions-death-penalty/'
response = requests.post('https://talk.theintercept.com/api/v1/graph/ql', headers = headers, data = data)
print('')