from os import listdir
#import sys
import string
import datetime
from flask import Flask, render_template, request, flash
import util
import cat_enquirer

application = Flask(__name__)
application.secret_key = 'random string'
#if (sys.version.find('anaconda') != -1) or (sys.version.find('Continuum') != -1):
#  sub_path = "/nn"
#else:
sub_path = "/"

catlist_path = "catlist.csv"
save_path = "saves"
log_path = "logs/request_log"
catlist = util.read_csv_to_tuples(catlist_path)
saves = [f for f in listdir(save_path)]
saves.sort(key=lambda k:(k[1],k[3],k[4]))
saves_l = list(map(util.unpack_name, saves))
saves_l.sort(key=lambda k:(k[1],k[3],k[4]))
nn_list = list(enumerate(saves_l))
translator = str.maketrans('', '', string.punctuation)

@application.route(sub_path, methods = ['POST', 'GET'])
def home_page_nn():
  if request.method == 'POST':
    result = request.form
    sentence = result.get("sentence")
    if not sentence:
      return render_template('home-page-nn.html', sub_path=sub_path, sentence=sentence, nn_list=nn_list, catlist=catlist)
    with open(log_path, 'a') as f:
      f.write(str(datetime.datetime.now()) + "|" + request.environ.get('HTTP_X_REAL_IP', request.remote_addr) + "|" + sentence + '\n')
    sentence = sentence.lower()
    sentence = sentence.translate(translator)
    
    nn_checked_list=[]
    for res in result:
      if res[0:3]=="nn_":
        nn_checked_list.append(int(res[3:]))
      if len(nn_checked_list)>2: break
    
    nn_output_names=[]
    nn_output_lists=[]
    
    for nncl in nn_checked_list:
      nn_output_names.append(saves[nncl])
      
      config = util.TrainConfig(dataset=nn_list[nncl][1][0],
                         nn_type=nn_list[nncl][1][1],
                         input_length=nn_list[nncl][1][2],
                         num_layers=nn_list[nncl][1][3],
                         hidden_size=nn_list[nncl][1][4],
                         num_labels=nn_list[nncl][1][5],
                         keep_prob=nn_list[nncl][1][6],
                         learning_rate=nn_list[nncl][1][7],
                         lr_decay_start=nn_list[nncl][1][8],
                         lr_decay_rate=nn_list[nncl][1][9],
                         number_epochs=nn_list[nncl][1][10],
                         save_path=save_path)

      out_list = cat_enquirer.cat_model_enquarer([sentence], ['1'], catlist, config)     # suppose label 1 exists !!!
      nn_output_lists.append(out_list[0][2])

#http://flask.pocoo.org/docs/0.10/patterns/streaming/#streaming-with-context
    return render_template('home-page-nn.html', sub_path=sub_path, sentence=sentence, nn_list=nn_list, nn_names=nn_output_names, nn_lists=nn_output_lists, nn_checked_list=nn_checked_list, catlist=catlist)
  else:
    sentence = ""
    return render_template('home-page-nn.html', sub_path=sub_path, sentence=sentence, nn_list=nn_list, catlist=catlist)

@application.route("/nn/log")
def log_page_nn():
  with open(log_path, 'r') as f:
    ff=f.readlines()
  
  fff = []  
  for fl in ff:
    try:
      fff.append(fl.split('|')[2])
    except Exception:
      pass

  return render_template('log-nn.html', fff=fff)
