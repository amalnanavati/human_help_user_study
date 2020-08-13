from sklearn.cluster import KMeans
import numpy as np
import time
import csv
import pprint
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import math
import scipy.stats

def kmeansAnalyzeDataset(dataset, descriptor, xlabel, ylabel, zlabel, frequencies, isBusyness=False):
    if isBusyness: busynessNumericOrder = [0.0, 1.0/7, 1.0/3]
    randomSeed = int(time.time())
    ks, inertias = [], []
    previousDifference, currentDifference = None, None
    maxSecondDifference, maxSecondDifferenceK = None, None
    for k in range(2, 15):
        kmeans = KMeans(n_clusters=k, random_state=randomSeed).fit(dataset)
        ks.append(k)
        inertias.append(kmeans.inertia_)
        if k > 2:
            previousDifference = currentDifference
            currentDifference = inertias[-1]-inertias[-2]
            if previousDifference is not None:
                secondDifference = currentDifference-previousDifference
                if maxSecondDifference is None or secondDifference > maxSecondDifference:
                    maxSecondDifference = secondDifference
                    maxSecondDifferenceK = k-1
        print("descriptor {} k {} cluster_centers_ {}, inertia_ {}".format(descriptor, k, kmeans.cluster_centers_, kmeans.inertia_))

    print("descriptor", descriptor, "maxSecondDifferenceK", maxSecondDifferenceK)

    fig = plt.figure()
    ax = fig.add_subplot()
    ax.plot(ks, inertias)
    ax.set_xlabel("K (Num Clusters)")
    ax.set_ylabel("Inertia")
    plt.savefig(baseDir+"kValuesForClusteringHumans{}.png".format(descriptor))
    plt.clf()

    # Based on this plot, visually the elbow point is maxSecondDifferenceK
    k = maxSecondDifferenceK
    kmeans = KMeans(n_clusters=k, random_state=randomSeed).fit(dataset)

    # Do Analysis
    labelToFrequencyToCount = {i : {} for i in range(k)}
    labelToCount = {i : 0 for i in range(k)}
    for i in range(kmeans.labels_.shape[0]):
        label = kmeans.labels_[i]
        frequency = frequencies[i]
        if frequency not in labelToFrequencyToCount[label]:
            labelToFrequencyToCount[label][frequency] = 0
        labelToFrequencyToCount[label][frequency] += 1
        labelToCount[label] += 1

    print("descriptor", descriptor, "labelToFrequencyToCount")
    pprint.pprint(kmeans.cluster_centers_)
    pprint.pprint(labelToFrequencyToCount)
    pprint.pprint(labelToCount)
    pprint.pprint({label : {frequency: labelToFrequencyToCount[label][frequency] / labelToCount[label] for frequency in labelToFrequencyToCount[label]} for label in labelToFrequencyToCount})

    # 3D scatterplot
    colors = ["b", "r", "g", "m", "k"]
    pointMarker = "^"
    centerMarker = "o"
    colorsForDataset = np.vectorize(lambda i: colors[i%len(colors)])(kmeans.labels_)
    colorsForCenters = [colors[i%len(colors)] for i in range(k)]

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(
        dataset[:, 0],
        dataset[:, 1],
        dataset[:, 2],
        c=colorsForDataset,
        marker=pointMarker,
    )
    ax.scatter(
        kmeans.cluster_centers_[:, 0],
        kmeans.cluster_centers_[:, 1],
        kmeans.cluster_centers_[:, 2],
        c=colorsForCenters,
        marker=centerMarker,
    )

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_zlabel(zlabel)
    ax.legend()

    plt.savefig(baseDir+"fullScatterWithClusters{}.png".format(descriptor))
    plt.clf()

    if isBusyness:
        for clusterI in range(k): # create a separate graph per cluster
            print("clusterI", clusterI)
            # Make a full graph of everyone's data
            indices = np.where(kmeans.labels_ == clusterI)
            filteredDataset = dataset[indices]
            filteredFrequencies = frequencies[indices]
            sortedFrequencies = np.argsort(filteredFrequencies)
            numPeople = filteredDataset.shape[0]
            numCols = 7
            numRows = int(math.ceil(numPeople/numCols))
            fig = plt.figure(figsize=(28,16))
            axes = fig.subplots(numRows, numCols)
            fig.suptitle('People in cluster {}'.format(clusterI))
            numI = -1
            for i in sortedFrequencies:
                numI += 1
                rowI = numI // numCols
                colI = numI % numCols
                # Add the human response line
                axes[rowI][colI].plot(busynessNumericOrder, filteredDataset[i,:], c="k")
                axes[rowI][colI].set_ylim([-0.1,1.1])
                axes[rowI][colI].set_xlabel("Busyness")
                axes[rowI][colI].set_ylabel("Likelihood of Helping")
                axes[rowI][colI].set_title("Freq %1.1f" % filteredFrequencies[i])
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            plt.savefig(baseDir + "fullScatterWithClusters_everyone_cluser_{}{}.png".format(clusterI, descriptor))
            plt.clf()

            # Make the frequency to willingness bar chart partitioned y busyness and the clusters.
            # Graph the human responses as a Bernoulli RV, inversely weighted for num people, with error bars
            busynessOrder = ["free time", "medium", "high"]
            fig = plt.figure(figsize=(16,8))
            axes = fig.subplots(1, len(busynessOrder))
            fig.suptitle('Cluster {} (n={}): Human Responses by Busyness and Frequency, Inversely Weighted by Num Requests Per Person'.format(clusterI, filteredDataset.shape[0]))

            # Constant for the Wilson Confidence Interval for Bernoulli random variables
            # https://brainder.org/2012/04/21/confidence-intervals-for-bernoulli-trials/
            alpha = 0.05
            kForErrorBar = scipy.stats.norm.ppf(1-alpha/2)

            freqOrder = [(gid+1)/5.0 for gid in range(5)]
            for i in range(len(axes)):
                busyness = busynessOrder[i]
                print("i", i, "busyness", busyness)
                noNum = []
                yesNum = []
                errorBars = [[], []]
                for freqOfAsking in freqOrder:
                    print("freqOfAsking", freqOfAsking)
                    peopleIWithThisFrequency = np.where(filteredFrequencies == freqOfAsking)
                    filteredDatasetWithThisFrequency = filteredDataset[peopleIWithThisFrequency]
                    x = np.sum(filteredDatasetWithThisFrequency[:,i], axis=0) # ith index is busyness i
                    n = filteredDatasetWithThisFrequency.shape[0]
                    print("filteredDatasetWithThisFrequency")
                    pprint.pprint(filteredDatasetWithThisFrequency)
                    print(x)
                    print(n)
                    p = x/n
                    q = 1.0-p

                    yesNum.append(p)
                    noNum.append(q)

                    print("busyness {}, freqOfAsking {}, p {}, q {}, confWidth {}".format(busyness, freqOfAsking, p, q, kForErrorBar*(p*q/n)**0.5))

                    # # Wald Confidence Intervals
                    # errorBars[0].append(kForErrorBar*(p*q/n)**0.5)
                    # errorBars[1].append(kForErrorBar*(p*q/n)**0.5)

                    # Wilson Confidence Intervals
                    xBar = x + kForErrorBar**2.0/2.0
                    nBar = n + kForErrorBar**2.0
                    pBar = xBar/nBar
                    errorBars[0].append(p-(pBar-(kForErrorBar/nBar)*(n*p*q+kForErrorBar**2.0/4.0)**0.5))
                    errorBars[1].append((pBar+(kForErrorBar/nBar)*(n*p*q+kForErrorBar**2.0/4.0)**0.5)-p)
                print("perPersonResponse_numTimesHelped", "kForErrorBar", kForErrorBar, "errorBars", errorBars)
                p1 = axes[i].bar(freqOrder, yesNum, width=0.1, color=[1.0,0.5,0.0])
                axes[i].errorbar(freqOrder, yesNum, yerr=errorBars, color=[0.0,0.0,0.0], ecolor=[0.0,0.0,0.0])
                p2 = axes[i].bar(freqOrder, noNum, width=0.1, bottom=yesNum, color=[0.0,0.5,1.0])
                axes[i].set_title("Busyness: %s" % (busyness))
                axes[i].set_xlabel("Frequency of Asking")
                axes[i].set_ylabel("Proportion")
                axes[i].legend((p1[0], p2[0]), ('Helped Acurately', 'Didn\'t Help Accurately'))
            # plt.show()
            plt.tight_layout(rect=[0, 0.03, 1, 0.95])
            plt.savefig(baseDir + "perPersonResponse_numTimesHelped_clusterI_{}{}.png".format(clusterI, descriptor))
            plt.clf()

        # Make an averaged graph for this cluster
        fig = plt.figure(figsize=(28,16))
        axes = fig.subplots(1,k)
        fig.suptitle('Average Willingness to Help For Cluster {}'.format(clusterI))
        for i in range(k): # create a separate graph per cluster
            indices = np.where(kmeans.labels_ == i)
            filteredDataset = dataset[indices]
            avgValues = np.mean(filteredDataset, axis=0)
            stdDev = np.std(filteredDataset, axis=0)
            axes[i].plot(busynessNumericOrder, avgValues, c="k")
            axes[i].errorbar(busynessNumericOrder, avgValues, yerr=stdDev, ecolor="k")
            axes[i].set_ylim([-0.1,1.1])
            axes[i].set_xlabel("Busyness")
            axes[i].set_ylabel("Likelihood of Helping")
            axes[i].set_title("Cluster {}: {}".format(i, kmeans.cluster_centers_[i, :]))
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "fullScatterWithClusters_averaged{}.png".format(descriptor))
        plt.clf()


if __name__ == "__main__":
    baseDir = "../flask/ec2_outputs/"

    dataset = []
    frequencies = []
    numResponsesDataset = []
    with open(baseDir+"humanHelpUserStudyDataWithExclusion.csv", "r") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        for row in reader:

            frequency = float(row[1])
            frequencies.append(frequency)

            highBusynessWillingnessToHelp = float(row[2])
            mediumBusynessWillingnessToHelp = float(row[3])
            lowBusynessWillingnessToHelp = float(row[4])
            dataset.append([lowBusynessWillingnessToHelp, mediumBusynessWillingnessToHelp, highBusynessWillingnessToHelp])

            reponsesToCount = {}
            totalCount = 0
            for i in range(48, 48+20):
                response = row[i]
                print(response)
                if response not in ["IGNORED", "CANT_HELP", "HELPED_ACCURATELY"]:
                    continue
                if response not in reponsesToCount:
                    reponsesToCount[response] = 0
                reponsesToCount[response] += 1
                totalCount += 1

            numResponsesDatapoint = []
            for response in ["IGNORED", "CANT_HELP", "HELPED_ACCURATELY"]:
                if response in reponsesToCount:
                    numResponsesDatapoint.append(reponsesToCount[response]/totalCount)
                else:
                    numResponsesDatapoint.append(0.0)
            numResponsesDataset.append(numResponsesDatapoint)

    dataset = np.array(dataset)
    frequencies = np.array(frequencies)
    kmeansAnalyzeDataset(
        dataset,
        "_willingnessToHelpByBusyness",
        xlabel='Willingness to Help for Free Time',
        ylabel='Willingness to Help for Medium',
        zlabel='Willingness to Help for High',
        frequencies=frequencies,
        isBusyness=True,
    )

    # numResponsesDataset = np.array(numResponsesDataset)
    # print("numResponsesDataset")
    # pprint.pprint(numResponsesDataset)
    # kmeansAnalyzeDataset(
    #     numResponsesDataset,
    #     "_numResponsesBreakdown",
    #     xlabel='Frequency of IGNORED Responses',
    #     ylabel='Frequency of CANT_HELP Responses',
    #     zlabel='Frequency of HELPED_ACCURATELY Responses',
    #     frequencies=frequencies,
    # )

    # plt.show()
