import random
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter

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
        output = m0*x[0] + m1*x[1]
        return output
    return twoDLinearFunction

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
        func = parameterizedFuncion(params)
        for x in xs:
            yPred = func(x)
            y = ys[index]
            sqredError = (y-yPred)**2
            index = index + 1
            sum = sum + sqredError
            size = len(xs)
        print(minSumSqredError)
        print(sum/size)
        if minSumSqredError is None or sum/size < minSumSqredError:
            minSumSqredError = sum/size
            bestParams = params

        index = 0
        sum = 0

    print(bestParams, type(bestParams))
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
    return bestParams

if __name__ == "__main__":
    # Generate a fake dataset. This is a liner dataset, where the line with best
    # fit should be something like y=10x-3

    # xs = [[x/100] for x in range(0, 100)]
    # ys = [10*x[0]-3+(random.random()-0.5)*10 for x in xs]

    # xs = [[x/100] for x in range(0, 100)]
    # ys = [10**x[0]+(random.random()-0.5)*10 for x in xs]

    xs = [[x/100] for x in range(0, 100)]
    test = []
    count = 1/100
    ys = []
    for x in xs:
        ys.append([x[0], count+1/100])
        test.append([count+1/100])
    zs = [10*y[0]+(random.random()-0.5)*10 for y in ys]
    print(len(xs))
    print(len(ys))


    # Generate the parameter range
    # parameterizedFunc = oneDLinearParametrizedFunction
    #
    # paramValues = []
    # for m in range(-100, 100, 1):
    #     for b in range(-100, 100, 1):
    #         paramValues.append([m, b])


    # parameterizedFunc = quadraticParameterizedFunction
    #
    # paramValues = []
    # for a in range(-50, 50, 2):
    #     for b in range(-50, 50, 2):
    #         for c in range(-50, 50, 2):
    #             paramValues.append([a, b, c])

    # parameterizedFunc = oneDExponentialParametrizedFunction
    #
    # paramValues = []
    # for k in range(2, 100, 1):
    #     paramValues.append([k])

    parameterizedFunc = twoDLinearParametrizedFunction

    paramValues = []
    for a in range(-5, 5, 2):
         for b in range(-5, 5, 2):
            paramValues.append([a, b])

    bestParams = performOptimization(ys, zs, parameterizedFunc, paramValues)

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
    # for x in xs:
    #     yPredVals.append(func(x))
    # plt.plot(xs, yPredVals)
    # plt.show()


    zPredVals = []
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    print(len(xs))
    print(len(test))
    ax.scatter(xs, test, zs)
    func = parameterizedFunc(bestParams)

    for y in ys:
         zPredVals.append(func(y))
    print(zPredVals)
    X = np.arange(-5, 5, 0.25)
    Y = np.arange(-5, 5, 0.25)
    X, Y = np.meshgrid(X, Y)
    R = np.sqrt(X**2 + Y**2)
    Z = np.sin(R)
    surf = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm, linewidth=0, antialiased=False)
    ax.set_zlim(-1.01, 1.01)
    ax.zaxis.set_major_locator(LinearLocator(10))
    ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
    fig.colorbar(surf, shrink=0.5, aspect=5)
    plt.show()

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
