#!/usr/bin/env python
import socket
import threading
import select
import sys
from Utilities import Utilities

class Receiver(threading.Thread):
    def __init__(self, socket):
        super(Receiver, self).__init__()
        self.list = [socket]
        self.cards = []
        self.gameover = False
        self.support_command = ["playernum", "gamestart", "dealcard", "gameover",
                                "win", "lose", "notbusted", "tie"]

    def safeExit(self):
        socket = self.list.pop()
        socket.close()
        sys.exit()

    def exitingPromp(self):
        s = False
        while not s:
            inputs = raw_input("press q for exiting\n")
            if inputs.lower() == 'q':
                self.safeExit()
            else:
                self.exitingPromp()

    def logicHelper(self, socket, command_name, command_list):
        if command_name == "playernum":
            comm = int(command_list.pop(0))
            if comm == 1:
                print "You have connected to the game, waiting another player to join..."
            elif comm == 2:
                print "The Game will begin soon."
            else:
                pass
        elif command_name == "gamestart":
            comm = command_list.pop(0)
            print "You are Player " + comm + ". Dealing the two starting cards..."
        elif command_name == "dealcard":
            num_cards = int(command_list.pop(0))
            new_cards = Utilities.translate_cards([c for c in command_list[:num_cards]])
            self.cards.extend(new_cards)
            for card in new_cards:
                print card.get("string")
            score = Utilities.calculate_score(self.cards)
            if score > 21:
                self.gameover = True
            if self.gameover:
                socket.send("gameover")
            else:
                decision = raw_input('Hit or Stay?\n')
                while decision.strip().lower() not in ['hit', 'stay']:
                    decision = raw_input("Didn't get that, hit or stay?\n")
                if decision.strip().lower() == 'stay':
                    socket.send("stay")
                    print "You choose to stay, waiting on the other player..."
                else:
                    socket.send("hit")
        elif command_name == "gameover":
            print "YOU LOSE. You busted."
            self.exitingPromp()
        elif command_name == "lose":
            print "YOU LOSE. You have lower score."
            self.exitingPromp()
        elif command_name == "win":
            print "YOU WIN! You have higher score."
            self.exitingPromp()
        elif command_name == "notbusted":
            print "YOU WIN! The other player busted."
            self.exitingPromp()
        elif command_name == "tie":
            print "YOU TIE! You have same score."
            self.exitingPromp()
        else:
            pass

    def run(self):
        while True:
            (readable, writable, exceptional) = select.select(self.list, [], [])

            for soc in readable:
                try:
                    recvdata = soc.recv(1024)
                    command_list = recvdata.strip().split(" ")
                    if len(command_list) < 1:
                        continue
                    command_name = command_list.pop(0)
                    if command_name not in self.support_command:
                        continue
                    self.logicHelper(soc, command_name, command_list)

                except Exception, e:
                    print e
                    print "ERROR happens, please re-open the game"
                    self.exitingPromp()


class Client(object):
    def __init__(self):
        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receiver = None

    def run(self):
        TCP_PORT = 50001
        ip = raw_input("Enter the server ip address:(empty means local server)\n")
        if not ip:
            ip = "127.0.0.1"

        def reconnect():
            try:
                self.client_sock.connect((ip, TCP_PORT))
            except Exception, e:
                print e
                i = raw_input("Press r for retry:\n")
                if i.lower() == "r":
                    reconnect()
                else:
                    print "Exiting..."
                    sys.exit()

        reconnect()

        self.receiver = Receiver(self.client_sock)
        self.receiver.start()

if __name__ == "__main__":
    Client().run()