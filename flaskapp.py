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

colors = {
    'Black': '#000000',
    'Red':   '#FF0000',
    'Green': '#00FF00',
    'Blue':  '#0000FF',
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

    # ?color=Black&_from=5&to=10
    color = 'Black'
    _from = 5
    to = 10

    try:
        # Grab the inputs arguments from the URL
        # This is automated by the button
        args = request.args

        return_str = return_str + " " + str(args)

        # Get all the form arguments in the url with defaults
        color = colors[getitem(args, 'color', 'Black')]
        _from = int(getitem(args, '_from', 0))
        to = int(getitem(args, 'to', 10))
        return_str = return_str + ' in try '
        
        c = 1#3
        p = 8#12
        r = 0
        d = 300#51

        filename = '/home/erikad/flaskapp/pickle/'+str(c)+'_'+str(p)+'_'+str(r)+'_'+str(d)+'.pickle'
        return_str = return_str + filename
        if (os.path.isfile(filename)):
            with open(filename, 'rb') as handle:
                ans2 = pickle.load(handle)
                for k in ans2.keys():
                    print k
                    return_str = return_str + 'len ' + str(k) + " " + str(len(ans2[k]))
                x = ans2['t']
                y = ans2['y0']

                fig = figure(title="Polynomial2")
                fig.line(x, y, color=color, line_width=2)
        else:
            return_str = return_str + ' file not found '

    except Exception as e:
        return_str = return_str+ " Hello exception " + e.__doc__ + e.message
        return return_str

    #x = list(range(_from, to + 1))
    fig = figure(title="Polynomial2")
    #fig.line(x, [i ** 2 for i in x], color=color, line_width=2)
    fig.line(x, y, color=color, line_width=2)

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
        color=color,
        _from=_from,
        to=to
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
