import csv
import math
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm

if __name__ == "__main__":
    # Read in the per response data
    X, Y = [], []
    totalNumRecentTimesDidNotHelp = 0
    count = 0
    with open("../flask/ec2_outputs/humanHelpUserStudyPerResponseData.csv", "r") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        for row in reader:
            uuid, taskI, busyness, freqOfAsking, freqOfHelpingAccurately, responseNumber, prosociality, slowness, busynessNumeric, numRecentTimesDidNotHelp, age = row
            X.append([float(busynessNumeric), float(freqOfAsking), int(numRecentTimesDidNotHelp)])
            Y.append(int(responseNumber))
            totalNumRecentTimesDidNotHelp += int(numRecentTimesDidNotHelp)
            count += 1
    meanNumRecentTimesDidNotHelp = totalNumRecentTimesDidNotHelp / count

    # Load the model
    interceptFixed = 0.674073
    interceptRandomMin = -1.62701
    interceptRandomMean = 0.09246
    interceptRandomMax = 4.18524
    busynessCoefficient = -5.734255
    numRecentTimesDidNotHelpCoefficient = -0.209316
    busynessFreqOfAskingCoefficient = -8.425234

    def probabilityOfHelpingAccurately(busyness, freqOfAsking, numRecentTimesDidNotHelp, interceptRandom=None):
        if interceptRandom is None:
            interceptRandom = interceptRandomMean
        logit = interceptFixed + interceptRandom + busynessCoefficient*busyness + numRecentTimesDidNotHelpCoefficient*numRecentTimesDidNotHelp + busynessFreqOfAskingCoefficient*busyness*freqOfAsking
        probability = math.e**logit / (1 + math.e**logit)
        return probability

    # Generate the graph of the surface
    busynessRange = np.arange(0.0, 1.0, 0.01)
    interceptRandomRange = np.arange(interceptRandomMin, interceptRandomMax, 0.05)

    busyness, interceptRandom = np.meshgrid(busynessRange, interceptRandomRange)
    freqOfAsking = 0.6
    probabilitOfHelping = probabilityOfHelpingAccurately(busyness, freqOfAsking, meanNumRecentTimesDidNotHelp, interceptRandom)

    fig = plt.figure()
    ax = fig.gca(projection='3d')
    # surf = ax.plot_surface(busyness, interceptRandom, probabilitOfHelping, cmap=cm.coolwarm,
    #                         linewidth=0, antialiased=False)
    # fig.colorbar(surf, shrink=0.5, aspect=5)
    surf = ax.plot_wireframe(busyness, interceptRandom, probabilitOfHelping)
    ax.set_zlim(-0.01, 1.01)
    ax.set_xlabel("Busyness")
    ax.set_ylabel("Random Intercept")
    ax.set_zlabel("Prob of Helping Accurately")
    plt.show()
