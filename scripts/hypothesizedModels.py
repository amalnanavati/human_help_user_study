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
    for x in xRange:
        xs.append(x)
        ys.append(func(x))
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

def hypothesis2(busyness, prosociality):
    """
    Hypothesis 2: More asking gets more help
    (e.g., shows necessity, annoys people into helping)
    """
    def likelihoodOfHelping(frequencyOfAsking):
        if busyness == Busyness.HIGH:
            likelihood = 0
        elif busyness == Busyness.MEDIUM:
            likelihood = 0.3*frequencyOfAsking+0.5
        else:
            likelihood = 0.2*frequencyOfAsking+0.8
        return likelihood
    return likelihoodOfHelping

def hypothesis3(busyness, prosociality):
    """
    Hypothesis 3: More asking gets less help
    (e.g., annoys people, shows incompetence)
    """
    def likelihoodOfHelping(frequencyOfAsking):
        if busyness == Busyness.HIGH:
            likelihood = 0
        elif busyness == Busyness.MEDIUM:
            likelihood = -0.5*frequencyOfAsking+0.8
        else:
            likelihood = -0.2*frequencyOfAsking+1.0
        return likelihood
    return likelihoodOfHelping

def allIndependentHypothesis(busyness, prosociality):
    """
    Busyness, Frequency, and
    Prosociality are all independent
    """
    def likelihoodOfHelping(frequencyOfAsking):
        if busyness == Busyness.HIGH:
            busynessOffset = 0.7
        elif busyness == Busyness.MEDIUM:
            busynessOffset = 0.4
        else:
            busynessOffset = 0.0

        if prosociality == prosociality.HIGH:
            prosocialityOffset = 0.1
        else:
            prosocialityOffset = 0.0

        return -0.2*frequencyOfAsking+0.2 + busynessOffset + prosocialityOffset

    return likelihoodOfHelping

def prosocialityIndependentHypothesis(busyness, prosociality):
    """
    Busyness and Frequency interact,
    Prosociality is independent
    """
    def likelihoodOfHelping(frequencyOfAsking):
        if busyness == Busyness.HIGH:
            busynessMultiplier = 1.0
        elif busyness == Busyness.MEDIUM:
            busynessMultiplier = 0.5
        else:
            busynessMultiplier = 0.0

        if prosociality == prosociality.HIGH:
            prosocialityOffset = 0.1
        else:
            prosocialityOffset = 0.0

        return busynessMultiplier*(-0.2*frequencyOfAsking+0.9) + prosocialityOffset

    return likelihoodOfHelping

def allInteractHypothesis(busyness, prosociality):
    """
    Busyness, Frequency, and
    Prosociality interact
    """
    def likelihoodOfHelping(frequencyOfAsking):
        if busyness == Busyness.HIGH:
            busynessMultiplier = 1.0
        elif busyness == Busyness.MEDIUM:
            busynessMultiplier = 0.5
        else:
            busynessMultiplier = 0.0

        if prosociality == prosociality.HIGH:
            prosocialityMultiplier = 1.0
        else:
            prosocialityMultiplier = 0.7

        return prosocialityMultiplier*busynessMultiplier*(-0.2*frequencyOfAsking+0.9)

    return likelihoodOfHelping

if __name__ == "__main__":
    colors = ["b", "r", "g", "m", "k"]

    # noProsocialityHypotheses = [hypothesis1, hypothesis2, hypothesis3]
    #
    # fig = plt.figure(figsize=(16,4))
    # axes = fig.subplots(1, len(noProsocialityHypotheses))
    # # if len(noProsocialityHypotheses) == 1:
    # #     axes = [axes]
    # fig.suptitle('Predicted Graphs Across Hypotheses')
    # for i in range(len(noProsocialityHypotheses)):
    #     hypothesis = noProsocialityHypotheses[i]
    #     k = 0
    #     for busyness in Busyness:
    #         title = ""
    #         title += hypothesis.__doc__#+"\n"
    #         # title += "Busyness {}".format(busyness.name)
    #         axes[i].set_title(title)
    #
    #         # j = 0
    #         # for prosociality in Prosociality:
    #         xs, ys = getXsAndYs(hypothesis(busyness, Prosociality.LOW), [x/100 for x in range(20, 105, 5)])
    #         axes[i].plot(xs, ys, c=colors[k%len(colors)], label="Busy {}".format(busyness.name))
    #         axes[i].set_xlim([-0.19,1.0])
    #         axes[i].set_ylim([-0.1,1.1])
    #         axes[i].set_xlabel("Frequency of Asking")
    #         axes[i].set_ylabel("Likelihood of Helping")
    #         axes[i].legend()
    #             # j += 1
    #         k += 1
    # plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    # plt.savefig("../flask/ec2_outputs/hypotheses.png")

    hypotheses = [allIndependentHypothesis, prosocialityIndependentHypothesis, allInteractHypothesis]

    fig = plt.figure(figsize=(20,4))
    axes = fig.subplots(1, len(hypotheses))
    fig.suptitle('Predicted Graphs Across Hypotheses')
    for i in range(len(hypotheses)):
        hypothesis = hypotheses[i]
        k = 0
        for busyness in Busyness:
            for prosociality in Prosociality:
                title = ""
                title += hypothesis.__doc__#+"\n"
                # title += "Busyness {}".format(busyness.name)
                axes[i].set_title(title)

                # j = 0
                # for prosociality in Prosociality:
                xs, ys = getXsAndYs(hypothesis(busyness, prosociality), [x/100 for x in range(20, 105, 5)])
                axes[i].plot(xs, ys, c=colors[k%len(colors)], label="Busy {}, Prosoc {}".format(busyness.name, prosociality.name))
                axes[i].set_xlim([-0.0,1.0])
                axes[i].set_ylim([-0.1,1.1])
                axes[i].set_xlabel("Frequency of Asking")
                axes[i].set_ylabel("Likelihood of Helping")
                axes[i].legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
                    # j += 1
                k += 1
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig("../flask/ec2_outputs/hypotheses.png")
