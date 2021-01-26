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
# mpl.rcParams['text.color'] = 'white'
# sns.set(style="whitegrid")
# sns.set_style("white")
# sns.set(style="whitegrid",font_scale=2)
import ptitprince as pt

baseDir = "../flask/ec2_outputs_evaluation/"

def makePolicyGraphs(surveyData, descriptor=""):
    # gid_to_policy_descriptor = ["Hybrid", "Contextual", "Individual"]

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
        # gid = surveyData[uuid]["gid"]
        policy = surveyData[uuid]["policy"]#gid_to_policy_descriptor[gid]
        for metric in metricsToData:
            metricsToData[metric].append([policy, surveyData[uuid]["policyResults"]["metrics"][metric]])

    for metric in metricsToData:
        # metricsToData[metric].sort(key=lambda x: gid_to_policy_descriptor.index(x[0]))
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
                         width_viol = .6, ax = ax, orient = "h")#, order=gid_to_policy_descriptor)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "policy_{}_{}.png".format(metric, descriptor))
        plt.clf()

def makeGranularityParameterSweepGraph(surveyData, descriptor=""):
    metricToYLabel = {
        "cumulativeReward" : "Cumulative Reward",
        "numCorrectRooms" : "Num Correct Rooms",
        "numAsking" : "Num Asks",
        "numHelping" : "Num Help",
        "numHelpingRejected" : "Num Refused Help",
        "rewardAdjusted" : "Reward Adjusted",
    }

    metricToTitle = {
        "cumulativeReward" : "Cumulative Reward Across Latent Helpfulness Granularity",
        "numCorrectRooms" : "Num Correct Rooms Across Latent Helpfulness Granularity",
        "numAsking" : "Num Asks Across Latent Helpfulness Granularity",
        "numHelping" : "Num Help Across Latent Helpfulness Granularity",
        "numHelpingRejected" : "Num Refused Help Across Latent Helpfulness Granularity",
        "rewardAdjusted" : "Reward Adjusted Across Latent Helpfulness Granularity",
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
        policy = surveyData[uuid]["policy"]
        try:
            numBuckets = float(policy[6:])
            policyName = policy[:6]
        except:
            numBuckets = float(policy[10:])
            policyName = policy[:10]
        for metric in metricsToData:
            metricsToData[metric].append([uuid[:4], policyName, policy, numBuckets, surveyData[uuid]["policyResults"]["metrics"][metric]])

    for metric in metricsToData:
        metricsToData[metric] = pd.DataFrame(metricsToData[metric], columns = ['UUID', 'Policy', 'Policy With Bucket', 'Num Buckets', metric])
        print(metric, metricsToData[metric])

    pal = [(77/255,175/255,74/255),(55/255,126/255,184/255),(228/255,26/255,28/255)]#sns.color_palette()#"tab10") # sns.color_palette(n_colors=3) # "colorblind" # "Set2"
    # pal = [pal[9], pal[3], pal[8]]
    sigma = 0.2
    for metric in metricsToData:
        fig, ax = plt.subplots(1, 1, figsize=(4,4))
        sns.lineplot(data=metricsToData[metric], x="Num Buckets", y=metric, hue="Policy", ax=ax)
        fig.suptitle(metricToTitle[metric])
        ax.set_xlabel("Num Buckets")
        ax.set_ylabel(metricToYLabel[metric])
        # handles, labels = ax.get_legend_handles_labels()
        # ax.legend(handles=handles[0:], labels=labels[0:], loc='lower left')
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "parameter_sweep_{}_{}.png".format(descriptor, metric))

        fig, ax = plt.subplots(1, 1, figsize=(4,4))
        sns.lineplot(data=metricsToData[metric], x="Num Buckets", y=metric, hue='UUID', ax=ax)
        ax.get_legend().remove()
        fig.suptitle(metricToTitle[metric])
        ax.set_xlabel("Num Buckets")
        ax.set_ylabel(metricToYLabel[metric])
        # handles, labels = ax.get_legend_handles_labels()
        # ax.legend(handles=handles[0:], labels=labels[0:], loc='lower left')
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "parameter_sweep_individual_{}_{}.png".format(descriptor, metric))

        fig = plt.figure(figsize=(8,8))
        ax = fig.subplots(1, 1)
        fig.suptitle(metricToTitle[metric])
        pt.RainCloud(x = "Policy With Bucket", y = metric, data = metricsToData[metric], bw = sigma,
                         width_viol = .6, ax = ax, orient = "h")
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "parameter_sweep_scatterplot_{}_{}.png".format(metric, descriptor))
        plt.clf()

def makeLengthOfTrialParameterSweepGraph(surveyData):
    metricToYLabel = {
        "cumulativeReward" : "Cumulative Reward / Episode Length",
        "numCorrectRooms" : "Num Correct Rooms / Episode Length",
        "numAsking" : "Num Asks / Episode Length",
        "numHelping" : "Num Help / Episode Length",
        "numHelpingRejected" : "Num Refused Help / Episode Length",
        "rewardAdjusted" : "Reward Adjusted / Episode Length",
    }

    metricToTitle = {
        "cumulativeReward" : "Cumulative Reward / Episode Length Across Length of Trial",
        "numCorrectRooms" : "Num Correct Rooms / Episode Length Across Length of Trial",
        "numAsking" : "Num Asks Across / Episode Length Length of Trial",
        "numHelping" : "Num Help Across / Episode Length Length of Trial",
        "numHelpingRejected" : "Num Refused Help / Episode Length Across Length of Trial",
        "rewardAdjusted" : "Reward Adjusted Across / Episode Length Length of Trial",
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
        policy = surveyData[uuid]["policy"]
        numBuckets = int(policy[6:])
        for metric in metricsToData:
            metricsToData[metric].append([uuid[:4], numBuckets, surveyData[uuid]["policyResults"]["metrics"][metric] / numBuckets])

    for metric in metricsToData:
        metricsToData[metric] = pd.DataFrame(metricsToData[metric], columns = ['UUID', 'Num Buckets', metric])
        print(metric, metricsToData[metric])

    pal = [(77/255,175/255,74/255),(55/255,126/255,184/255),(228/255,26/255,28/255)]#sns.color_palette()#"tab10") # sns.color_palette(n_colors=3) # "colorblind" # "Set2"
    # pal = [pal[9], pal[3], pal[8]]
    sigma = 0.2
    for metric in metricsToData:
        fig, ax = plt.subplots(1, 1, figsize=(4,4))
        sns.lineplot(data=metricsToData[metric], x="Num Buckets", y=metric, ax=ax, palette = pal)
        fig.suptitle(metricToTitle[metric])
        ax.set_xlabel("Lenth of Trial")
        ax.set_ylabel(metricToYLabel[metric])
        # handles, labels = ax.get_legend_handles_labels()
        # ax.legend(handles=handles[0:], labels=labels[0:], loc='lower left')
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "length_of_trial_parameter_sweep_{}.png".format(metric))

        fig, ax = plt.subplots(1, 1, figsize=(4,4))
        sns.lineplot(data=metricsToData[metric], x="Num Buckets", y=metric, hue='UUID', ax=ax)
        ax.get_legend().remove()
        fig.suptitle(metricToTitle[metric])
        ax.set_xlabel("Lenth of Trial")
        ax.set_ylabel(metricToYLabel[metric])
        # handles, labels = ax.get_legend_handles_labels()
        # ax.legend(handles=handles[0:], labels=labels[0:], loc='lower left')
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "length_of_trial_parameter_sweep_individual_{}.png".format(metric))

def makeActionEntropiesGraph(surveyData, descriptor=""):
    # pprint.pprint(surveyData)

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

    actionEntropyData = []
    policies = set()
    for uuid in surveyData:
        policy = surveyData[uuid]["policy"]
        policies.add(policy)
        pomcpc = float(policy[6:policy.find("-")])
        for i in range(len(surveyData[uuid]["actionEntropies"])):
            actionEntropy = surveyData[uuid]["actionEntropies"][i]
            actionName = surveyData[uuid]["actionNames"][i]
            actionEntropyData.append([policy, actionEntropy, actionName])

        for metric in metricsToData:
            metricsToData[metric].append([uuid[:4], pomcpc, policy, surveyData[uuid]["policyResults"]["metrics"][metric]])

    policies = sorted(list(policies))
    actionEntropyData = pd.DataFrame(actionEntropyData, columns = ['Policy', 'Action Entropy', 'Action Name'])
    # print("actionEntropyData", actionEntropyData)

    for metric in metricsToData:
        metricsToData[metric].sort()
        metricsToData[metric] = pd.DataFrame(metricsToData[metric], columns = ['UUID', 'POMCP C', 'Policy', metric])

    pal = [(77/255,175/255,74/255),(55/255,126/255,184/255),(228/255,26/255,28/255)]#sns.color_palette()#"tab10") # sns.color_palette(n_colors=3) # "colorblind" # "Set2"
    # pal = [pal[9], pal[3], pal[8]]
    sigma = 0.2

    fig = plt.figure(figsize=(8,8))
    ax = fig.subplots(1, 1)
    fig.suptitle('Action Entropy By Policy')

    pt.RainCloud(x = "Policy", y = 'Action Entropy', hue='Action Name', data = actionEntropyData, palette = pal, bw = sigma, alpha=0.65, dodge=True,
                     width_viol = .6, ax = ax, orient = "h", order=policies)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "action_entropy_by_policy_fo_rollout_{}.png".format(descriptor))
    plt.clf()

    pal = [(77/255,175/255,74/255),(55/255,126/255,184/255),(228/255,26/255,28/255)]#sns.color_palette()#"tab10") # sns.color_palette(n_colors=3) # "colorblind" # "Set2"
    # pal = [pal[9], pal[3], pal[8]]
    sigma = 0.2
    for metric in metricsToData:
        print("metricsToData[metric]", metricsToData[metric])

        fig = plt.figure(figsize=(8,8))
        ax = fig.subplots(1, 1)
        fig.suptitle(metricToTitle[metric])

        pt.RainCloud(x = "Policy", y = metric, data = metricsToData[metric], palette = pal, bw = sigma,
                         width_viol = .6, ax = ax, orient = "h")
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "action_entropy_by_policy_fo_rollout_{}_{}.png".format(metric, descriptor))
        plt.clf()

        fig, ax = plt.subplots(1, 1, figsize=(4,4))
        sns.lineplot(data=metricsToData[metric], x="POMCP C", y=metric, ax=ax, palette = pal)
        fig.suptitle(metricToTitle[metric])
        ax.set_xlabel("POMCP C")
        ax.set_ylabel(metricToYLabel[metric])
        # handles, labels = ax.get_legend_handles_labels()
        # ax.legend(handles=handles[0:], labels=labels[0:], loc='lower left')
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "action_entropy_by_policy_fo_rollout_parameter_sweep_{}_{}.png".format(metric, descriptor))

        fig, ax = plt.subplots(1, 1, figsize=(4,4))
        sns.lineplot(data=metricsToData[metric], x="POMCP C", y=metric, hue='UUID', ax=ax)
        ax.get_legend().remove()
        fig.suptitle(metricToTitle[metric])
        ax.set_xlabel("POMCP C")
        ax.set_ylabel(metricToYLabel[metric])
        # handles, labels = ax.get_legend_handles_labels()
        # ax.legend(handles=handles[0:], labels=labels[0:], loc='lower left')
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(baseDir + "action_entropy_by_policy_fo_rollout_parameter_sweep_individual_{}_{}.png".format(metric, descriptor))

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

    # surveyData = {}
    # with open("../flask/ec2_outputs_evaluation/humanHelpUserStudyDataLengthOfTrialParameterSweep.csv", "r") as f:
    #     reader = csv.reader(f)
    #     headers = next(reader, None)
    #     for row in reader:
    #         uuid = row[0]
    #         policy = row[1]
    #         key = uuid+policy
    #         surveyData[key] = {"policy":policy, "policyResults" : {"metrics" : {}}}
    #         for metric in metricToColumn:
    #             surveyData[key]["policyResults"]["metrics"][metric] = float(row[metricToColumn[metric]])
    #
    # makeLengthOfTrialParameterSweepGraph(surveyData)

    ############################################################################

    # surveyData = {}
    # with open("../flask/ec2_outputs_evaluation/humanHelpUserStudyDataActionEntropiesFORolloutMaxDepthVaries.csv", "r") as f:
    #     reader = csv.reader(f)
    #     headers = next(reader, None)
    #     for row in reader:
    #         uuid = row[0]
    #         policy = row[2]
    #         key = uuid+policy
    #         actionEntropy = float(row[9])
    #         actionName = row[10]
    #         if key not in surveyData:
    #             surveyData[key] = {"policy":policy, "policyResults" : {"metrics" : {}}, "actionEntropies":[], "actionNames":[]}
    #             for metric in metricToColumn:
    #                 surveyData[key]["policyResults"]["metrics"][metric] = float(row[metricToColumn[metric]+1])
    #         surveyData[key]["actionEntropies"].append(actionEntropy)
    #         surveyData[key]["actionNames"].append(actionName)
    #
    # makeActionEntropiesGraph(surveyData, descriptor="_hybrid_max_depth_varies")

    surveyData = {}
    with open("../flask/ec2_outputs_evaluation/humanHelpUserStudyDataHumanInconvenienceParameterSweep2To3.csv", "r") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        for row in reader:
            uuid = row[0]
            policy = row[2]
            key = uuid+policy
            if key not in surveyData:
                surveyData[key] = {"policy":policy, "policyResults" : {"metrics" : {}}, "actionEntropies":[], "actionNames":[]}
                for metric in metricToColumn:
                    surveyData[key]["policyResults"]["metrics"][metric] = float(row[metricToColumn[metric]+1])

    makeGranularityParameterSweepGraph(surveyData, descriptor="asking_penalty_2_to_3")

    # surveyData = {}
    # # with open("../flask/ec2_outputs_evaluation/humanHelpUserStudyDataWithExclusionCorrected.csv", "r") as f:
    # # with open("../flask/ec2_outputs_evaluation/humanHelpUserStudyDataWithExclusionHybridMoreRangeAndNoiseOnIndividualPeople.csv", "r") as f:
    # # with open("../flask/ec2_outputs_evaluation/humanHelpUserStudyDataRepeatOldIndividualToTestMethodology.csv", "r") as f:
    # with open("../flask/ec2_outputs_evaluation/humanHelpUserStudyDataHumanHelpPenalty2WrongRoomPenalty0.csv", "r") as f:
    #     reader = csv.reader(f)
    #     headers = next(reader, None)
    #     for row in reader:
    #         uuid = row[0]
    #         policy = row[2]
    #         # gid = policy_descriptor_to_gid[policy]
    #         # if uuid+"a" in surveyData:
    #         #     key = uuid+"b"
    #         # elif uuid in surveyData:
    #         #     key = uuid+"a"
    #         # else:
    #         #     key = uuid
    #         key = uuid+policy
    #         if key not in surveyData:
    #             surveyData[key] = {"policy":policy, "policyResults" : {"metrics" : {}}}
    #             for metric in metricToColumn:
    #                 surveyData[key]["policyResults"]["metrics"][metric] = float(row[metricToColumn[metric]+1])
    #
    # makePolicyGraphs(surveyData, "_Human_Help_Penalty_2_Wrong_Room_Penalty_0")
