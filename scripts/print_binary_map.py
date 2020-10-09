def print_binary_map(map):
    one_char = u"\u2B1C" # white square
    zero_char = u"\u2B1B" # black square
    for row in map:
        print("".join([one_char if val == 1 else zero_char for val in row]))

a = [[0,0,1,0,0],[1,1,0,1,0],[1,0,0,0,1],[1,1,1,1,1],[0,0,0,0,0]]
print_binary_map(a)
