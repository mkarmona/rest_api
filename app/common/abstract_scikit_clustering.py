from __future__ import print_function

import logging
from optparse import OptionParser
import sys
from time import time

import requests, json
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer

from text_preprocessing_spacy import TextPreProcessor


# Display progress logs on stdout
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

# parse commandline arguments
op = OptionParser()
op.add_option("--clusters",
              dest="n_clusters", type="int", default=5,
              help="Number of clusters.")
op.add_option("--lsa",
              dest="n_components", type="int",
              help="Preprocess documents with latent semantic analysis.")
op.add_option("--no-minibatch",
              action="store_false", dest="minibatch", default=True,
              help="Use ordinary k-means algorithm (in batch mode).")
op.add_option("--no-idf",
              action="store_false", dest="use_idf", default=True,
              help="Disable Inverse Document Frequency feature weighting.")
op.add_option("--use-hashing",
              action="store_true", default=False,
              help="Use a hashing feature vectorizer")
#
# In order to perform machine learning on text documents, we first need to turn the text content into numerical feature vectors.
# Bags of words : The most intuitive way to do so is the bags of words representation:
# 1) assign a fixed integer id to each word occurring in any document of the training set (for instance by building a dictionary from words to integer indices).
# 2) for each document #i, count the number of occurrences of each word w and store it in X[i, j] as the value of feature #j where j is the index of word w in the dictionary
# The bags of words representation implies that n_features is the number of distinct words in the corpus: this number is typically larger that 100,000.
op.add_option("--n-features", type=int, default=100000,
              help="Maximum number of features (dimensions)"
                   " to extract from text.")
op.add_option("--verbose",
              action="store_true", dest="verbose", default=False,
              help="Print progress reports inside k-means algorithm.")

print(__doc__)
op.print_help()

(opts, args) = op.parse_args()
if len(args) > 0:
    op.error("this script takes no arguments.")
    sys.exit(1)


abstract_list = list()
        

for x in range(1, 10):
    europePMC_url = "http://www.ebi.ac.uk/europepmc/webservices/rest/search?query=diabetes&format=json&resulttype=core&pageSize=1000&page=%s"%x
    print(europePMC_url)
    r = requests.get(europePMC_url)
    data = json.loads(r.content)
    for result in data['resultList']['result']:
    
        abstract = result.get('abstractText',None)
    
        if abstract is not None:
            abstract_list.append(abstract)
      
print("%d abstracts" % len(abstract_list))

print()


print("Extracting features from the training dataset using a sparse vectorizer")
t0 = time()

if opts.use_hashing:
    if opts.use_idf:
        # Perform an IDF normalization on the output of HashingVectorizer
        hasher = HashingVectorizer(n_features=opts.n_features,
                                   stop_words='english', non_negative=True,
                                   norm=None, binary=False)
        vectorizer = make_pipeline(hasher, TfidfTransformer())
    else:
        vectorizer = HashingVectorizer(n_features=opts.n_features,
                                       stop_words='english',
                                       non_negative=False, norm='l2',
                                       binary=False)
else:
    text_pre_processor = TextPreProcessor()
    vectorizer = TfidfVectorizer(max_df=0.5, max_features=opts.n_features,
                                 min_df=2,tokenizer=text_pre_processor.tokenize_text, stop_words='english',
                                 use_idf=opts.use_idf,strip_accents =  'ascii')
X = vectorizer.fit_transform(abstract_list)

print("done in %fs" % (time() - t0))
print("n_samples: %d, n_features: %d" % X.shape)
print()

if opts.n_components:
    print("Performing dimensionality reduction using LSA")
    t0 = time()
    # Vectorizer results are normalized, which makes KMeans behave as
    # spherical k-means for better results. Since LSA/SVD results are
    # not normalized, we have to redo the normalization.
    svd = TruncatedSVD(opts.n_components)
    normalizer = Normalizer(copy=False)
    lsa = make_pipeline(svd, normalizer)

    X = lsa.fit_transform(X)

    print("done in %fs" % (time() - t0))

    explained_variance = svd.explained_variance_ratio_.sum()
    print("Explained variance of the SVD step: {}%".format(
        int(explained_variance * 100)))

    print()


###############################################################################
# Do the actual clustering

if opts.minibatch:
    km = MiniBatchKMeans(n_clusters=opts.n_clusters, init='k-means++', n_init=1,
                         init_size=1000, batch_size=1000, verbose=opts.verbose)
else:
    km = KMeans(n_clusters=opts.n_clusters, init='k-means++', max_iter=100, n_init=1,
                verbose=opts.verbose)

print("Clustering sparse data with %s" % km)
t0 = time()
km.fit(X)
print("done in %0.3fs" % (time() - t0))
print()



if not opts.use_hashing:
    print("Top terms per cluster:")

    if opts.n_components:
        original_space_centroids = svd.inverse_transform(km.cluster_centers_)
        order_centroids = original_space_centroids.argsort()[:, ::-1]
    else:
        order_centroids = km.cluster_centers_.argsort()[:, ::-1]

    terms = vectorizer.get_feature_names()
    for i in range(opts.n_clusters):
        print("Cluster %d:" % i, end='')
        print("Label %d:" %km.labels_[i],end='')
        for ind in order_centroids[i, :10]:
            print(' %s' % terms[ind], end='')
        print()