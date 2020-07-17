import matplotlib.pyplot as plt
from enum import Enum

class Busyness(Enum):
    FREE_TIME = 0
    MEDIUM = 1
    HIGH = 2

class Prosociality(Enum):
    LOW = 0 # below the median
    HIGH = 1 # above the median

def getXsAndYs(func, xRange):
    xs, ys = [], []
    for x in xrange:
        xs.append(x)
        ys.append(func, x)
    return xs, ys

def sampleHypothesis(busyness, prosociality):
    """
    Given a busyness and prosociality level, returns a function that takes in a
    frequency of asking for help in [0.2, 1.0] and returns a likelihood of
    helping in [0.0, 1.0]
    """
    def likelihoodOfHelping(frequencyOfAsking):
        """
        Takes in frequencyOfAsking in [0.2, 1.0] and returns likelihood of
        helping in [0.0, 1.0]
        """
        return frequencyOfAsking
    return likelihoodOfHelping

def hypothesis1(busyness, prosociality):
    """
    Hypothesis 1: Neither frequency not prosociality matter
    """
    def likelihoodOfHelping(frequencyOfAsking):
        if busyness == Busyness.HIGH:
            likelihood = 0
        elif busyness == Busyness.MEDIUM:
            likelihood = 0.5
        else:
            likelihood = 1.0
        return likelihood
    return likelihoodOfHelping

if __name__ == "__main__":
    hypothesisToGraph = [hypothesis1]

    colors = ["b", "r", "g", "m", "k"]

    fig = plt.figure(figsize=(8,8))
    axes = fig.subplots(len(hypothesisToGraph), len(Busyness))
    fig.suptitle('RoSAS Results By Frequency')
    for i in range(len(hypothesisToGraph)):
        hypothesis = hypothesisToGraph[i]
        k = 0
        for busyness in Busyness:
            axes[i][k].set_title("Busyness: {}".format(busyness.name))

            for prosociality in Prosociality:
                xs, ys = getXsAndYs(hypothesis(busyness, prosociality), range(0.2, 1.0, 0.05))

            axes[i][k].plot(xs, yw, c=colors[i%len(colors)])
            axes[i].set_xlim([0,1.1])
            axes[i].set_ylim([0,1.1])
            axes[i].set_xlabel("Frequency of Asking")
            axes[i].set_ylabel("Likelihood of Helping")
            k += 1
    # plt.show()
    plt.savefig("../flask/ec2_outputs/rosas.png")

    for i in range(len(hypothesisToGraph)):
