from coarse_learner import *
from numpy import array
from random import sample, random
from itertools import chain
from multiprocessing import Pool
import sys
__author__ = 'ymo'
parallel_processing = False


def trainmulticrf(feats_train_fine, feats_train_coarse, label_train_fine, label_train_coarse, tag):
    fine_tags = list(set(chain(*label_train_fine)))
    traincrf((feats_train_fine + feats_train_coarse,
              masklabel(label_train_fine + label_train_coarse),
              tag + '__coarse'))
    if not parallel_processing:
        for fine_tag in fine_tags:
            traincrf((feats_train_fine, masklabel(label_train_fine, mask=fine_tag), tag+'_' + fine_tag))
    else:
        p = Pool(min(12, len(fine_tags)))
        jobs = [(feats_train_fine,
                 masklabel(label_train_fine, mask=fine_tag), tag+'_' + fine_tag) for fine_tag in fine_tags]
        p.map(traincrf, jobs)
        p.close()
    return fine_tags


def predictcrf_helper(feats, bags):
    pred_fine, score_fine = predictcrf(feats, bags)
    return score_fine


def predictmulticrf(feats_val, fine_tags, tag, alpha=0.5):
    beta = 1.0 - alpha
    pred_coarse, score_coarse = predictcrf(feats_val, tag + '__coarse')
    score_fine_list = [predictcrf_helper(feats_val, tag+'_' + fine_tag) for fine_tag in fine_tags]
    final_score_fine = []
    for i in range(len(score_coarse)):
        craft_score_fine = []
        for j in range(len(score_coarse[i])):
            # if no fine grained labels acquired
            if len(fine_tags) == 0:
                high = score_coarse[i][j]
            else:
                high = max([score_fine_list[k][i][j] for k in range(len(fine_tags))])
            craft_score_fine.append(score_coarse[i][j]*alpha + high*beta)
        final_score_fine.append(craft_score_fine)
    return final_score_fine


def fine_uncertainty(feats, fine_tags, tag, alpha=0.5):
    beta = 1.0 - alpha
    unk_coarse = coarse_uncertainty(feats, tag + '__coarse')
    unk_fine_list = []
    for fine_tag in fine_tags:
        unk_fine = coarse_uncertainty(feats, tag+'_' + fine_tag)
        unk_fine_list.append(unk_fine)
    final_unk_fine = []
    for i in range(len(unk_coarse)):
        # if no fine grained labels acquired
        if len(fine_tags) == 0:
            high = unk_coarse[i]
        else:
            high = max([unk_fine_list[k][i] for k in range(len(fine_tags))])
        final_unk_fine.append(unk_coarse[i]*alpha + high*beta)
    return unk_coarse, final_unk_fine


def hybrid_learner(exp, step_size=50.0, initial_size=200, active=False, fine_ratio=1.0):
    step_size_fine = int(step_size*fine_ratio)
    step_size_coarse = int(step_size - step_size*fine_ratio)

    # handle the fraction that do not round up
    overhead = 1.0 * step_size*fine_ratio - step_size_fine
    if random() < overhead:
        step_size_fine += 1
    overhead = 1.0 * (step_size - step_size*fine_ratio) - step_size_coarse
    if random() < overhead:
        step_size_coarse += 1

    feats_train_coarse, feats_train_fine, feats_val, feats_pool, label_train_coarse,\
        label_train_fine, label_val, label_pool = exp
    if len(feats_train_fine) + len(feats_train_coarse) < initial_size:
        feats_train_fine, feats_pool, label_train_fine, label_pool = \
            train_test_split(feats_pool, label_pool, train_size=initial_size, random_state=42)
        if fine_ratio < 1.0:
            feats_train_fine, feats_train_coarse, label_train_fine, label_train_coarse = \
                train_test_split(feats_train_fine, label_train_fine,
                                 train_size=int(fine_ratio*initial_size), random_state=42)
    if active:
        tag = 'hybrid_active_%d_%d' % (len(label_train_fine), len(label_train_coarse))
    else:
        tag = 'hybrid_passive_%d_%d' % (len(label_train_fine), len(label_train_coarse))
    print >> sys.stderr, '= Experiment on [%s]' % tag, ' <-', \
        len(feats_train_fine), len(feats_train_coarse), len(feats_pool), len(feats_val)

    fine_tags = trainmulticrf(feats_train_fine, feats_train_coarse, label_train_fine, label_train_coarse, tag)
    #print >> sys.stderr, 'Fine tags', fine_tags
    score_val = predictmulticrf(feats_val, fine_tags, tag)
    pr, roc = calculate_auc(masklabel(label_val), score_val)
    obj = {'coarse': False, 'active': active, 'pr': pr, 'roc': roc,
           'size': len(feats_train_fine) + len(feats_train_coarse), 'ratio': fine_ratio,
           'fine_size': len(feats_train_fine), 'coarse_size': len(feats_train_coarse)}
    # trace(obj)
    #  open('report/%s_report.txt' % tag,'w').write(tag + '\r\n' +
    #       bio_classification_report(masklabel(label_val), score_val))
    if active:
        unk_coarse, final_unk_fine = fine_uncertainty(feats_pool, fine_tags, tag)
        unk_coarse = array(unk_coarse)
        final_unk_fine = array(final_unk_fine)
        indices_next_fine = final_unk_fine.argsort()[::-1][:step_size_fine]
        args_unk_coarse = unk_coarse.argsort()[::-1]
        new_args_unk_coarse = []
        for v in args_unk_coarse:
            if v not in indices_next_fine:
                new_args_unk_coarse.append(v)
        indices_next_coarse = new_args_unk_coarse[:step_size_coarse]
    else:
        indices_next_fine = sample(range(len(label_pool)), step_size_fine)
        indices_next_coarse = sample(set(range(len(label_pool))) - set(indices_next_fine), step_size_coarse)

    # print indices_next_fine, len(indices_next_fine)
    # print indices_next_coarse, len(indices_next_coarse)
    feats_next, feats_rest, labels_next, labels_rest = partition_set(feats_pool, label_pool, indices_next_fine)
    feats_train_fine.extend(feats_next)
    label_train_fine.extend(labels_next)
    feats_next, feats_rest, labels_next, labels_rest = partition_set(feats_rest, labels_rest, indices_next_coarse)
    feats_train_coarse.extend(feats_next)
    label_train_coarse.extend(labels_next)
    feats_pool = feats_rest
    label_pool = labels_rest
    return [feats_train_coarse, feats_train_fine, feats_val, feats_pool, label_train_coarse,
            label_train_fine, label_val, label_pool], obj
