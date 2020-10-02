"""
Authors: originally by Galal Hassan, heavily modified by Joseph Malibiran
Last Modified: October 2, 2020
"""


import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json
import queue

clients_lock = threading.Lock()
connected = 0

#Dictionary
clients = {}

#Queue
msgQueue = queue.Queue() 

# Connection loop continuously listens for messages and stores them in a queue to be processed separately
def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      #data = str(data)

      msgDict = json.loads(data) # Convert [string json] to [python dictionary] TODO not working?
      msgDict['ip'] = str(addr[0]) # Append 'ip' and 'source', the address of message sender, to python dictionary
      msgDict['port'] = str(addr[1])
      msgString = json.dumps(msgDict) # Convert new dictionary back into string
      #msgQueue.append(msgString) # Append new string to message queue to be processed later
      msgQueue.put(msgString)

#UNTESTED
def processMessages(sock):

   while True:

      if msgQueue.empty() == False:
         msgDict = json.loads(msgQueue.get())

         if msgDict['flag'] == 1: # New Client Connection
            srcAddress = msgDict['ip'] + ":"  + msgDict['port']
            clients[srcAddress] = {}
            clients[srcAddress]['lastPing'] = datetime.now()
            clients[srcAddress]['position'] = {"x": 0,"y": 0,"z": 0}
            clients[srcAddress]['ip'] = str(msgDict['ip'])
            clients[srcAddress]['port'] = str(msgDict['port'])
            print('[Notice] New Client Added: ', str(srcAddress))

            # Inform all currently connected clients of the arrival of the new client. 
            print('[Notice] Sending connected clients the data of the new client...')
            newMsgDict = {"cmd": 0,"player":{"ip":str(msgDict['ip']), "port":str(msgDict['port']), "position":{"x": 0,"y": 0,"z": 0}}}
            msgJson = json.dumps(newMsgDict)
            for targetClient in clients:
               sock.sendto(bytes(msgJson,'utf8'), (clients[targetClient]['ip'], int(clients[targetClient]['port']))) 

            # Send newly connected client a list of currently connected clients. 
            print('[Notice] Sending the new client the data of connected clients...')
            GameState = {"cmd": 3, "players": []}
            clients_lock.acquire()

            for clientKey in clients:
               newPlayerDict = {}
               newPlayerDict['ip'] = clients[clientKey]['ip']
               newPlayerDict['port'] = clients[clientKey]['port']
               newPlayerDict['position'] = clients[clientKey]['position']
               GameState['players'].append(newPlayerDict)
            
            msgState = json.dumps(GameState)

            sock.sendto(bytes(msgState,'utf8'), (clients[srcAddress]['ip'], int(clients[srcAddress]['port']))) 
            clients_lock.release()
               
         elif msgDict['flag'] == 2: # Client Ping
            keyString = msgDict['ip'] + ":"  + msgDict['port']
            print('[Routine] Received client ping from: ', keyString)

            if keyString in clients:
               clients[keyString]['lastPing'] = datetime.now()
               #TODO send Pong back to client
            else:
               print('[Error] Client ping has invalid client address key! Aborting proceedure...')
         
         elif msgDict['flag'] == 4: # Client Coordinates
            keyString = msgDict['ip'] + ":"  + msgDict['port']
            print('[Routine] Received client coordinates from: ', keyString)

            if keyString in clients:
               clients[keyString]['position']['x'] = msgDict['x']
               clients[keyString]['position']['y'] = msgDict['y']
               clients[keyString]['position']['z'] = msgDict['z']
            else:
               print('[Error] Client coordinate update has invalid client address key! Aborting proceedure...')
               

# Every loop, the server checks if a client has not sent a ping in the last 5 seconds. 
# If a client did not meet the ping conditions, the server drops the client from the game.
# If a client is dropped, the server sends a message to all clients currently connected to inform them of the dropped player. (Implementation Missing)
def cleanClients(sock):
   while True:
      # Loop through clients
      for c in list(clients.keys()):

         # Every loop, the server checks if a client has not sent a ping in the last 5 seconds.
         if (datetime.now() - clients[c]['lastPing']).total_seconds() > 5:
            droppedClientAddress = c
            # Drop the client from the game.
            print('[Notice] Dropped Client: ', c)
            clients_lock.acquire()
            del clients[c]
            
            #Sends a message to all clients currently connected to inform them of the dropped player. 
            msgDict = {"cmd": 2,"player":{"id":str(droppedClientAddress)}}

            msgJson = json.dumps(msgDict)
            for targetClient in clients:
               sock.sendto(bytes(msgJson,'utf8'), (clients[targetClient]['ip'], int(clients[targetClient]['port']))) 

            clients_lock.release()
            

      time.sleep(1)

# Every loop, the server updates the current state of the game. This game state contains the id’s and colours of all the players currently in the game.
# Every loop, the server sends a message containing the current state of the game. This game state contains the id’s and colours of all players currently in the game.
def gameLoop(sock):
   while True:
      
      # The server updates the current state of the game. This game state contains the id’s and colours of all the players currently in the game.
      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
      #print ('[Notice] Client List:')
      #print (clients)
      for c in clients:
         player = {}
         clients[c]['position'] = {"x": 0, "y": 0, "z": 0}
         player['id'] = str(c)
         player['position'] = clients[c]['position']
         GameState['players'].append(player)

      # Sends a message containing the current state of the game. This game state contains the id’s and colours of all players currently in the game.
      msgState = json.dumps(GameState)
      #print ('[Notice] Game State:')
      #print(s)
      for c in clients:
         sock.sendto(bytes(msgState,'utf8'), (clients[c]['ip'],int(clients[c]['port'])))
      clients_lock.release()
      time.sleep(1)

def main():
   print('[Notice] Setting up server... ')
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(processMessages, (s,))
   start_new_thread(cleanClients, (s,))
   print('[Notice] Server running.')
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
