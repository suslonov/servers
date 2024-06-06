import os
import io
from PIL import Image
import pickle
import json
import pandas as pd
import torch
import torch.nn as nn
from torchvision import models, transforms
from db_nn_art import db_nn_art
# import requests

# headers = {'Content-Type': "application/json"}
# url = "http://nn-art.r-synergy.com/to-process"
# res = requests.get(url, headers=headers)
# if res.status_code != 200:
#     print("error getting coinmarketcap data", res.status_code)
#     print(res.json())
#     exit(0)
# d = res.json()
# if not d:
#     exit(0)

with db_nn_art() as db:
    list_of_loaded_images = db.get_unprocessed_images_list()

if not list_of_loaded_images:
    exit(0)

data_dir = '/media/Data2/data/images'
metadata_fn = "/media/Data2/data/metadata.json"
features_dir = "/media/Data2/data/features"
features_file = os.path.join(features_dir, "pytorch_rn50.pkl")
featurize_images = True
device = torch.device("cuda:0")

data_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

model = models.resnet50(pretrained=True)
model.eval()
model.to(device)
cut_model = nn.Sequential(*list(model.children())[:-1])

all_outputs = []
all_ids = []

with open(features_file, "rb") as f:
    (all_outputs, all_ids) = pickle.load(f)

metadata = pd.read_json(metadata_fn, lines=True)

for l in list_of_loaded_images:
    with db_nn_art() as db:
        image_data = db.get_image_from_db(l[0])

    buf = io.BytesIO(image_data)
    image = Image.open(buf).convert("RGB")
    # image
    inputs = data_transform(image)
    inputs = inputs.reshape([1, 3, 224, 224])
    inputs = inputs.to(device)
    outputs = torch.squeeze(cut_model(inputs)).detach()

    k = 10
    with torch.no_grad():
        features = torch.from_numpy(all_outputs).float().to("cpu:0")
        features = features / torch.sqrt(torch.sum(features ** 2, dim=1, keepdim=True))
        features = features.to(device)
        # indicies = torch.arange(0, features.shape[0]).to(device)
        # print("loaded features")

    with torch.no_grad():
        ll = len(features)//2
        all_dists1 = torch.sum(features[0:ll] * outputs, dim=1).to(device)
        all_dists2 = torch.sum(features[ll:] * outputs, dim=1).to(device)
        all_dists = torch.cat((all_dists1, all_dists2), 0)

        # all_dists = torch.sum(features * outputs, dim=1).to(device)
        dists, inds = torch.topk(all_dists, k, sorted=True)
        matches = [inds.cpu().numpy()]

    image_matches = []
    for m in matches[0]:
        image_matches.append((metadata.iloc[m]["Title"], metadata.iloc[m]["Thumbnail_Url"], metadata.iloc[m]["Image_Url"]))

    with db_nn_art() as db:
        db.add_results_to_db(json.dumps(image_matches), l[0])
        db.set_image_processed(l[0])


