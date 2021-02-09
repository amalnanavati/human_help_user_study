from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 1, 100)

# the comma is to get just the first element of the list returned
plot1, = plt.plot(x, x**2)
plot2, = plt.plot(x, x**3)

title_proxy = Rectangle((0,0), 0, 0, color='w')

plt.legend([title_proxy, plot1, title_proxy, plot2],
           ["title1", "label1","title2", "label2"])

plt.show()







# import pandas as pd
# from matplotlib import pyplot as plt
# import matplotlib as mpl
# import seaborn as sns
#
# fig = plt.figure(figsize=(8,8))
# ax = fig.subplots(1, 1)
#
# ax.arrow(x=1, y=1, dx=2, dy=3, width=.08, length_includes_head=True, color="r")
#
# plt.show()





# import pandas as pd
# from matplotlib import pyplot as plt
# import matplotlib as mpl
# import seaborn as sns
#
# #Read in data & create total column
# stacked_bar_data = pd.read_csv("/Users/amaln/Downloads/stacked_bar.csv")
# stacked_bar_data["total"] = stacked_bar_data.Series1 + stacked_bar_data.Series2
#
# # #Set general plot properties
# # sns.set_style("white")
# # sns.set_context({"figure.figsize": (12, 5)})
#
# fig = plt.figure(figsize=(8,8))
# ax = fig.subplots(1, 1)
#
# #Plot 1 - background - "total" (top) series
# sns.barplot(x = stacked_bar_data.Group, y = stacked_bar_data.total, color = "red", ax=ax)
#
# #Plot 2 - overlay - "bottom" series
# bottom_plot = sns.barplot(x = stacked_bar_data.Group, y = stacked_bar_data.Series1, color = "#0000A3", ax=ax)
#
#
# topbar = plt.Rectangle((0,0),1,1,fc="red", edgecolor = 'none')
# bottombar = plt.Rectangle((0,0),1,1,fc='#0000A3',  edgecolor = 'none')
# l = ax.legend([bottombar, topbar], ['Bottom Bar', 'Top Bar'], loc=1, ncol = 2, prop={'size':16})
# l.draw_frame(False)
#
# # #Optional code - Make plot look nicer
# # sns.despine(left=True)
# # bottom_plot.set_ylabel("Y-axis label")
# # bottom_plot.set_xlabel("X-axis label")
# #
# # #Set fonts to consistent 16pt size
# # for item in ([bottom_plot.xaxis.label, bottom_plot.yaxis.label] +
# #              bottom_plot.get_xticklabels() + bottom_plot.get_yticklabels()):
# #     item.set_fontsize(16)
#
# plt.show()




# import matplotlib.pyplot as plt
# import numpy as np
# from matplotlib.patches import Polygon
# import traceback
#
# import csv
# import pprint
# import random
# import pandas as pd
#
# import seaborn as sns
# #sns.set(style="darkgrid")
# #sns.set(style="whitegrid")
# #sns.set_style("white")
# sns.set(style="whitegrid",font_scale=2)
# import matplotlib.collections as clt
# import ptitprince as pt
#
# policies = ["Proposed", "Only Fixed", "Only Random"]
# busynesses = ["high", "medium", "low"]
# data = []
# for _ in range(100):
#     i = random.choice(range(len(policies)))
#     policy = policies[i]
#     val = np.random.normal(10-2*i, 2.0)
#     data.append([policy, val, random.choice(busynesses)])
# df = pd.DataFrame(data, columns = ['Policy', 'Cumulative Reward', 'Busyness'])
# print(df)
#
# dy = "Cumulative Reward"
# dx = "Policy"
# pal = "Set1"#sns.color_palette(n_colors=3)
# ort = "v"
# dhue = "Busyness"
# sigma = .2
#
# f, ax = plt.subplots(figsize=(14, 7))
#
# # # sns.barplot(x = "Policy", y = "Cumulative Reward", data = df, capsize= .1)
# # ax=pt.half_violinplot(x = dx, y = dy, data = df, palette = pal, cut = 0., scale = "area", width = .6, inner = None, orient = ort)
# # ax=sns.stripplot( x = dx, y = dy, data = df, palette = pal, edgecolor = "white",
# #                  size = 3, jitter = .1, zorder = 0, orient = ort)
# # ax=sns.boxplot( x = dx, y = dy, data = df, color = "black", width = .15, zorder = 10,\
# #             showcaps = True, boxprops = {'facecolor':'none', "zorder":10},\
# #             showfliers=True, whiskerprops = {'linewidth':2, "zorder":10},\
# #                saturation = 1, orient = ort)
#
# pt.RainCloud(x = dx, y = dy, data = df, palette = pal, bw = sigma, hue=dhue, alpha=0.65, dodge=True, pointplot = True,
#                  width_viol = .6, ax = ax, orient = ort)
# plt.title("Cumulative Reward by Policy")
# plt.tight_layout(rect=[0, 0.03, 1, 0.95])
#
# # g = sns.FacetGrid(df, col = "Busyness", height = 6)
# # g = g.map_dataframe(pt.RainCloud, x = dx, y = dy, data = df,
# #                     orient = ort)
# # g.fig.subplots_adjust(top=0.75)
# # g.fig.suptitle("Cumulative Reward by Policy",  fontsize=26)
#
# plt.show()



# def f(n):
#     percentZero = 0.1
#     percentOne = 1.0-percentZero
#     dataset = [0 for _ in range(int(percentZero*n))]+[1 for _ in range(int(percentOne*n))]
#     print(n, np.mean(dataset), np.std(dataset))
#
# for n in [10, 100, 1000, 10000]:
#     f(n)



# filepath = "../flask/ec2_outputs/humanHelpUserStudyDataWithExclusionNumeric.csv"
# dataset = []
# with open(filepath, "r") as f:
#     reader = csv.reader(f)
#     headers = next(reader, None)
#     for row in reader:
#         busyness, frequency, prosociality, willingnessToHelp = row
#         dataset.append([busyness, frequency, prosociality, willingnessToHelp])
#
# pprint.pprint(dataset)
