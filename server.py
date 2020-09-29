"""
Authors: originally by Galal Hassan, heavily modified by Joseph Malibiran
Last Modified: September 28, 2020
"""


import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0

#Dictionary
clients = {}

#Queue
msgQueue = [] 

# Connection loop continuously listens for messages and stores them in a queue to be processed separately
def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      data = str(data)
      
      msgDict = json.loads(data) # Convert [string json] to [python dictionary]
      msgDict['source'] = str(addr) # Append 'source', the address of message sender, to python dictionary
      msgString = json.dumps(msgDict) # Convert new dictionary back into string
      msgQueue.append(msgString) # Append new string to message queue to be processed later

   """
      if addr in clients:

         # If the server receives a heartbeat message:
         if 'heartbeat' in data:

            # Update last heartbeat time
            clients[addr]['lastBeat'] = datetime.now()

      else: 
         # When a new client connects:
         if 'connect' in data:

            # The server adds the new client to a dictionary of clients it has.
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = 0
            print('[Notice] New Client Added: ', str(addr))

            # Inform all currently connected clients of the arrival of the new client. 
            msgDict = {"cmd": 0,"player":{"id":str(addr)}}
            msgJson = json.dumps(msgDict)
            for targetClient in clients:
               sock.sendto(bytes(msgJson,'utf8'), (targetClient[0],targetClient[1])) 

            # Send newly connected client a list of currently connected clients. 
            GameState = {"cmd": 3, "players": []}
            clients_lock.acquire()
            for c in clients:
               player = {}
               clients[c]['color'] = {"R": 0, "G": 0, "B": 0}
               player['id'] = str(c)
               player['color'] = clients[c]['color']
               GameState['players'].append(player)
            
            msgState = json.dumps(GameState)
            sock.sendto(bytes(msgState,'utf8'), (addr[0],addr[1])) 
            clients_lock.release()
   """

#UNTESTED
def processMessages(sock):
   while True:
      if msgQueue.count > 0:
         msgDict = json.loads(msgQueue.pop)
         
         if msgDict['flag'] == 1: # New Client Connection
            srcAddress = msgDict['source']
            clients[srcAddress] = {}
            clients[srcAddress]['lastPing'] = datetime.now()
            clients[srcAddress]['position'] = {"x": 0,"y": 0,"z": 0}
            print('[Notice] New Client Added: ', str(srcAddress))

            # Inform all currently connected clients of the arrival of the new client. 
            newMsgDict = {"cmd": 0,"player":{"id":str(srcAddress)}}
            msgJson = json.dumps(newMsgDict)
            for targetClient in clients:
               sock.sendto(bytes(msgJson,'utf8'), (targetClient[0],targetClient[1])) 

            # Send newly connected client a list of currently connected clients. 
            GameState = {"cmd": 3, "players": []}
            clients_lock.acquire()
            for c in clients:
               player = {}
               clients[c]['position'] = {"x": 0, "y": 0, "z": 0}
               player['id'] = str(c)
               player['color'] = clients[c]['color']
               GameState['players'].append(player)
            
               msgState = json.dumps(GameState)
               sock.sendto(bytes(msgState,'utf8'), (srcAddress[0],srcAddress[1])) 
               clients_lock.release()
               
         elif msgDict['flag'] == 2: # Client Ping
            clients[msgDict['source']]['lastPing'] = datetime.now()
               


# Every loop, the server checks if a client has not sent a heartbeat in the last 5 seconds. 
# If a client did not meet the heartbeat conditions, the server drops the client from the game.
# If a client is dropped, the server sends a message to all clients currently connected to inform them of the dropped player. (Implementation Missing)
def cleanClients(sock):
   while True:
      # Loop through clients
      for c in list(clients.keys()):

         # Every loop, the server checks if a client has not sent a heartbeat in the last 5 seconds.
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            droppedClientAddress = c
            # Drop the client from the game.
            print('[Notice] Dropped Client: ', c)
            clients_lock.acquire()
            del clients[c]
            
            #Sends a message to all clients currently connected to inform them of the dropped player. 
            msgDict = {"cmd": 2,"player":{"id":str(droppedClientAddress)}}

            msgJson = json.dumps(msgDict)
            for targetClient in clients:
               sock.sendto(bytes(msgJson,'utf8'), (targetClient[0],targetClient[1])) 

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
         clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
         player['id'] = str(c)
         player['color'] = clients[c]['color']
         GameState['players'].append(player)

      # Sends a message containing the current state of the game. This game state contains the id’s and colours of all players currently in the game.
      msgState = json.dumps(GameState)
      #print ('[Notice] Game State:')
      #print(s)
      for c in clients:
         sock.sendto(bytes(msgState,'utf8'), (c[0],c[1]))
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
