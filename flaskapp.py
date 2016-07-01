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
import numpy as np

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

convert_drive_init = [0.001,0.003,0.01,0.03,0.1,0.3]

def find_nearest(array,value):
    idx = (np.abs(array-value)).argmin()
    return array[idx]

def getitem(obj, item, default):
    if item not in obj:
        return default
    else:
        return obj[item]


app.config.from_object(__name__)

@app.route('/')
def polynomial():
    """
    Embeded daisy drive visualizer.
    """
    return_str = ''
    try:
        # Grab the inputs arguments from the URL
        # This is automated by the button
        args = request.args

        return_str = return_str + " " + str(args)

        # Get all the form arguments in the url with defaults
        try:
            chain_length = int(getitem(args, 'chain_length', 5))
        except:
            # "must be an integer" error message?
            chain_length = 5

        try:
            payload_cost = float(getitem(args, 'payload_cost', 0.35))*100
        except:
            payload_cost = 35

        try:
            repeated_seeding = on_off[getitem(args, 'repeated_seeding', 'no')]
        except:
            repeated_seeding = 0

        try:
            homing = float(getitem(args, 'homing', 0.8))*10
        except:
            homing = 0

        try:
            drive_init_raw = int(getitem(args, 'drive_init', .1))
            drive_init = convert_drive_init[drive_init_raw] * 1000.0
        except:
            drive_init = 100

        # fix bad inputs
        avail_c = np.arange(1,7,1)
        avail_p =  np.arange(2,41,3)
        avail_r =  np.array([0,1])
        avail_d =  np.append(np.array([1]), np.arange(100,1001,50))

        chain_length = find_nearest(avail_c, chain_length)
        payload_cost = find_nearest(avail_p, payload_cost)
        repeated_seeding = find_nearest(avail_r, repeated_seeding)
        drive_init = find_nearest(avail_d, drive_init)
        
        filename = '/home/erikad/flaskapp/pickle/'+str(chain_length)+'_'+str(payload_cost)+'_'+str(repeated_seeding)+'_'+str(drive_init)+'.pickle'
        return_str = return_str + filename

        if (os.path.isfile(filename)):
            with open(filename, 'rb') as handle:
                ans2 = pickle.load(handle)
                for k in ans2.keys():
                    print k
                    return_str = return_str + '<br>Length of ' + str(k) + " is " + str(len(ans2[k]))+'.<br>'

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
                fig = figure()
                fig.multi_line(xs = x, ys = y, color = color, line_width = 4, line_alpha = alpha_vals)
                fig.xaxis.axis_label = "Time (generations)"
                fig.yaxis.axis_label = "Allele frequency"

        else:
            return_str = return_str + ' file not found '

    except Exception as e:
        return_str = return_str+ "<br>Exception " + e.__doc__ + e.message
        return return_str

    # Configure resources to include BokehJS inline in the document.
    # For more details see:
    #   http://bokeh.pydata.org/en/latest/docs/reference/resources_embedding.html#bokeh-embed
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    # For more details see:
    #   http://bokeh.pydata.org/en/latest/docs/user_guide/embedding.html#components
    script, div = components(fig, INLINE)

    #return_str = return_str + '<br>' + str(repeated_seeding)
    #return return_str
    r = 'no'
    if repeated_seeding > 0:
        r = 'yes'

    html = render_template(
        'embed.html',
        plot_script=script,
        plot_div=div,
        js_resources=js_resources,
        css_resources=css_resources,
        chain_length = chain_length,
        payload_cost = float(payload_cost)/100.0,
        repeated_seeding = repeated_seeding,
        r_val = r,
        drive_init = drive_init_raw,
        homing =homing/10.0
    )
    return encode_utf8(html)

if __name__ == '__main__':
  app.run()
