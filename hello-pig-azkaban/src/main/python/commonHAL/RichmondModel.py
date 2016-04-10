import sys
import os
import cPickle as pickle
import pycrfsuite
import math
import random
import json
import scipy.sparse
import argparse
import numpy as np
import matplotlib.pyplot as plt
import UncertaintySamplingController
from sklearn.cross_validation import train_test_split
from numpy import array
from random import sample
from BaseModel import BaseModel
from itertools import chain


class CRFModelHelper():
    workbase = '/tmp/crfmodel/%d' %random.randint(0,100000000)
    os.makedirs(workbase)
    @staticmethod
    def sequence_uncertainty(tagger, xseq):
        use_marginal = True
        lseq = tagger.tag(xseq)
        if use_marginal:
            mseq = [ tagger.marginal(lseq[i], i) for i in range(len(lseq))]
            useq = [ min(p , 1.0-p) for p in mseq]
            return max(useq)
        else:
            p = tagger.probability(lseq)
            return min(p, 1.0-p)
    @staticmethod
    def getTrainer():
        crfpar={
            'c1': 1.0,  # coefficient for L1 penalty
            'c2': 1e-3,  # coefficient for L2 penalty
            'max_iterations': 40,  # stop earlier
            # include transitions that are possible, but not observed
            'feature.possible_transitions': True
        }
        trainer = pycrfsuite.Trainer(verbose=False)
        trainer.set_params(crfpar)
        return trainer
    @staticmethod
    def coarse_uncertainty(feats, tag):
        tagger = pycrfsuite.Tagger()
        tagger.open('%s/%s.crf' % (CRFModelHelper.workbase, tag))
        y_unk = [CRFModelHelper.sequence_uncertainty(tagger, xseq) for xseq in feats]
        return y_unk
    @staticmethod
    def traincrf((feats, labels, tag)):
        crf=CRFModelHelper.getTrainer()
        for xseq, yseq in zip(feats, labels):
            crf.append(xseq, yseq)
        crf.train('%s/%s.crf' % (CRFModelHelper.workbase, tag))
        return True
    @staticmethod
    def predictcrf(feats, tag):
        tagger = pycrfsuite.Tagger()
        tagger.open('%s/%s.crf' % (CRFModelHelper.workbase, tag))
        y_pred = []
        y_score = []
        for xseq in feats:
            lseq = tagger.tag(xseq)
            mags = []
            for i in range(len(lseq)):
                mag = tagger.marginal(lseq[i], i)
                if lseq[i] == 'token':
                    mag = 1.0 - mag
                mags.append(mag)
            y_pred.append(lseq)
            y_score.append(mags)
        return y_pred, y_score
    @staticmethod
    def predict_help():
        return
    @staticmethod
    def predictcrf2(feats, tag):
        k = 12
        taggers = [ pycrfsuite.Tagger() for i in range(k)]
        [ tagger.open('model/%s.crf' % tag) for tagger in taggers ]
        return


class RichmondModel(BaseModel):
    def __init__(self, train_size_fine, train_size_coarse, pool_size=None, test_size=None, pond_size=1000):
        print >> sys.stderr, 'Loading features and Labels'
        feats, labels, fines = pickle.load(open('richmond_data/ex.pickle'))
        train_x, pool_x, train_z, pool_z, train_y, pool_y = \
            train_test_split(feats, fines, labels, train_size=train_size_fine + train_size_coarse)
        train_fine_x, train_coarse_x, train_fine_z, train_coarse_z, train_fine_y, train_coarse_y = \
            train_test_split(train_x, train_z, train_y, train_size=train_size_fine)
        pond_x, pool_x, pond_z, pool_z, pond_y, pool_y= train_test_split(pool_x, pool_z, pool_y, train_size=pond_size)
        test_x, pool_x, test_z, pool_z, test_y, pool_y= train_test_split(pool_x, pool_z, pool_y, train_size=test_size)
        self.training_examples_fine = [train_fine_x, train_fine_z, train_fine_y]
        self.training_examples_coarse = [train_coarse_x, train_coarse_z, train_coarse_y]
        self.pool_examples = [pool_x, pool_z, pool_y]
        self.pond_examples = [pond_x, None, None]
        self.test_examples = [test_x, test_z, test_y]
        self.fine_crf_models = None
        self.coarse_crf_model = None
        print >> sys.stderr, 'Loading done fine=%d coarse=%d pool=%d test=%d pond=%d total=%d' % \
                             (len(self.training_examples_fine[1]),
                              len(self.training_examples_coarse[1]),
                              len(self.pool_examples[1]),
                              len(self.test_examples[1]),
                              len(self.pond_examples[0]),
                              len(labels))
    @staticmethod
    def masklabel(labels, mask = None):
        new_labels = []
        for label in labels:
            if mask is None:
                new_labels.append(['orgname' if v != 'token' else v for v in label])
            else:
                new_labels.append([ mask if v == mask else 'token' for v in label])
        return new_labels

    def fit(self):
        self.fine_crf_models = []
        fine_tags = list(set(chain(*self.training_examples_fine[1])))
        self.coarse_crf_model = 'coarse'
        CRFModelHelper.traincrf((self.training_examples_fine[0] + self.training_examples_coarse[0],
                  self.training_examples_fine[2] + self.training_examples_coarse[2], self.coarse_crf_model))
        for fine_tag in fine_tags:
            fine_crf_model = 'fine_' + fine_tag
            CRFModelHelper.traincrf((self.training_examples_fine[0],
                                     self.masklabel(self.training_examples_fine[1], mask=fine_tag), fine_crf_model))
            self.fine_crf_models.append(fine_crf_model)

    def predict_scores(self, examples):
        fine_scores_list = []
        for crf_model_key in self.fine_crf_models:
            fine_scores = CRFModelHelper.predictcrf(examples, crf_model_key)
            fine_scores_list.append(fine_scores)
        coarse_scores = CRFModelHelper.predictcrf(examples, self.coarse_crf_model)
        return coarse_scores, fine_scores_list

    def get_pool_size(self):
        return len(self.pool_examples[2])

    def predict_pool_scores(self):
        return self.predict_scores(self.pool_examples)

    def predict_test_scores(self):
        return self.predict_scores(self.test_examples)

    def get_test_labels(self):
        return self.test_examples[2]

    def predict_pond_scores(self):
        return self.predict_scores(self.pond_examples)


    @staticmethod
    def unittest():
        print 'Start testing [ %s ]' % RichmondModel
        pool_size = 900
        test_size = 700
        train_fine_size = 500
        train_coarse_size = 600
        model = RichmondModel(train_fine_size, train_coarse_size, pool_size, test_size, pond_size=1000)
        print 'Fine Size [ %d ] Coarse Size [ %d ]' % (len(model.training_examples_fine[0]),
                                                       len(model.training_examples_coarse[0]))
        model.fit()
        controller = UncertaintySamplingController.UncertaintySamplingController(model)
        print controller.current_metric()
        print 'EOF testing [ %s ]' % RichmondModel

    def coarse_learner(exp, step_size=50, initial_size=200, active = False):
        feats_train, feats_val, feats_pool, label_train, label_val, label_pool = exp
        if len(feats_train) < initial_size:
            feats_train, feats_pool, label_train, label_pool = \
                train_test_split(feats_pool, label_pool, train_size=initial_size, random_state=42)
        if active:
            tag = 'coarse_active_%d' % len(label_train)
        else:
            tag = 'coarse_passive_%d' % len(label_train)
        print '= Experiment on [%s]' % tag + ' <-',len(feats_train), len(feats_pool),len(feats_val)
        traincrf((feats_train, masklabel(label_train), tag))
        pred_val, score_val = predictcrf(feats_val, tag)
        pr, roc = calculate_auc(masklabel(label_val), score_val)
        obj = {'coarse':True, 'active': active, 'pr': pr, 'roc': roc, 'size': len(feats_train)}
        trace(obj)
        #open('report/%s_report.txt' % tag,'w').write(tag + '\r\n' + bio_classification_report(masklabel(label_val), score_val))
        if active:
            unk = array(coarse_uncertainty(feats_pool, tag))
            indices_next = unk.argsort()[-step_size:][::-1]
        else:
            indices_next = sample(range(len(label_pool)),step_size)
        feats_next, feats_rest, labels_next, labels_rest = partition_set(feats_pool, label_pool, indices_next)
        feats_train.extend(feats_next)
        label_train.extend(labels_next)
        feats_pool=feats_rest
        label_pool=labels_rest
        #print '->',len(feats_train), len(feats_pool),len(label_train), len(label_pool)
        return [feats_train, feats_val, feats_pool, label_train, label_val, label_pool]

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t')
    args = parser.parse_args()
    if args.t == 'unittest':
        RichmondModel.unittest()
