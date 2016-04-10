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
    print >> sys.stderr, 'Starting [ %s %s ] deployment from [ %s ] into [ %s ]' % \
                         (task_model, task_lab, local_src, remote_dest)
    call(['dali', 'fs', '-rm', '-r', '-f', remote_dest])
    call(['dali', 'fs', '-mkdir',remote_path])
    call(['dali', 'fs', '-put', local_src, remote_path])
    print >> sys.stderr, 'Finished deployment'


def build_tasks_lab_specific(param):
    if param['lab'] == 'manyTypes':
        for task_method in ['coarse', 'fine']:
            for task_algo in ['active', 'passive']:
                param['method'] = task_method
                param['algo'] = task_algo
                yield param
    elif param['lab'] == 'dynamicRatio':
        for param['fine_cost'] in np.linspace(start=1, stop=10, num=10):
            param['algo'] = 'fixed_fine_ratio'
            for param['fine_ratio'] in np.linspace(start=0.0, stop=1.0, num=11):
                yield param
            param['algo'] = 'bandit_uncertainty_sampling'
            yield param
    else:
        assert False, 'Unknown lab type [ %s ]' % param['lab']


def build_tasks(task_model, task_lab, task_split, task_iteration, task_repeat, task_budget, deploy_files = False):
    eta_inc_map = {'manyTypes': {'interval': 0.00015, 'RCV1': 0.01},
                   'dynamicRatio': {'interval': 0.00032, 'RCV1': 0.012}}
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
    local_path = 'tasks'
    generate_task_files(local_path, task_lab, task_list, task_split, task_model, eta_inc, deploy_files)

if __name__ == '__main__':
    redeploy_all = True
    build_tasks(task_model='interval',
                task_lab='manyTypes',
                task_split=100,
                task_iteration=300,
                task_repeat=400,
                task_budget=4,
                deploy_files=False or redeploy_all)

    build_tasks(task_model='RCV1',
                task_lab='manyTypes',
                task_split=100,
                task_iteration=100,
                task_repeat=25,
                task_budget=150,
                deploy_files=False or redeploy_all)

    build_tasks(task_model='interval',
                task_lab='dynamicRatio',
                task_split=300,
                task_iteration=300,
                task_repeat=40,
                task_budget=4,
                deploy_files=False or redeploy_all)

    build_tasks(task_model='RCV1',
                task_lab='dynamicRatio',
                task_split=300,
                task_iteration=100,
                task_repeat=5,
                task_budget=150,
                deploy_files=False or redeploy_all)