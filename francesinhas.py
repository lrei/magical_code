from francesinhas.apps.restaurants.models import User, Rating, Restaurant
from django.core.exceptions import ObjectDoesNotExist
from math import *
from operator import itemgetter

####
# Users
####


def sim_distance(user1, user2):
    rests = []
    prefs = {}
    prefs[user1] = Rating.objects.filter(user=user1)
    prefs[user2] = Rating.objects.filter(user=user2)
    for item in prefs[user1]:
        try:
            r = Rating.objects.filter(user=user2).get(restaurant=item.restaurant)
        except ObjectDoesNotExist:
            pass
        else:
            rests.append(r.restaurant)    
    # if they have no ratings in common, return 0
    if len(rests) == 0:
        return 0
    # Add up all the preferences, their squares and the products
    sumSq = 0.0
    for rest in rests:
        r1 = float(Rating.objects.filter(user=user1).get(restaurant=rest).value)/100.0
        r2 = float(Rating.objects.filter(user=user2).get(restaurant=rest).value)/100.0
        #print r1, " - ", r2
        sumSq += sqrt(pow(r1-r2,2))
    return 1/(1+sumSq)

    
# Gets recommendations for a user by using a weighted average
# of every other user's rankings
def get_recommendations(user, similarity=sim_distance):
    totals = {}
    simSums = {}
    prefs = {}
    prefs[user] = Rating.objects.filter(user=user)
    
    for other in User.objects.all():
        if other == user: # don't compare "me" (user) to "myself" (user = other)
            continue
        sim = similarity(user, other)
        if sim <= 0: # ignore scores of zero or lower
            continue
        prefs[other] = Rating.objects.filter(user=other)
        for item in prefs[other]:
            r = Rating.objects.filter(user=other).get(restaurant=item.restaurant)
            try: # only score restaurents "I" (user) haven't score
                t = Rating.objects.filter(user=user).get(restaurant=item.restaurant)
            except ObjectDoesNotExist:
                # Similarity * Score
                totals.setdefault(r.restaurant, 0)
                totals[r.restaurant] += \
                Rating.objects.filter(user=other).get(restaurant=r.restaurant).value * sim
                # Sum of similarities
                simSums.setdefault(r.restaurant, 0)
                simSums[r.restaurant] += sim
    # Create the normalized list
    rankings = [(total/simSums[item], item) for item, total in totals.items()]
    rankings.sort()
    rankings.reverse()
    return rankings
    
    
######
# Restaurants
#####

def rest_sim_distance(rest1, rest2):
    users = []
    prefs = {}
    prefs[rest1] = Rating.objects.filter(restaurant=rest1)
    prefs[rest2] = Rating.objects.filter(restaurant=rest2)
    
    for item in prefs[rest1]:
        try:
            r = Rating.objects.filter(restaurant=rest2).get(user=item.user)
        except ObjectDoesNotExist:
            pass
        else:
            print r.user
            users.append(r.user)
    # if they have no ratings in common, return 0
    if len(users) == 0:
        return 0
    # Add up all the preferences, their squares and the products
    sumSq = r1 = r2 = 0.0
    for user in users:
        r1 = float(Rating.objects.filter(restaurant=rest1).get(user=user).value)/100.0
        r2 = float(Rating.objects.filter(restaurant=rest2).get(user=user).value)/100.0
        #print r1, " - ", r2
        sumSq += sqrt(pow(r1-r2,2))
    return 1/(1+sumSq)
    


def calculate_similar_restaurants(n=5):
	# Create a dictionary of items showing which restaurants are most similar to another.
	result = {}
	distances = {}
	restaurants = Restaurant.objects.all()
	
	for rest in restaurants:
	    # Find the most similar items to this one
	    sim = {}
	    for other in restaurants:
	        if other == rest:
	            continue
	        sim[other] = rest_sim_distance(rest, other)
	        
	    scores = sorted(sim.iteritems(), key=itemgetter(1), reverse=True)
	    result[rest] = scores[0:n]
	return result


def get_recommended_restaurants(user, sims):
    ratings = Rating.objects.filter(user=user)
    rated = [rating.restaurant for rating in ratings]
    scores = {}
    totalSim = {}
    
    # Loop over items similar to this one
    for rest in rated:
        for (rest2, sim) in sims[rest]:
            # Ignore if this user has already rated this item
            # Ignore if sim = 0
            if rest2 in rated or sim == 0.0:
                continue
            # Weighted sum of rating times similarity
            scores.setdefault(rest2, 0)
            rating = Rating.objects.get(user=user, restaurant=rest)
            scores[rest2] += sim * rating.value
            
            # Sum of all the similarities
            totalSim.setdefault(rest2, 0)
            totalSim[rest2] += sim
    # Divide each total score by total weighting to get an average
    rankings = [(score/totalSim[item],item) for item,score in scores.items( )]
    # Return the rankings from highest to lowest
    rankings.sort()
    rankings.reverse()
    return rankings