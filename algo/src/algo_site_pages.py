from flask import Flask, render_template, request, flash
import json
import os
if  "__file__" in globals():
    os.sys.path.append(os.path.dirname(os.path.abspath(__file__)))
else:
    os.sys.path.append(os.path.abspath('.'))
import zipline_utils

application = Flask(__name__)
application.secret_key = 'random string'
sub_path = "/"

@application.route(sub_path, methods = ['POST', 'GET'])
def home_page_algo():

    if request.method == 'POST':
        result = request.form
        alg_name = result.get("alg_name")
        if result.get("AlgNameCode"):
            return algorithm_code_page(alg_name)

        algorithms_list = zipline_utils.load_algs_from_db()
        alg = next(i for i in algorithms_list if i[1] == alg_name)
        extractor=json.loads(alg[2][1:-1])
        params_list = [(e,extractor[e]) for e in extractor if extractor[e]]
        _runs_list = zipline_utils.load_runs_from_db(alg_name=alg_name)
        runs_list = [(i[0], str(i[1]), json.loads(i[3][1:-1]), json.loads(i[4][1:-1]), json.loads(i[5][1:-1]), i[7][1:-1]) for i in _runs_list]
        for r in runs_list:
            r[2]['start'] = r[2]['start'][0:10]
            r[2]['end'] = r[2]['end'][0:10]

        return render_template('home-page-algo.html', sub_path=sub_path, algorithms_list=algorithms_list, alg_name=alg_name, params_list=params_list, runs_list=runs_list)
    else:
        algorithms_list = zipline_utils.load_algs_from_db()
        return render_template('home-page-algo.html', sub_path=sub_path, algorithms_list=algorithms_list, alg_name="", params_list=[], runs_list=[])

@application.route('/signals', methods = ['POST', 'GET'])
def algorithm_signals_page():
    return algorithm_signals_N(request)

@application.route('/moresignals', methods = ['POST'])
def algorithm_signals_page_more():
    signals_from = int(request.form.get("SignalsFrom"))
    signals_to = int(request.form.get("SignalsTo"))
    return algorithm_signals_N(request, signals_from, signals_to)

def algorithm_signals_N(request, signals_from=0, signals_to=10):
    algorithms_list = zipline_utils.load_algs_from_db()
    if request.method == 'POST':
        result = request.form
        alg_name = result.get("alg_name")
        if not alg_name:
            alg_name = result.get("AlgNameMore")

        if result.get("AlgNameCode"):
            return algorithm_code_page(alg_name)

        algorithm_id = next(i[0] for i in algorithms_list if i[1] == alg_name)
        signals_list = zipline_utils.load_signals_from_db(algorithm_id=algorithm_id, last_signals=signals_from+signals_to)
        s_list = []
        for s in signals_list[signals_from:signals_to]:
            signals_id = s[0]
            signals_extractor = json.loads(s[6][1:-1])
            signals = json.loads(zipline_utils.load_signals_data_from_db(signals_id))
            l = []
            for se in signals_extractor:
                if signals_extractor[se] == 'simple':
                    l.append((se, signals[se]))
                elif signals_extractor[se] == 'array' or signals_extractor[se] == 'pandas':
                    l.append((se, signals[se]))
            s1 = (s[1], s[3], s[4], s[5], s[7], l)
            s_list.append(s1)

        return render_template('algo-signals-page.html', sub_path=sub_path, algorithms_list=algorithms_list, s_list=s_list, alg_name=alg_name)
    else:
        (algorithm_id, _, alg_name) = zipline_utils.get_last_signal_from_db()
        signals_list = zipline_utils.load_signals_from_db(algorithm_id=algorithm_id, last_signals=signals_from+signals_to)
        s_list = []
        for s in signals_list[signals_from:signals_to]:
            signals_id = s[0]
            signals_extractor = json.loads(s[6][1:-1])
            signals = json.loads(zipline_utils.load_signals_data_from_db(signals_id))
            l = []
            for se in signals_extractor:
                if signals_extractor[se] == 'simple':
                    l.append((se, signals[se]))
                elif signals_extractor[se] == 'array' or signals_extractor[se] == 'pandas':
                    l.append((se, signals[se]))
            s1 = (s[1], s[3], s[4], s[5], s[7], l)
            s_list.append(s1)

        return render_template('algo-signals-page.html', sub_path=sub_path, algorithms_list=algorithms_list, s_list=s_list, alg_name=alg_name)

@application.route('/run/<sid>', methods = ['GET'])
def algorithm_run_page(sid):
    saved_run_id = sid

    _runs_list = zipline_utils.load_runs_from_db(saved_run_id=saved_run_id)
    if len(_runs_list) == 0: return
    run_data = (_runs_list[0][0], str(_runs_list[0][1]), json.loads(_runs_list[0][3][1:-1]), json.loads(_runs_list[0][4][1:-1]), json.loads(_runs_list[0][5][1:-1]), _runs_list[0][7][1:-1])

    algorithms_list = zipline_utils.load_algs_from_db(algorithm_id=_runs_list[0][2])
    if len(algorithms_list) == 0: return
    alg = algorithms_list[0]
    alg_name = alg[1]
    # extractor=json.loads(alg[2][1:-1])
    # params_list = [(e,extractor[e]) for e in extractor if extractor[e]]

    text_output = zipline_utils.load_text_output_from_db(saved_run_id)
    if len(text_output) > 65535:
        _text_output = text_output[:32750] + '\n\n---------------------\n\n' + text_output[-32750:]
    else:
        _text_output = text_output

    chart_columns = ["benchmark_period_return", "algorithm_period_return"]
    x_columns = ["benchmark_period_return", "algorithm_period_return", "portfolio_value"]
    if _runs_list[0][6]:
        xdata = zipline_utils.load_xdata1_from_db(saved_run_id)
        _x_values = xdata.loc[:, x_columns].reset_index().values.tolist()
        x_values = [(i[0], '{0:.4%}'.format(i[1]), '{0:.4%}'.format(i[2]), '{:,.2f}'.format(i[3])) for i in _x_values]

        _chart_values = xdata.loc[:, chart_columns].reset_index().values.tolist()
        chart_values = [('new Date('+str(i[0].year)+", "+str(i[0].month-1)+", "+str(i[0].day)+')', i[1], i[2]) for i in _chart_values]

    else:
        x_values = []
        chart_values = []

    return render_template('algo-run-page.html', sub_path=sub_path, alg_name=alg_name, run_data=run_data, x_columns=["Trading dates"]+x_columns, x_values=x_values, chart_values=chart_values, text_output=_text_output)

def algorithm_code_page(alg_name):

    with open("algorithms/"+alg_name+".py", 'r') as f:
        code = list(f)

    return render_template('algo-alg-page.html', alg_name=alg_name, code=code)

@application.route('/journal', methods = ['POST', 'GET'])
def algorithm_journal_page():
    return algorithm_journal_N(request)

@application.route('/morejournal', methods = ['POST'])
def algorithm_journal_page_more():
    journal_from = int(request.form.get("JournalFrom"))
    journal_to = int(request.form.get("JournalTo"))
    return algorithm_journal_N(request, journal_from, journal_to)

def algorithm_journal_N(request, journal_from=0, journal_to=1000):
    journal_list = zipline_utils.load_journal_from_db(last_row=journal_from+journal_to)
    return render_template('algo-journal-page.html', sub_path=sub_path, j_list=journal_list[journal_from:journal_to])
