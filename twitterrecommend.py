import twitter

# requires python-twitter (recent version with new twitter authentication)

# consumer key
ckey = ''
# consumer secret
csec = ''
# access token
atkn = ''
# access token secret
atknsec = ''

api = twitter.Api(consumer_key=ckey,
                        consumer_secret=csec,
                        access_token_key=atkn,
                        access_token_secret=atknsec)

#print api.VerifyCredentials()

# a list of people "I" (the authenticated user) follow
myfriends = api.GetFriendIDs()['ids']

# Create a dictionary that contains a list of users that each person "I"
# follow (my friends), follows.
theirfriends = dict()
# Create a similarity score for each individual "I" follow
sim = dict()
# Create a set of new users (users "I" don't follow)
newusers = set()

for uid in myfriends:
    # print uid
    theirfriends[uid] = api.GetFriendIDs(user=uid)['ids']
    # similarity score = the number of users they follow that "I" also follow
    sim[uid] = len([i for i in theirfriends[uid] if i in myfriends])
    newusers |= set([i for i in theirfriends[uid] if i not in myfriends])

# Calculate the maximum similarity value to normalize the similarity score
max = 0
for v in sim.values():
    if v > max:
        max = v

# calculate the score for each new user
scores = dict()
for nuser in newusers:
    score = 0
    for myfriend, hisfriends in theirfriends.iteritems():
        if nuser in hisfriends:
            score = score + float(sim[myfriend])/max
            
    scores[nuser] = score

# print the top 10 results
slist = sorted(scores, key=scores.__getitem__, reverse=True)[:10]

for p in slist:
    print p
    user = api.GetUser(p)
    print user.name
    print scores[p]
    print " "
    