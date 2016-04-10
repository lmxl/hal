from subprocess import call
import sys, os, json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_palette(sns.color_palette("hls", 20))

def update_from_HDFS():
    dali_get = ["/usr/local/linkedin/bin/dali", "fs", "-copyToLocal"]
    webfs = "webhdfs://eat1-nertznn01.grid.linkedin.com:50070"
    call(["rm", "-rf", "results"])
    call(["mkdir", "-p", "results"])
    call(dali_get + [webfs + "/user/ymo/hal/results"])

def get_raw_results(halid, task_lab):
    path = 'results/' + task_lab + '/' + halid
    results = dict()
    for filename in os.listdir(path):
        if not filename.startswith('part-'):
            continue
        for line in open(path + '/' + filename):
            x = json.loads(line)
            for k, v in x.items():
                if k not in results:
                    results[k] = []
                results[k].append(v)
    df = pd.DataFrame(results)
    return df

def get_results(halid, task_lab):
    df = get_raw_results(halid, task_lab)
    row_total = df.shape[0]
    col_total = df.shape[1]
    if task_lab == 'manyTypes':
        df['config'] = [ a + '/' + b for (a,b) in zip(df['algo'], df['method'])]
        df = df.groupby(['config', 'round']).agg({'prauc': np.mean})
    elif task_lab == 'dynamicRatio':
        df['config'] = [str(b) if a == 'fixed_fine_ratio' else 'bandit' for (a,b) in zip(df['algo'], df['fine_ratio'])]
        df['fine_cost'] = [str(a) for a in df['fine_cost']]
        df_mixed = df.copy(deep=True)
        df['fine_cost'] = ['mixed' for a in df['fine_cost']]
        df = pd.concat([df, df_mixed]).groupby(['fine_cost', 'config', 'round']).agg({'prauc': np.mean})
    print 'Processed result [ %s %s ] from [ %d rows %d repeats %d columns ] into [ %d rows ]' %\
          (halid, task_lab, row_total, row_total/df.shape[0], col_total, df.shape[0])
    return df

def show_figure(df, legend_loc=4):
    for key in df.index.levels[0]:
        x = df.index.levels[1]
        y = df.loc[key]
        plt.plot(x, y)
    plt.legend(df.index.levels[0], loc=legend_loc)
    plt.xlabel('Iteration')
    plt.ylabel('P-R AUC')


def main():
    # update_from_HDFS()

    for j, task_model in enumerate(['interval', 'RCV1']):
        plt.figure(figsize=(28,20), dpi=300)
        z = get_results(task_model, 'dynamicRatio')
        for i, v in enumerate(z.index.levels[0]):
            plt.subplot(4,3,i+1)
            plt.title('%s: Ratio at %d' % (task_model, i+1))
            show_figure(z.loc[v])
        plt.savefig('figure/%s-bandit.png' % task_model)

    plt.figure(figsize=(20, 6), dpi=300)
    for i, task_model in enumerate(['interval', 'RCV1']):
        plt.subplot(1, 2, i+1)
        df = get_results(task_model, 'manyTypes')
        plt.title('%s: Comparing Fine/Coarse Active/Passive' % task_model)
        show_figure(df)
    plt.savefig('figure/draft.png')

if __name__ == '__main__':
    main()
