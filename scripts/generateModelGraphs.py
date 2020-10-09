import csv, pprint, os, json, pickle
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
# sns.set(style="whitegrid")
# sns.despine()
# sns.set_style("white")
# sns.set(style="whitegrid",font_scale=2)
import ptitprince as pt

if __name__ == "__main__":
    baseDir = "../flask/ec2_outputs/processedData/"

    # load the survey data
    surveyDataFromCSV = {}
    with open('/Users/amaln/Documents/PRL/human_help_user_study/flask/ec2_outputs/humanHelpUserStudyPerResponseData.csv') as csvfile:
     surveyDataCSV = csv.reader(csvfile)
     i = -1
     for row in surveyDataCSV:
         i += 1
         if i == 0:
             header = row
         else:
            uuid = int(row[0])
            if uuid not in surveyDataFromCSV:
                surveyDataFromCSV[uuid] = []
            surveyDataFromCSV[uuid].append({})
            for j in range(1,len(row)):
                try:
                    surveyDataFromCSV[uuid][-1][header[j]] = float(row[j])
                except Exception:
                    surveyDataFromCSV[uuid][-1][header[j]] = row[j]

    print("surveyDataFromCSV")
    pprint.pprint(surveyDataFromCSV)

    # Load the model parameters
    modelParamsFixed = None
    modelParamsRandom = {}
    with open('/Users/amaln/Documents/PRL/human_help_user_study/flask/ec2_outputs/processedData/finalModel.csv') as csvfile:
     modelParamsCSV = csv.reader(csvfile)
     i = -1
     for row in modelParamsCSV:
         i += 1
         if i == 0:
             continue
         elif i == 1:
             modelParamsFixed = [float(row[i]) for i in range(2, len(row))]
         else:
             uuid = int(row[0])
             modelParamsRandom[uuid] = float(row[1])

    print("modelParamsRandom")
    pprint.pprint(modelParamsRandom)
    modelParamsFixed = np.array(modelParamsFixed)
    print("modelParamsFixed", modelParamsFixed)

    # Graph frequency on the x axis, proportion on the y, with shaded bernoulli error, and the model predictions overlaid on top
    pal = [(77/255,175/255,74/255),(55/255,126/255,184/255),(228/255,26/255,28/255)]#sns.color_palette()#"tab10") # sns.color_palette(n_colors=3) # "colorblind" # "Set2"
    #pal = [pal[9], pal[3], pal[8]]
    busynesses = ['free time', 'medium', 'high']
    frequencies = [0.2, 0.4, 0.6, 0.8, 1.0]
    busynessToFrequencyToPercentageHelpings = {busyness : {freq : [] for freq in frequencies} for busyness in busynesses}
    # busynessToFrequencyToPercentageHelpingsErrorBars = {busyness : {freq : [] for freq in frequencies} for busyness in busynesses}
    for uuid in surveyDataFromCSV:
        busynessToResponses = {busyness : [] for busyness in busynesses}
        for datapoint in surveyDataFromCSV[uuid]:
            busyness = datapoint['Busyness']
            frequency = datapoint['Past Frequency of Asking']
            humanResponse = int(datapoint['Human Response'])
            busynessToResponses[busyness].append(humanResponse)
        for busyness in busynessToResponses:
            n = len(busynessToResponses[busyness])
            p = sum(busynessToResponses[busyness])/n
            busynessToFrequencyToPercentageHelpings[busyness][frequency].append(p)
            # busynessToFrequencyToPercentageHelpingsErrorBars[busyness][frequency].append(k*(p*(1-p)/n)**0.5)
    print("busynessToFrequencyToPercentageHelpings")
    pprint.pprint(busynessToFrequencyToPercentageHelpings)
    # print("busynessToFrequencyToPercentageHelpingsErrorBars")
    # pprint.pprint(busynessToFrequencyToPercentageHelpingsErrorBars)

    # For Wald's Interval
    alpha = 0.05
    k = scipy.stats.norm.ppf(1-alpha/2)
    busynessToErrorBarLower = {busyness : [None for _ in range(len(frequencies))] for busyness in busynesses}
    busynessToErrorBarUpper = {busyness : [None for _ in range(len(frequencies))] for busyness in busynesses}
    frequencyToErrorBarLower = {busyness : [None for _ in range(len(frequencies))] for busyness in busynesses}
    frequencyToErrorBarUpper = {busyness : [None for _ in range(len(frequencies))] for busyness in busynesses}
    busynessFrequencyProportionDataset = []
    for busyness in busynessToFrequencyToPercentageHelpings:
        for frequency in busynessToFrequencyToPercentageHelpings[busyness]:
            i = int(frequency*5)-1
            n = len(busynessToFrequencyToPercentageHelpings[busyness][frequency])
            p = sum(busynessToFrequencyToPercentageHelpings[busyness][frequency])/n
            busynessToErrorBarLower[busyness][i] = p-k*(p*(1-p)/n)**0.5
            busynessToErrorBarUpper[busyness][i] = p+k*(p*(1-p)/n)**0.5
            busynessFrequencyProportionDataset.append([busyness, frequency, p, "Data"])
    frequenciesForModel = [i/100 for i in range(20, 101)]
    busynessesToNumeric = {'free time':0, 'medium':1/7, 'high':1/3}
    for busyness in busynessesToNumeric:
        busynessNumeric = busynessesToNumeric[busyness]
        for frequency in frequenciesForModel:
            datapoint = np.array([1, busynessNumeric, busynessNumeric*frequency])
            logit = np.dot(datapoint, modelParamsFixed)
            p = math.e**logit / (1 + math.e**logit)
            busynessFrequencyProportionDataset.append([busyness, frequency, p, "Model", busynessNumeric])
    busynessFrequencyProportionDataset = pd.DataFrame(busynessFrequencyProportionDataset, columns = ['Busyness', 'Frequency of Asking', 'Proportion Helping', "Type", "Busyness Numeric"])

    fig, ax = plt.subplots(1, 1, figsize=(6,4))
    sns.lineplot(data=busynessFrequencyProportionDataset, x="Frequency of Asking", y="Proportion Helping", hue="Busyness", style="Type", ax=ax, palette = pal)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    # for i in range(len(ax.lines)):
    #     ax.lines[i].set_linestyle("--")
    for i in range(len(busynesses)):
        color = pal[i]
        ax.fill_between(frequencies, busynessToErrorBarLower[busynesses[i]], busynessToErrorBarUpper[busynesses[i]], color=color, alpha=0.25)
    fig.suptitle("Proportion Helping By Frequency of Asking")
    ax.set_xlabel("Frequency of Asking")
    ax.set_ylabel("Proportion of Times the Human Helped")
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "frequency_busyness.png")
    plt.clf()

    # fig, ax = plt.subplots(1, 1, figsize=(6,4))
    # sns.lineplot(data=busynessFrequencyProportionDataset, x="Busyness Numeric", y="Proportion Helping", hue="Frequency of Asking", style="Type", ax=ax, palette = pal)
    # ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    # # for i in range(len(ax.lines)):
    # #     ax.lines[i].set_linestyle("--")
    # for i in range(len(busynesses)):
    #     color = pal[i]
    #     ax.fill_between(frequencies, busynessToErrorBarLower[busynesses[i]], busynessToErrorBarUpper[busynesses[i]], color=color, alpha=0.25)
    # fig.suptitle("Proportion Helping By Frequency of Asking")
    # ax.set_ylabel("Proportion Helping")
    # plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    # plt.savefig(baseDir + "frequency_busyness.png")
    # plt.clf()

    # Add the model lines for UUID
    fig, axes = plt.subplots(1, 2, figsize=(6,4), sharey='row')
    fig.suptitle("Modeled Individual Differences")
    # Busyness on the x axis
    busynesses = [i/100 for i in range(101)]
    data = []
    for uuid in modelParamsRandom:
        randomParam = modelParamsRandom[uuid]
        # frequency = surveyDataFromCSV[uuid][0]['Past Frequency of Asking']
        frequency = 0.4
        for busyness in busynesses:
            logit = np.dot(np.array([1,1,busyness,busyness*frequency]), np.array([randomParam]+list(modelParamsFixed)))
            p = math.e**logit / (1 + math.e**logit)
            data.append([busyness, frequency, p, uuid])
    data = pd.DataFrame(data, columns = ['Busyness', 'Frequency of Asking', 'Proportion Helping', "UUID"])
    sns.lineplot(data=data, x="Busyness", y="Proportion Helping", hue="UUID", ax=axes[0], legend=False, alpha=0.25)
    axes[0].set_ylabel('Predicted Probability of Helping')
    # Frequency on the x axis
    frequencies = [i/100 for i in range(101)]
    busyness = busynessesToNumeric['medium']
    data = []
    for uuid in modelParamsRandom:
        randomParam = modelParamsRandom[uuid]
        frequency = surveyDataFromCSV[uuid][0]['Past Frequency of Asking']
        for frequency in frequencies:
            logit = np.dot(np.array([1,1,busyness,busyness*frequency]), np.array([randomParam]+list(modelParamsFixed)))
            p = math.e**logit / (1 + math.e**logit)
            data.append([busyness, frequency, p, uuid])
    data = pd.DataFrame(data, columns = ['Busyness', 'Frequency of Asking', 'Proportion Helping', "UUID"])
    sns.lineplot(data=data, x="Frequency of Asking", y="Proportion Helping", hue="UUID", ax=axes[1], legend=False, alpha=0.25)
    axes[1].set_ylabel('')
    for j in range(len(axes)):
        for i in range(len(axes[j].lines)):
            axes[j].lines[i].set_linestyle("--")
            axes[j].lines[i].set_color(pal[0])
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(baseDir + "individual_factors.png")
    plt.clf()
