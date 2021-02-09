import csv, pprint, os, json, pickle
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from mpl_toolkits.mplot3d import Axes3D
from enum import Enum
import numpy as np
import datetime
import traceback
import shutil
import scipy.stats
import random
import time
import math

import pandas as pd
import seaborn as sns
sns.set(style="darkgrid", font="Palatino")
# mpl.rcParams['text.color'] = 'white'
# sns.set(style="whitegrid")
# sns.set_style("white")
# sns.set(style="whitegrid",font_scale=2)
import ptitprince as pt

def readCSV(filepath):
    surveyData = {}

    with open(filepath, "r") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        headersToIndex = {headers[i] : i for i in range(len(headers))}
        for row in reader:
            uuid = row[headersToIndex["User ID"]]
            surveyData[uuid] = {colName : row[i] for colName, i in headersToIndex.items()}

    return surveyData


def computeOverallProportionHelpfulness(hybridNumAsking, hybridNumHelping, comparisonNumAsking, comparisonNumHelping):
    # retval = (hybridNumHelping + comparisonNumHelping) / (hybridNumAsking + comparisonNumAsking)
    retval = hybridNumHelping / hybridNumAsking
    # print("overallProportionHelpfulness", retval)
    return retval

def makeGraphs(individualData, contextualData, descriptor=""):
    ############################################################################
    # Make RoSAS Graphs
    ############################################################################
    rosasDifferences = []
    rosasRawDifferences = []
    for baseline, data in [("Hybrid v. Individual", individualData), ("Hybrid v. Contextual", contextualData)]:
        for uuid in data:
            for rosasCategory in ["Competence", "Warmth", "Discomfort", "Curiosity"]:
                hybridVal = float(data[uuid]["Hybrid RoSAS "+rosasCategory])
                comparisonVal = float(data[uuid]["Comparison RoSAS "+rosasCategory])
                rosasDifferences.append((baseline, rosasCategory, hybridVal-comparisonVal))
            for rosasCategory in ["Reliable", "Competent", "Knowledgeable", "Interactive", "Responsive", "Capable", "Organic", "Sociable", "Emotional", "Compassionate", "Happy", "Feeling", "Awkward", "Scary", "Strange", "Awful", "Dangerous", "Aggressive", "Investigative", "Inquisitive", "Curious"]:
                hybridVal = float(data[uuid]["Hybrid RoSAS Raw "+rosasCategory])
                comparisonVal = float(data[uuid]["Comparison RoSAS Raw "+rosasCategory])
                rosasRawDifferences.append((baseline, rosasCategory, hybridVal-comparisonVal))
    rosasDifferences = pd.DataFrame(rosasDifferences, columns = ['Baseline', "RoSAS Category", "Difference"])
    rosasRawDifferences = pd.DataFrame(rosasRawDifferences, columns = ['Baseline', "RoSAS Category", "Difference"])

    pal = [(77/255,175/255,74/255),(55/255,126/255,184/255),(228/255,26/255,28/255)]#sns.color_palette()#"tab10") # sns.color_palette(n_colors=3) # "colorblind" # "Set2"
    # pal = [pal[9], pal[3], pal[8]]
    sigma = 0.2

    for rosasDescriptor, data, multiplier in [("Combined", rosasDifferences, 1), ("Raw", rosasRawDifferences, 2)]:
        # RoSAS Differences Barplot
        fig = plt.figure(figsize=(6*multiplier,4*multiplier))
        # fig.patch.set_facecolor('k')
        ax = fig.subplots(1, 1)
        fig.suptitle("Differences Amongst RoSAS Scores")
        g = sns.barplot(x = "RoSAS Category", y = "Difference", data = data, hue="Baseline", alpha=1,
                         ax = ax)
        handles, labels = ax.get_legend_handles_labels()
        l = ax.legend(handles=handles[0:], labels=labels[0:], bbox_to_anchor=(1.05, 1), loc='upper left')#, facecolor='k', edgecolor='darkgrey')
        ax.set_xlabel('RoSAS Category')
        ax.set_ylabel('Hybrid - Baseline Difference')
        g.set_xticklabels(g.get_xticklabels(), rotation=30)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "rosas_difference_barplot_{}_{}.png".format(rosasDescriptor, descriptor))
        plt.clf()

    ############################################################################
    # Make Forced Choice Q Graphs
    ############################################################################
    forcedChoiceQData = []
    for baseline, data in [("Hybrid v. Individual", individualData), ("Hybrid v. Contextual", contextualData)]:
        for uuid in data:
            for forcedChoiceQ in ["Which robot asked for help more times?", "Which robot asked for help at more appropriate times?", "Which robot respected your time?", "Which robot did you prefer interacting with?", "Which robot would you be more willing to help?", "Which robot was more annoying?", "Which robot was more likeable?", "Which robot was more competent?", "Which robot was more stubborn?", "Which robot was more curious?", "Which robot was more polite?", "Which robot inconvenienced you more?", "Which robot would you be more willing to help in the future?", "Which robot was better at adapting its behavior to you as an individual?", "Which robot was better at adapting its behavior to the situation(s) you were in?", "Which robot did you help more?", "Which robot did you not help more (e.g. saying \"Can't Help\" or ignoring it)?"]:
                val = float(data[uuid][forcedChoiceQ])
                forcedChoiceQData.append((baseline, forcedChoiceQ, val))
    forcedChoiceQData = pd.DataFrame(forcedChoiceQData, columns = ['Baseline', "Forced Choice Question", "Value"])

    pal = [(77/255,175/255,74/255),(55/255,126/255,184/255),(228/255,26/255,28/255)]#sns.color_palette()#"tab10") # sns.color_palette(n_colors=3) # "colorblind" # "Set2"
    # pal = [pal[9], pal[3], pal[8]]
    sigma = 0.2

    # Forced Choice Qs Barplot
    fig = plt.figure(figsize=(12,15))
    # fig.patch.set_facecolor('k')
    ax = fig.subplots(1, 1)
    fig.suptitle("Forced Choice Q Results")
    g = sns.barplot(x = "Forced Choice Question", y = "Value", data = forcedChoiceQData, hue="Baseline", alpha=1,
                     ax = ax)
    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:], bbox_to_anchor=(1.05, 1), loc='upper left')#, facecolor='k', edgecolor='darkgrey')
    ax.set_xlabel('Forced Choice Question')
    ax.set_ylabel('Response')
    g.set_xticklabels(g.get_xticklabels(), rotation=90)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "forced_choice_qs_barplot_{}.png".format(descriptor))
    plt.clf()

    ############################################################################
    # Make NASA-TLX
    ############################################################################
    nasaTLXDifferences = []
    for baseline, data in [("Hybrid v. Individual", individualData), ("Hybrid v. Contextual", contextualData)]:
        for uuid in data:
            for nasaTLXCategory in ["Mental Demand", "Physical Demand", "Temporal Demand", "Performance", "Effort", "Frustration"]:
                hybridVal = float(data[uuid]["Hybrid NASA TLX "+nasaTLXCategory])
                comparisonVal = float(data[uuid]["Comparison NASA TLX "+nasaTLXCategory])
                nasaTLXDifferences.append((baseline, nasaTLXCategory, hybridVal-comparisonVal))
    nasaTLXDifferences = pd.DataFrame(nasaTLXDifferences, columns = ['Baseline', "NASA TLX Category", "Difference"])

    pal = [(77/255,175/255,74/255),(55/255,126/255,184/255),(228/255,26/255,28/255)]#sns.color_palette()#"tab10") # sns.color_palette(n_colors=3) # "colorblind" # "Set2"
    # pal = [pal[9], pal[3], pal[8]]
    sigma = 0.2

    # NASA TLX Differences Barplot
    fig = plt.figure(figsize=(12,8))
    # fig.patch.set_facecolor('k')
    ax = fig.subplots(1, 1)
    fig.suptitle("Differences Amongst RoSAS Scores")
    g = sns.barplot(x = "NASA TLX Category", y = "Difference", data = nasaTLXDifferences, hue="Baseline", alpha=1,
                     ax = ax)
    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:], bbox_to_anchor=(1.05, 1), loc='upper left')#, facecolor='k', edgecolor='darkgrey')
    ax.set_xlabel('NASA TLX Category')
    ax.set_ylabel('Hybrid - Baseline Difference')
    g.set_xticklabels(g.get_xticklabels(), rotation=30)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "nasa_tlx_difference_barplot_{}_{}.png".format(rosasDescriptor, descriptor))
    plt.clf()

    ############################################################################
    # Make Graphs of Objective Measures
    ############################################################################
    gid_to_policy_descriptor = ["Hybrid", "Contextual", "Individual"]

    metricToYLabel = {
        "cumulativeReward" : "Cumulative Reward",
        "numCorrectRooms" : "Num Correct Rooms",
        "numAsking" : "Num Asking",
        "numHelping" : "Num Helping",
        "numHelpingRejected" : "Num Helping Rejected",
    }

    metricToTitle = {
        "cumulativeReward" : "Cumulative Reward Across Policies",
        "numCorrectRooms" : "Num Correct Rooms Across Policies",
        "numAsking" : "Num Asking Across Policies",
        "numHelping" : "Num Helping Across Policies",
        "numHelpingRejected" : "Num Helping Rejected Across Policies",
    }

    metricsToData = {
        "cumulativeReward" : [],
        "numCorrectRooms" : [],
        "numAsking" : [],
        "numHelping" : [],
        "numHelpingRejected" : [],
    }

    metricsToDataPaired = {
        "cumulativeReward" : [],
        "numCorrectRooms" : [],
        "numAsking" : [],
        "numHelping" : [],
        "numHelpingRejected" : [],
    }

    metricsToDataDifference = {
        "cumulativeReward" : [],
        "numCorrectRooms" : [],
        "numAsking" : [],
        "numHelping" : [],
        "numHelpingRejected" : [],
    }

    proportionAskingData = []
    proportionHelpingData = []
    proportionAskingHelpingData = []
    numHelpingRejectedData = []
    numAskingHelpingJitter = []
    numAskingHelpingJitterPaired = []
    numAskingHelpingBelief = []
    jitterNoiseStd = 0.5
    numMeanFinalBeliefBuckets = 5
    minMeanFinalBelief = None
    maxMeanFinalBelief = None
    for baseline, data in [("Hybrid v. Individual", individualData), ("Hybrid v. Contextual", contextualData)]:
        for uuid in data:
            hybridMeanFinalBelief = float(data[uuid]["Hybrid Mean Final Belief"])
            if minMeanFinalBelief is None or hybridMeanFinalBelief < minMeanFinalBelief:
                minMeanFinalBelief = hybridMeanFinalBelief
            if maxMeanFinalBelief is None or hybridMeanFinalBelief > maxMeanFinalBelief:
                maxMeanFinalBelief = hybridMeanFinalBelief
    print("minMeanFinalBelief", minMeanFinalBelief, "maxMeanFinalBelief", maxMeanFinalBelief)
    meanFinalBeliefBucketWidth = (maxMeanFinalBelief-minMeanFinalBelief)/numMeanFinalBeliefBuckets
    meanFinalBeliefBuckets = []
    for i in range(numMeanFinalBeliefBuckets):
        lower = minMeanFinalBelief + i*meanFinalBeliefBucketWidth
        upper = minMeanFinalBelief + (i+1)*meanFinalBeliefBucketWidth
        if i < numMeanFinalBeliefBuckets-1:
            upper -= 0.01
        meanFinalBeliefBuckets.append("%.2f - %.2f" % (lower, upper))
    print("meanFinalBeliefBuckets", meanFinalBeliefBuckets)

    numAskingBuckets = 5
    minNumAsking = 0
    maxNumAsking = 20
    numAskingBucketWidth = (maxNumAsking-minNumAsking)/numAskingBuckets
    numAskingBucketNames = []
    for i in range(numAskingBuckets):
        lower = minNumAsking + i*numAskingBucketWidth
        upper = minNumAsking + (i+1)*numAskingBucketWidth
        if i < numAskingBuckets-1:
            upper -= 0.01
        numAskingBucketNames.append("%.2f - %.2f" % (lower, upper))
    print("numAskingBucketNames", numAskingBucketNames)

    numHelpingBuckets = 4
    minNumHelping = 0
    maxNumHelping = 20
    numHelpingBucketWidth = (maxNumHelping-minNumHelping)/numHelpingBuckets
    numHelpingBucketNames = []
    for i in range(numHelpingBuckets):
        lower = minNumHelping + i*numHelpingBucketWidth
        upper = minNumHelping + (i+1)*numHelpingBucketWidth
        if i < numHelpingBuckets-1:
            upper -= 0.01
        numHelpingBucketNames.append("%.2f - %.2f" % (lower, upper))
    print("numHelpingBucketNames", numHelpingBucketNames)

    numOverallProportionHelpfulnessBuckets = 5
    minOverallProportionHelpfulness = None
    maxOverallProportionHelpfulness = None
    for baseline, data in [("Hybrid v. Individual", individualData), ("Hybrid v. Contextual", contextualData)]:
        for uuid in data:

            hybridNumAsking = int(data[uuid]["Hybrid Num Asking"])
            hybridNumHelping = int(data[uuid]["Hybrid Num Helping"])
            comparisonNumAsking = int(data[uuid]["Comparison Num Asking"])
            comparisonNumHelping = int(data[uuid]["Comparison Num Helping"])

            overallProportionHelpfulness = computeOverallProportionHelpfulness(hybridNumAsking, hybridNumHelping, comparisonNumAsking, comparisonNumHelping)

            if minOverallProportionHelpfulness is None or overallProportionHelpfulness < minOverallProportionHelpfulness:
                minOverallProportionHelpfulness = overallProportionHelpfulness
            if maxOverallProportionHelpfulness is None or overallProportionHelpfulness > maxOverallProportionHelpfulness:
                maxOverallProportionHelpfulness = overallProportionHelpfulness
    print("minOverallProportionHelpfulness", minOverallProportionHelpfulness, "maxOverallProportionHelpfulness", maxOverallProportionHelpfulness)
    overallProportionHelpfulnessBucketWidth = (maxOverallProportionHelpfulness-minOverallProportionHelpfulness)/numOverallProportionHelpfulnessBuckets
    overallProportionHelpfulnessBuckets = []
    for i in range(numOverallProportionHelpfulnessBuckets):
        lower = minOverallProportionHelpfulness + i*overallProportionHelpfulnessBucketWidth
        upper = minOverallProportionHelpfulness + (i+1)*overallProportionHelpfulnessBucketWidth
        # if i < numOverallProportionHelpfulnessBuckets-1:
        #     upper -= 0.01
        overallProportionHelpfulnessBuckets.append("[%.2f, %.2f)" % (lower, upper))
    print("overallProportionHelpfulnessBuckets", overallProportionHelpfulnessBuckets)

    for baseline, data in [("Hybrid v. Individual", individualData), ("Hybrid v. Contextual", contextualData)]:
        for uuid in data:
            for metric in metricsToData:
                csvMetric = metricToYLabel[metric]
                hybridVal = float(data[uuid]["Hybrid "+csvMetric])
                comparisonVal = float(data[uuid]["Comparison "+csvMetric])
                metricsToData[metric].append(["Hybrid", hybridVal, baseline])
                metricsToData[metric].append([baseline[10:], comparisonVal, baseline])
                metricsToDataPaired[metric].append([baseline, hybridVal, comparisonVal])
                metricsToDataDifference[metric].append([hybridVal-comparisonVal, baseline])
            hybridNumAsking = int(data[uuid]["Hybrid Num Asking"])
            hybridNumHelping = int(data[uuid]["Hybrid Num Helping"])
            comparisonNumAsking = int(data[uuid]["Comparison Num Asking"])
            comparisonNumHelping = int(data[uuid]["Comparison Num Helping"])
            numAskingHelpingJitter.append(["Hybrid", hybridNumAsking+(random.random()-0.5)*jitterNoiseStd, hybridNumHelping+(random.random()-0.5)*jitterNoiseStd, (hybridNumHelping+(random.random()-0.5)*jitterNoiseStd)/hybridNumAsking])
            numAskingHelpingJitter.append([baseline[10:], comparisonNumAsking+(random.random()-0.5)*jitterNoiseStd, comparisonNumHelping+(random.random()-0.5)*jitterNoiseStd, (comparisonNumHelping+(random.random()-0.5)*jitterNoiseStd)/comparisonNumAsking])
            numAskingHelpingJitterPaired.append([baseline, hybridNumAsking+(random.random()-0.5)*jitterNoiseStd, hybridNumHelping+(random.random()-0.5)*jitterNoiseStd, comparisonNumAsking+(random.random()-0.5)*jitterNoiseStd, comparisonNumHelping+(random.random()-0.5)*jitterNoiseStd])

            overallProportionHelpfulness = computeOverallProportionHelpfulness(hybridNumAsking, hybridNumHelping, comparisonNumAsking, comparisonNumHelping)
            hybridMeanFinalBelief = float(data[uuid]["Hybrid Mean Final Belief"])
            # comparisonMeanFinalBelief = float(data[uuid]["Comparison Mean Final Belief"])
            if hybridMeanFinalBelief == maxMeanFinalBelief:
                hybridMeanFinalBeliefBucketI = numMeanFinalBeliefBuckets-1
            else:
                hybridMeanFinalBeliefBucketI = int(math.floor((hybridMeanFinalBelief-minMeanFinalBelief)/meanFinalBeliefBucketWidth))

            if hybridNumAsking == maxNumAsking:
                hybridNumAskingBucketI = numAskingBuckets-1
            else:
                hybridNumAskingBucketI = int(math.floor((hybridNumAsking-minNumAsking)/numAskingBucketWidth))

            if comparisonNumAsking == maxNumAsking:
                comparisonNumAskingBucketI = numAskingBuckets-1
            else:
                comparisonNumAskingBucketI = int(math.floor((comparisonNumAsking-minNumAsking)/numAskingBucketWidth))

            if hybridNumHelping == maxNumHelping:
                hybridNumHelpingBucketI = numHelpingBuckets-1
            else:
                hybridNumHelpingBucketI = int(math.floor((hybridNumHelping-minNumHelping)/numHelpingBucketWidth))

            if overallProportionHelpfulness == maxOverallProportionHelpfulness:
                overallProportionHelpfulnessBucketI = numOverallProportionHelpfulnessBuckets-1
            else:
                overallProportionHelpfulnessBucketI = int(math.floor((overallProportionHelpfulness-minOverallProportionHelpfulness)/overallProportionHelpfulnessBucketWidth))
            # print("overallProportionHelpfulness", overallProportionHelpfulness, "overallProportionHelpfulnessBuckets[overallProportionHelpfulnessBucketI]", overallProportionHelpfulnessBuckets[overallProportionHelpfulnessBucketI])

            numAskingHelpingBelief.append(["Hybrid", hybridNumAsking, hybridNumHelping, hybridNumHelping/hybridNumAsking, hybridNumAsking-hybridNumHelping, hybridNumHelping-hybridNumAsking, hybridMeanFinalBelief, meanFinalBeliefBuckets[hybridMeanFinalBeliefBucketI], numAskingBucketNames[hybridNumAskingBucketI], numAskingBucketNames[hybridNumAskingBucketI], numHelpingBucketNames[hybridNumHelpingBucketI], overallProportionHelpfulnessBuckets[overallProportionHelpfulnessBucketI]])
            numAskingHelpingBelief.append([baseline[10:], comparisonNumAsking, comparisonNumHelping, comparisonNumHelping/comparisonNumAsking, comparisonNumAsking-comparisonNumHelping, comparisonNumHelping-comparisonNumAsking, hybridMeanFinalBelief, meanFinalBeliefBuckets[hybridMeanFinalBeliefBucketI], numAskingBucketNames[hybridNumAskingBucketI], numAskingBucketNames[comparisonNumAskingBucketI], numHelpingBucketNames[hybridNumHelpingBucketI], overallProportionHelpfulnessBuckets[overallProportionHelpfulnessBucketI]])

            for busyness in range(1,7):
                busynessFloat = (busyness-1)/5.0*0.4

                hybridAskingP = float(data[uuid]["Hybrid Busyness "+str(busyness)+" Proportion Asking"])
                comparisonAskingP = float(data[uuid]["Comparison Busyness "+str(busyness)+" Proportion Asking"])
                proportionAskingData.append(["Hybrid", busynessFloat, hybridAskingP])
                proportionAskingData.append([baseline[10:], busynessFloat, comparisonAskingP])

                hybridHelpingP = float(data[uuid]["Hybrid Busyness "+str(busyness)+" Proportion Helping"])
                comparisonHelpingP = float(data[uuid]["Comparison Busyness "+str(busyness)+" Proportion Helping"])
                proportionHelpingData.append(["Hybrid", busynessFloat, hybridHelpingP])
                proportionHelpingData.append([baseline[10:], busynessFloat, comparisonHelpingP])

                if hybridAskingP > 0: proportionAskingHelpingData.append(["Hybrid", busynessFloat, hybridHelpingP/hybridAskingP])
                if comparisonAskingP > 0: proportionAskingHelpingData.append([baseline[10:], busynessFloat, comparisonHelpingP/comparisonAskingP])

                hybridNumHelpingRejected = float(data[uuid]["Hybrid Busyness "+str(busyness)+" Num Helping Rejected"])
                comparisonNumHelpingRejected = float(data[uuid]["Comparison Busyness "+str(busyness)+" Num Helping Rejected"])
                numHelpingRejectedData.append(["Hybrid", busynessFloat, hybridNumHelpingRejected])
                numHelpingRejectedData.append([baseline[10:], busynessFloat, comparisonNumHelpingRejected])

    for metric in metricsToData:
        metricsToData[metric] = pd.DataFrame(metricsToData[metric], columns = ['Policy', metric, 'Baseline'])
        metricsToDataPaired[metric] = pd.DataFrame(metricsToDataPaired[metric], columns = ['Baseline', "Hybrid "+metric, "Comparison "+metric])
        metricsToDataDifference[metric] = pd.DataFrame(metricsToDataDifference[metric], columns = [metric+" Difference", 'Baseline'])
    numAskingHelpingJitter = pd.DataFrame(numAskingHelpingJitter, columns = ['Policy', 'Num Asking', 'Num Helping', 'Num Helping / Num Asking'])
    # numAskingHelpingJitterPaired = pd.DataFrame(numAskingHelpingJitterPaired, columns = ['Baseline', 'Hybrid Num Asking', 'Hybrid Num Helping', 'Comparison Num Asking', 'Comparison Num Helping'])
    numAskingHelpingBelief = pd.DataFrame(numAskingHelpingBelief, columns = ['Policy', 'Num Asking', 'Num Helping', 'Num Helping / Num Asking', 'Num Helping Rejected', 'Negative Num Helping Rejected', 'Mean Final Belief', 'Mean Final Belief Bucket', 'Hybrid Num Asking Bucket', 'Num Asking Bucket', 'Hybrid Num Helping Bucket', 'Overall Human Proportion Helpfulness'])
    proportionAskingData = pd.DataFrame(proportionAskingData, columns = ['Policy', 'Busyness', 'Proportion'])
    proportionHelpingData = pd.DataFrame(proportionHelpingData, columns = ['Policy', 'Busyness', 'Proportion'])
    proportionAskingHelpingData = pd.DataFrame(proportionAskingHelpingData, columns = ['Policy', 'Busyness', 'Proportion'])
    numHelpingRejectedData = pd.DataFrame(numHelpingRejectedData, columns = ['Policy', 'Busyness', 'Proportion'])

    # Generate boxplots for each of the four metrics
    pal = [(77/255,175/255,74/255),(55/255,126/255,184/255),(228/255,26/255,28/255)]#sns.color_palette()#"tab10") # sns.color_palette(n_colors=3) # "colorblind" # "Set2"
    pal2 = [(r/2,g/2,b/2) for r,g,b in pal]
    pal3 = [(r+(1-r)/2,g+(1-g)/2,b+(1-b)/2) for r,g,b in pal]
    # pal = [pal[9], pal[3], pal[8]]
    sigma = 0.2
    for metric in metricsToData:
        # Metrics By Policy RainCloud
        fig = plt.figure(figsize=(8,8))
        ax = fig.subplots(1, 1)
        fig.suptitle(metricToTitle[metric])
        pt.RainCloud(x = "Policy", y = metric, data = metricsToData[metric], palette = pal, bw = sigma,
                         width_viol = .6, ax = ax, orient = "h", order=gid_to_policy_descriptor)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "policy_{}_{}.png".format(metric, descriptor))
        plt.clf()

        # Differences Barplot
        fig = plt.figure(figsize=(12,8))
        # fig.patch.set_facecolor('k')
        ax = fig.subplots(1, 1)
        fig.suptitle(metricToTitle[metric]+" Differences")
        g = sns.barplot(x = "Baseline", y = metric+" Difference", data = metricsToDataDifference[metric], alpha=1,
                         ax = ax)
        handles, labels = ax.get_legend_handles_labels()
        l = ax.legend(handles=handles[0:], labels=labels[0:], bbox_to_anchor=(1.05, 1), loc='upper left')#, facecolor='k', edgecolor='darkgrey')
        ax.set_ylabel('Hybrid - Baseline Difference '+metricToYLabel[metric])
        g.set_xticklabels(g.get_xticklabels(), rotation=30)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "policy_difference_barplot_{}_{}.png".format(metric, descriptor))
        plt.clf()

    # Num Times Asked Helped Scatterplot
    fig = plt.figure(figsize=(4,4))
    # fig.patch.set_facecolor('k')
    ax = fig.subplots(1, 1)
    fig.suptitle("Num Times Asked / Helped Across Policies")
    sns.scatterplot(x = "Num Asking", y = "Num Helping", data = numAskingHelpingJitter, palette = pal, hue="Policy", style="Policy", style_order=['Contextual', 'Individual', 'Hybrid'], alpha=1,
                     ax = ax, hue_order=gid_to_policy_descriptor)
    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:])#, facecolor='k', edgecolor='darkgrey')
    # for text in l.get_texts():
    #     text.set_color("k")
    ax.set_xlabel('Number of Times the Robot Asked')
    ax.set_ylabel('Number of Times the Human Helped')
    ax.plot([0,20], [0,20], linewidth=2, linestyle='--', alpha=0.5)
    # ax.xaxis.label.set_color('white')
    # ax.yaxis.label.set_color('white')
    # ax.tick_params(axis='x', colors='white')
    # ax.tick_params(axis='y', colors='white')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policy_num_asking_helping_jitter_{}.png".format(descriptor))
    plt.clf()

    fig = plt.figure(figsize=(4,4))
    # fig.patch.set_facecolor('k')
    ax = fig.subplots(1, 1)
    fig.suptitle("Num Times Asked / Helped Across Policies")
    sns.scatterplot(x = "Num Asking", y = "Num Helping / Num Asking", data = numAskingHelpingJitter, palette = pal, hue="Policy", style="Policy", style_order=['Contextual', 'Individual', 'Hybrid'], alpha=1,
                     ax = ax, hue_order=gid_to_policy_descriptor)
    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:])#, facecolor='k', edgecolor='darkgrey')
    ax.set_xlabel('Number of Times the Robot Asked')
    ax.set_ylabel('Proportion of Times the Human Helped')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policy_num_asking_helping_jitter_proportion_{}.png".format(descriptor))
    plt.clf()

    # Num Times Asked Helped Arrowplot
    fig = plt.figure(figsize=(8,8))
    # fig.patch.set_facecolor('k')
    ax = fig.subplots(1, 1)
    fig.suptitle("Change From Baseline to Hybrid")
    hybridVContextualColor = "r"
    hybridVIndividualColor = "b"
    for baseline, hybridNumAsking, hybridNumHelping, comparisonNumAsking, comparisonNumHelping in numAskingHelpingJitterPaired:
        # Account for jitter putting it over the line
        hybridNumHelping = min(hybridNumHelping, hybridNumAsking)
        comparisonNumHelping = min(comparisonNumHelping, comparisonNumAsking)
        if "Individual" in baseline:
            color = hybridVIndividualColor
        else:
            color = hybridVContextualColor
        x = comparisonNumAsking
        y = comparisonNumHelping
        dx = hybridNumAsking-comparisonNumAsking
        dy = hybridNumHelping-comparisonNumHelping
        ax.arrow(x, y, dx, dy, head_width=.24, length_includes_head=True, color=color, alpha=0.70)

    ax.set_xlabel('Number of Times the Robot Asked')
    ax.set_ylabel('Number of Times the Human Helped')
    ax.plot([0,20], [0,20], linewidth=2, linestyle='--', alpha=0.5)

    hybridVContextualBox = plt.Rectangle((0,0),1,1,fc=hybridVContextualColor, edgecolor = 'none')
    hybridVIndividualBox = plt.Rectangle((0,0),1,1,fc=hybridVIndividualColor,  edgecolor = 'none')
    l = ax.legend([hybridVContextualBox, hybridVIndividualBox], ['Hybrid v. Contextual', 'Hybrid v. Individual'], loc='upper left', ncol = 1)
    l.draw_frame(False)

    plt.savefig(baseDir + "policy_num_asking_helping_jitter_arrow_{}.png".format(descriptor))
    plt.clf()

    # Proportion of Times Asked By Busyness
    fig, ax = plt.subplots(1, 1, figsize=(4,4))
    # fig.patch.set_facecolor('k')
    sns.lineplot(data=proportionAskingData, x="Busyness", y="Proportion", hue="Policy", ax=ax, palette = pal, hue_order=gid_to_policy_descriptor)
    fig.suptitle("Proportion of Times Asked By Busyness")
    ax.set_xlabel("Human Busyness")
    ax.set_ylabel("Proportion of Times the Robot Asked")
    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:], loc='lower left')#, facecolor='k', edgecolor='darkgrey')
    # for text in l.get_texts():
    #     text.set_color("k")
    # ax.xaxis.label.set_color('white')
    # ax.yaxis.label.set_color('white')
    # ax.tick_params(axis='x', colors='white')
    # ax.tick_params(axis='y', colors='white')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policies_pct_asking_{}.png".format(descriptor))

    # Proportion of Times Asked By Busyness
    fig, ax = plt.subplots(1, 1, figsize=(4,4))
    # fig.patch.set_facecolor('k')
    sns.lineplot(data=proportionHelpingData, x="Busyness", y="Proportion", hue="Policy", ax=ax, palette = pal, hue_order=gid_to_policy_descriptor)
    fig.suptitle("Proportion of Times Helped By Busyness")
    ax.set_xlabel("Human Busyness")
    ax.set_ylabel("Proportion of Times the Human Helped")
    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:], loc='lower left')#, facecolor='k', edgecolor='darkgrey')
    # for text in l.get_texts():
    #     text.set_color("k")
    # ax.xaxis.label.set_color('white')
    # ax.yaxis.label.set_color('white')
    # ax.tick_params(axis='x', colors='white')
    # ax.tick_params(axis='y', colors='white')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policies_pct_helping_{}.png".format(descriptor))

    # Proportion of Times Asked By Busyness
    fig, ax = plt.subplots(1, 1, figsize=(4,4))
    # fig.patch.set_facecolor('k')
    sns.lineplot(data=proportionAskingHelpingData, x="Busyness", y="Proportion", hue="Policy", ax=ax, palette = pal, hue_order=gid_to_policy_descriptor)
    fig.suptitle("Proportion of Times Helped / Asked By Busyness")
    ax.set_xlabel("Human Busyness")
    ax.set_ylabel("Proportion of Times the Human Helped")
    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:], loc='lower left')#, facecolor='k', edgecolor='darkgrey')
    # for text in l.get_texts():
    #     text.set_color("k")
    # ax.xaxis.label.set_color('white')
    # ax.yaxis.label.set_color('white')
    # ax.tick_params(axis='x', colors='white')
    # ax.tick_params(axis='y', colors='white')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policies_pct_helping_Asking_{}.png".format(descriptor))

    # Proportion of Times Asked By Busyness
    fig, ax = plt.subplots(1, 1, figsize=(4,4))
    # fig.patch.set_facecolor('k')
    sns.lineplot(data=numHelpingRejectedData, x="Busyness", y="Proportion", hue="Policy", ax=ax, palette = pal, hue_order=gid_to_policy_descriptor)
    fig.suptitle("Num Helping Rejected By Busyness")
    ax.set_xlabel("Human Busyness")
    ax.set_ylabel("Num Times The Human Said No")
    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:], loc='upper right')#, facecolor='k', edgecolor='darkgrey')
    # for text in l.get_texts():
    #     text.set_color("k")
    # ax.xaxis.label.set_color('white')
    # ax.yaxis.label.set_color('white')
    # ax.tick_params(axis='x', colors='white')
    # ax.tick_params(axis='y', colors='white')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policies_num_helping_rejected_{}.png".format(descriptor))

    # Stacked Barplot
    fig, ax = plt.subplots(1, 1, figsize=(12,8))

    sns.barplot(x = "Mean Final Belief Bucket", y = "Num Asking", data = numAskingHelpingBelief, palette = pal2, hue="Policy", alpha=1,
                ax = ax, hue_order=gid_to_policy_descriptor, order=meanFinalBeliefBuckets)

    sns.barplot(x = "Mean Final Belief Bucket", y = "Num Helping", data = numAskingHelpingBelief, palette = pal, hue="Policy", alpha=1,
                ax = ax, hue_order=gid_to_policy_descriptor, order=meanFinalBeliefBuckets)

    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:], bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policies_num_asking_helping_by_final_hybrid_belief_barplot_{}.png".format(descriptor))

    # Stacked Barplot
    fig, ax = plt.subplots(1, 1, figsize=(12,8))

    sns.barplot(x = "Hybrid Num Helping Bucket", y = "Num Asking", data = numAskingHelpingBelief, palette = pal2, hue="Policy", alpha=1,
                ax = ax, hue_order=gid_to_policy_descriptor, order=numHelpingBucketNames)

    sns.barplot(x = "Hybrid Num Helping Bucket", y = "Num Helping", data = numAskingHelpingBelief, palette = pal, hue="Policy", alpha=1,
                ax = ax, hue_order=gid_to_policy_descriptor, order=numHelpingBucketNames)

    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:], bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policies_num_asking_helping_by_hybrid_helping_barplot_{}.png".format(descriptor))

    # Stacked Barplot
    fig, ax = plt.subplots(1, 1, figsize=(9,6))

    # sns.set_context(rc = {'patch.linecolor': 'k'}) # {'patch.linewidth': 0.0}
    sns.barplot(x = "Overall Human Proportion Helpfulness", y = "Num Asking", data = numAskingHelpingBelief, palette = pal, hue="Policy", alpha=1,
                ax = ax, hue_order=gid_to_policy_descriptor, order=overallProportionHelpfulnessBuckets, capsize=0.1, errwidth=2.0)

    sns.barplot(x = "Overall Human Proportion Helpfulness", y = "Num Helping", data = numAskingHelpingBelief, palette = pal3, hue="Policy", alpha=1,
                ax = ax, hue_order=gid_to_policy_descriptor, order=overallProportionHelpfulnessBuckets, capsize=0.1, errwidth=2.0, errcolor="grey")

    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=[labels[i]+(" Num Asking" if i < len(labels)/2 else " Num Helping") for i in range(len(labels))], loc='upper left') # , bbox_to_anchor=(1.05, 1)

    ax.set_xlabel("Human Helpfulness")
    ax.set_ylabel("Number")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policies_num_asking_helping_by_overall_helpfulness_barplot_{}.png".format(descriptor))

    # Stacked Barplot
    with mpl.rc_context({"yaxis.labellocation": 'bottom'}):
        fig, ax = plt.subplots(1, 1, figsize=(7,5))

        # sns.set_context(rc = {'patch.linecolor': 'k'}) # {'patch.linewidth': 0.0}
        sns.barplot(x = "Overall Human Proportion Helpfulness", y = "Num Helping", data = numAskingHelpingBelief, palette = pal, hue="Policy", alpha=1,
                    ax = ax, hue_order=gid_to_policy_descriptor, order=overallProportionHelpfulnessBuckets, capsize=0.1, errwidth=2.0)

        sns.barplot(x = "Overall Human Proportion Helpfulness", y = "Negative Num Helping Rejected", data = numAskingHelpingBelief, palette = pal3, hue="Policy", alpha=1,
                    ax = ax, hue_order=gid_to_policy_descriptor, order=overallProportionHelpfulnessBuckets, capsize=0.1, errwidth=2.0, errcolor="grey")

        handles, labels = ax.get_legend_handles_labels()
        l = ax.legend(handles=handles[0:3], labels=labels[0:3], loc='upper left') # , bbox_to_anchor=(1.05, 1) # [labels[i]+(" Num Helping" if i < len(labels)/2 else " Num Helping Rejected") for i in range(len(labels))]

        ax.set_xlabel("Human Helpfulness")
        ax.set_ylabel("Num Help Rejected   |               Num Help")

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "policies_num_helping_and_rejected_by_overall_helpfulness_barplot_{}.png".format(descriptor))

    # Stacked Barplot
    fig, ax = plt.subplots(1, 1, figsize=(9,6))

    sns.barplot(x = "Overall Human Proportion Helpfulness", y = "Num Helping / Num Asking", data = numAskingHelpingBelief, palette = pal, hue="Policy", alpha=1,
                ax = ax, hue_order=gid_to_policy_descriptor, order=overallProportionHelpfulnessBuckets)

    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:], loc='upper left') # bbox_to_anchor=(1.05, 1),

    ax.set_xlabel("Human Helpfulness")
    ax.set_ylabel("Proportion of Times the Human Helped")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policies_proportion_helping_by_overall_helpfulness_barplot_{}.png".format(descriptor))

    # Stacked Barplot
    fig, ax = plt.subplots(1, 1, figsize=(12,8))

    sns.barplot(x = "Num Asking Bucket", y = "Num Helping Rejected", data = numAskingHelpingBelief, palette = pal, hue="Policy", alpha=1,
                ax = ax, hue_order=gid_to_policy_descriptor, order=numAskingBucketNames)

    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:], bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policies_num_helping_rejected_by_num_asking_{}.png".format(descriptor))

    # Stacked Barplot
    fig, ax = plt.subplots(1, 1, figsize=(12,8))

    sns.barplot(x = "Hybrid Num Asking Bucket", y = "Num Helping Rejected", data = numAskingHelpingBelief, palette = pal, hue="Policy", alpha=1,
                ax = ax, hue_order=gid_to_policy_descriptor, order=numAskingBucketNames)

    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:], bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policies_num_helping_rejected_by_hybrid_num_asking_{}.png".format(descriptor))

    # Stacked Barplot
    fig, ax = plt.subplots(1, 1, figsize=(9,6))

    sns.barplot(x = "Overall Human Proportion Helpfulness", y = "Num Helping Rejected", data = numAskingHelpingBelief, palette = pal, hue="Policy", alpha=1,
                ax = ax, hue_order=gid_to_policy_descriptor, order=overallProportionHelpfulnessBuckets)

    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:], loc='upper right')

    ax.set_xlabel("Human Helpfulness")
    ax.set_ylabel("Num Times Help Requests Were Turned Down")

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policies_num_helping_rejected_by_overall_helpfulnessg_{}.png".format(descriptor))

    # Stacked Barplot
    fig, ax = plt.subplots(1, 1, figsize=(12,8))

    sns.barplot(x = "Num Asking Bucket", y = "Num Helping", data = numAskingHelpingBelief, palette = pal, hue="Policy", alpha=1,
                ax = ax, hue_order=gid_to_policy_descriptor, order=numAskingBucketNames)

    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:], bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policies_num_helping_by_num_asking_{}.png".format(descriptor))

    # Stacked Barplot
    fig, ax = plt.subplots(1, 1, figsize=(12,8))

    sns.barplot(x = "Hybrid Num Asking Bucket", y = "Num Helping", data = numAskingHelpingBelief, palette = pal, hue="Policy", alpha=1,
                ax = ax, hue_order=gid_to_policy_descriptor, order=numAskingBucketNames)

    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:], bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policies_num_helping_by_hybrid_num_asking_{}.png".format(descriptor))

    # Stacked Barplot
    fig, ax = plt.subplots(1, 1, figsize=(12,8))

    sns.barplot(x = "Hybrid Num Asking Bucket", y = "Num Helping / Num Asking", data = numAskingHelpingBelief, palette = pal, hue="Policy", alpha=1,
                ax = ax, hue_order=gid_to_policy_descriptor, order=numAskingBucketNames)

    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:], bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policies_proportion_helping_by_hybrid_num_asking_{}.png".format(descriptor))

    # Stacked Barplot
    fig, ax = plt.subplots(1, 1, figsize=(12,8))

    sns.barplot(x = "Num Asking Bucket", y = "Num Helping / Num Asking", data = numAskingHelpingBelief, palette = pal, hue="Policy", alpha=1,
                ax = ax, hue_order=gid_to_policy_descriptor, order=numAskingBucketNames)

    handles, labels = ax.get_legend_handles_labels()
    l = ax.legend(handles=handles[0:], labels=labels[0:], bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "policies_proportion_helping_by_num_asking_{}.png".format(descriptor))


if __name__ == "__main__":
    baseDir = "../flask/evaluation_2021/"

    individualFilepath = baseDir+"ec2_outputs_evaluation_2021_hybrid_v_individual/humanHelpUserStudyDataHybrid_vs_Individual.csv"
    contextualFilepath = baseDir+"ec2_outputs_evaluation_2021_hybrid_v_contextual/humanHelpUserStudyDataHybrid_vs_Contextual.csv"

    individualData = readCSV(individualFilepath)
    contextualData = readCSV(contextualFilepath)

    makeGraphs(individualData, contextualData, descriptor="")
