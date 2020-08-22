import matplotlib.pyplot as plt

baseDir = "../flask/ec2_outputs/"

def getErrorBar(means, waldLower, waldUpper):
    return [[means[i]-waldLower[i] for i in range(len(means))], [waldUpper[i]-means[i] for i in range(len(means))]]

def generateFrequencyGraph():
    frequencies = [.2, .4, .6, .8, 1.0]
    means = [.34, .24, .27, .31, .11]
    waldLower = [.21, .16, .16, .20, .06]
    waldUpper = [.49, .36, .42, .45, .18]

    errorBars = getErrorBar(means, waldLower, waldUpper)

    fig = plt.figure()
    ax = fig.subplots()
    ax.plot(frequencies, means, color=[1.0, 0.5, 0.0])
    ax.errorbar(frequencies, means, yerr=errorBars, color=[1.0, 0.5, 0.0], ecolor="k", capsize=5)
    ax.set_ylim([0.0, 1.0])
    ax.set_title("Frequency")
    ax.set_xlabel("Frequency of Asking")
    ax.set_ylabel("Likelihood of Helping Accurately")
    plt.savefig(baseDir+"spssGEEOutputFrequency.png")
    # plt.show()

def generateBusynessGraph():
    busynesses = [0.0, 1/7.0, 1/3.0]
    means = [.47, .28, .08]
    waldLower = [.39, .22, .05]
    waldUpper = [.55, .36, .13]

    errorBars = getErrorBar(means, waldLower, waldUpper)

    fig = plt.figure()
    ax = fig.subplots()
    ax.plot(busynesses, means, color=[1.0, 0.5, 0.0])
    ax.errorbar(busynesses, means, yerr=errorBars, color=[1.0, 0.5, 0.0], ecolor="k", capsize=5)
    ax.set_ylim([0.0, 1.0])
    ax.set_title("Busyness")
    ax.set_xlabel("Busyness")
    ax.set_ylabel("Likelihood of Helping Accurately")
    plt.savefig(baseDir+"spssGEEOutputBusyness.png")
    # plt.show()

def generateBusynessInteractionGraph():
    busynesses = ["free time", "medium", "high"]
    frequencies = {busyness : [.2, .4, .6, .8, 1.0] for busyness in busynesses}
    means = {
        "free time" : [.51, .44, .50, .61, .31],
        "medium" : [.43, .19, .25, .44, .17],
        "high" : [.14, .15, .13, .07, .02],
    }
    waldLower = {
        "free time" : [.32, .29, .35, .46, .15],
        "medium" : [.26, .11, .13, .30, .07],
        "high" : [.06, .08, .05, .02, .00],
    }
    waldUpper = {
        "free time" : [.69, .59, .65, .75, .52],
        "medium" : [.63, .32, .42, .59, .36],
        "high" : [.32, .27, .27, .20, .08],
    }
    errorBars = {busyness : getErrorBar(means[busyness], waldLower[busyness], waldUpper[busyness]) for busyness in busynesses}

    busynessToColor = {"high":"r", "medium":"b", "free time":"g"}

    fig = plt.figure()
    ax = fig.subplots()
    for busyness in busynesses:
        ax.plot(frequencies[busyness], means[busyness], color=busynessToColor[busyness], label=busyness)
        ax.errorbar(frequencies[busyness], means[busyness], yerr=errorBars[busyness], color=busynessToColor[busyness], ecolor=busynessToColor[busyness], capsize=5)
    ax.set_ylim([0.0, 1.0])
    ax.set_title("Busyness * Frequency of Asking")
    ax.set_xlabel("Frequency of Asking")
    ax.set_ylabel("Likelihood of Helping Accurately")
    ax.legend()
    plt.savefig(baseDir+"spssGEEOutputBusynessFrequencyOfAsking.png")
    # plt.show()

if __name__ == "__main__":
    generateFrequencyGraph()
    generateBusynessGraph()
    generateBusynessInteractionGraph()
