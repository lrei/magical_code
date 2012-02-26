#Adapted from PIC
# This is sample code for learning the basics of the algorithm.
# It's not meant to be part of a production anti-spam system!
# Terrible for a large dataset

import sys
import os
import glob
import re
import math
import sqlite3
from decimal import *

DEFAULT_THRESHOLD = 0.7

def get_words(doc):
    """Splits text into words."""
    splitter = re.compile('\\W*')
    # Split the words by non-alpha characters
    words = [s.lower() for s in splitter.split(doc) 
          if len(s)>2 and len(s)<20]
    # Return the unique set of words only
    return dict([(w,1) for w in words])
  
  
class Classifier:
    def __init__(self, get_features, filename=None): 
        self.fc = {} # Counts of feature/category combinations
        self.cc = {} # Counts of documents in each category
        self.get_features = get_features # feature extraction function

    def setup_db(self, dbfile):
        """Sets up the database."""
        print "db:", dbfile
        # "connect to the file" (or create it)
        self.con = sqlite3.connect(dbfile)
        # create the tables if they don't exist
        self.con.execute(
            'create table if not exists fc(feature,category,count)')
        self.con.execute('create table if not exists cc(category,count)')
        self.con.execute('create table if not exists ct(category,threshold)')
    
    def inc_feature_count(self, f, cat):
        """Increases the count of a feture/category pair"""
        count = self.feature_count(f, cat)
        if count == 0:
            self.con.execute("insert into fc values ('%s','%s',1)" % (f, cat))
        else:
            self.con.execute(
                "update fc set count=%d where feature='%s' and category='%s'" 
                % (count+1, f, cat))
        self.con.commit()

    def feature_count(self, f, cat):
        """Returns the number of times a feature has appeared int a \
        category.
        """
        res = self.con.execute(
        'select count from fc where feature="%s" and category="%s"'
            %(f, cat)).fetchone()
            
        if res == None:
            return 0
        else:
            return float(res[0])

    def inc_category_count(self, cat):
        """Increases the count of a category."""
        count = self.category_count(cat)
        if count == 0:
            self.con.execute("insert into cc values ('%s',1)" % (cat))
        else:
            self.con.execute("update cc set count=%d where category='%s'" 
                % (count+1, cat))
        self.con.commit()

    def category_count(self, cat):
        """Returns the number of items in a category."""
        res = self.con.execute('select count from cc where category="%s"'
                %(cat)).fetchone()
        if res == None:
            return 0
        else:
            return float(res[0])

    def categories(self):
        """Returns a list of categories."""
        cur = self.con.execute('select category from cc');
        return [d[0] for d in cur]

    def total_count(self):
        """Returns the total number of items."""
        res = self.con.execute('select sum(count) from cc').fetchone();
        if res == None:
            return 0
        return res[0]

    def train(self, item, cat):
        """Extracts the features from an item and increases the counts for \
        this classification (category) for every feature.
        Also increaes the total count for the category.
        """
        features = self.get_features(item)
        # Increment the count for every feature with this category
        for f in features:
            self.inc_feature_count(f, cat)
        # Increment the count for this category
        self.inc_category_count(cat)
        
    
    def train_from_dir(self, path, cat):
        """Loads examples of a given category from a directory and uses them \
        to perform the training.
        """
        dirfiles = glob.glob(os.path.join(path, '*'))
        total = len(dirfiles)
        count = 0
        for infile in dirfiles:
            f = open(infile, "r")
            text = f.read()
            self.train(text, cat)
        
    
    def feature_prob(self, f, cat):
        """Returns the probabiity that a feature is in a particular category.
        """
        if self.category_count(cat) == 0:
            return 0
        # The total number of times this feature appeared in this 
        # category divided by the total number of items in this category
        pfc = self.feature_count(f, cat)
        pc  = self.category_count(cat)
        return float(pfc)/pc
        
    def weighted_prob(self, f, cat, prf, weight=1.0, ap=0.5):
        """Returns the weighted probability that a feature is in a \
        particular category. Adds an inital probability value for features \
        with a specified weight.
        """
        basicprob = prf(f, cat) # Calculate current probability
        # Count the number of times this feature has appeared in all cats
        totals = sum([self.feature_count(f, c) for c in self.categories()])
        # Calculate the weighted average
        bp = ((weight*ap)+(totals*basicprob))/(weight+totals)
        return bp
    
class NaiveBayes(Classifier):
    def __init__(self, get_features):
        Classifier.__init__(self, get_features)
        self.thresholds = {}
  
    def doc_prob(self, doc, cat):
        """Returns the probability of the item belonging to category \
        - Pr(Document | Category).
        """
        features = self.get_features(doc)   
        # Multiply the probabilities of all the features together
        p = Decimal(1)
        for f in features:
            p *= Decimal(str(self.weighted_prob(f, cat, self.feature_prob))) 
        return p

    def prob(self, doc, cat):
        """Returns the probability that an document belongs to a category \
        - Pr(Category | Document).
        """
        catprob = self.category_count(cat) / self.total_count() # Pr(Category)
        docprob = self.doc_prob(doc, cat) # Pr(Document | Category)
        return docprob*Decimal(str(catprob)) # Pr(Category | Document)
  
    def set_threshold(self, cat, t):
        """Sets the minimum probability that an item must have to be \
        considered to belong to a particular category."""
        self.con.execute("update ct set threshold=%f where category='%s'" 
                % (t, cat))
    
    def get_threshold(self, cat):
        """Returns the threshold value of a category."""
        t = self.con.execute('select threshold from ct where category="%s"'
                %(cat)).fetchone()
                
        if t is None:
            return 1.0
            
        return self.thresholds[cat]
  
    def classify(self, doc, default=None):
        """Classify a document as belonging to a certain category.
        Returns the category the document belongs to."""
        probs = {}
        
        # Find the category with the highest probability
        max = Decimal(0)
        for cat in self.categories():
            probs[cat] = self.prob(doc, cat)
            if probs[cat] > max: 
                max = probs[cat]
                best = cat

        if max == 0.0:
            return default
            
        # Make sure the probability exceeds threshold*next best
        for cat in probs:
            if cat == best:
                continue
            if probs[cat]*Decimal(str(self.get_threshold(best)))>probs[best]:
                return default
        
        print probs[best]
        return best
 
def print_help():
      print "python ", sys.argv[0], "train [database ][dataset_dir] [category] [default_treshold]"
      print "python ", sys.argv[0], "classify [database] [file]"
      print "python ", sys.argv[0], "threshold [database] [category] [treshold]"
      
def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)
    
    filter = NaiveBayes(get_words)
    filter.setup_db(sys.argv[2])
    
    if sys.argv[1] == "train":
        filter.train_from_dir(sys.argv[3], sys.argv[4])
        filter.set_threshold(sys.argv[4], DEFAULT_THRESHOLD)
    elif sys.argv[1] == "classify":
        f = open(sys.argv[3])
        text = f.read()
        print filter.classify(text, default='unknown')
    elif sys.argv[1] == "threshold":
        t = float(sys.argv[4])
        filter.set_threshold(sys.argv[3], t)
    else:
        print_help()

if __name__ == "__main__":
    main()