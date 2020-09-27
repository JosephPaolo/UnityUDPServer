"""
Author: Galal 

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

# Connection loop continuously listens for messages and 
def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      data = str(data)
      if addr in clients:

         # If the server receives a heartbeat message:
         if 'heartbeat' in data:

            # Update last heartbeat time
            clients[addr]['lastBeat'] = datetime.now()
      else: 
         # When a new client connects:
         if 'connect' in data:

            # The server adds the new client to a list of clients it has.
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = 0
            print('[Notice] New Client Added: ', clients[addr])

            # Inform all currently connected clients of the arrival of the new client. TODO
            msgDict = {"cmd": 0,"player":{"id":str(addr)}}
            msgJson = json.dumps(msgDict)
            for targetClient in clients:
               sock.sendto(bytes(msgJson,'utf8'), (targetClient[0],targetClient[1]))

            #Send newly connected client a list of currently connected clients. TODO

# Every loop, the server checks if a client has not sent a heartbeat in the last 5 seconds. 
# If a client did not meet the heartbeat conditions, the server drops the client from the game.
# If a client is dropped, the server sends a message to all clients currently connected to inform them of the dropped player. (Implementation Missing)
def cleanClients():
   while True:
      # Loop through clients
      for c in list(clients.keys()):

         # Every loop, the server checks if a client has not sent a heartbeat in the last 5 seconds.
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:

            # Drop the client from the game.
            print('[Notice] Dropped Client: ', c)
            clients_lock.acquire()
            del clients[c]
            clients_lock.release()

            #Sends a message to all clients currently connected to inform them of the dropped player. TODO

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
      s=json.dumps(GameState)
      #print ('[Notice] Game State:')
      #print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      time.sleep(1)

def main():
   print('[Notice] Setting up server... ')
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,())
   print('[Notice] Server running.')
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
