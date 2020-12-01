import random

def get_random_alpha_numeric_string(stringLength=10):
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join((random.choice(lettersAndDigits) for i in range(stringLength)))

def print_binary_map(map):
    zero_char = u"\u2B1C"
    one_char = u"\u2B1B"
    print(zero_char)
    for row in map:
        print("".join([one_char if val else zero_char for val in row]))
