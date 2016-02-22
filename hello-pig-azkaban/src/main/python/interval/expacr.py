# -*- coding: utf-8 -*-
import sys, math, random, json, numpy, copy
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import average_precision_score
import matplotlib.pyplot as plt
from sklearn.feature_extraction import DictVectorizer
from sklearn.cross_validation import cross_val_score
from sklearn.cross_validation import cross_val_predict
from sklearn import linear_model
from sklearn.datasets import load_svmlight_file

from exputil import generateEx2, lpp_coarse, lpp_fine, X_test, X_val
    

feature = []

err = 0.1 #error rate
rp = 1 #number of test iteration
nl = 250 #number of learning cycle
train_size = 150
pool_size = 1000
num_config = 4

label = [[] for n in range(0, nl) ]
label = [[[] for n in range(nl) ] for e in range(num_config)]
for e in range(0, rp):
    print >> sys.stderr, "iteration %d/%d" %(e,rp)
    dspool = generateEx2(pool_size, err)
    dstrain = generateEx2(train_size, err)
    train_ex = [copy.deepcopy(dstrain) for cfg in range(num_config)]
    pool_ex = [copy.deepcopy(dspool) for cfg in range(num_config)]
    for n in range(0, nl):
        pred = []
        #for c in range(0,num_config):
        pred.append(lpp_coarse(train_ex[0], pool_ex[0], 0))
        pred.append(lpp_coarse(train_ex[2], pool_ex[2], 1))
        pred.append(lpp_fine(train_ex[1], pool_ex[1], 0))
        pred.append(lpp_fine(train_ex[3], pool_ex[3], 1))
        for cfg in range(num_config):
            label[cfg][n] += pred[cfg]
    feature += list(X_test)


area = [ [ average_precision_score([math.floor(v%2) for v in feature], label[cfg][n]) for n in range(nl)] 
    for cfg in range(num_config)]
lcolor = ["b","r", "g","y"]
text = ["Active Coarse", "Passive Coarse", "Active FineGrain", "Passive FineGrain"]
print json.dumps(area)
#plt.figure()
#for cfg in range(num_config):
#    plt.plot(range(train_size,train_size+nl), area[cfg], c=color[cfg], label=text[cfg], linewidth=1)
#plt.ylabel("AUC")
#plt.xlabel("Example Counts")
#plt.title("AUC learning curve step=[%d] rp=[%d] noise=[%.2f]"%(1,rp,err))
#plt.legend(loc=4)
#plt.savefig("/Users/yujimo/Dropbox/Shared/TextAnalysis/icdm15/fig/curve-synth.eps")