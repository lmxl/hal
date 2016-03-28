import sys

import math, random, json, numpy, copy
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import *
from sklearn.datasets import load_svmlight_file
from sklearn import metrics
from sklearn.utils import resample
from sklearn.cross_validation import train_test_split
from scipy.sparse import coo_matrix, vstack
from sklearn.metrics import average_precision_score
from toposort import toposort_flatten
val_t = 0.5
def caculate_tpr(parent_vector, children_vectors):
    length = len(parent_vector)
    output_vector = []
    for i in range(0, length):
        ph_c = 0
        ph_s = 0
        for j in range(len(children_vectors)):
            if children_vectors[j][i] > val_t:
                ph_c += 1
                ph_s += children_vectors[j][i]
        output_vector.append((parent_vector[i] + ph_s)/(ph_c + 1))
    return np.array(output_vector)
def lpp_tpr(dataset, explore, fine, tpr = True):
    [train_x, train_z, pool_x, pool_z ] = dataset
    if fine == 0:
        key = target
        cat = set(z_y[key])
        train_y = np.array( [1 if x in cat else 0 for x in train_z])
        model = LogisticRegression(solver='liblinear', penalty='l2', C=10)
        model.fit(train_x,train_y)
        prob_y = model.predict_proba(test_x)[:,1]
        pool_conf = [ abs(v-0.5) for v in model.predict_proba(pool_x)[:,1] ]
    else:
        prob_y = {}
        pool_y = {}
        for key in cat_order:
            if key not in z_y:
                continue
            # leaf node is not a key in topo_data, we return an empty children set instead
            sub_cats = topo_data.get(key, set())
            cat = set(z_y[key])
            train_y = np.array( [1 if x in cat else 0 for x in train_z])
            model = LogisticRegression(solver='liblinear', penalty='l2', C=10)
            if sum(train_y)==0 or sum(train_y)==len(train_y):
                continue
            if sum(train_y)<10:
                continue
            model.fit(train_x,train_y)
            parent_prob_y=model.predict_proba(test_x)[:,1]
            parent_pool_y=model.predict_proba(pool_x)[:,1]

            pool_y_children = []
            prob_y_children = []
            for sub_cat in sub_cats:
                if sub_cat not in pool_y:
                    continue
                pool_y_children.append(pool_y[sub_cat])
                prob_y_children.append(prob_y[sub_cat])
            pool_y[key] = caculate_tpr(parent_pool_y, pool_y_children)
            prob_y[key] = caculate_tpr(parent_prob_y, prob_y_children)
        pool_conf = [abs(v-0.5) for v in pool_y[target]]

    if explore == 0:
        pc = np.argsort(pool_conf)[:step_size]
    else:
        pc = random.sample(range(len(pool_conf)), step_size)

    train_x = vstack([train_x, pool_x[pc]])
    train_z = np.array(list(train_z)+ list(pool_z[pc]))
    pc=sorted(pc)
    for i in range(len(pc)-1,-1,-1):
        pool_x = vstack([pool_x[:pc[i]], pool_x[pc[i]+1:]])
    pool_z = np.array([pool_z[i] for i in range(len(pool_z)) if i not in pc])
    print >> sys.stderr, len(prob_y)
    print >> sys.stderr, prob_y.keys()
    area = average_precision_score(test_y, prob_y[target])
    print >> sys.stderr, len([v for v in prob_y[target] if v<0.5]),len([v for v in prob_y[target] if v>0.5])
    return [area,  [train_x, train_z, pool_x, pool_z]]

def lpp(dataset, explore, fine, tpr = False):
    [train_x, train_z, pool_x, pool_z ] = dataset
    if fine == 0:
        key = target
        cat = set(z_y[key])
        train_y = np.array([1 if x in cat else 0 for x in train_z])
        model = LogisticRegression(solver='liblinear', penalty='l2', C=10)           
        model.fit(train_x, train_y)
        prob_y = model.predict_proba(test_x)[:,1]
        pool_conf = [ abs(v-0.5) for v in model.predict_proba(pool_x)[:,1] ]
    else:
        prob_y = numpy.zeros(len(test_z))
        pool_y = numpy.zeros(len(pool_z))
        for key in z_y:
            if not key.startswith(main):
                continue
            cat = set(z_y[key])
            train_y = np.array( [1 if x in cat else 0 for x in train_z])
            model = LogisticRegression(solver='liblinear', penalty='l2', C=10)           
            if sum(train_y)==0 or sum(train_y)==len(train_y):
                continue
            if sum(train_y)<10:
                continue    
            model.fit(train_x,train_y)
            m_prob_y=model.predict_proba(test_x)[:,1]
            m_pool_y=model.predict_proba(pool_x)[:,1]
            
            for i in range(0,len(test_z)):
                prob_y[i] = max(prob_y[i], m_prob_y[i])
            for i in range(0,len(pool_z)):
                pool_y[i] = max(pool_y[i], m_pool_y[i])
        pool_conf = [ abs(v-0.5) for v in pool_y ]
    
    if explore == 0:
        pc = np.argsort(pool_conf)[:step_size]
    else:
        pc = random.sample(range(len(pool_conf)), step_size)
    
    train_x = vstack([train_x, pool_x[pc]])
    train_z = np.array(list(train_z)+ list(pool_z[pc]))
    pc=sorted(pc)
    for i in range(len(pc)-1,-1,-1):
        pool_x = vstack([pool_x[:pc[i]], pool_x[pc[i]+1:]])
    pool_z = np.array([pool_z[i] for i in range(len(pool_z)) if i not in pc])
    area = average_precision_score(test_y, prob_y)
    print >> sys.stderr, len([v for v in prob_y if v<0.5]),len([v for v in prob_y if v>0.5])
    return [area,  [train_x, train_z, pool_x, pool_z]]

for line in sys.stdin:
    print >> sys.stderr, "[INFO]", line
rcv1_home = 'rcv1'
train_size = 2000
main='E'
step_size = 200
rp=1
nl = 91 #number of learning cycle
num_config = 4
#configs = [[10,0],[1,0],[0,1],[1,1]]
#text = ["Active Coarse", "Passive Coarse", "Active FineGrain", "Passive FineGrain"]
configs = [[0,1],[1,1],[0,1],[1,1]]
text = ["Active HAL", "Passive HAL", "Active TPR", "Passive TPR"]
num_config = len(text)
print >> sys.stderr, "Loading features and labels..."
train = []
train_id = []


all_x, all_z = load_svmlight_file(rcv1_home +'/train.dat')
test_x, test_z = load_svmlight_file(rcv1_home +'/test.dat')
z_y = json.load(open(rcv1_home +'/full_topics.json'))
target= main + 'CAT'

key = target
cat = set(z_y[key])
test_y = np.array( [1 if x in cat else 0 for x in test_z])

topo_data = {}
hfp = open(rcv1_home + '/topics.hier.dat')
hfp.readline()
for line in hfp.readlines():
    pnode, cnode, desc = line.split(' ', 2)
    if not pnode.startswith(main):
        continue
    if pnode not in topo_data:
        topo_data[pnode] = set()
    dest = topo_data[pnode]
    dest.add(cnode)
cat_order = toposort_flatten(topo_data)

label = [[] for n in range(0, nl) ]
label = [[[] for n in range(nl) ] for e in range(num_config)]
for e in range(0, rp):
    print >> sys.stderr, "iteration %d/%d" %(e,rp)
    train_x, pool_x, train_z, pool_z = train_test_split(all_x, all_z, train_size=train_size)
    dataset = [ [copy.deepcopy(train_x),copy.deepcopy(train_z),copy.deepcopy(pool_x),copy.deepcopy(pool_z)] for cfg in range(num_config)]
    print >> sys.stderr, "train_ex=%d, train_z=%d, pool_x=%d, pool_z=%d" %(train_x.shape[0], train_z.shape[0], pool_x.shape[0], pool_z.shape[0])
    for n in range(0, nl):
        for cfg in range(num_config):
            print >> sys.stderr, "step %d/%d" %(n,cfg)
            #print dataset[0][1].shape[0]
            if cfg>1:
                [pred, dataset[cfg]] = lpp_tpr(dataset[cfg], configs[cfg][0], configs[cfg][1])
            else:
                [pred, dataset[cfg]] = lpp(dataset[cfg], configs[cfg][0], configs[cfg][1])
            label[cfg][n].append(pred)


area = [ [ sum(label[cfg][n])/rp for n in range(nl)] for cfg in range(num_config)]
print json.dumps(area)
#color = ["b","r", "g","y"]
#plt.figure()
#for cfg in range(num_config):
#    plt.plot(range(train_size,train_size+nl*step_size,step_size), area[cfg], c=color[cfg], label=text[cfg], linewidth=1)
#plt.ylabel("AUC")
#plt.xlabel("Example Counts")
#plt.title("AUC learning curve rp=[%d] step=[%d]"%(rp, step_size))
#plt.legend(loc=4)
#plt.savefig("/home/ymo/Dropbox/projects/rcv1/curve-rcv1-tpf.eps")
#json.dump(area, open('/home/ymo/Dropbox/projects/rcv1/curve-rcv1-tpf.json','w'))
