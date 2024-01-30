import json


def save_file(file_path, data):
    f = open(file_path, 'w')
    f.write(data)
    f.close()


def load_setup():
    global setup
    try:
        f = open('setup.json', 'r')
        return json.load(f)
    except:
        return {}