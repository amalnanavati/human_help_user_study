import csv
import sklearn.tree
import sklearn.linear_model
import sklearn.metrics
import numpy as np
import matplotlib.pyplot as plt
import pprint

def decisionTree(trainX, trainY, testX, testY, plot=False):
    decisionTree = sklearn.tree.DecisionTreeClassifier()#(max_depth=3)
    fittedDecisionTree = decisionTree.fit(trainX, trainY)

    if plot:
        fig = plt.figure(figsize=(48,24))
        ax = fig.subplots()
        tree.plot_tree(decisionTree, ax=ax)
        plt.savefig("../flask/ec2_outputs/decisionTree.png")

    testYPred = fittedDecisionTree.predict(testX)
    return testYPred, fittedDecisionTree

def logisticRegression(trainX, trainY, testX, testY, plot=False):
    logisticRegression = sklearn.linear_model.LogisticRegression()
    fittedLogisticRegression = logisticRegression.fit(trainX, trainY)

    if plot:
        # Generate the plot of frequency on the x, partitioned by busyness
        fig = plt.figure()
        ax = fig.subplots()

        # Plot the predictor
        busynessToColor = {}
        busynessToLabel = {}
        for busyness, color, label in [(0.0, "g", "free time"), (1/7.0, "b", "medium"), (1/3.0, "r", "high")]:
            busynessToColor[busyness] = color
            busynessToLabel[busyness] = label
            frequencies = [i/100.0 for i in range(20, 101)]
            X = np.array([[busyness, frequency] for frequency in frequencies])
            Y = fittedLogisticRegression.predict_proba(X)
            ax.plot(X[:,1], Y[:,1], c=color, label=label, linestyle="--")
        # Plot the averages for the test datapoints
        # TODO: add error bars!
        busynessToFrequencyToMean = {}
        for i in range(len(trainX)):
            busyness, frequency = trainX[i]
            if busyness not in busynessToFrequencyToMean:
                busynessToFrequencyToMean[busyness] = {}
            if frequency not in busynessToFrequencyToMean[busyness]:
                busynessToFrequencyToMean[busyness][frequency] = []
            y = trainY[i]
            busynessToFrequencyToMean[busyness][frequency].append(y)
        for busyness in busynessToFrequencyToMean:
            xs, ys = [], []
            for frequency in [0.2, 0.4, 0.6, 0.8, 1.0]:
                xs.append(frequency)
                ys.append(np.mean(busynessToFrequencyToMean[busyness][frequency]))
            ax.plot(xs, ys, c=busynessToColor[busyness], label=busynessToLabel[busyness], marker="o")
        # ax.legend()
        plt.show()

    testYPred = fittedLogisticRegression.predict(testX)
    return testYPred, fittedLogisticRegression

def alwaysPredictNotHelp(trainX, trainY, testX, testY, plot=False):
    testYPred = np.zeros(testY.shape)
    return testYPred, None

def alwaysPredictHelp(trainX, trainY, testX, testY, plot=False):
    testYPred = np.ones(testY.shape)
    return testYPred, None

if __name__ == "__main__":
    busynessListRaw, freqOfAskingList, freqOfHelpingAccuratelyList, responseNumberList = [], [], [], []
    busynessList = []
    # busynessMapping = {"high": 2, "medium": 1, "free time": 0}
    with open("../flask/ec2_outputs/humanHelpUserStudyPerResponseData.csv", "r") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        for row in reader:
            uuid, taskI, busyness, freqOfAsking, freqOfHelpingAccurately, responseNumber, prosociality, slowness, busynessNumeric, numRecentTimesDidNotHelp, age = row
            busynessListRaw.append(busyness)
            busynessList.append(busynessNumeric)#busynessMapping[busyness])
            freqOfAskingList.append(freqOfAsking)
            freqOfHelpingAccuratelyList.append(freqOfHelpingAccurately)
            responseNumberList.append(responseNumber)

    # busynessEncoder = preprocessing.LabelEncoder()
    # busynessList = busynessEncoder.fit_transform(busynessListRaw)
    # print("busynessEncoder", busynessEncoder, busynessEncoder.get_params(), busynessEncoder.transform(["high", "medium", "free time"]))

    # X = np.zeros((len(busynessList), 3))
    X = np.zeros((len(busynessList), 2))
    Y = np.zeros(len(busynessList))
    for i in range(len(busynessList)):
        X[i][0] = busynessList[i]
        X[i][1] = freqOfAskingList[i]
        # X[i][2] = freqOfHelpingAccuratelyList[i]
        Y[i] = responseNumberList[i]

    trainingSetSize = int(0.80*len(busynessList))
    numSamplesIndices = np.arange(len(busynessList))
    numRepeats = 50
    classifiers = {
        "Decision Tree" : decisionTree,
        "Logistic Regression" : logisticRegression,
        "Always Predict Not Help" : alwaysPredictNotHelp,
        "Always Predict Help" : alwaysPredictHelp,
    }
    accuracies = {classifierName : [] for classifierName in classifiers}
    f1Scores = {classifierName : [] for classifierName in classifiers}
    confusionMatrices = {classifierName : [] for classifierName in classifiers}

    for repeatI in range(numRepeats):
        # TODO (amal): balance the test dataset
        np.random.shuffle(numSamplesIndices)

        trainIndices = numSamplesIndices[:trainingSetSize]
        testIndices = numSamplesIndices[trainingSetSize:]

        trainX = X[trainIndices]
        testX = X[testIndices]

        trainY = Y[trainIndices]
        testY = Y[testIndices]

        # logisticRegression(trainX, trainY, testX, testY, True)
        # raise Exception()

        for classifierName, classifierFn in classifiers.items():
            testYPred, _ = classifierFn(trainX, trainY, testX, testY)

            accuracy = sklearn.metrics.accuracy_score(testY, testYPred)
            accuracies[classifierName].append(accuracy)

            f1Score = sklearn.metrics.f1_score(testY, testYPred)
            f1Scores[classifierName].append(f1Score)

            # true negative, true positive, false negative, false positive
            tn, fp, fn, tp = sklearn.metrics.confusion_matrix(testY, testYPred).ravel()
            confusionMatrices[classifierName].append([[tn/(tn+fn), fn/(tn+fn)], [fp/(tp+fp), tp/(tp+fp)]])


    # print("accuracies")
    # pprint.pprint(accuracies)
    # print("f1Scores")
    # pprint.pprint(f1Scores)
    # print("confusionMatrices")
    # pprint.pprint(confusionMatrices)

    print("average accuracies")
    pprint.pprint({classifierName : np.mean(accuracies[classifierName], axis=0) for classifierName in classifiers})
    print("average f1Scores")
    pprint.pprint({classifierName : np.mean(f1Scores[classifierName], axis=0) for classifierName in classifiers})
    print("average confusionMatrices")
    pprint.pprint({classifierName : np.mean(confusionMatrices[classifierName], axis=0) for classifierName in classifiers})
