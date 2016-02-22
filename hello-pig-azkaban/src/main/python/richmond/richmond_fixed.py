import os, math, sys
import numpy as np

import cPickle as pickle
# import richmond
# feats, labels, fines = richmond.loadEx()
# pickle.dump((feats, labels, fines), open( "/tmp/ex.pickle", "wb" ) )
fine_ratio = 0.5
for line in sys.stdin:
    print >> sys.stderr, "[INFO]", line
    fine_ratio = float(line.strip())

print >> sys.stderr, 'Loading features and Labels'
feats, labels, fines = pickle.load(open('richmond_data/ex.pickle'))

from sklearn.cross_validation import train_test_split
feats_pool, feats_val, label_pool, label_val = \
    train_test_split(feats, fines, test_size=0.8)
from hybrid_learner import *
print >> sys.stderr, 'Loading done'
l = 0.2
e = 0.1
cost_r = 5
budget_t = 25

step_size = 1.0 * budget_t/ (cost_r * fine_ratio + (1 - fine_ratio))

exp = [[], [], feats_val, feats_pool, [], [], label_val, label_pool]
deltas = []
for i in range(100):
    exp2, obj = hybrid_learner(exp, active=True, initial_size=400, fine_ratio=fine_ratio, step_size=step_size)
    exp = exp2
    print >> sys.stderr, obj
    trace(obj)