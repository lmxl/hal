from subprocess import call
import sys, os, json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_palette(sns.color_palette("hls", 20))

def update_result_from_HDFS(dataset=None):
    dali_get = ["/usr/local/linkedin/bin/dali", "fs", "-copyToLocal"]
    webfs = "webhdfs://eat1-nertznn01.grid.linkedin.com:50070"
    default_list = ['interval', 'richmond', 'rcv1', 'richmond-fixed']
    if dataset is not None:
        default_list = dataset
    for halid in default_list:
        print >> sys.stderr, 'Updating results from [ %s ]' % halid
        call(["rm", "-rf", "result/" + halid])
        call(["mkdir", "-p", "result"])
        call(dali_get + [webfs + "/user/ymo/hal/" + halid, "result"])

def get_manytypes(halid):
    text = ["Active Coarse", "Passive Coarse", "Active FineGrain", "Passive FineGrain"]
    path = 'result/' + halid + '/many_types'
    area = []
    round = []
    algo = []
    for filename in os.listdir(path):
        for line in open(path + '/' + filename):
            x = json.loads(line)
            for (i, key) in enumerate(text):
                area += x[i]
                round += range(len(x[i]))
                algo += [key] * len(x[i])
    df = pd.DataFrame({'area':area, 'algo':algo, 'round':round})
    return df.groupby(['algo', 'round']).agg({'area': np.mean})


def get_rcv1():
    text = ["Active HAL", "Passive HAL", "Active TPR", "Passive TPR"]
    path = 'result/rcv1'
    area = []
    round = []
    algo = []
    for filename in os.listdir(path):
        x = json.load(open(path +'/' + filename))
        for (i, key) in enumerate(text):
            area += x[i]
            round += range(len(x[i]))
            algo += [key] * len(x[i])
    df = pd.DataFrame({'area':area, 'algo':algo, 'round':round})
    return df.groupby(['algo', 'round']).agg({'area': np.mean})

def get_richmond(get_field='pr'):
    path = 'result/richmond'
    area = []
    round = []
    algo = []
    pr_prev = -1.0
    deltas = []
    for filename in os.listdir(path):
        sx = open(path + '/' + filename).read().replace('}', '}#').split('#')[:-1]
        for (round_n, json_str) in enumerate(sx):
            x = json.loads(json_str)

            if pr_prev<0:
                pr_prev = x['pr']
            x['delta'] = x['pr'] - pr_prev
            pr_prev = x['pr']
            deltas.append(abs(x['delta']))
            x['ndelta'] = 0.2 * min(1.0, abs(x['delta'] / (0.000001 +np.median(deltas))))
            print x['delta']

            area += [x[get_field]]
            round += [round_n]
            algo += ['dynamic']
    df = pd.DataFrame({'area':area, 'algo':algo, 'round':round})
    return df.groupby(['algo', 'round']).agg({'area': np.mean})


def get_richmond_fixed():
    path = 'result/richmond-fixed'
    area = []
    round = []
    algo = []
    for filename in os.listdir(path):
        sx = open(path + '/' + filename).read().replace('}', '}#').split('#')[:-1]
        for (round_n, json_str) in enumerate(sx):
            x = json.loads(json_str)
            area += [x['pr']]
            round += [round_n]
            algo += [str(x['ratio'])]
    df = pd.DataFrame({'area':area, 'algo':algo, 'round':round})
    return df.groupby(['algo', 'round']).agg({'area': np.mean})


def show_figure(df, legend_loc=4):
    for key in df.index.levels[0]:
        x = df.index.levels[1]
        y = df.loc[key]
        plt.plot(x, y)
    plt.legend(df.index.levels[0], loc=legend_loc)
    plt.xlabel('Iteration')
    plt.ylabel('P-R AUC')

def regular_plot():
    plt.subplot(2,2,1)
    plt.title('RCV1: Comparing HAL and TPR')
    show_figure(get_rcv1())

    plt.subplot(2,2,2)
    plt.title('Interval: Comparing Fine/Coarse Active/Passive')
    show_figure(get_manytypes())

    plt.subplot(2,2,3)
    plt.title('Richmond: Dynamic Ratio')
    show_figure(get_richmond())


    plt.subplot(2,2,4)
    show_figure(pd.concat([get_richmond_fixed(), get_richmond()]))

    plt.show()

def interval_bandit():
    path = 'result/interval/dynamic_ratio'
    area = []
    round = []
    algo = []
    ratios = []
    text = ['bandit', '0.0', '0.1', '0.2', '0.3', '0.4', '0.5', '0.6', '0.7', '0.8', '0.9', '1.0']
    max_cost = 5
    cost = range(1, max_cost + 1)
    for filename in os.listdir(path):
        for line in open(path + '/' + filename):
            x = json.loads(line)
            for (j, r) in enumerate(cost):
                for (i, key) in enumerate(text):
                    area += x[i + j * len(text)]
                    round += range(len(x[i]))
                    algo += [key] * len(x[i])
                    ratios += [r] * len(x[i])
    df = pd.DataFrame({'area':area, 'algo': algo, 'round':round, 'ratio': ratios})
    return [df[df.ratio==r].groupby(['algo', 'round']).agg({'area': np.mean}) for r in cost]

def plotManyTypes():
    plt.subplot(1,2,1)
    plt.title('Interval: Comparing Fine/Coarse Active/Passive')
    show_figure(get_manytypes('interval'))
    plt.subplot(1,2,2)
    plt.title('RCV1: Comparing Fine/Coarse Active/Passive')
    show_figure(get_manytypes('rcv1'))
    plt.show()
def main():
    update_result_from_HDFS(dataset=['interval'])
    plotManyTypes()

    z = interval_bandit()

    for (i, z1) in enumerate(z):
        plt.subplot(2,3,i+1)
        plt.title('Interval: Ratio at %d' % (i+1))
        show_figure(z1)
    plt.show()

    # show_figure(pd.concat([get_richmond_fixed(), get_richmond()]))

    #show_figure(get_richmond('ratio_p'))
    #plt.ylabel('Ratio')
    #plt.show()




if __name__ == '__main__':
    main()
