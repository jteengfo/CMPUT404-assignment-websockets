#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2013-2014 Abram Hindle
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import flask
from flask import Flask, request, redirect
from flask_sockets import Sockets
import gevent
from gevent import queue
import time
import json
import os

app = Flask(__name__)
sockets = Sockets(app)
app.debug = True

class World:
    def __init__(self):
        self.clear()
        # we've got listeners now!
        self.listeners = list()
        
    def add_set_listener(self, listener):
        self.listeners.append( listener )

    def update(self, entity, key, value):
        entry = self.space.get(entity,dict())
        entry[key] = value
        self.space[entity] = entry
        self.update_listeners( entity )

    def set(self, entity, data):
        self.space[entity] = data
        self.update_listeners( entity )

    def update_listeners(self, entity):
        '''update the set listeners'''
        print("Listeners:", self.listeners)
        print("number of listeners:", len(self.listeners))
        for listener in self.listeners:
            print("sending to listener:")
            # listener
            listener.put(json.dumps({entity: self.get(entity)}))
            # listener.put(entity, self.get(entity)
            # listener.put(json.dumps({"entity": entity, "data": self.get(entity)}))
            # listener.put(json.dump({entity: self.get(entity)}))
            # listener(entity, self.get(entity))
        pass

    def clear(self):
        self.space = dict()

    def get(self, entity):
        return self.space.get(entity,dict())
    
    def world(self):
        return self.space

class Client:
    def __init__(self):
        self.queue = queue.Queue()

    def put(self, v):
        self.queue.put_nowait(v)

    def get(self):
        return self.queue.get()
   
def set_listener( entity, data ):
    ''' do something with the update ! '''
    # # XXX: TODO IMPLEMENT ME
    # message = json.dumps({entity: data})                      # message from updated entity and data
    # for listener in myWorld.listeners:
    #     listener.put(message)
    pass
    
# def send_all(msg):
#     for listener in myWorld.listeners:
#         listener.put(msg)
        
# def send_all_json(obj):
#     send_all( json.dumps(obj) )

myWorld = World()        

# myWorld.add_set_listener( set_listener )
    
@app.route('/')
def hello():
    '''Return something coherent here.. perhaps redirect to /static/index.html '''
    return redirect("/static/index.html", code=302)

def read_ws(ws,client):
    '''A greenlet function that reads from the websocket and updates the world'''
    # XXX: TODO IMPLEMENT ME
    try: 
        while True:
            msg = ws.receive()                                  # receive message from client
            print("Check1")
            # print(msg)
            print("received {}".format(msg))
            if msg is not None:                                 # if message is not empty
                print(f"Received message from client: {msg}")
                packet = json.loads(msg)                        # load message into packet
                print(f"Packet: {packet}")
                print("Type: ", type(packet))
                # print("entity: ", packet["entity"])
                # print("data: ", packet["data"])
                for key in packet:
                    # print("key: ", key)
                    # print("value: ", value)
                    myWorld.set(key, packet[key])
                # myWorld.set(packet["entity"], packet["data"])
                # myWorld.set(packet["entity"], packet["data"])
                # for entity, data in packet.items():
                    # for key, value in data.items():
                    #     myWorld.update(entity, key, value)
            else:
                break                                           # if message is empty, break
    except Exception as e:
        print("WS Error %s" % e)
    # except:
    #     # '''Done'''
    #     print("Some error occured.")

@sockets.route('/subscribe')
def subscribe_socket(ws):
    '''Fufill the websocket URL of /subscribe, every update notify the
       websocket and read updates from the websocket '''
    # XXX: TODO IMPLEMENT ME
    client = Client()                                       # create client queue
    myWorld.add_set_listener(client)                            # add client to listeners
    ws.send(json.dumps(myWorld.world()))
    print("Got a client websocket subscription")
    g = gevent.spawn(read_ws, ws, client)                       # something spawn i forgot what gevent does
    try:
        while True:
            msg = client.get()                                  # get message from client
            print("got a message.")
            print("sending %s" % msg)
            ws.send(msg)                                        # send message to websocket
    except Exception as e:# WebSocketError as e:
        print("WS Error %s" % e)
    finally:
        myWorld.listeners.remove(client)                        # remove client from listeners
        gevent.kill(g)                                          # kill greenlet
    


# I give this to you, this is how you get the raw body/data portion of a post in flask
# this should come with flask but whatever, it's not my project.
def flask_post_json():
    '''Ah the joys of frameworks! They do so much work for you
       that they get in the way of sane operation!'''
    if (request.json != None):
        return request.json
    elif (request.data != None and request.data.decode("utf8") != u''):
        return json.loads(request.data.decode("utf8"))
    else:
        return json.loads(request.form.keys()[0])

@app.route("/entity/<entity>", methods=['POST','PUT'])
def update(entity):
    '''update the entities via this interface'''
    if request.method == 'POST':
        myWorld.set(entity, flask_post_json())
        return json.dumps(myWorld.get(entity))
    elif request.method == 'PUT':
        data = flask_post_json()
        for key, value in data.items():
            myWorld.update(entity, key, value)
        return json.dumps(myWorld.get(entity))

@app.route("/world", methods=['POST','GET'])    
def world():
    '''you should probably return the world here'''
    return json.dumps(myWorld.world())

@app.route("/entity/<entity>")    
def get_entity(entity):
    '''This is the GET version of the entity interface, return a representation of the entity'''
    return json.dumps(myWorld.get(entity))


@app.route("/clear", methods=['POST','GET'])
def clear():
    '''Clear the world out!'''
    myWorld.clear()
    return redirect("/static/index.html", code=200)



if __name__ == "__main__":
    ''' This doesn't work well anymore:
        pip install gunicorn
        and run
        gunicorn -k flask_sockets.worker sockets:app
    '''
    app.run()
