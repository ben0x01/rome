import random
import string


def generate_random_string(length: int = None) -> str:
    if length is None:
        length = random.randint(5, 20)
    characters = string.ascii_lowercase
    return "".join(random.choice(characters) for _ in range(length))


def need_to_generate_random_symbol() -> bool:
    return random.randint(1, 100000) < 50000


def get_random_route(routes: list) -> list:
    return random.choice(routes)
