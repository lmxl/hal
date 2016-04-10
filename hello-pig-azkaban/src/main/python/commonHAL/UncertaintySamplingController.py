import IntervalModel
import sklearn.metrics
import numpy as np
import random
import math
import sys

class UncertaintySamplingController:
    def __init__(self, baseModel, pond_enabled=False, reward_factor = 1.0):
        self.model = baseModel
        self.reward_factor = reward_factor
        if pond_enabled:
            self.pond_enabled = pond_enabled
            self.pond_uncertainty = self.current_uncertainty(data_group='pond')
            self.fine_rewards = []
            self.coarse_rewards = []

    def compute_reward(self):
        assert self.pond_enabled, 'pond not enabled'
        new_ucties = self.current_uncertainty(data_group='pond')
        reward = self.reward_factor * np.mean([abs(i-j) for (i, j) in zip(self.pond_uncertainty, new_ucties)])
        self.pond_uncertainty = new_ucties
        print >> sys.stderr, 'rewards = %.4f' % reward
        return reward

    def current_metric(self):
        return self.current_pr_auc()

    def current_pr_auc(self):
        labels = self.model.get_test_labels()
        preds = self.score_alpha_beta(self.model.predict_test_scores())
        auc = sklearn.metrics.average_precision_score(labels, preds)
        return auc

    def uncertainty_alpha_beta(self, method, data_group, agg=False):
        if data_group == 'test':
            coarse_scores, fine_scores_list = self.model.predict_test_scores()
        elif data_group == 'pond':
            coarse_scores, fine_scores_list = self.model.predict_pond_scores()
        elif data_group == 'pool':
            coarse_scores, fine_scores_list = self.model.predict_pool_scores()
        else:
            assert False, 'unknown data_group [ %s ]' % data_group
        if method == 'hybrid':
            preds = self.score_alpha_beta((coarse_scores, fine_scores_list))
        elif method == 'coarse':
            preds = self.score_alpha_beta((coarse_scores, []))
        elif method == 'fine':
            preds = self.score_alpha_beta(([], fine_scores_list))
        else:
            assert False, 'Unknown method [ %s ]' % method
        ucties = self.pred_to_uncertainty(preds)
        return ucties

    def current_uncertainty(self, data_group, algo='alpha_beta_max', method='hybrid'):
        if algo == 'alpha_beta_max':
            return self.uncertainty_alpha_beta(method, data_group=data_group)
        if algo == 'agg_alpha_beta_max':
            return self.uncertainty_alpha_beta(method, data_group=data_group, agg=True)

    def recommend_acquisition_ids(self, num_recommend, algo, method='hybrid'):
        if algo == 'active':
            ucties = self.current_uncertainty(method=method, data_group='pool')
        elif algo == 'passive':
            ucties = [random.random() for i in range(self.model.get_pool_size())]
        else:
            assert False, 'Unknown algo [ %s ]' % algo
        neg_ucties = -np.array(ucties)
        pc = np.argpartition(neg_ucties, num_recommend)[:num_recommend]
        return pc, -neg_ucties[pc]

    def learn_coarse(self, step_size, algo):
        ids, ucties = self.recommend_acquisition_ids(step_size, method='coarse', algo=algo)
        self.model.acquire_example_ids(ids, example_type='coarse')
        self.model.fit()

    def learn_fine(self, step_size, algo):
        ids, ucties = self.recommend_acquisition_ids(step_size, method='fine', algo=algo)
        self.model.acquire_example_ids(ids, example_type='fine')
        self.model.fit()

    def learn_by_cost(self, budget_size, algo, cost_ratio, fixed_fine_budget_ratio=None):
        budget_size = float(budget_size)
        if algo == 'fixed_fine_ratio':
            step_size_all = budget_size/(cost_ratio*fixed_fine_budget_ratio + (1 -fixed_fine_budget_ratio))
            budget_size_fine = fixed_fine_budget_ratio*cost_ratio*step_size_all
            budget_size_coarse = (1-fixed_fine_budget_ratio)*step_size_all
            step_size_fine = int(budget_size_fine / cost_ratio)
            step_size_coarse = int(budget_size_coarse)
            # handle the fraction that do not round up
            overhead = budget_size_fine/cost_ratio - step_size_fine
            if random.random() < overhead:
                step_size_fine += 1
            overhead = budget_size_coarse - step_size_coarse
            if random.random() < overhead:
                step_size_coarse += 1
            ids, ucties = self.recommend_acquisition_ids(step_size_fine, method='fine', algo='active')
            self.model.acquire_example_ids(ids, example_type='fine')
            self.model.fit()
            ids, ucties = self.recommend_acquisition_ids(step_size_coarse, method='coarse', algo='active')
            self.model.acquire_example_ids(ids, example_type='coarse')
            self.model.fit()
        elif algo == 'bandit_uncertainty_sampling':
            step_size_fine = int(budget_size / cost_ratio)
            step_size_coarse = int(budget_size)
            # handle the fraction that do not round up
            overhead = 1.0 * budget_size/cost_ratio - step_size_fine
            if random.random() < overhead:
                step_size_fine += 1
            overhead = budget_size - step_size_coarse
            if random.random() < overhead:
                step_size_coarse += 1

            if len(self.coarse_rewards) == 0:
                self.go_allin_type(max(1, step_size_coarse), method='coarse', algo='active')
                self.coarse_rewards.append(self.compute_reward())
            elif len(self.fine_rewards) == 0:
                self.go_allin_type(max(1, step_size_fine), method='fine', algo='active')
                self.fine_rewards.append(self.compute_reward())
            else:
                n_play_fine = len(self.fine_rewards)
                n_play_coarse = len(self.coarse_rewards)
                expect_fine = np.mean(self.fine_rewards) + math.sqrt(2.0* math.log(n_play_coarse+ n_play_fine)/ n_play_fine)
                expect_coarse = np.mean(self.coarse_rewards) + math.sqrt(2.0* math.log(n_play_coarse+ n_play_fine)/ n_play_coarse)
                print >> sys.stderr, 'diff [ %.4f = %.4f - %.4f ] nplay fine [ %d ] coarse [ %d ]' % \
                                     (expect_fine - expect_coarse, expect_fine, expect_coarse, n_play_fine, n_play_coarse)
                if expect_fine > expect_coarse:
                    self.go_allin_type(step_size_fine, method='fine', algo='active')
                    self.fine_rewards.append(self.compute_reward())
                else:
                    self.go_allin_type(step_size_coarse, method='coarse', algo='active')
                    self.coarse_rewards.append(self.compute_reward())
        else:
            assert False, 'Unknown algo [ %s ]' % algo

    def go_allin_type(self, step_size, method, algo):
        ids, ucties = self.recommend_acquisition_ids(step_size, method=method, algo=algo)
        self.model.acquire_example_ids(ids, example_type=method)
        self.model.fit()

    @staticmethod
    def score_max(raw_scores_list):
        raw_scores = [max(raw_scores_tuple) for raw_scores_tuple in zip(*raw_scores_list)]
        return raw_scores

    @staticmethod
    def pred_to_uncertainty(preds):
        ucties = [0.5 - abs(v - 0.5) for v in preds]
        return ucties

    @staticmethod
    def score_alpha_beta(raw_scores):
        # alpha -> coarse weight
        # beta -> fine weight
        alpha = 0.5
        beta = 1.0 - alpha
        coarse_scores, fine_scores_list = raw_scores
        num_preds = len(coarse_scores)
        num_fines = len(fine_scores_list)
        if num_fines > 0:
            fine_scores = UncertaintySamplingController.score_max(fine_scores_list)
        else:
            # dummy scores
            fine_scores = coarse_scores
        # in case of fine only prediction
        if len(coarse_scores) == 0:
            coarse_scores = fine_scores
        hybrid_scores = [alpha*scores_tuple[0] + beta*scores_tuple[1]
                         for scores_tuple in zip(coarse_scores, fine_scores)]
        return hybrid_scores

    @staticmethod
    def unittest():
        controllers = list()
        controllers.append(IntervalModel.IntervalModel.unittest())
        for controller in controllers:
            preds = controller.score_alpha_beta(controller.model.predict_test_scores())
            assert min(preds) >= 0.0, 'negative uncertainty [%f]' % min(preds)
            assert max(preds) <= 1.0, 'prediction over 1.0 [%f]' % max(preds)
            ucties = controller.current_uncertainty()
            assert min(ucties) >= 0.0, 'negative uncertainty [%f]' % min(ucties)
            assert max(ucties) <= 0.5, 'uncertainty over 0.5 [%f]' % max(ucties)
            controller.learn_coarse(10)
            controller.learn_fine(10)


if __name__ == '__main__':
    UncertaintySamplingController.unittest()