from flask import Flask, request, g, render_template
app = Flask(__name__)

from collections import Counter
import csv
import sqlite3
import logging
import time
import json
import os
import pickle 

from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.util.string import encode_utf8

hex_color = {
    'y0':'#2c6c87',
    'y1':'#417a93',
    'y2':'#56899f',
    'y3':'#6b98ab',
    'y4':'#80a6b7',
    'y5':'#95b5c3',
    'y6':'#aac4cf',
    'y7':'#bfd2db',
}

on_off = {
    'yes': 1,
    'no':0,
}

alphas = {
    'y0':1,
    'y1':0.9,
    'y2':0.8,
    'y3':0.7,
    'y4':0.6,
    'y5':0.5,
    'y6':0.4,
    'y7':0.3,
}

def getitem(obj, item, default):
    if item not in obj:
        return default
    else:
        return obj[item]

DATABASE = '/var/www/html/flaskapp/bart.db'

app.config.from_object(__name__)

def connect_to_database():
    return sqlite3.connect(app.config['DATABASE'])

def get_db():
    db = getattr(g, 'db', None)
    if db is None:
        db = g.db = connect_to_database()
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def execute_query(query, args=()):
    cur = get_db().execute(query, args)
    rows = cur.fetchall()
    cur.close()
    return rows

@app.route('/')
def polynomial():
    """ Very simple embedding of a polynomial chart
    """
    return_str = 'here1'

    chain_length = 3
    payload_cost = 4
    repeated_seeding = 5
    drive_init = 6

    try:
        # Grab the inputs arguments from the URL
        # This is automated by the button
        args = request.args

        return_str = return_str + " " + str(args)

        # Get all the form arguments in the url with defaults
        chain_length = int(getitem(args, 'chain_length', 1))
        payload_cost = int(getitem(args, 'payload_cost', 8))
        repeated_seeding = on_off[getitem(args, 'repeated_seeding', 'yes')]
        drive_init = int(getitem(args, 'drive_init', 300))

        c = chain_length #2 #3
        p = payload_cost #8#12
        r = repeated_seeding #0
        d = drive_init #300 #51

        filename = '/home/erikad/flaskapp/pickle/'+str(c)+'_'+str(p)+'_'+str(r)+'_'+str(d)+'.pickle'
        return_str = return_str + filename

        if (os.path.isfile(filename)):
            with open(filename, 'rb') as handle:
                ans2 = pickle.load(handle)
                for k in ans2.keys():
                    print k
                    return_str = return_str + '<br>Length of ' + str(k) + " is " + str(len(ans2[k]))+'.<br>'
                #fig = figure(title="Polynomial2")
                fig = figure()

                # assemble x and y for plotting multiple lines
                x = []
                y = []
                color = []
                alpha_vals = []

                for k in [i for i in ans2.keys() if i != 't']:
                    if len(ans2[k]) > 0:
                        x.append(ans2['t'])
                        y.append(list(ans2[k]))
                        color.append(hex_color[k])
                        alpha_vals.append(alphas[k])

                return_str = return_str +'<br>'+ ' x len '+str(len(x)) + ' '
                return_str = return_str +'<br>'+ ' y len ' +str(len(y)) + ' '

                # draw all of the lines
                fig.multi_line(xs = x, ys = y, color = color, line_width = 3, line_alpha = alpha_vals)

        else:
            return_str = return_str + ' file not found '

    except Exception as e:
        return_str = return_str+ " Hello exception " + e.__doc__ + e.message
        return return_str

    #x = list(range(_from, to + 1))
    #fig = figure(title="Polynomial2")
    #fig.line(x, [i ** 2 for i in x], color=color, line_width=2)
    #fig.line(x, y, color='#000000', line_width=2)

    # Configure resources to include BokehJS inline in the document.
    # For more details see:
    #   http://bokeh.pydata.org/en/latest/docs/reference/resources_embedding.html#bokeh-embed
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    # For more details see:
    #   http://bokeh.pydata.org/en/latest/docs/user_guide/embedding.html#components
    script, div = components(fig, INLINE)
    html = render_template(
        'embed.html',
        plot_script=script,
        plot_div=div,
        js_resources=js_resources,
        css_resources=css_resources,
        chain_length = chain_length,
        payload_cost = payload_cost,
        repeated_seeding = repeated_seeding,
        drive_init= drive_init
    )
    return encode_utf8(html)

def print_data():
    """Respond to a query of the format:
    myapp/?dest=Fremont&time=600&station=plza&day=0
    with ETD data for the time and location specified in the query"""
    start_time = time.time()
    cur = get_db().cursor()
    try:
        minute_of_day = int(request.args.get('time'))
    except ValueError:
        minute_of_day = 600
        #return "Time must be an integer"
    station = request.args.get('station')
    print minute_of_day
    day = request.args.get('day')
    dest = request.args.get('dest')
    result = execute_query(
        """SELECT etd, count(*)
           FROM etd
           WHERE dest = ? AND minute_of_day = ?
                 AND station = ? AND day_of_week = ?
           GROUP BY etd""",
        (dest, minute_of_day, station, day)
    )
    str_rows = [','.join(map(str, row)) for row in result]
    query_time = time.time() - start_time
    logging.info("executed query in %s" % query_time)
    cur.close()
    header = 'etd,count\n'

    dummy_data = "1,2,3,4,5,6,8"
    return dummy_data
    return header + '\n'.join(str_rows)

@app.route('/countme/<input_str>')
def count_me(input_str):
    input_counter = Counter(input_str)
    response = []
    for letter, count in input_counter.most_common():
        response.append('"{}": {}'.format(letter, count))
    return '<br>'.join(response)

'''
@app.route("/viewdb")
def viewdb():
    rows = execute_query("""SELECT * FROM natlpark""")
    return '<br>'.join(str(row) for row in rows)

@app.route("/state/<state>")
def sortby(state):
    rows = execute_query("""SELECT * FROM natlpark WHERE state = ?""",
                         [state.title()])
    return '<br>'.join(str(row) for row in rows)
'''

if __name__ == '__main__':
  app.run()
