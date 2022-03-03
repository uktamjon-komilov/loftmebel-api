from random import choices
from string import digits


def generate_random_number(n=6):
    return "".join(choices(digits, k=n))