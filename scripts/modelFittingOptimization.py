import random
import matplotlib.pyplot as plt
import numpy as np

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
        output = a*x**2 + b*x + c
        return output
    return quadraticFunction

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
    average = 0
    small = 9223372036854775807
    size = 0
    for val in paramValues:
        func = parameterizedFuncion(val)
        for x in xs:
            yPred = func(x)
            y = ys[index]
            sqredError = (y-yPred)**2
            index = index + 1
            average = average + sqredError
            size = len(xs)
        if average/size < small:
            small = average/size
        index = 0
        average = 0

    print(small)
    return small

    bestParams = None
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
    xs = [[x/100] for x in range(0, 100)]
    ys = [10*x[0]-3+random.random() for x in xs]

    # Generate the parameter range
    paramValues = []
    for m in range(-100, 100, 1):
        for b in range(-100, 100, 1):
            paramValues.append([m, b])

    bestParams = performOptimization(xs, ys, oneDLinearParametrizedFunction, paramValues)

    ############################################################################
    # STEP 2
    # Write code to visualize 1) the data, and 2) the bestFunction, using matplotlib.
    # Matplotlib has great tutorials. Start with the scatterplot tutorial
    # https://matplotlib.org/3.2.2/gallery/shapes_and_collections/scatter.html
    # and the plot tutorial https://matplotlib.org/tutorials/introductory/pyplot.html
    #
    ############################################################################

    yPredVals = []
    plt.scatter(xs, ys)
    for x in xs:
        yPredVals.append(10*x[0] + (-3)) #what should I put in for m and b
    plt.plot(xs, yPredVals)
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
