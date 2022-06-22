import base64

import math
from numpy import empty
from torch import equal
from detect import run
from flask import Flask, request
from os.path import exists
import yaml
import cv2
import numpy as np
from PIL.ExifTags import *
from PIL import Image

app = Flask(__name__)

def save_image(encoded_image, img_name):
    image_name = "images/" + img_name
    with open(img_name, "wb") as fh:
        fh.write(base64.b64decode(encoded_image))
    
    im = Image.open(image_name)
    im=im.rotate(270, expand=True)
    im.save(image_name)

@app.route('/test-img', methods=['GET'])
def get_test_img():
    try:
        img = request.args.get('image')
        print(img)
        if(exists(img)):
            img = img
        elif(exists("test-images/" + img)):
            img = "test-images/" + img
        else:
            img = "test-images/test3.jpg"
    except:
        img = "test-images/test3.jpg"
    run(img)
    return "ok"

@app.route('/detect', methods=['POST'])
def detect():
    request_data = request.get_json()
    img = request_data['image']

    save_image(img)
    run("capture.jpg")

    return request_data['image']

@app.route("/test", methods=['GET'])
def get_card_placing():
    with open("runs/detect/exp/labels/12.txt", encoding="utf-8") as f:
        res = [[l for l in line.split()] for line in f] # load detections into list of lists.
        test = map_ids_with_classes()
        for i in range(len(res)):
            id = res[i][0]
            
            # Replace class id with class name
            res[i][0] = test.get(int(id))
            print(id + " " +test.get(int(id)))

    talon, remaining = find_talon(res)
    founds, remaining1 = find_foundations(remaining)
    #tableaus = find_tableaus(remaining1)
    print(talon)
    print("'''"*20)
    print(founds)
    print("'''"*20)
    
    print(remaining1)
    test_tableaus(remaining1)
    return""# convert_to_json(founds, talon, None)

def convert_to_json(foundation, talon, tableaus):
    data = {"talon": talon,"f1": foundation[0], 
    "f2": foundation[1], "f3": foundation[2], "f4": foundation[3],
    "t1": tableaus[0], "t2": tableaus[1], "t3":tableaus[2],
    "t4": tableaus[3], "t5": tableaus[4], "t6": tableaus[5],
    "t7": tableaus[6]}
    return data

def test_tableaus(tableaus):
    tableaus.sort(key=lambda x: x[1])

    tab = [[],[],[],[],[],[],[]]
    seen = []
    for i in tableaus:
        if(i[0] in seen):
            continue
        if float(i[1]) < 0.14:
            tab[0].append(i[0])
        elif float(i[1]) < 0.28:
            tab[1].append(i[0])
        elif float(i[1]) < 0.4:
            tab[2].append(i[0])
        elif float(i[1]) < 0.54:
            tab[3].append(i[0])
        elif float(i[1]) < 0.68:
            tab[4].append(i[0])
        elif float(i[1]) < 0.81:
            tab[5].append(i[0])
        elif float(i[1]) < 0.96:
            tab[6].append(i[0])
        
        seen.append(i[0])

    print(tab)
        

def find_tableaus(tableaus):
    tableaus.sort(key=lambda x: x[1])
    ts = []
    seen = []
    for i, t in enumerate(tableaus):
        if t[0] in seen:
            continue
        seen.append(t[0])
        ts.append(t)

    tableau = [[], [], [], [], [], [], []]

    print(tableaus)
    
    lastx = 0
    for t in tableaus:
        continue

    index = 0
    prev = ts[0]
    tableau[0].append(prev[0])
    for t in ts[1:]:
        cal = math.dist((float(prev[1]), float(prev[2])), (float(t[1]), float(t[2])))
        if cal > 0.1:
            index += 1
            print(f"index: {index}")
            print(f"cal: {cal}")

        tableau[index].append(t[0])
        prev = t
    return tableau

def find_foundations(detection_list):
    foundations = []
    rest = []
    for i in detection_list:
        if float(i[1]) > 0.35 and float(i[2]) < 0.3:
            foundations.append(i)
        else:
            # card is not in foundation
            rest.append(i)
    
    # check which foundation is furthest to the left
    foundations.sort(key=lambda x: x[1])
    founds = []
    seen = []
    for i, found in enumerate(foundations):
        if not found[0] in seen:
            seen.append(found[0])
            founds.append(found[0])
    
    # dirty hack to ensure the length is always 4
    while len(founds) < 4:
        founds.append("")

    return founds, rest

def find_talon(detection_list):
    min_x = 1
    min = []
    for i in detection_list:
        if float(i[1]) < min_x and float(i[2]) < 0.3:
            min_x = float(i[1])
            min = i

    remaining = [i for i in detection_list if min[0] != i[0]]
    return min[0], remaining

def map_ids_with_classes():
    with open("data/data.yaml") as stream:
        names = yaml.load(stream)['names']
        ids = [i for i in range(52)]
        res = {ids[i]: names[i] for i in range(len(names))}
    return res


if __name__ == "__main__":
    app.run()