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

import pandas as pd
import seaborn as sns
# sns.set(style="darkgrid")
# sns.set(style="whitegrid")

# sns.set(style="white", font_scale=2, font="Palatino")
sns.set(style="white", font="Palatino")

# sns.set(style="dark", font_scale=1.5)
# sns.set(style="whitegrid",font_scale=2)
import ptitprince as pt

if __name__ == "__main__":
    pal = "Set2"
    baseDir = "../flask/ec2_outputs_evaluation/"

    proposed_beliefs = [
        [0.0, 0.16429, 0.27143, 0.39286, 0.13571, 0.03571],
        [0.0, 0.01533, 0.13671, 0.53547, 0.2449, 0.06759],
        [0.0, 0.01533, 0.13671, 0.53547, 0.2449, 0.06759],
        [0.0, 0.00061, 0.03321, 0.48705, 0.36735, 0.11178],
        [0.0, 4.0e-5, 0.01076, 0.42689, 0.42629, 0.13602],
        [0.0, 0.0, 0.00174, 0.28653, 0.52257, 0.18916],
    ]
    only_fixed_beliefs = [
        [1.0/6.0 for i in range(6)],
        [1.0/6.0 for i in range(6)],
        [1.0/6.0 for i in range(6)],
        [1.0/6.0 for i in range(6)],
        [1.0/6.0 for i in range(6)],
        [1.0/6.0 for i in range(6)],
    ]
    only_random_beliefs = [
        [0.0, 0.16429, 0.25714, 0.42143, 0.13571, 0.02143],
        [0.0, 0.03729, 0.16602, 0.52987, 0.22745, 0.03937],
        [0.0, 0.09362, 0.31269, 0.51249, 0.07733, 0.00387],
        [0.0, 0.02116, 0.20104, 0.64166, 0.12906, 0.00708],
        [0.0, 0.0041, 0.11088, 0.68914, 0.18477, 0.01111],
        [0.0, 0.00073, 0.05641, 0.68275, 0.24402, 0.01609],
    ]

    for descriptor, beliefs, std in [
        # ("proposed", proposed_beliefs, 2.427516),
        # ("only_fixed", only_fixed_beliefs, 2.427516),
        # ("only_random", only_random_beliefs, 1.666155),
        ("custom", [[0.0, 0.0, 0.00174, 0.28653, 0.52257, 0.18916],[0.39286, 0.27143+0.13571, 0.16429+0.03571, 0.0, 0.0, 0.0],[0.12, 0.16429, 0.17143, 0.24286, 0.15571, 0.15571],[0.0, 0.0, 0, 0.10653, 0.47257+0.00174, 0.42916]], 2.427516)
    ]:
        for i in range(len(beliefs)):
            # fig, ax = plt.subplots(1, 1, figsize=(3.3,3.3))
            fig, ax = plt.subplots(1, 1, figsize=(1.5,1.5))
            ax.set_aspect(10/0.7)
            data = pd.DataFrame([(j*0.8*std - 2*std, beliefs[i][j]) for j in range(len(beliefs[i]))], columns = ['Random Effect', 'Probability'])

            sns.lineplot(data=data, x="Random Effect", y="Probability", ax=ax, palette = pal, linewidth=3)
            ax.set_title("")
            ax.set_xlabel("")
            # ax.set_xlim([int(round(-2*std)), int(round(2*std))])
            # ax.set_xticks([int(round(-2*std*10))/10, int(round(2*std*10))/10])
            ax.set_xlim([-5, 5])
            ax.set_xticks([-5,5])
            ax.set_ylabel("")
            ax.set_ylim([0.0,0.7])
            ax.set_yticks([0.0, 0.7])

            plt.tight_layout()#rect=[0, 0.03, 1, 0.95])
            sns.despine()
            plt.savefig(baseDir + "{}_{}.png".format(descriptor, i))
            plt.clf()
