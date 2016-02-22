import os, math, sys
import numpy as np

import cPickle as pickle
# import richmond
# feats, labels, fines = richmond.loadEx()
# pickle.dump((feats, labels, fines), open( "/tmp/ex.pickle", "wb" ) )

print >> sys.stderr, 'Loading features and Labels'
feats, labels, fines = pickle.load(open('richmond_data/ex.pickle'))

from sklearn.cross_validation import train_test_split
feats_pool, feats_val, label_pool, label_val = \
    train_test_split(feats, fines, test_size=0.8)
from hybrid_learner import *
print >> sys.stderr, 'Loading done'
l = 0.2
e = 0.1
ratio_p = 0.5
cost_r = 5
budget_t = 25
target_prev = 0
exp = [[], [], feats_val, feats_pool, [], [], label_val, label_pool]
deltas = []
for i in range(100):
    if random.random() > ratio_p:
        heads = True
    else:
        heads = False
    if heads:
        exp2, obj = hybrid_learner(exp, active=True, initial_size=400, fine_ratio=0.0, step_size=budget_t)
    else:
        exp2, obj = hybrid_learner(exp, active=True, initial_size=400, fine_ratio=1.0, step_size=budget_t/cost_r)

    target = obj['pr']
    if i == 0:
        target_prev = target

    obj['ratio_p'] = ratio_p
    obj['heads'] = heads

    target_delta = (target - target_prev) * (2.0 * int(heads) - 1.0)
    deltas.append(abs(target_delta))
    normalized_target_delta = target_delta/ (np.median(deltas) + 0.0000001)
    # maximum cap to step size
    if abs(normalized_target_delta) > 1.0:
        normalized_target_delta /= abs(normalized_target_delta)

    print >> sys.stderr, 'iteration %d [ratio=%.4f coarse=%s pr=%.4f delta=%.4f ndelta=%.4f' % (i, ratio_p, heads, target, target - target_prev, normalized_target_delta)
    ratio_p += normalized_target_delta * l
    ratio_p = min(ratio_p, 1 - e)
    ratio_p = max(ratio_p, e)
    obj['ratio_p_next'] = ratio_p
    target_prev = target
    exp = exp2
    trace(obj)