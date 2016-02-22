import sys, math, random, json, numpy, copy
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import average_precision_score
import matplotlib.pyplot as plt
X_test = np.arange(0.0, 18.0, 0.01)[:, np.newaxis]
X_val = [math.floor(v)%2 for v in X_test]


def generateEx2(num, p):
    n = 2
    k = 3
    eg = [[], [], []]
    for i in range(0,num):
        v = random.uniform(0,k**n*2)
        c = math.floor(v)
        if random.uniform(0,1) < p:
            while True:
                s = random.uniform(0,k**n*2)
                if math.floor(s)%2==c%2:
                    continue
                c = math.floor(s)
                break
        if c%2 == 0 :
            c = 0
            eg[2].append(0)
        else:
            eg[2].append(1)
        eg[1].append(c)
        eg[0].append([v])
    return eg


# coarse learner
def lpp_coarse(utrain, upool, explore):
    clf_1 = GradientBoostingRegressor(n_estimators=300, learning_rate=0.9, max_depth=1, random_state=0, subsample=0.8)
    clf_1.fit(utrain[0], utrain[2])

    # predict pool examples confidence
    c_k = [ abs(v-0.5) for v in clf_1.predict(upool[0])]
    if explore == 0:
        pc = np.argsort(c_k)[:1]
    else:
        pc = [random.randint(0, len(c_k)-1)]
    utrain[0] += list(np.array(upool[0])[pc])
    utrain[1] += list(np.array(upool[1])[pc])
    utrain[2] += list(np.array(upool[2])[pc])
    upool[0] = [upool[0][i] for i in range(len(upool[0])) if i not in pc]
    upool[1] = [upool[1][i] for i in range(len(upool[1])) if i not in pc]
    upool[2] = [upool[2][i] for i in range(len(upool[2])) if i not in pc]
    y_1 = [ v for v in clf_1.predict(X_test)]
    return y_1
    

# fine learner
def lpp_fine(utrain, upool, explore):
    # utrain=copy.deepcopy(utrain)
    # upool=copy.deepcopy(upool)
    
    crf_x = numpy.zeros(len(X_test))
    crf_xp = numpy.zeros(len(upool[0]))
    for i in range(1,18,2):
        y = []
        for (j, v) in enumerate(utrain[1]):
            if v!=i and utrain[2][j] == 0:
                y.append(0)
            else:
                if v==i:
                    y.append(1)
                else:
                    y.append(0)

        clf_2 = GradientBoostingRegressor(n_estimators=30, learning_rate=0.9, max_depth=1, random_state=0, subsample=0.8)
        clf_2.fit(utrain[0],y)   
        yy = clf_2.predict(X_test)
        yyp = clf_2.predict(upool[0])
        for i in range(0,len(yy)):
            crf_x[i] = max(crf_x[i] , yy[i])
        for i in range(0,len(yyp)):
            crf_xp[i] = max(crf_xp[i] , yyp[i])
    
    c_k = [ abs(v-0.5) for v in crf_xp]
    if explore == 0:
        pc = np.argsort(c_k)[:1]
    else:
        pc = [random.randint(0, len(c_k)-1)]
    utrain[0] += list(np.array(upool[0])[pc])
    utrain[1] += list(np.array(upool[1])[pc])
    utrain[2] += list(np.array(upool[2])[pc])
    upool[0] = [upool[0][i] for i in range(len(upool[0])) if i not in pc]
    upool[1] = [upool[1][i] for i in range(len(upool[1])) if i not in pc]
    upool[2] = [upool[2][i] for i in range(len(upool[2])) if i not in pc]    
            
    return list(crf_x)