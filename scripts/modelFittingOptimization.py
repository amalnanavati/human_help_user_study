import random
import matplotlib.pyplot as plt
import numpy as np
import csv
import pprint
import math

#filepath = "../flask/ec2_outputs/humanHelpUserStudyDataWithExclusionNumeric.csv"
filepath = "../flask/ec2_outputs/humanHelpUserStudyPerResponseData.csv"
dataset = []
with open(filepath, "r") as f:
    reader = csv.reader(f)
    headers = next(reader, None)
    for row in reader:
        # busyness, frequency, prosociality, willingnessToHelp = row
        # dataset.append([busyness, frequency, prosociality, willingnessToHelp])
        uuid, busyness, pastFrequencyofAsking, pastFrequencyofHelpingAccurately, humanResponse, prosociality = row
        dataset.append([uuid, busyness, pastFrequencyofAsking, pastFrequencyofHelpingAccurately, humanResponse, prosociality])
#pprint.pprint(dataset)

def oneDLinearParametrizedFunction(params):
    """
    Input: a list of parameter values
    Output: a 1D linear function, given those parameter values
    """
    def oneDLinearFunction(x):
        """
        Input: a 1D list, x
        Output: f(x) = m*x + b, where m and b are given by params
        """
        m = params[0]
        b = params[1]
        output = m*x[0] + b
        return output
    return oneDLinearFunction

def threeDLinearParametrizedFunction(params):
    """
    Input: a list of parameter values
    Output: a 3D linear function, given those parameter values
    """
    def threeDLinearFunction(x):
        """
        Input: a 3D list, x
        Output: f(x, y, z) = m0*x[0] + m1*x[1] + m2*x[2] + b, where ms and b are given by params
        """
        m0 = params[0]
        m1 = params[1]
        m2 = params[2]
        b = params[3]
        output = m0*x[0] + m1*x[1] + m2*x[2] + b
        return output
    return threeDLinearFunction

def quadraticParameterizedFunction(params):
    """
    Input: a list of parameter values
    Output: a 1D quadratic function, given those parameter values
    """
    def quadraticFunction(x):
        """
        Input: a 1D list, x
        Output: f(x) = a*x^2 + b*x + c, where a, b, and c are given by params
        """
        a = params[0]
        b = params[1]
        c = params[2]
        output = a*x[0]**2 + b*x[0] + c
        return output
    return quadraticFunction

def oneDExponentialParametrizedFunction(params):
    """
    Input: a list of parameter values that must be greater than 0 and not equal to 1
    Output: a 1D exponential function, given those parameter values
    """
    def oneDExponentialFunction(x):
        """
        Input: a 1D list, x
        Output: f(x) = k^x, where k is given by params
        """
        k = params[0]
        output = k**x[0]
        return output
    return oneDExponentialFunction

def twoDLinearParametrizedFunction(params):
    """
    Input: a list of parameter values
    Output: a 2D linear function, given those parameter values
    """
    def twoDLinearFunction(x):
        """
        Input: a 3D list, x
        Output: f(x, y) = m0*x[0] + m1*x[1] + b, where ms and b are given by params
        """
        m0 = params[0]
        m1 = params[1]
        b = params[2]
        output = m0*x[0] + m1*x[1] + b
        return output
    return twoDLinearFunction

def newParametrizedFunction(params):
    def newFunction(x):
        u = params[0]
        k = params[1]
        b = params[2]
        output = u/(1+math.exp(-k*(x[0]-b)))
        return output
    return newFunction

def averageEachXValue(unique_list):
    my_x_vals = []
    new_dataset = []
    x_count = 0
    for i in range(len(unique_list)):
        for j in range(i, len(unique_list)): # to prevent duplicates, j starts at i and goes up
            datapoint0 = unique_list[i]
            pastFreqOfHelping0 = datapoint0[0][0]
            response0 = datapoint0[0][1]
            count0 = datapoint0[1]
            datapoint1 = unique_list[j]
            pastFreqOfHelping1 = datapoint1[0][0]
            response1 = datapoint1[0][1]
            count1 = datapoint1[1]
            if pastFreqOfHelping0 not in my_x_vals:
                if pastFreqOfHelping0 == pastFreqOfHelping1:
                    totalCount = count0 + count1
                    avgResponse = (response0*count0 + response1*count1)/totalCount
                    x_count = x_count + 1
                    if(x_count > 1):
                        my_x_vals.append(pastFreqOfHelping0)
                        new_dataset.append([pastFreqOfHelping0, avgResponse])
        x_count = 0
    return new_dataset

def performOptimization(xs, ys, parameterizedFuncion, paramValues):
    """
    Inputs:
        xs: a length-n list of m-dimensional datapoints, where each datapoint
            is a length-m list. So this is a 2D, n by m, list
        ys: a length-n list, where each entry is a number that is the y-value
            for the x-value at the same index in xs
        parameterizedFuncion: a function that takes in a length-k list of
            parameters, and returns a function that takes in an x and returns
            the predicted y
        paramValues: an arbitrary-length list of length-k lists, where each
            length-k list corresponds to one parameter setting to be inputted into
            parameterizedFuncion

    """
    index = 0
    sum = 0
    minSumSqredError = None
    size = 0
    bestParams = None
    for params in paramValues:
        #print(params)
        func = parameterizedFuncion(params)
        for x in xs:
            #print(x)
            yPred = func(x)
            #print("pred ", yPred)
            y = ys[index]
            #print("actual ", y)
            sqredError = (y-yPred)**2
            index = index + 1
            sum = sum + sqredError
            size = len(xs)
        #print("meanSqrdError: ", sum/size)
        #print("params: ", params)
        if minSumSqredError is None or sum/size < minSumSqredError:
            minSumSqredError = sum/size
            bestParams = params

        index = 0
        sum = 0

    print("BEST PARAMS: ", bestParams, type(bestParams))
    return bestParams




    ############################################################################
    # STEP 1
    # Loop over paramValues
    # For each paramValue, get the function for those parameters
    # Loop over all the xs, and for each x get the corresponding y
    # Input x to the function, to get the predicted y
    # Get the squared error between the actual y and the predicted y (e.g. (y-yPred)**2)
    # Across all xs, average the squared distance to get the mean squared error
    # Across all paramValues, find the paramValue with the smallest mean squared
    # error and return that
    #
    #
    ############################################################################

if __name__ == "__main__":
    # Generate a fake dataset. This is a liner dataset, where the line with best
    # fit should be something like y=10x-3

    # xs = [[x/100] for x in range(0, 100)]
    # ys = [10*x[0]-3+(random.random()-0.5)*10 for x in xs]

    # xs = [[x/100] for x in range(0, 100)]
    # ys = [10**x[0]+(random.random()-0.5)*10 for x in xs]



    # numSamples = 10
    #
    # xSamples = [x / numSamples for x in range(0, numSamples)]
    # xs = []
    # ySamples = [y / numSamples for y in range(0, numSamples)]
    # ys = []
    # xAndY = []
    # for i in range(len(xSamples)):
    #     for j in range(len(ySamples)):
    #         xAndY.append([xSamples[i], ySamples[j]])
    #         xs.append(xSamples[i])
    #         ys.append(ySamples[j])
    # zs = [3 * x + 4 * y + (random.random()-0.5) * 5 for x,y in xAndY]
    xs = []
    ys = []
    xAndY = []
    count = []
    xAndYAndCount = []
    for data in dataset:
        #x = float(data[1])
        x = float(data[2])
        #y = float(data[3])
        y = float(data[4])
        if data[1] == "free time":
        #if ([x, y] != [0.0, 0.0]):
            xs.append([x])
            ys.append(y)
            xAndY.append([x, y])
    # uniqueX = set(xs)
    # print(uniqueX)
    # uniqueXToYs = {}
    # for x in uniqueX:
    #     uniqueXToYs[x] = []
    #for i in range(0, len(xs)):

    for val in xAndY:
        c = xAndY.count(val)
        count.append(c)
        if(val not in xAndYAndCount):
            xAndYAndCount.append([val, c])
    #print(xAndYAndCount)

    unique_list = []
    for x in xAndYAndCount:
        # check if exists in unique_list or not
        if x not in unique_list:
            unique_list.append(x)
            # print list
    # average_x_vals = []
    # for val in unique_list:
    #     sum = val[0][0] * val[1]
    #     if val[0][0] not in average_x_vals:
    #         average_x_vals.append([val[0][0], sum])
    #     else:
    #         old_sum = average_x_vals[val[0][0]]
    #         average_x_vals[val[0][0], ] = average_x_vals[val[0][0], sum]
        #average =
    print("Unique list: ", unique_list)


    new_dataset = averageEachXValue(unique_list)

                # Append the values to your new dataset(s).
                # pastFreqOfHelping0 is x, avgResponse is y.
                # No need to color it by count since count has been averaged away
    #print(new_dataset)

    x_vals = []
    y_vals = []
    for i in new_dataset:
        x_vals.append([i[0]])
        y_vals.append(i[1])


        # for i in range(len(xSamples)):
    #     for j in range(len(ySamples)):
    #         xAndY.append([xSamples[i], ySamples[j]])
    #         xs.append(xSamples[i])
    #         ys.append(ySamples[j])
            #zs = [x * y for x,y in xAndY]






    # Generate the parameter range
    parameterizedFunc = newParametrizedFunction
    # parameterizedFunc = oneDLinearParametrizedFunction
    #
    paramValues = []
    # for u in range(-10, 10, 1):
    #     for k in range(-100, 100, 1):
    #             paramValues.append([u/100, k/100])

    #paramValues = [[5, -50, 1]]
    # for u in range(0, 10, 1):
    #     for k in range(-100, 0, 1):
    #         for b in range(-50, 50, 1):
    #             paramValues.append([u/10, k, b/10])

    for u in range(0, 10, 1):
        for k in range(-100, 0, 1):
            for b in range(-5, 5, 1):
                paramValues.append([u/10, k, b])


    # parameterizedFunc = quadraticParameterizedFunction
    #
    # paramValues = []
    # for a in range(-50, 50, 2):
    #      for b in range(-50, 50, 2):
    #          for c in range(-50, 50, 2):
    #              paramValues.append([a, b, c])

    # parameterizedFunc = oneDExponentialParametrizedFunction
    #
    # paramValues = []
    # for k in range(2, 100, 1):
    #     paramValues.append([k])

    # bestParams = performOptimization(xs, ys, parameterizedFunc, paramValues)

    # parameterizedFunc = twoDLinearParametrizedFunction
    #
    # paramValues = []
    # for a in range(-5, 5, 2):
    #      for b in range(-4, 5, 2):
    #          for c in range(-4, 5, 2):
    #             paramValues.append([a, b, c])
    #
    # #print(paramValues)

    #bestParams = performOptimization(xAndY, zs, parameterizedFunc, paramValues)

    bestParams = performOptimization(xs, ys, parameterizedFunc, paramValues)


    ############################################################################
    # STEP 2
    # Write code to visualize 1) the data, and 2) the bestFunction, using matplotlib.
    # Matplotlib has great tutorials. Start with the scatterplot tutorial
    # https://matplotlib.org/3.2.2/gallery/shapes_and_collections/scatter.html
    # and the plot tutorial https://matplotlib.org/tutorials/introductory/pyplot.html
    #
    ############################################################################

    # yPredVals = []
    # plt.scatter(xs, ys)
    # func = parameterizedFunc(bestParams)
    # for x in x:
    #     yPredVals.append(func(x))
    # scatterplot = plt.scatter(xs, ys, c=count, vmin=0, vmax=50, s=35)
    # plt.colorbar(scatterplot)
    # plt.xlabel('X axis: Past Frequency of Helping Accurately')
    # plt.ylabel('Y axis: Human Response')
    # plt.title("Busyness: Free Time")
    # plt.show()
    # plt.plot(xs, yPredVals)
    # plt.show()



    plt.scatter(x_vals, y_vals)
    yPredVals = []
    xAndYPredVals = []
    #countPred = []
    #xAndYPredAndCount = []
    func = parameterizedFunc(bestParams)
    xs.sort(key=lambda x: x[0])
    for x in xs:
        y = func(x)
        yPredVals.append(y)
        #xAndYPredVals.append([x, y])
    #print(xAndYPredVals)
    print("XS: ", xs)
    print("yPredVals: ", yPredVals)
    #plt.xticks(np.arange(0, 1, step=0.05))
    plt.plot(xs, yPredVals)
    plt.xlabel('X axis: Past Frequency of Asking')
    plt.ylabel('Y axis: Average Human Response')
    plt.title("Busyness: Free Time")
    plt.show()


    # for val in xAndYPredVals:
    #     c = xAndYPredVals.count(val)
    #     if(val not in xAndYAndCount):
    #         xAndYPredAndCount.append([val, c])

    # uniquePredlist = []
    # for x in xAndYPredAndCount:
    #     if x not in uniquePredlist:
    #         uniquePredlist.append(x)





#     zPredVals = []
#     fig = plt.figure()
#     ax = fig.add_subplot(111, projection='3d')
#     #print(len(xSamples))
#     #print(len(ySamples))
#     #print("xs: ", xSamples)
#     #print("ys: ", ySamples)
#     #print("zs: ", zs)
#
#     ax.scatter(xs, ys, zs)
#     func = parameterizedFunc(bestParams)
#
#
#     #print(zPredVals)
#     #print(zs)
#     xArr = []
#     for x in xSamples:
#         xArr.append(x)
#     yArr = []
#     for y in ySamples:
#         yArr.append(y)
#     zArr = []
#     for z in zPredVals:
#         zArr.append([z])
#     X = np.arange(0,1.1,0.1)
#     Y = np.arange(0,1.1,0.1)
#     #X = np.array(xs).reshape((-1, 1))
#     #Y = np.array(ys).reshape((-1, 1))
#     for x in X:
#         for y in Y:
#             zPredVals.append(func([x, y]))
#     X, Y = np.meshgrid(X, Y)
#     Z = np.array(zPredVals).reshape(X.shape)
#     ax.plot_wireframe(X, Y, Z, rstride=1, cstride=1)
#     ax.set_xlabel('X axis: Frequency of Ask')
#     ax.set_ylabel('Y axis: Willingness to Help')
#     axes.set_title("Free Time")

#     ax.set_zlabel('Z axis')
#
# plt.show()

############################################################################
    # STEP 3
    # Once the above two steps work, message Amal, before starting on step 3.
    #
    # Generate additional datasets for the 3D linear parametriced function
    # (don't graph this since it is very difficult to graph in 4D), and the
    # 1D quadratic function. Also, play around with scenarios where
    # your data is one type (e.g. 1D linear or 1D quadratic) and the parametrized
    # function is another type. Also, play around with cases where your paramValues
    # are either two coarse (e.g. large distances between successive param values),
    # too fine (such small distance between successive paramValues that you have a
    # lot of paramValues to iterate over), and in the wrong range (e.g. if the
    # true parameters are m=10 and b=-3, try paramValues where the ranges are far
    # from the actual values). Finally, write your own new parameterized functions,
    # and play around with fitting that to different datasets. Basically, the
    # point of step 3 is to: 1) test your code to make sure it works in a variety
    # of scenarios, and 2) gain intuition over the strengths and weaknesses of
    # this brute-force approach to optimization.
    #
    #
    ############################################################################

    # make an exponential (y = k^x) 1D parametized function


    ############################################################################
    # STEP 4
    #
    # By this time, Amal should have provided you real data from the experiment.
    # The xs are 3D (frequency, busyness, prosociality). Try to write out
    # parameterized functions for the real data, see how well they fit, and try
    # to find a parameterized function that fits well. This part is challenging,
    # so ask Amal for help as needed.
    #
    ############################################################################
