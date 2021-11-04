import json
id2comment = {}
children = {0:[]}
f = open('nyt.json', encoding='utf-8')
comments = json.load(f)['results']['comments']
cnt = 0
def build_dict(x):
    global cnt
    cnt += 1
    id2comment[x['commentID']] = x
    if x['parentID']:
        children.setdefault(x['parentID'], []).append(x['commentID'])
    else:
        children[0].append(x['commentID'])
    for y in x['replies']:
        build_dict(y)

for x in comments:
    build_dict(x)

cnt = 0
def print_children(x, depth):
    global cnt
    cnt += 1
    print('\t' * depth, id2comment[x]['userDisplayName'], '-', id2comment[x]['commentID'])
    for y in children.get(x, []):
        print_children(y, depth + 1)

for x in children[0]:
    print_children(x, 0)

def update_children(x):
    x['replies'] = [id2comment[y] for y in children.get(x['commentID'], [])]
    x['replyCount'] = len(x['replies'])
    cnt = 1
    for y in x['replies']:
        cnt += update_children(y)
    x.pop('depth')
    return cnt

cnt = 0
for x in comments:
    cnt += update_children(x)

f.close()

