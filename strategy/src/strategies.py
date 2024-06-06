import os
if  "__file__" in globals():
    os.sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    os.sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
else:
    os.sys.path.append(os.path.abspath('.'))
    os.sys.path.append(os.path.dirname(os.path.abspath('.')))

from flask import Flask, render_template, request, jsonify, flash
from datetime import datetime, timedelta
import hashlib
import numpy as np

application = Flask(__name__)
application.secret_key = 'random string'
sub_path = "/"

from deribit_minimax_web import deribit_minimax_web_web, deribit_minimax_web_get_stop_losses_touched
from deribit_minimax_web import deribit_minimax_web_get_instruments, deribit_minimax_web_write_bundle
from deribit_minimax_web import deribit_minimax_web_get_active_positions, deribit_minimax_web_update_positions
from deribit_minimax_web import deribit_minimax_web_get_active_bundles, deribit_minimax_web_close_positions, deribit_minimax_web_get_closed_bundles
from deribit_minimax_monitor import deribit_minimax_monitor_get_page_data
import server_output_module

MIN_END_TERM = 3
MAX_TERM = 90
DEFAULT_TERM = 3

def add_positions_page():
    current_date = datetime.utcnow().replace(microsecond=0)
    instruments = []
    for i in deribit_minimax_web_get_instruments():
        i_expiration = datetime.strptime(i.split("-")[1], '%d%b%y')
        if i_expiration >= current_date + timedelta(days=MIN_END_TERM) and i_expiration <= current_date + timedelta(days=MAX_TERM):
            instruments.append(i)
    return render_template('position-add-deribit-minimax.html', sub_path = "/minimax_add_position", 
                           bundle_id = None,
                           open_date = current_date,
                           expiration = None,
                           instruments = instruments,
                           bundle = [0, 1, 2, 3])


@application.route('/minimax_add_position', methods = ['POST'])
def position_add_deribit_minimax():
    current_date = datetime.utcnow().replace(microsecond=0)
    MAX_INSTRUMENTS = 4
    if request.method == 'POST':
        result = request.form
        open_date_bundle = result.get("open_date", default="")
        if len(open_date_bundle) == 19:
            open_date_bundle = datetime.strptime(open_date_bundle, '%Y-%m-%d %H:%M:%S')
        else:
            open_date_bundle = datetime.strptime(open_date_bundle, '%Y-%m-%d')
        expiration = datetime.strptime(result.get("expiration", default=""), '%Y-%m-%d')
        bundle = []
        all_instruments = deribit_minimax_web_get_instruments()
        for i in range(MAX_INSTRUMENTS):
            instrument = result.get("instrument" + str(i), default="").strip()
            if not instrument or not instrument in all_instruments:
                continue
            number = float(result.get("number" + str(i), default=""))
            direction = result.get("direction" + str(i), default="").lower()
            if direction not in ["buy", "sell"]:
                continue
            open_date = result.get("open_date" + str(i), default="")
            if open_date == "":
                open_date = open_date_bundle
            else:
                if len(open_date) == 19:
                    open_date = datetime.strptime(open_date, '%Y-%m-%d %H:%M:%S')
                else:
                    open_date = datetime.strptime(open_date, '%Y-%m-%d')
            initial_price = float(result.get("initial_price" + str(i), default=""))
            initial_margin = float(result.get("initial_margin" + str(i), default=""))
            bundle.append({"instrument": instrument, "status": 1, "number" :number, 
                           "direction": 1 if direction == "buy" else -1, 
                           "open_date": open_date, "initial_price": initial_price, 
                           "initial_margin": initial_margin})
        bundle_id = deribit_minimax_web_write_bundle(open_date_bundle, expiration, bundle)
        instruments = []
        for i in all_instruments:
            i_expiration = datetime.strptime(i.split("-")[1], '%d%b%y')
            if i_expiration >= current_date + timedelta(days=MIN_END_TERM) and i_expiration <= current_date + timedelta(days=MAX_TERM):
                instruments.append(i)
        return render_template('position-add-deribit-minimax.html', sub_path = "/minimax_add_position", 
                               bundle_id = bundle_id,
                               open_date = open_date_bundle,
                               expiration = expiration.date(),
                               instruments = instruments,
                               bundle = bundle)


def update_positions_page():
    to_update = deribit_minimax_web_get_active_positions()
    return render_template('position-update-deribit-minimax.html', sub_path = "/minimax_update_position", 
                           to_update = to_update)


@application.route('/minimax_update_position', methods = ['POST'])
def position_update_deribit_minimax():
    to_update = deribit_minimax_web_get_active_positions()
    if request.method == 'POST':
        result = request.form
        for i in to_update:
            key = i["instrument"] +"_" + ("-1" if i["direction"] == -1 else "+1")
            current_price = result.get("price_" + key, default="")
            maintenance_margin = result.get("margin_" + key, default="")
            if current_price:
                i["current_price"] = float(current_price)
            if maintenance_margin:
                i["maintenance_margin"] = float(maintenance_margin)
        deribit_minimax_web_update_positions(to_update)
        return render_template('position-update-deribit-minimax.html', sub_path = "/minimax_update_position", 
                               to_update = to_update)

def close_positions_page():
    bundles, positions = deribit_minimax_web_get_active_bundles()
    return render_template('position-close-deribit-minimax.html', sub_path = "/minimax_close_position", 
                           bundles = bundles, positions = positions)

def report_positions_page():
    bundles, positions = deribit_minimax_web_get_closed_bundles()
    return render_template('position-report-deribit-minimax.html', sub_path = "/minimax_close_position", 
                           bundles = bundles, positions = positions)


@application.route('/minimax_close_position', methods = ['POST'])
def position_close_deribit_minimax():
    bundles, positions = deribit_minimax_web_get_active_bundles()
    if request.method == 'POST':
        result = request.form
        to_close = []
        for p in positions:
            key = str(p["bundle_id"])  + "_" +  p["instrument"]
            if "close_" + key in result:
                close_date = result.get("close_date_" + key, default="")
                if close_date:
                    if len(close_date) == 19:
                        close_date = datetime.strptime(close_date, '%Y-%m-%d %H:%M:%S')
                    else:
                        close_date = datetime.strptime(close_date, '%Y-%m-%d')
                else:
                    close_date = datetime.utcnow()
                end_price = result.get("end_price_" + key, default="")
                to_close.append((p["bundle_id"], p["instrument"], end_price, close_date))

        deribit_minimax_web_close_positions(to_close)
        bundles, positions = deribit_minimax_web_get_active_bundles()
        return render_template('position-close-deribit-minimax.html', sub_path = "/minimax_close_position", 
                               bundles = bundles, positions = positions)

@application.route('/minimax', methods = ['POST', 'GET'])
def home_page_deribit_minimax_web():
    stop_losses = [(l[0], l[1], l[2].date(), l[3]) for l in deribit_minimax_web_get_stop_losses_touched()]
    
    if request.method == 'POST':
        result = request.form
        button_selector = result.get("SubmitButton", default="")
        if button_selector is None:
            button_selector = "RunCalculation"
        term = int(result.get("term", default=DEFAULT_TERM))
        if button_selector == "AddPositions":
            return add_positions_page()
        if button_selector == "UpdatePositions":
            return update_positions_page()
        if button_selector == "Portfolio":
            return close_positions_page()
        if button_selector == "Report":
            return report_positions_page()
        process_id = result.get("process_id", default="")
        if not len(process_id) == 32 or sum([smb == " " for smb in process_id]) > 0:
            process_id = ""
        if not process_id:
            process_id = hashlib.md5(("minimax" + str(datetime.now())).encode()).hexdigest()
            return render_template('home-page-deribit-minimax.html', sub_path = "/minimax", 
                                    form_submitted = 0,
                                    process_id = process_id,
                                    stages = [],
                                    recommendations = [],
                                    stop_losses = stop_losses,
                                    term=term)

        stages = []; recommendations=[]
        stages, recommendations = deribit_minimax_web_web(process_id, term)
        return render_template('home-page-deribit-minimax.html', sub_path = "/minimax",
                                form_submitted = 1 if not recommendations else 0,
                                process_id = process_id,
                                stages = stages,
                                recommendations = recommendations,
                                stop_losses = stop_losses,
                                term=term)
    else:
        process_id = hashlib.md5(("minimax" + str(datetime.now())).encode()).hexdigest()
        term = DEFAULT_TERM
        return render_template('home-page-deribit-minimax.html', sub_path = "/minimax", 
                                form_submitted = 0,
                                process_id = process_id,
                                stages = [],
                                recommendations = [],
                                stop_losses = stop_losses,
                                term=term)


@application.route('/minimax-monitor3908903214', methods = ['GET'])
def home_page_deribit_minimax_monitor():
    now_date, wallet_data, wallet_names, exchange_positions, exchange_positions_names, exchange_orders, exchange_orders_names = deribit_minimax_monitor_get_page_data()
    return render_template('home-page-deribit-minimax-monitor.html', 
                           now_date=now_date,
                           wallet_data=wallet_data,
                           wallet_names=wallet_names,
                           exchange_positions=exchange_positions,
                           exchange_positions_names=exchange_positions_names,
                           exchange_orders=exchange_orders,
                           exchange_orders_names=exchange_orders_names)

@application.route('/mev-bribes-monitor-json', methods = ['GET'])
def home_page_mev_bribes_monitor_json():
    return jsonify(server_output_module.monitor_output1()), 200

@application.route('/mev-bribes-monitor', methods = ['POST', 'GET'])
def home_page_mev_bribes_monitor():
    row = None
    if request.method == 'POST':
        result = request.form
        # flash(result)
        row = result.get("row", default=None)
        if row:
            row = int(row)
        
    attack_summary_table, one_attack_type_line = server_output_module.monitor_output2(row, 100)
    return render_template('home-page-attack-history.html', sub_path = "/mev-bribes-monitor",
                           attack_summary_table = attack_summary_table,
                           one_attack_type_line = one_attack_type_line,
                           checked_row = (0 if row is None else row))
