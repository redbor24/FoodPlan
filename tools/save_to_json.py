import json


def save_to_json(items, filename):
    with open(filename, 'a') as file:
        json.dump(items, file, indent=4, ensure_ascii=False)
