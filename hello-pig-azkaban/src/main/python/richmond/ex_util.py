__author__ = 'ymo'
import json
import sys

def partition_set(feats, labels, indices):
    indices=set(indices)
    feats_select = []
    feats_unselect = []
    labels_select = []
    labels_unselect = []
    for i in range(len(labels)):
        if i in indices:
            feats_select.append(feats[i])
            labels_select.append(labels[i])
        else:
            feats_unselect.append(feats[i])
            labels_unselect.append(labels[i])
    return feats_select, feats_unselect, labels_select, labels_unselect


def masklabel(labels, mask = None):
    new_labels = []
    for label in labels:
        if mask is None:
            new_labels.append(['orgname' if v != 'token' else v for v in label])
        else:
            new_labels.append([ mask if v == mask else 'token' for v in label])
    return new_labels

def word2features(sent, i):
    word = sent[i]
    features = [
        'bias',
        #'word.lower=' + word.lower(),
        'word[-3:]=' + word[-3:],
        'word[-2:]=' + word[-2:],
        'word.isupper=%s' % word.isupper(),
        'word.istitle=%s' % word.istitle(),
        'word.isdigit=%s' % word.isdigit(),
        'word.len=%d' % len(word)
    ]
    if i > 0:
        word1 = sent[i - 1][0]
        features.extend([
            #  '-1:word.lower=' + word1.lower(),
            '-1:word.istitle=%s' % word1.istitle(),
            '-1:word.isupper=%s' % word1.isupper()
        ])
    else:
        features.append('BOS')

    if i < len(sent) - 1:
        word1 = sent[i + 1][0]
        features.extend([
            '+1:word.lower=' + word1.lower(),
            '+1:word.istitle=%s' % word1.istitle(),
            '+1:word.isupper=%s' % word1.isupper()
        ])
    else:
        features.append('EOS')
    return features


def sent2features(sent):
    return [word2features(sent, i) for i in range(len(sent))]

def trace(obj):
    print json.dumps(obj,indent=1, sort_keys=True)
