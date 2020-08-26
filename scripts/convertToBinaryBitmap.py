import json
import pprint
import numpy as np

def loadGameLog(filepath):
    f = open(filepath,)
    data = json.load(f)
    return data

def print_binary_map(map):
    one_char = u"\u2B1C"
    zero_char = u"\u2B1B"
    print(zero_char)
    for row in map:
        print("".join([one_char if val == 1 else zero_char for val in row]))

if __name__ == "__main__":
    filepath ="../flask/assets/map3.json"
    data = loadGameLog(filepath)
    twoDArray = []
    for i in data["layers"]:
        if i["name"] == "World":
            twoDArray = np.reshape(i["data"], (50, 44))
    twoDArray[twoDArray != 0] = 1
    print_binary_map(twoDArray)