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

import pandas as pd
import seaborn as sns
sns.set(style="darkgrid", font="Palatino")
mpl.rcParams['text.color'] = 'white'
# sns.set(style="whitegrid")
# sns.set_style("white")
# sns.set(style="whitegrid",font_scale=2)
import ptitprince as pt

baseDir = "../flask/ec2_outputs_evaluation/"

def makePolicyGraphs(surveyData, descriptor=""):
    gid_to_policy_descriptor = ["Hybrid", "Contextual", "Individual"]

    metricToYLabel = {
        "cumulativeReward" : "Cumulative Reward",
        "numCorrectRooms" : "Num Correct Rooms",
        "numAsking" : "Num Asks",
        "numHelping" : "Num Help",
        "numHelpingRejected" : "Num Refused Help",
        "rewardAdjusted" : "Reward Adjusted",
    }

    metricToTitle = {
        "cumulativeReward" : "Cumulative Reward Across Policies",
        "numCorrectRooms" : "Num Correct Rooms Across Policies",
        "numAsking" : "Num Asks Across Policies",
        "numHelping" : "Num Help Across Policies",
        "numHelpingRejected" : "Num Refused Help Across Policies",
        "rewardAdjusted" : "Reward Adjusted Across Policies",
    }

    metricsToData = {
        "cumulativeReward" : [],
        "numCorrectRooms" : [],
        "numAsking" : [],
        "numHelping" : [],
        "numHelpingRejected" : [],
        "rewardAdjusted" : [],
    }

    for uuid in surveyData:
        gid = surveyData[uuid]["gid"]
        policy = gid_to_policy_descriptor[gid]
        for metric in metricsToData:
            metricsToData[metric].append([policy, surveyData[uuid]["policyResults"]["metrics"][metric]])

    for metric in metricsToData:
        metricsToData[metric].sort(key=lambda x: gid_to_policy_descriptor.index(x[0]))
        metricsToData[metric] = pd.DataFrame(metricsToData[metric], columns = ['Policy', metric])

    pal = [(77/255,175/255,74/255),(55/255,126/255,184/255),(228/255,26/255,28/255)]#sns.color_palette()#"tab10") # sns.color_palette(n_colors=3) # "colorblind" # "Set2"
    # pal = [pal[9], pal[3], pal[8]]
    sigma = 0.2
    for metric in metricsToData:
        print("metricsToData[metric]", metricsToData[metric])

        fig = plt.figure(figsize=(8,8))
        ax = fig.subplots(1, 1)
        fig.suptitle(metricToTitle[metric])

        pt.RainCloud(x = "Policy", y = metric, data = metricsToData[metric], palette = pal, bw = sigma,
                         width_viol = .6, ax = ax, orient = "h", order=gid_to_policy_descriptor)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "policy_{}_{}.png".format(metric, descriptor))
        plt.clf()

if __name__ == "__main__":
    metricToColumn = {
        "cumulativeReward" : 2,
        "numCorrectRooms" : 3,
        "numAsking" : 4,
        "numHelping" : 5,
        "numHelpingRejected" : 6,
        "rewardAdjusted" : 7,
    }
    policy_descriptor_to_gid = {"Hybrid":0, "Contextual":1, "Individual":2}

    surveyData = {}
    with open("../flask/ec2_outputs_evaluation/humanHelpUserStudyDataWithExclusionCorrected.csv", "r") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        for row in reader:
            uuid = row[0]
            policy = row[1]
            gid = policy_descriptor_to_gid[policy]
            surveyData[uuid] = {"gid":gid, "policyResults" : {"metrics" : {}}}
            for metric in metricToColumn:
                surveyData[uuid]["policyResults"]["metrics"][metric] = float(row[metricToColumn[metric]])

    makePolicyGraphs(surveyData, "_correctedIndividual")
