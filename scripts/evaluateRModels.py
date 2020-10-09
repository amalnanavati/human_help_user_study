import csv
import math
import pprint
import numpy as np
import scipy.optimize
import sklearn.metrics
import sklearn.tree
import sklearn.linear_model

class ModelParams(object):
    def __init__(self, filepath):
        with open(filepath, "r") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            i = -1
            self.uuids = []
            self.random_effects = []
            for row in reader:
                i += 1
                if i == 0:
                    self.fixed_effects = np.array([float(param) for param in row[2:]])
                uuid = int(row[0])
                random_intercept = float(row[1])
                self.uuids.append(uuid)
                self.random_effects.append(random_intercept)
        self.random_effects = np.array(self.random_effects)

    def get_probability(self, datapoint, start, end, random_effect=None):
        logit = np.dot(datapoint[start:end], self.fixed_effects)
        # if uuid is not None:
        #     uuid_i = self.uuids.find(uuid)
        #     if uuid_i > -1: # A random effect exists for that user
        #         random_effect = self.random_effects[uuid_i]
        #         logit += random_effect
        if random_effect is not None:
            logit += random_effect
        prob = math.e**logit / (1 + math.e**logit)
        return prob

    def get_optimal_random_effect(self, datapoints, start, end, method="cross_entropy"):

        if len(datapoints) == 0:
            return np.array([0.0])

        if method == "cross_entropy":
            def loss_fn(random_effect):
                loss = 0.0
                for i in range(len(datapoints)):
                    x = datapoints[i].get_datapoint_numeric()[start:end]
                    y = datapoints[i].human_response
                    logit = np.dot(x, self.fixed_effects)
                    logit += random_effect
                    p = math.e**logit / (1 + math.e**logit)
                    loss += -y*math.log(p) - (1-y)*math.log(1-p)
                return loss
        elif method == "mean_sq":
            def loss_fn(random_effect):
                loss = 0.0
                for i in range(len(datapoints)):
                    x = datapoints[i].get_datapoint_numeric()[start:end]
                    y = datapoints[i].human_response
                    logit = np.dot(x, self.fixed_effects)
                    logit += random_effect
                    p = math.e**logit / (1 + math.e**logit)
                    loss += (y-p)**2.0
                loss /= len(datapoints)
                return loss

        min_random_effect = np.min(self.random_effects)
        max_random_effect = np.max(self.random_effects)
        initial_random_effect = np.random.random()*(max_random_effect-min_random_effect)+min_random_effect

        result = scipy.optimize.minimize(loss_fn, initial_random_effect)

        if not result.success:
            print("Optimization failed: %s" % result.message)

        random_effect = result.x

        return random_effect

    def get_fixed_effect_predictor(self, start, end):

        def fixed_effect_predictor(train_x, train_y, train_weights, test_x, plot=False):
            logit = np.dot(test_x[:,start:end], self.fixed_effects)
            prob = math.e**logit / (1 + math.e**logit)
            return (prob > 0.5).astype(int), None

        return fixed_effect_predictor

class Datapoint(object):
    def __init__(self, row):
        self.uuid = int(row[0])
        self.task_i = int(row[1])
        self.busyness = row[2]
        self.past_frequency_of_asking = float(row[3])
        self.past_frequency_of_helping_accurately = float(row[4])
        self.human_response = int(row[5])
        self.prosociality = float(row[6])
        self.slowness = float(row[7])
        self.busyness_numeric = float(row[8])
        self.num_recent_times_did_not_help = int(row[9])
        self.age = int(row[10])

    def get_datapoint_numeric(self):
        return np.array([1.0, self.busyness_numeric, self.busyness_numeric*self.past_frequency_of_asking])

class UUIDDatapoint(object):
    def __init__(self):
        self.datapoints = []

    def add_row(self, row):
        self.datapoints.append(Datapoint(row))

    def get_datapoints(self):
        sorted_datapoints = sorted(self.datapoints, key=lambda x: x.task_i)
        return sorted_datapoints

def load_dataset(filepath):
    uuid_col = 0

    dataset = {}
    with open(filepath, "r") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        for row in reader:
            uuid = int(row[uuid_col])
            if uuid not in dataset:
                dataset[uuid] = UUIDDatapoint()
            dataset[uuid].add_row(row)
    return dataset

def decision_tree(train_x, train_y, train_weights, test_x, plot=False):
    decision_tree = sklearn.tree.DecisionTreeClassifier()#(max_depth=3)
    fitted_decision_tree = decision_tree.fit(train_x, train_y, sample_weight=train_weights)

    if plot:
        fig = plt.figure(figsize=(48,24))
        ax = fig.subplots()
        tree.plot_tree(decision_tree, ax=ax)
        plt.savefig("../flask/ec2_outputs/decision_tree.png")

    test_y_pred = fitted_decision_tree.predict(test_x)
    return test_y_pred, fitted_decision_tree

def logistic_regression(train_x, train_y, train_weights, test_x, plot=False):
    logistic_regression = sklearn.linear_model.LogisticRegression()
    fitted_logistic_regression = logistic_regression.fit(train_x, train_y, sample_weight=train_weights)

    test_y_pred = fitted_logistic_regression.predict(test_x)
    return test_y_pred, fitted_logistic_regression

def always_predict_not_help(train_x, train_y, train_weights, test_x, plot=False):
    test_y_pred = np.zeros(test_x.shape[0])
    return test_y_pred, None

def always_predict_help(train_x, train_y, train_weights, test_x, plot=False):
    test_y_pred = np.ones(test_x.shape[0])
    return test_y_pred, None

def random_predictor(train_x, train_y, train_weights, test_x, plot=False):
    test_y_pred = np.random.randint(2, size=test_x.shape[0])
    return test_y_pred, None

if __name__ == "__main__":

    base_dir = "/Users/amaln/Documents/PRL/human_help_user_study/flask/ec2_outputs/processedData/80-20/"
    raw_filepath = base_dir+"%d_%s.csv"
    num_partitions = 5

    # raw_filepath = "/Users/amaln/Documents/PRL/human_help_user_study/flask/ec2_outputs/processedData/hold-one-out/%d_%s.csv"
    # num_partitions = 140

    metrics_to_test = {
        "Accuracy" : sklearn.metrics.accuracy_score,
        "F1" : sklearn.metrics.f1_score,
        "MCC" : sklearn.metrics.matthews_corrcoef,

        # "confusion_matrix" : sklearn.metrics.confusion_matrix,
    }
    results = {metric : [] for metric in metrics_to_test}

    baseline_models = {
        "Decision Tree" : decision_tree,
        # "Logistic Regression" : logistic_regression,
        # "Always Predict Not Help" : always_predict_not_help, # NOTE: Keeping this model produces a runtime error with sklearn.metrics.matthews_corrcoef
        # "Always Predict Help" : always_predict_help, # NOTE: Keeping this model produces a runtime error with sklearn.metrics.matthews_corrcoef
        # "Random" : random_predictor,
        # "Fixed Effects" : None, # Will add per param
    }
    baseline_results = {
        model_name : {
            metric : [] for metric in metrics_to_test
        } for model_name in baseline_models
    }
    baseline_results["Only Fixed"] = {metric : [] for metric in metrics_to_test}
    baseline_results["Only Random"] = {metric : [] for metric in metrics_to_test}
    baseline_results["Only Intercept"] = {metric : [] for metric in metrics_to_test}

    total_params = None
    total_params_only_fixed = None
    total_params_only_random = None
    total_params_only_intercept = None

    for i in range(num_partitions+1):
        # Load the Model Params
        if i < num_partitions:
            params = ModelParams(raw_filepath % (i, "model"))
            if total_params is None:
                total_params = params.fixed_effects
            else:
                total_params += params.fixed_effects
            params_only_fixed = ModelParams(raw_filepath % (i, "model_only_fixed"))
            if total_params_only_fixed is None:
                total_params_only_fixed = params_only_fixed.fixed_effects
            else:
                total_params_only_fixed += params_only_fixed.fixed_effects
            params_only_random = ModelParams(raw_filepath % (i, "model_only_random"))
            if total_params_only_random is None:
                total_params_only_random = params_only_random.fixed_effects
            else:
                total_params_only_random += params_only_random.fixed_effects
            params_only_intercept = ModelParams(raw_filepath % (i, "model_only_intercept"))
            if total_params_only_intercept is None:
                total_params_only_intercept = params_only_intercept.fixed_effects
            else:
                total_params_only_intercept += params_only_intercept.fixed_effects
        else:
            params.fixed_effects = total_params / num_partitions
            print("Proposed with averaging fixed effects", params.fixed_effects)
            # params.fixed_effects = np.array([0.674073, -5.734255, -0.209316, -8.425234])
            params_only_fixed.fixed_effects = total_params_only_fixed / num_partitions
            params_only_random.fixed_effects = total_params_only_random / num_partitions
            params_only_intercept.fixed_effects = total_params_only_intercept / num_partitions
        print("Model: %d" % i)
        # print("  Fixed: %s" % params.fixed_effects)
        # print("  Random: %s" % params.random_effects)
        # print("  Random Min %f, Median %f, Mean %f, Max %f" % (
        #     np.min(params.random_effects),
        #     np.median(params.random_effects),
        #     np.mean(params.random_effects),
        #     np.max(params.random_effects),
        # ))

        # Add variants of the trained model as baselines
        # baseline_models["Fixed Effects"] = params.get_fixed_effect_predictor()

        # Load Train Set
        train_set = load_dataset(raw_filepath % (min(i, num_partitions-1), "train"))
        train_set_numeric = []
        train_set_weights = []
        train_set_labels = []
        for uuid in train_set:
            datapoints = train_set[uuid].get_datapoints()
            for k in range(len(datapoints)):
                train_set_numeric.append(datapoints[k].get_datapoint_numeric())
                train_set_weights.append(1.0/len(datapoints))
                train_set_labels.append(datapoints[k].human_response)
        train_set_numeric = np.array(train_set_numeric)
        train_set_weights = np.array(train_set_weights)
        train_set_labels = np.array(train_set_labels)

        # Load the Test Set
        test_set = load_dataset(raw_filepath % (min(i, num_partitions-1), "test"))
        test_set_numeric = []
        test_set_weights = []
        test_set_labels = []
        for uuid in test_set:
            datapoints = test_set[uuid].get_datapoints()
            for k in range(len(datapoints)):
                test_set_numeric.append(datapoints[k].get_datapoint_numeric())
                test_set_weights.append(1.0/len(datapoints))
                test_set_labels.append(datapoints[k].human_response)
        test_set_numeric = np.array(test_set_numeric)
        test_set_weights = np.array(test_set_weights)
        test_set_labels = np.array(test_set_labels)
        if i == num_partitions:
            for uuid in train_set:
                test_set[uuid] = train_set[uuid]
            test_set_numeric = np.concatenate((train_set_numeric, test_set_numeric), axis=0)
            test_set_weights = np.concatenate((train_set_weights, test_set_weights), axis=0)
            test_set_labels = np.concatenate((train_set_labels, test_set_labels), axis=0)

        # Evaluate the R Model
        y_true = []
        y_pred_probs = []
        y_pred_probs_only_fixed  = []
        y_pred_probs_only_random = []
        y_pred_probs_only_intercept = []
        y_weights = []
        for uuid in test_set:
            datapoints = test_set[uuid].get_datapoints()
            for k in range(len(datapoints)):
                y = datapoints[k].human_response
                y_true.append(y)
                y_weights.append(1.0/len(datapoints))

                # print("Proposed")
                random_effect = params.get_optimal_random_effect(datapoints[:k], 0, 4)
                # print(random_effect)
                prob = params.get_probability(datapoints[k].get_datapoint_numeric(), 0, 4, random_effect)
                # print("UUID", uuid, "k", k, "random_effect", random_effect, "human_response", y, "prob", prob)
                y_pred_probs.append(prob)

                # print("Only Fixed")
                prob_only_fixed = params_only_fixed.get_probability(datapoints[k].get_datapoint_numeric(), 0, 4)
                y_pred_probs_only_fixed.append(prob_only_fixed)

                # print("Only Random")
                random_effect_only_random = params_only_random.get_optimal_random_effect(datapoints[:k], 0, 1)
                # print(random_effect_only_random)
                prob_only_random = params_only_random.get_probability(datapoints[k].get_datapoint_numeric(), 0, 1, random_effect_only_random)
                y_pred_probs_only_random.append(prob_only_random)

                # print("Only Intercept")
                prob_only_intercept = params_only_intercept.get_probability(datapoints[k].get_datapoint_numeric(), 0, 1)
                y_pred_probs_only_intercept.append(prob_only_intercept)

        y_true = np.array(y_true)
        y_pred = (np.array(y_pred_probs) > 0.5).astype(int)
        y_pred_only_fixed = (np.array(y_pred_probs_only_fixed) > 0.5).astype(int)
        y_pred_only_random = (np.array(y_pred_probs_only_random) > 0.5).astype(int)
        y_pred_only_intercept = (np.array(y_pred_probs_only_intercept) > 0.5).astype(int)

        for metric in metrics_to_test:
            try:
                result = metrics_to_test[metric](y_true, y_pred, sample_weight=y_weights, labels=[0,1])
                result_only_fixed = metrics_to_test[metric](y_true, y_pred_only_fixed, sample_weight=y_weights, labels=[0,1])
                result_only_random = metrics_to_test[metric](y_true, y_pred_only_random, sample_weight=y_weights, labels=[0,1])
                result_only_intercept = metrics_to_test[metric](y_true, y_pred_only_intercept, sample_weight=y_weights, labels=[0,1])
            except Exception as e:
                result = metrics_to_test[metric](y_true, y_pred, sample_weight=y_weights)
                result_only_fixed = metrics_to_test[metric](y_true, y_pred_only_fixed, sample_weight=y_weights)
                result_only_random = metrics_to_test[metric](y_true, y_pred_only_random, sample_weight=y_weights)
                result_only_intercept = metrics_to_test[metric](y_true, y_pred_only_intercept, sample_weight=y_weights)
            print(metric)
            print("  Proposed", result)
            print("  Only Fixed", result_only_fixed)
            print("  Only Random", result_only_random)
            print("  Only Intercept", result_only_intercept)
            results[metric].append(result)
            baseline_results["Only Fixed"][metric].append(result_only_fixed)
            baseline_results["Only Random"][metric].append(result_only_random)
            baseline_results["Only Intercept"][metric].append(result_only_intercept)

        # Evaluate the baselines
        for model_name in baseline_models:
            test_set_preds, _ = baseline_models[model_name](
                train_set_numeric, train_set_labels,
                train_set_weights, test_set_numeric,
            )
            for metric in baseline_results[model_name]:
                try:
                    result = metrics_to_test[metric](test_set_labels, test_set_preds, sample_weight=test_set_weights, labels=[0,1])
                except Exception as e:
                    result = metrics_to_test[metric](test_set_labels, test_set_preds, sample_weight=test_set_weights)
                baseline_results[model_name][metric].append(result)

    for metric in metrics_to_test:
        print(metric)
        print("   Proposed Model", metric, np.mean(results[metric], axis=0), np.std(results[metric], axis=0))
        for model_name in baseline_results:
            print("  ", model_name, np.mean(baseline_results[model_name][metric], axis=0), np.std(baseline_results[model_name][metric], axis=0))

    # Write to CSV
    header = ["Partition"]
    for metric in metrics_to_test:
        header += [metric+" Proposed"]
        for model_name in baseline_results:
            header += [metric+" "+model_name]
    with open(base_dir+"results.csv", "w") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(header)
        for i in range(num_partitions):
            row = [i]
            for metric in metrics_to_test:
                row += [results[metric][i]]
                for model_name in baseline_results:
                    row += [baseline_results[model_name][metric][i]]
            writer.writerow(row)

    # Write to CSV
    header = ["Partition", "Model", "Accuracy", "F1", "MCC"]
    with open(base_dir+"results_long.csv", "w") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(header)
        for i in range(num_partitions):
            for model_name in list(baseline_results.keys())+["Proposed"]:
                row = [i, model_name]
                if model_name == "Proposed":
                    for metric in metrics_to_test:
                        row += [results[metric][i]]
                else:
                    for metric in metrics_to_test:
                        row += [baseline_results[model_name][metric][i]]
                writer.writerow(row)
    print("Wrote CSV")
