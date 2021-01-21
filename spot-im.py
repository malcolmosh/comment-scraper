from CommentScraper import base_header
import requests, os, random, binascii, json
from requests import HTTPError
import time

rCnt = 0
def random_id():
    id = ''.join([hex(random.randint(0, 15))[-1] for _ in range(32)])
    return '{}-{}-{}-{}-{}'.format(id[:8], id[8:12], id[12:16], id[16:20], id[20:])

def authenticate(postID, spotID, deviceID):
    # get token
    endPoint = "https://api-2-0.spot.im/v1.0.0/authenticate"
    headers = base_header()
    headers["Content-Type"] = "application/json"
    headers["Host"] = "api-2-0.spot.im"
    headers["x-post-id"] = postID
    headers["x-spot-id"] = spotID
    headers["x-spotim-device-uuid"] = deviceID
    res = requests.post(endPoint, headers = headers)
    return res.headers['x-access-token']

def load_comments(token, postID, spotID, deviceID, viewID, maxDepth = 10, maxReply = 2):
    global rCnt
    cookies = {"device_uuid": deviceID, "access_token": token}
    endPoint = "https://api-2-0.spot.im/v1.0.0/conversation/read"
    headers = base_header()
    headers["Content-Type"] = "application/json"
    headers["Host"] = "api-2-0.spot.im"
    headers["x-post-id"] = postID
    headers["x-spot-id"] = spotID
    headers["x-spotim-device-uuid"] = deviceID
    headers["x-spotim-page-view-id"] = viewID
    payload = {"sort_by":"oldest","offset":0,"count":200,"depth":maxDepth}

    
    data = requests.post(endPoint, headers = headers, cookies = cookies, data=json.dumps(payload)).json()
    requestCnt = 1
    hasNxt = data['conversation']['has_next']
    offset = data['conversation']['offset']
    while hasNxt:
        time.sleep(random.random())
        payload['offset'] = offset
        dataNxt = requests.post(endPoint, headers = headers, cookies = cookies, data=json.dumps(payload)).json()
        rCnt += 1
        print('sent {} requests.'.format(rCnt))
        data['conversation']['comments'].extend(dataNxt['conversation']['comments'])
        hasNxt = dataNxt['conversation']['has_next']
        offset = dataNxt['conversation']['offset']

        requestCnt += 1

    cmtCnt = 0
    for cmt in data['conversation']['comments']:
        cmtCnt += 1
        if cmt['replies_count'] > 0 and cmt['depth'] < maxDepth:
            (childRequestCnt, childCmtCnt) = load_replies(cmt, headers, cookies, payload, endPoint, maxDepth, maxReply)
            requestCnt += childRequestCnt
            cmtCnt += childCmtCnt

    print(requestCnt, ' requests made, ', cmtCnt, ' comments received for post ', postID)
    return data

def load_replies(parentNode, headers, cookies, payload, endPoint, maxDepth, maxReply):
    global rCnt
    requestCnt, cmtCnt = 0, 0
    if len(parentNode["id"]) > 0:
        payload["parent_id"] = parentNode["id"]

    hasNxt = parentNode['has_next']
    offset = parentNode['offset']
    while hasNxt and len(parentNode['replies']) < maxReply:
        time.sleep(random.random())
        requestCnt += 1
        payload['offset'] = offset
        dataNxt = requests.post(endPoint, headers = headers, cookies = cookies, data=json.dumps(payload)).json()

        rCnt += 1
        print('sent {} requests.'.format(rCnt))

        parentNode['replies'].extend(dataNxt['conversation']['comments'])
        hasNxt = dataNxt['conversation']['has_next']
        offset = dataNxt['conversation']['offset']

        requestCnt += 1

    for cmt in parentNode['replies']:
        cmtCnt += 1
        if cmt['replies_count'] > 0 and cmt['depth'] < maxDepth:
            (childRequestCnt, childCmtCnt) = load_replies(cmt, headers, cookies, payload, endPoint, maxDepth, maxReply)
            requestCnt += childRequestCnt
            cmtCnt += childCmtCnt

    return (requestCnt, cmtCnt)

def request_routine():
    postID = "urn:uri:base64:8e8baf7b-4b76-5f6c-bebf-c650b8a6d83a"
    spotID = "sp_ANQXRpqH"
    deviceID = random_id()
    viewID = random_id()
    token = authenticate(postID, spotID, deviceID)
    comments = load_comments(token, postID, spotID, deviceID, viewID)
    with open('test.json', 'w') as f:
        json.dump(comments, f)

    # cmtCnt = 0
    # requestCnt = 1
    # API_ENDPOINT = "https://api-2-0.spot.im/v1.0.0/conversation/read"
    # def load_replies(parentNode, parentID):
    #         nonlocal cmtCnt, requestCnt
    #         hasNextPage = parentNode['has_next']
    #         offset = len(parentNode['comments'])
    #         while hasNextPage:
    #             requestCnt += 1
    #             response = requests.post(API_ENDPOINT, headers = headers, data = __build_request_more_payload__(cursor, parentID, assetID))
    #             try:
    #                 response.raise_for_status()
    #                 replies = response.json()
    #             except HTTPError as e:
    #                 error("Failed to get part of comments for article: {}\n{}".format(articleURL, repr(e)))
    #                 break
    #             parentNode['nodes'] += replies['data']['comments']['nodes']
    #             hasNextPage = replies['data']['comments']['hasNextPage']
    #             cursor = replies['data']['comments']['endCursor']

    #         for cmt in parentNode['nodes']:
    #             cnt += 1
    #             if cmt['replyCount'] > 0 and 'replies' not in cmt:
    #                 cmt['replies'] = {
    #                         "nodes": [],
    #                         "hasNextPage": True,
    #                         "startCursor": None,
    #                         "endCursor": cmt['created_at'],
    #                         "__typename": "CommentConnection"
    #                     }
    #             if 'replies' in cmt:
    #                 load_replies(assetID, cmt['replies'], cmt['id'])

def export():
    postID = "urn:uri:base64:28f3b6ea-367e-5f4a-bd42-462ed82ba6dc"
    spotID = "sp_ANQXRpqH"
    deviceID = random_id()# "f6885446-c9a0-4f83-84e6-6620d1701d9b"
    print(deviceID)
    endPoint = "https://open-api.spot.im/v1/spot-conversation-events/text-only"
    headers = base_header()
    #headers["Content-Type"] = "application/json"
    # headers["Host"] = "open-api.spot.im"
    # headers["x-post-id"] = postID
    # headers["x-spot-id"] = spotID
    # headers["x-spotim-device-uuid"] = deviceID
    token = authenticate()
    res = requests.get(endPoint, headers = headers, params={"token": token, "spot_id": spotID, "post_id": postID, "etag": 0})
    return res.headers['x-access-token']



request_routine()