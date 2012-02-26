import opml
import feedparser
import re
from numpy import *
from py_nnma import *

# Adapted from Programming Collective Intelligence
# requires Numpy & py_nnma

defflist=['http://today.reuters.com/rss/topNews',
          'http://today.reuters.com/rss/domesticNews',
          'http://today.reuters.com/rss/worldNews',
          'http://hosted.ap.org/lineups/TOPHEADS-rss_2.0.xml',
          'http://hosted.ap.org/lineups/USHEADS-rss_2.0.xml',
          'http://hosted.ap.org/lineups/WORLDHEADS-rss_2.0.xml',
          'http://hosted.ap.org/lineups/POLITICSHEADS-rss_2.0.xml',
          'http://www.nytimes.com/services/xml/rss/nyt/HomePage.xml',
          'http://www.nytimes.com/services/xml/rss/nyt/International.xml',
          'http://news.google.com/?output=rss',
          'http://feeds.salon.com/salon/news',
          'http://www.foxnews.com/xmlfeed/rss/0,4313,0,00.rss',
          'http://www.foxnews.com/xmlfeed/rss/0,4313,80,00.rss',
          'http://www.foxnews.com/xmlfeed/rss/0,4313,81,00.rss',
          'http://rss.cnn.com/rss/edition.rss',
          'http://rss.cnn.com/rss/edition_world.rss',
          'http://rss.cnn.com/rss/edition_us.rss']


def strip_HTML(h):
    p = ''
    s = 0
    for c in h:
        if c == '<':
            s=1
        elif c == '>':
            s = 0
            p += ' '
        elif s == 0:
            p += c
    return p


def separate_words(text):
    splitter = re.compile('\\W*')
    return [s.lower() for s in splitter.split(text) if len(s) > 3]


def get_article_words(opmlfile = None):
	allwords = {}
	articlewords = []
	articletitles = []
	articlelinks = {}
	ec = 0
	
	if opmlfile is not None:
		outline = opml.parse(opmlfile)
		# get the list of feeds from the OPML file
		feedlist = []
		for folder in outline:
			for feed in folder:
				feedlist.append(feed.xmlUrl)
	else:
		feedlist = defflist
		
	# Loop over every feed
	for feed in feedlist:
		f = feedparser.parse(feed)
	
		# Loop over every article
		for e in f.entries:
			# Ignore entries without these fields
			if 'title' not in e or 'link' not in e or 'description' not in e:
				continue
			# Ignore identical articles
			if e.title in articletitles:
				continue
	  
			# Extract the words
			txt = e.title.encode('utf8') + \
				strip_HTML(e.description.encode('utf8'))
			words = separate_words(txt)
			articlewords.append({})
			articletitles.append(e.title)
			articlelinks[e.title] = e.link
	  
			# Increase the counts for this word in allwords and articlewords
			for word in words:
				allwords.setdefault(word, 0)
				allwords[word] += 1
				articlewords[ec].setdefault(word, 0)
				articlewords[ec][word] += 1
				
			ec += 1
			
	return allwords, articlewords, articletitles, articlelinks


def makematrix(allw, articlew):
	wordvec = []
  
	# Only take words that are common but not too common
	for w, c in allw.items():
		if c > 3 and c < len(articlew) * 0.6:
			wordvec.append(w) 
  
	# Create the word matrix
	wm = [[(w in f and f[w] or 0) for w in wordvec] for f in articlew]
  
	return wm, wordvec


def showfeatures(w,h,titles,wordvec,narticles=3,out='features.txt'): 
  outfile=file(out,'w')  
  pc,wc=shape(h)
  toppatterns=[[] for i in range(len(titles))]
  patternnames=[]
  
  # Loop over all the features
  for i in range(pc):
    slist=[]
    # Create a list of words and their weights
    for j in range(wc):
      slist.append((h[i,j],wordvec[j]))
    # Reverse sort the word list
    slist.sort()
    slist.reverse()
    
    # Print the first six elements
    n=[s[1] for s in slist[0:6]]
    outfile.write(str(n)+'\n')
    patternnames.append(n)
    
    # Create a list of articles for this feature
    flist=[]
    for j in range(len(titles)):
      # Add the article with its weight
      flist.append((w[j,i],titles[j]))
      toppatterns[j].append((w[j,i],i,titles[j]))
    
    # Reverse sort the list
    flist.sort()
    flist.reverse()
    
    # Show the top 3 articles
    for f in flist[0:narticles]:
      outfile.write(str(f)+'\n')
    outfile.write('\n')

  outfile.close()
  # Return the pattern names for later use
  return toppatterns,patternnames

def showarticles(titles,toppatterns,patternnames,out='articles.txt'):
  outfile=file(out,'w')  
  
  # Loop over all the articles
  for j in range(len(titles)):
    outfile.write(titles[j].encode('utf8')+'\n')
    
    # Get the top features for this article and
    # reverse sort them
    toppatterns[j].sort()
    toppatterns[j].reverse()
    
    # Print the top three patterns
    for i in range(3):
      outfile.write(str(toppatterns[j][i][0])+' '+
                    str(patternnames[toppatterns[j][i][1]])+'\n')
    outfile.write('\n')
    
  outfile.close()
  
  
def cluster(k=10, maxiter=100, opmlfile=None):
    allw, articlew, titles, links = get_article_words(opmlfile)
    data, wordvec = makematrix(allw, articlew)
    datam = array(data) # convert to numpy array format
    stop = 1e-5
    args = dict(k=k, eps=stop, maxcount=maxiter, verbose=False)
    weights, features, res, count, converged = NMF(*[datam], **args)
    toppatterns, patternnames = showfeatures(weights, features, titles, wordvec)
    showarticles(titles, toppatterns, patternnames)

if __name__ == "__main__":
    cluster()
    #cluster(k=100, maxiter=300, opmlfile="mysubscriptions.xml")
