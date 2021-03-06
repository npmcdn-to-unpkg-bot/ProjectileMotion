#!/usr/bin/env python
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from bokeh.plotting import figure
from bokeh.embed import components
import numpy as np
import sys
import itertools
sys.path.insert(0, 'modules/czml/czml')
import czml
from projectile import Projectile
from bs4 import BeautifulSoup


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

@app.route("/")
def hello():
    temp = render_template('viz.html',
                           topPlots=topPlots,
                           bottomPlots=bottomPlots)
    return temp

@socketio.on('connect')
def handle_connect():
    emit('loadData', doc.dumps())


class Plot():

    def __init__(self, x, y, title, xaxis_label="", yaxis_label=""):
        self.plot = figure(title=title, plot_width=600, plot_height=400)
        self.plot.line(x, y)
        self.plot.xaxis.axis_label = xaxis_label
        self.plot.yaxis.axis_label = yaxis_label

        script, div = components(self.plot)
        self.script = script
        self.div = div

        soup = BeautifulSoup(div, 'lxml')
        self.divid = soup.find_all('div', class_='plotdiv')[0]['id']

        self.title = title


if __name__ == '__main__':

    doc = czml.CZML()
    packet1 = czml.CZMLPacket(id='document', version='1.0')
    doc.packets.append(packet1)

    clock_packet = czml.CZMLPacket(id="document",
                                   name="CZML Path",
                                   version = "1.0",
                                   clock={"interval": "2000-01-01T11:58:55Z/2000-01-01T23:58:55Z",
                                          "currentTime:":"2000-01-01T11:58:55Z",
                                          "multiplier": 5})


    glider_packet = czml.CZMLPacket(id="path",
                                    name="path with GPS flight data",
                                    availability="2000-01-01T11:58:55Z/2000-01-01T23:58:55Z")

    # building the path packet that goes in glider
    color_pack = czml.Color(rgba=[255, 0, 255, 255])
    outlineColor_pack = czml.Color(rgba=[0, 255, 255, 255])
    polylineGlow_pack = czml.PolylineGlow(color=czml.Color(rgba=[255, 255, 0,  255]),
                                          glowPower=3)
    polylineOutline_pack = czml.PolylineOutline(color=color_pack,
                                                outlineColor=outlineColor_pack,
                                                outlineWidth=5,
                                                polylineGlow=polylineGlow_pack,
                                                )
    material_pack = czml.Material(polylineOutline=polylineOutline_pack)
    path_pack = czml.Path(material=material_pack, width=8, leadTime=0, trailTime=10000000,
                          resolution=5)
    glider_packet.path = path_pack

    position_pack = czml.Position(epoch="2000-01-01T11:58:55Z")

    p = Projectile(4000, 45)
    tof = np.ceil(p.timeOfFlight())
    time = np.arange(0, tof, 0.1)
    x, y = p.pos(time)
    y = (20925646.3255*.3048) + y
    z = np.zeros(time.size)

    vx, vy = p.vel(time)

    pos = zip(time, x, y, z)

    position_pack.cartesian = list(itertools.chain.from_iterable(pos))

    glider_packet.position = position_pack

    doc.append(clock_packet)
    doc.append(glider_packet)

    topPlots = {}

    displacement = list(map(np.linalg.norm, zip(x, y, z)))
    p = Plot(time, displacement, "Displacement vs Time", "Time", "Displacement")
    topPlots[p.divid] = p

    bottomPlots = {}

    speed = list(map(np.linalg.norm, zip(vx, vy, z)))
    p = Plot(time, speed, "Speed vs Time", "Time", "Speed")
    bottomPlots[p.divid] = p

    socketio.run(app, port=8081, debug=True)
