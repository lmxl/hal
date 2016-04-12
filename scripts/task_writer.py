import json
import sys
import random
import math
import numpy as np
from subprocess import call


def generate_task_files(task_path, task_lab, task_list, task_split, task_model, eta_inc, deploy_files):
    local_path = task_path + '/' + task_lab
    local_dest = local_path + '/' + task_model
    call(['rm', '-rf', local_dest])
    call(['mkdir', '-p', local_dest])
    random.shuffle(task_list)
    task_split = min(task_split, len(task_list))
    for i in range(task_split):
        with open(local_dest + '/task' + str(i), mode='w') as f_taskfile:
            for task_json in task_list[i::task_split]:
                f_taskfile.write(task_json + '\n')
    print >> sys.stderr, 'ETA [ %s %s %s tasks ] = %.1f Hr' % (task_model,
                                                               task_lab,
                                                               len(task_list),
                                                               eta_inc * math.ceil(1.0 * len(task_list) / task_split))
    if deploy_files:
        deploy_task_files(task_model, task_lab, local_src=local_dest)


def deploy_task_files(task_model, task_lab, local_src):
    remote_path = 'dali://nertz/user/ymo/hal/tasks' + '/' + task_lab
    remote_dest = remote_path + '/' + task_model
    dali_bin = '/usr/local/linkedin/bin/dali'
    print >> sys.stderr, 'Starting [ %s %s ] deployment from [ %s ] into [ %s ]' % \
                         (task_model, task_lab, local_src, remote_dest)
    call([dali_bin, 'fs', '-rm', '-r', '-f', remote_dest])
    call([dali_bin, 'fs', '-mkdir',remote_path])
    call([dali_bin, 'fs', '-put', local_src, remote_path])
    print >> sys.stderr, 'Finished deployment'


def build_tasks_lab_specific(param):
    if param['lab'] == 'manyTypes':
        for task_method in ['coarse', 'fine']:
            for task_algo in ['active', 'passive']:
                param['method'] = task_method
                param['algo'] = task_algo
                yield param
    elif param['lab'] == 'dynamicRatio':
        fine_cost_config = {
            'interval': [1.0, 1.1, 1.2, 1.5, 2.0, 4.0, 8.0, 16.0],
            'RCV1': [1.0, 1.1, 1.2, 1.5, 2.0, 4.0, 8.0, 16.0]}
        for param['fine_cost'] in fine_cost_config[param['model']]:
            param['algo'] = 'fixed_fine_ratio'
            for param['fine_ratio'] in np.linspace(start=0.0, stop=1.0, num=11):
                yield param
            param['algo'] = 'bandit_uncertainty_sampling'
            yield param
    else:
        assert False, 'Unknown lab type [ %s ]' % param['lab']


def build_tasks(task_model, task_lab, task_split, task_iteration, task_repeat, task_budget, deploy_files = False):
    eta_inc_map = {'manyTypes': {'interval': 0.00020, 'RCV1': 0.006},
                   'dynamicRatio': {'interval': 0.00028, 'RCV1': 0.0085}}
    eta_inc = eta_inc_map[task_lab][task_model] * task_iteration
    task_list = []
    param = dict()
    param['model'] = task_model
    param['lab'] = task_lab
    param['iteration'] = task_iteration
    param['budget'] = task_budget
    for j in range(task_repeat):
        param['repeat'] = j
        task_list += [json.dumps(v) for v in build_tasks_lab_specific(param)]
    local_path = '../build/tasks'
    generate_task_files(local_path, task_lab, task_list, task_split, task_model, eta_inc, deploy_files)

if __name__ == '__main__':
    redeploy_all = False
    interval_budget = 1
    interval_repeat = 200
    interval_iteration = 350
    RCV1_budget = 120
    RCV1_repeat = 50
    RCV1_iteration = 100

    build_tasks(task_model='interval',
                task_lab='manyTypes',
                task_split=10,
                task_iteration=interval_iteration,
                task_repeat=interval_repeat,
                task_budget=interval_budget,
                deploy_files=False or redeploy_all)

    build_tasks(task_model='RCV1',
                task_lab='manyTypes',
                task_split=20,
                task_iteration=RCV1_iteration,
                task_repeat=RCV1_repeat,
                task_budget=RCV1_budget,
                deploy_files=False or redeploy_all)

    build_tasks(task_model='interval',
                task_lab='dynamicRatio',
                task_split=300,
                task_iteration=interval_iteration,
                task_repeat=interval_repeat,
                task_budget=interval_budget,
                deploy_files=False or redeploy_all)

    build_tasks(task_model='RCV1',
                task_lab='dynamicRatio',
                task_split=700,
                task_iteration=RCV1_iteration,
                task_repeat=RCV1_repeat,
                task_budget=RCV1_budget,
                deploy_files=False or redeploy_all)