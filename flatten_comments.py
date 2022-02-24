from datetime import datetime

#scrape comments
!python3 CommentScraper.py --url https://www.theglobeandmail.com/opinion/article-our-shared-reality-and-the-knowledge-that-undergirds-it-is-being/

#load dataset 
with open("globemail.json", encoding='utf-8') as input:
    globemail = json.load(input)
    

#function to flatten hierarchical comments
comments = []

def flatten(data, parent):
    
    nodes = data['nodes']
    for n in nodes:
        actions = {action['__typename']: action['count'] for action in n['action_summaries']}
        cid = n['id']
        if n['user'] is not None and n['body'] is not None:
            comments.append(
                {
                    "comment_id":cid,
                    "username":n['user']['username'],
                    "user_id":n['user']['id'],
                    "timestamp":datetime.strptime(n['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ'),
                    "text":n['body'], 
                    "parent":parent
             }
                )
            
        if 'replies' in n:
            flatten(n['replies'], parent=cid)
            
    return comments


#flatten all comments
flatten(data=globemail['data']['asset']['comments'], parent=None)
    

#renseignements

#unique users 

def unique_users(data):
    user_ids=[]
    for comment in comments:
        if comment['user_id'] not in user_ids:
            user_ids.append(comment['user_id'])
    print(len(user_ids), "unique users")
    
def number_comments(data):
    print(len(comments), "unique comments")


unique_users(data=comments)
number_comments(data=comments)

