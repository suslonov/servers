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
import cvix_page

application = Flask(__name__)
application.secret_key = 'random string'
sub_path = "/"

def check_parameter_version(ver):
    if type(ver) != str:
        return ""
    lower_ver = ver.lower()
    if lower_ver not in ["v003", "v004", "v0041", "v0042", "v0043", "v0045", "v0046"]:
        return ""
    return lower_ver

@application.route(sub_path, methods = ['POST', 'GET'])
def home_page_wd():
    return render_template('home-page-blank.html')


@application.route('/<ver>/cvi', methods = ['GET'])
def render_cvix(ver):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    cvi_btc, cvi_eth, cvi, ema_cvi, ema_cvi_btc, ema_cvi_eth, chart_values_btc, chart_values_eth, chart_values = cvix_page.cvi_chart_page(ver)
    return render_template('home-page-cvi-' + ver +'.html', cvi_btc=cvi_btc, cvi_eth=cvi_eth, cvi=cvi, ema_cvi_btc=ema_cvi_btc, ema_cvi_eth=ema_cvi_eth, ema_cvi=ema_cvi, chart_values_btc=chart_values_btc, chart_values_eth=chart_values_eth, chart_values=chart_values)

@application.route('/<ver>/cvijson', methods = ['GET'])
def json_cvix(ver):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    cvi = cvix_page.cvix_last(ver)
    data = {'cvi': cvi[3], 'timestamp': cvi[0], 'cvi-btc': cvi[1], 'cvi-eth': cvi[2], 'cvi-ema': cvi[4], 'cvi-btc-ema': cvi[5], 'cvi-eth-ema': cvi[6], 'previous-timestamp': cvi[7], 'previous-timestamp-btc': cvi[8], 'previous-timestamp-eth': cvi[9], 'version': '0.0.4'}
    return jsonify(data), 200

@application.route('/<ver>/cvijson1', methods = ['GET'])
def json_cvix_cvxjson1(ver):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    cvi = cvix_page.cvix_last(ver)
    data = {"status": "Success", "cviData": [round(cvi[0].timestamp()*1000), cvi[1], cvi[4]], 'version': '0.0.3'}
    return jsonify(data), 200

@application.route('/<ver>/cvijson1000min', methods = ['GET'])
def json_cvix_1000_minute(ver):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    cvi = cvix_page.cvix_1000(ver, 'minute')
    return jsonify(cvi), 200

@application.route('/<ver>/cvijson100020min', methods = ['GET'])
def json_cvix_1000_20min(ver):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    cvi = cvix_page.cvix_1000_20min(ver)
    return jsonify(cvi), 200

@application.route('/<ver>/cvijson1000hour', methods = ['GET'])
def json_cvix_1000_hour(ver):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    cvi = cvix_page.cvix_1000(ver, 'hour')
    return jsonify(cvi), 200

@application.route('/<ver>/cvijson1000day', methods = ['GET'])
def json_cvix_1000_day(ver):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    cvi = cvix_page.cvix_1000(ver, 'day')
    return jsonify(cvi), 200

@application.route('/<ver>/cvi_changes_all', methods = ['GET'])
def get_changes_all(ver):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    cvi = cvix_page.cvix_changes_all(ver)
    return jsonify(cvi), 200

@application.route('/<ver>/cvi_changes_N/<n>', methods = ['GET'])
def get_changes_from_db(ver, n):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    if not n.isnumeric():
        return "Error 400: not a number", 400
    cvi = cvix_page.cvix_changes_N(ver, n)
    return jsonify(cvi), 200

@application.route('/<ver>/cvi_changes_all_ETH', methods = ['GET'])
def get_changes_all_ETH(ver):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    cvi = cvix_page.cvix_changes_all(ver, curr='ETH')
    return jsonify(cvi), 200

@application.route('/<ver>/cvi_changes_N_ETH/<n>', methods = ['GET'])
def get_changes_ETH_from_db(ver, n):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    if not n.isnumeric():
        return "Error 400: not a number", 400
    cvi = cvix_page.cvix_changes_N(ver, n, curr='ETH')
    return jsonify(cvi), 200


@application.route('/<ver>/ethvol', methods = ['GET'])
def render_ethvol(ver):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    ethvol_eth, ema_ethvol_eth, chart_values_eth = cvix_page.cvi_chart_page(ver, "ETH")
    return render_template('home-page-cvi-' + ver +'.html', ethvol_eth=ethvol_eth, ema_ethvol_eth=ema_ethvol_eth, chart_values_eth=chart_values_eth)

@application.route('/<ver>/ethvoljson', methods = ['GET'])
def json_ethvol(ver):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    ethvol = cvix_page.cvix_last(ver, "ETH")
    data = {'ethvol-eth': ethvol[1], 'timestamp': ethvol[0], 'ethvol-eth-ema': ethvol[2], 'previous-timestamp-eth': ethvol[3], 'version': '0.0.4.3'}
    return jsonify(data), 200

@application.route('/<ver>/ethvoljson1000min', methods = ['GET'])
def json_ethvol_1000_min(ver):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    ethvol = cvix_page.cvix_1000(ver, 'minute', "ETH")
    return jsonify(ethvol), 200

@application.route('/<ver>/ethvoljson1000hour', methods = ['GET'])
def json_ethvol_1000_hour(ver):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    ethvol = cvix_page.cvix_1000(ver, 'hour', "ETH")
    return jsonify(ethvol), 200

@application.route('/<ver>/ethvoljson1000day', methods = ['GET'])
def json_ethvol_1000_day(ver):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    ethvol = cvix_page.cvix_1000(ver, 'day', "ETH")
    return jsonify(ethvol), 200

@application.route('/<ver>/ethvol_changes_all', methods = ['GET'])
def get_changes_all_ETHVOL(ver):
    return get_changes_all_ETH(ver)

@application.route('/<ver>/ethvol_changes_N/<n>', methods = ['GET'])
def get_changes_ETHVOL_from_db(ver, n):
    return get_changes_ETH_from_db(ver, n)

@application.route('/<ver>/ethvolohlchour/<n>', methods = ['GET'])
def json_ethvol_ohlc_hour(ver, n):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    if not n.isnumeric():
        return "Error 400: not a number", 400
    ethvol = cvix_page.ethvol_ohlc_hours(ver, int(n))
    return jsonify(ethvol), 200

@application.route('/<ver>/ethvolohlcday/<n>', methods = ['GET'])
def json_ethvol_ohlc_day(ver, n):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    if not n.isnumeric():
        return "Error 400: not a number", 400
    ethvol = cvix_page.ethvol_ohlc_days(ver, int(n))
    return jsonify(ethvol), 200



@application.route('/cvi', methods = ['GET'])
def render_cvix_V3():
    return render_cvix("v003")

@application.route('/cvijson', methods = ['GET'])
def json_cvix_V3():
    return json_cvix("v003")

@application.route('/cvijson1', methods = ['GET'])
def json_cvix_cvxjson1_V3():
    return json_cvix_cvxjson1("v003")

@application.route('/cvijson1000min', methods = ['GET'])
def json_cvix_1000_minute_V3():
    return json_cvix_1000_minute("v003")

@application.route('/cvijson1000hour', methods = ['GET'])
def json_cvix_1000_hour_V3():
    return json_cvix_1000_hour("v003")

@application.route('/cvijson100020min', methods = ['GET'])
def json_cvix_1000_20min_V3():
    return json_cvix_1000_20min("v003")

@application.route('/cvijson1000day', methods = ['GET'])
def json_cvix_1000_day_V3():
    return json_cvix_1000_day("v003")

@application.route('/gvol-instant-cvi', methods = ['GET'])
def show_gvol_instant_cvi():
    df = cvix_page.gvol_instant_cvi()
    return render_template('home-page-cvi-gvol-instant-cvi.html', df=df, table_header=list(df.columns))

@application.route('/gvol-instant-cvi/<n>', methods = ['GET'])
def show_n_gvol_instant_cvi(n):
    if not n.isnumeric():
        return "Error 400: not a number", 400
    df = cvix_page.gvol_instant_cvi(n)
    return render_template('home-page-cvi-gvol-instant-cvi.html', df=df, table_header=list(df.columns))

@application.route('/<ver>', methods = ['GET'])
def version(ver):
    ver = check_parameter_version(ver)
    if not ver:
        return "Error 400: incorrect index version", 400
    elif ver == "v003":
        data = {'version': '0.0.3', 'Calculation':'V3', 'Smoothing':'V0(update on instant CVI deviation)', 'RenewPeriod':'1 hour', 'Threshold': '5%'}
    elif ver == "v004":
        data = {'version': '0.0.4', 'Calculation':'V4', 'Smoothing':'V4', 'RenewPeriod':'20 minutes', 'Threshold': '1%', 'Smoothing factor': 0.31}
    elif ver == "v0041":
        data = {'version': '0.0.4.1', 'Calculation':'V4', 'Smoothing':'V4', 'RenewPeriod':'1 hour', 'Threshold': '2%', 'Smoothing factor': 0.22}
    elif ver == "v0042":
        data = {'version': '0.0.4.2', 'Calculation':'V4', 'Smoothing':'V4', 'RenewPeriod':'1 hour', 'Threshold': '5%', 'Smoothing factor': 0.22}
    elif ver == "v0043":
        data = {'version': '0.0.4.3 (ETHVOL)', 'Calculation':'V4', 'Smoothing':'V4', 'RenewPeriod':'30 minutes', 'Threshold': '2.5%', 'Smoothing factor': "0.4/0.08", "Deviation Threshold": 0.15}
    elif ver == "v0045":
        data = {'version': '0.0.4.5', 'Calculation':'V4', 'Smoothing':'V5', 'RenewPeriod':'5 minutes', 'Threshold': '1%', 'Smoothing factor': "0.4/0.04", "Deviation Threshold": 0.2}
    elif ver == "v0046":
        data = {'version': '0.0.4.6', 'Calculation':'V4', 'Smoothing':'V6', 'RenewPeriod':'10 minutes', 'Threshold': '1%', 'Smoothing factor': "0.4/0.04", "Deviation Threshold": 0.2}
    else:
        return "Error 400: incorrect index version " + ver, 400
    return jsonify(data), 200

try:
    from IL_hedge import find_best_plan, find_best_plan_to_expiration
    from CVI_hedge import prepare_best_cvi_hedge
    from CVI_hedge_direct import prepare_best_cvi_hedge_direct

    MIN_END_TERM = 3
    MAX_TERM = 90

    @application.route('/il-hedge', methods = ['POST', 'GET'])
    def home_page_il_hedge():
        if request.method == 'POST':
            result = request.form
            no_hedge = "no_hedge" in result
            fit_ratio = "fit_ratio" in result
            to_expiration = "to_expiration" in result
            if not no_hedge:
                amount = float(result.get("amount", default=0))
            else:
                amount = 0
            if not no_hedge and not fit_ratio:
                ratios = {"condor": float(result.get("condor")),
                          "condor_left": float(result.get("condor_left")),
                          "condor_right": float(result.get("condor_right")),
                          "strangle": float(result.get("strangle"))}
            else:
                ratios = {"strangle": 0.159, "condor": 0.166, "condor_left": 0.159, "condor_right": 0.159}
            term = float(result.get("term", default=30))
    
            if to_expiration:
                best_strategies, rate, n_contracts, capital_adjustment = find_best_plan_to_expiration(amount, ratios, no_hedge, fit_ratio, term)
            else:
                best_strategies, rate, n_contracts, capital_adjustment = find_best_plan(amount, ratios, no_hedge, fit_ratio, term)
            if best_strategies:
                strategy = best_strategies[0][1]
                plan_price = best_strategies[0][3]
                adjusted_capital = round(capital_adjustment * plan_price, 2)
            else:
                strategy = ""
                plan_price = ""
                adjusted_capital = ""
            return render_template('home-page-option-strategy.html', sub_path = "/il-hedge",
                                    no_hedge = no_hedge, fit_ratio = fit_ratio, to_expiration = to_expiration,
                                    amount = amount, strategies_list = ratios,
                                    strategy = strategy, n_contracts = n_contracts,
                                    best_strategies = best_strategies, term = term, rate=rate, plan_price=plan_price, adjusted_capital=adjusted_capital)
        else:
            amount = 0
            term = 30
            ratios = {"strangle": 0.159, "condor": 0.166, "condor_left": 0.159, "condor_right": 0.159}
            return render_template('home-page-option-strategy.html', sub_path = "/il-hedge", 
                                    no_hedge = 0, fit_ratio = 0, to_expiration = 0,
                                    amount = "", strategies_list = ratios,
                                    strategy = "", n_contracts = "",
                                    best_strategies = [], term = term, rate="", plan_price="", adjusted_capital="")
    
    
    @application.route('/cvi-hedge', methods = ['POST', 'GET'])
    def home_page_cvi_hedge():
        if request.method == 'POST':
            result = request.form
            direct_request = "direct_request" in result
            amount = float(result.get("amount", default=0))
            term = float(result.get("term", default=30))
            strike_range = float(result.get("strike_range", default=1.0))
    
            if direct_request:
                best_strategies, rate_start, funding_fee = prepare_best_cvi_hedge_direct(amount, term, strike_range)
            else:
                best_strategies, rate_start, funding_fee = prepare_best_cvi_hedge(amount, term, strike_range)
    
            return render_template('home-page-cvi-hedge.html', sub_path = "/cvi-hedge",
                                    amount = amount, term = term, direct_request = direct_request, strike_range=strike_range,
                                    best_strategies = best_strategies, rate_start=rate_start, funding_fee=funding_fee)
        else:
            amount = 1000000
            term = 30
            strike_range = 0.2
            return render_template('home-page-cvi-hedge.html', sub_path = "/cvi-hedge", 
                                    amount = amount, term = term, direct_request = 0, strike_range=strike_range,
                                    best_strategies = [], rate_start=[], funding_fee={})
except:
    pass

# try:
from CVI_hedge_vega_theta2 import CVI_hedge_vega_theta2

@application.route('/cvi-theta-json', methods = ['POST', 'GET'])
def CVI_hedge_vega_theta_json():
    _cvi = cvix_page.cvix_last("v004")
    cvi = {'BTC': _cvi[5], 'ETH': _cvi[6]}
    capital = 100000
    return jsonify(CVI_hedge_vega_theta2(cvi, capital)), 200
    # return jsonify(CVI_hedge_vega_theta2(cvi, capital)), 200

@application.route('/cvi-theta', methods = ['POST', 'GET'])
def CVI_hedge_vega_theta_page():
    capital = 100000
    _cvi = cvix_page.cvix_last("v004")
    cvi = {'BTC': _cvi[5], 'ETH': _cvi[6]}
    return render_template('home-page-cvi-theta.html',
                           capital=capital,
                           data=CVI_hedge_vega_theta2(cvi, capital, for_json=False))

# except:
    # pass
