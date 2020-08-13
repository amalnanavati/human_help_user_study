import csv
import sklearn.tree
import sklearn.linear_model
import sklearn.metrics
import numpy as np
import matplotlib.pyplot as plt
import pprint

def decisionTree(trainX, trainY, testX, plot=False):
    decisionTree = sklearn.tree.DecisionTreeClassifier()#(max_depth=3)
    fittedDecisionTree = decisionTree.fit(trainX, trainY)

    if plot:
        fig = plt.figure(figsize=(48,24))
        ax = fig.subplots()
        tree.plot_tree(decisionTree, ax=ax)
        plt.savefig("../flask/ec2_outputs/decisionTree.png")

    testYPred = fittedDecisionTree.predict(testX)
    return testYPred

def logisticRegression(trainX, trainY, testX):
    logisticRegression = sklearn.linear_model.LogisticRegression()#(max_depth=3)
    fittedLogisticRegression = logisticRegression.fit(trainX, trainY)

    testYPred = fittedLogisticRegression.predict(testX)
    return testYPred

def alwaysPredictNotHelp(trainX, trainY, testX):
    testYPred = np.zeros(testY.shape)
    return testYPred

def alwaysPredictHelp(trainX, trainY, testX):
    testYPred = np.ones(testY.shape)
    return testYPred

if __name__ == "__main__":
    busynessListRaw, freqOfAskingList, freqOfHelpingAccuratelyList, responseNumberList = [], [], [], []
    busynessList = []
    # busynessMapping = {"high": 2, "medium": 1, "free time": 0}
    with open("../flask/ec2_outputs/humanHelpUserStudyPerResponseData.csv", "r") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        for row in reader:
            uuid, taskI, busyness, freqOfAsking, freqOfHelpingAccurately, responseNumber, prosociality, slowness, busynessNumeric, numRecentTimesDidNotHelp = row
            busynessListRaw.append(busyness)
            busynessList.append(busynessNumeric)#busynessMapping[busyness])
            freqOfAskingList.append(freqOfAsking)
            freqOfHelpingAccuratelyList.append(freqOfHelpingAccurately)
            responseNumberList.append(responseNumber)

    # busynessEncoder = preprocessing.LabelEncoder()
    # busynessList = busynessEncoder.fit_transform(busynessListRaw)
    # print("busynessEncoder", busynessEncoder, busynessEncoder.get_params(), busynessEncoder.transform(["high", "medium", "free time"]))

    X = np.zeros((len(busynessList), 3))
    Y = np.zeros(len(busynessList))
    for i in range(len(busynessList)):
        X[i][0] = busynessList[i]
        X[i][1] = freqOfAskingList[i]
        X[i][2] = freqOfHelpingAccuratelyList[i]
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

        for classifierName, classifierFn in classifiers.items():
            testYPred = classifierFn(trainX, trainY, testX)

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
