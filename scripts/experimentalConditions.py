# This import registers the 3D projection, but is otherwise unused.
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import
import numpy as np
import pprint
import matplotlib.pyplot as plt

class Sequence(object):
    def __init__(self, busyness, robotSeen, helpRequests):
        """
        busyness is an array of size (n,), robotSeen is a boolean array of size
        (n,), and helpRequests is a boolean array of size (m,) where m is the number
        of True values in robotSeen
        """
        self.busyness = busyness.copy()
        self.robotSeen = robotSeen.copy()
        self.seenIndices = np.where(self.robotSeen)[0]
        self.helpRequests = helpRequests.copy()

        self.getDatapoints()

    def getDatapoints(self):
        self.datapoints = []

        numTimesAsked = 0
        numTimesSeen = 0
        numTimesSeenSinceLastAsked = 0

        for i in range(self.seenIndices.shape[0]):
            seqI = self.seenIndices[i]
            askedForHelp = self.helpRequests[i]

            numTimesSeen += 1

            if askedForHelp:
                numTimesAsked += 1

                # Compute the datapoint
                frequency = numTimesAsked / numTimesSeen
                busynessVal = self.busyness[seqI]
                self.datapoints.append((frequency, numTimesSeenSinceLastAsked, busynessVal))
                # self.datapoints.append((numTimesAsked, numTimesSeen, numTimesSeenSinceLastAsked, busynessVal))

                numTimesSeenSinceLastAsked = 0
            else:
                numTimesSeenSinceLastAsked += 1

        return self.datapoints

    # def isSimilarTo(seq1, seq0):
    #     for data1 in seq1.datapoints:
    #         for data0 in seq0.datapoints:
    #             if data1 == data0:
    #                 return True
    #     return False

    def __repr__(self):
        retval = "B | "
        for busynessVal in self.busyness:
            retval += str(busynessVal) + " | "
        retval += "\n S | "
        for robotSeenVal in self.robotSeen:
            if robotSeenVal:
                retval += "* | "
            else:
                retval += "  | "
        retval += "\n H | "
        j = 0
        for i in range(len(self.busyness)):
            if i == self.seenIndices[j]:
                if self.helpRequests[j]:
                    retval += "* | "
                else:
                    retval += "  | "
                j += 1
            else:
                retval += "  | "
        retval += "\n F | "+str(self.datapoints)
        return retval

class CollectionOfSequences(object):
    def __init__(self):
        self.sequences = []
        self.totalSequences = 0
        self.totalDatapoints = 0

        self.datapointToSeqI = {}

        self.datapointToNormalizedNumSeq = {}

        self.similarSeqI = []

    def addSequence(self, sequence):
        self.similarSeqI.append(set())
        for datapoint in sequence.datapoints:
            if datapoint in self.datapointToSeqI:
                for seqI in self.datapointToSeqI[datapoint]:
                    self.similarSeqI[seqI].add(len(self.similarSeqI)-1)
                    self.similarSeqI[-1].add(seqI)

        for datapoint in sequence.datapoints:
            if datapoint not in self.datapointToSeqI:
                self.datapointToSeqI[datapoint] = []
                self.datapointToNormalizedNumSeq[datapoint] = 0
            self.datapointToSeqI[datapoint].append(len(self.sequences))
            self.datapointToNormalizedNumSeq[datapoint] += 1.0/np.count_nonzero(sequence.helpRequests)

        self.sequences.append(sequence)

        self.totalSequences += 1
        self.totalDatapoints += len(sequence.datapoints)

def getProbabilities(busynesses, robotSeen):
    """
    busyness is an array of size (n,), and robotSeen is a boolean array of size
    (n,). This function generates all the possibilities for when the robot asks
    for help, calculates the (frequency, time_since_last_asked, and busyness) tuples
    for them, and determines the probability of those.
    """
    seenIndices = np.where(robotSeen)[0]

    helpRequests = np.zeros(seenIndices.shape, dtype=np.bool)

    sequences = CollectionOfSequences()

    def getAllBinarySequences(sequence, i):
        if (i >= sequence.shape[0]):
            for busyness in busynesses:
                sequences.addSequence(Sequence(busyness, robotSeen, sequence))
        else:
            sequence[i] = False
            getAllBinarySequences(sequence, i+1)
            sequence[i] = True
            getAllBinarySequences(sequence, i+1)

    getAllBinarySequences(helpRequests, 0)

    # pprint.pprint(sequences.datapointToSeqI)
    print("---------------------------------------------------------------------")
    sortedDatapointToSeqI = sorted({k : len(v) for k, v in sequences.datapointToSeqI.items()}.items(), key=lambda item: item[1], reverse=True)
    pprint.pprint(sortedDatapointToSeqI)
    # pprint.pprint(sequences.sequences)


    seqIWithMostSimilarity = sorted({i : len(sequences.similarSeqI[i]) for i in range(len(sequences.similarSeqI))}.items(), key=lambda item: item[1], reverse=True)
    n = 2048
    sequencesWithMostSimilarity = [sequences.sequences[seqIWithMostSimilarity[i][0]] for i in range(n)]
    datapointsWithMostSimilarity = {}
    for sequence in sequencesWithMostSimilarity:
        for frequency, numTimesSeenSinceLastAsked, busynessVal in sequence.datapoints:
        # for numTimesAsked, numTimesSeen, numTimesSeenSinceLastAsked, busynessVal in sequence.datapoints:
        #     frequency = numTimesAsked / numTimesSeen
            newDatapoint = (frequency, numTimesSeenSinceLastAsked)
            if newDatapoint not in datapointsWithMostSimilarity:
                datapointsWithMostSimilarity[newDatapoint] = 0
            datapointsWithMostSimilarity[newDatapoint] += 1
    print("---------------------------------------------------------------------")
    pprint.pprint(seqIWithMostSimilarity[:n])
    print("---------------------------------------------------------------------")
    pprint.pprint(sequencesWithMostSimilarity)
    print("---------------------------------------------------------------------")
    sortedDatapointsWithMostSimilarity = sorted({k : v for k, v in datapointsWithMostSimilarity.items()}.items(), key=lambda item: item[1], reverse=True)
    pprint.pprint(sortedDatapointsWithMostSimilarity)

    print("Lowest Similarity: ", seqIWithMostSimilarity[n])
    print("Total Datapoints: ", sequences.totalDatapoints)
    print("Total Sequences: ", sequences.totalSequences)

    print("Sum: ", sum([v/sequences.totalSequences for k, v in sequences.datapointToNormalizedNumSeq.items()]))

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter([k[0] for k, v in sequences.datapointToNormalizedNumSeq.items()], [k[1] for k, v in sequences.datapointToNormalizedNumSeq.items()], [v/sequences.totalSequences for k, v in sequences.datapointToNormalizedNumSeq.items()], marker='o')
    ax.set_xlabel('Frequency')
    ax.set_ylabel('Time Since Last Asked')
    ax.set_zlabel('Count')
    plt.show()

    # sortedNumSimilarSequences = sorted([len(similarSeqISet) for similarSeqISet in sequences.similarSeqI], reverse=True)
    # plt.plot([k[0]/k[1] for k, v in sortedDatapointToSeqI], [v for k, v in sortedDatapointToSeqI], 'bo')
    # plt.show()

    # sortedNumSimilarSequences = sorted([len(similarSeqISet) for similarSeqISet in sequences.similarSeqI], reverse=True)
    # plt.plot([k[0] for k, v in sortedDatapointsWithMostSimilarity], [v for k, v in sortedDatapointsWithMostSimilarity], 'bo')
    # plt.show()

    # sortedNumSimilarSequences = sorted([len(similarSeqISet) for similarSeqISet in sequences.similarSeqI], reverse=True)
    # plt.plot(range(len(sortedNumSimilarSequences)), sortedNumSimilarSequences, 'b--')
    # plt.show()


if __name__ == "__main__":
    # busynesses = [
    #     np.array([2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0]),
    #     np.array([1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2]),
    #     np.array([0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1,0,2,1]),
    # ]
    busynesses = [
        np.ones((12,), dtype=np.int),
    ]
    # robotSeen = np.array([False, True,False, True,False, True,False, True,False, True,False, True,False, True,False, True,False, True,False, True,False, True,False, True])
    robotSeen = np.ones((12,), dtype=np.bool)
    getProbabilities(busynesses, robotSeen)
