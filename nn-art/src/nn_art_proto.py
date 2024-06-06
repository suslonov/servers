
import datetime
import json
from flask import Flask, render_template, request, jsonify
# from flask import flash

from db_nn_art import db_nn_art

application = Flask(__name__)
application.secret_key = 'random string'
sub_path = "/"

@application.route(sub_path, methods = ['POST', 'GET'])
def home_page_wd():
    if request.method == 'POST':
        file = request.files['inputFile']
        data = file.read()
        ts = datetime.datetime.now().timestamp()

        with db_nn_art(local=True) as db:
            db.add_image_to_db(data, ts)

        return render_template('home-page-art.html', sub_path=sub_path, image_list=[], image_ts=str(ts))
    else:
        return render_template('home-page-art.html', sub_path=sub_path, image_list=[], image_ts="")

@application.route(sub_path + "renew", methods = ['POST'])
def renew_page_wd():
    if request.method == 'POST':
        result = request.form
        ts = result.get('image_ts')

        with db_nn_art(local=True) as db:
            image_list_json = db.get_results_from_db(ts)

        if image_list_json is None:
            image_list = []
        else:
            image_list = json.loads(image_list_json)

        return render_template('home-page-art.html', sub_path=sub_path, image_list=image_list, image_ts=ts)
    else:
        return render_template('home-page-art.html', sub_path=sub_path, image_list=[], image_ts="")

@application.route(sub_path + "results/<ts>", methods = ['GET'])
def results_page_wd(ts):
    with db_nn_art(local=True) as db:
        image_list_json = db.get_results_from_db(ts)

    if image_list_json is None:
        image_list = []
    else:
        image_list = json.loads(image_list_json)

    return render_template('home-page-art.html', sub_path=sub_path, image_list=image_list, image_ts=ts)

@application.route(sub_path + "to-process", methods = ['GET'])
def to_process_page_wd():
    with db_nn_art(local=True) as db:
        l = db.get_unprocessed_images_list()
    ll = []
    for i in l:
        ll.append(str(i[0]))
    return jsonify(ll), 200




