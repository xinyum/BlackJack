#!/usr/bin/env python
import socket
import select
import time
import random
import sys
from Utilities import Utilities

class Logic(object):
    def __init__(self, playerlist):
        self.allcards = ['0101', '0102', '0103', '0104', '0201', '0202', '0203', '0204',
                         '0301', '0302', '0303', '0304', '0401', '0402', '0403', '0404',
                         '0501', '0502', '0503', '0504', '0601', '0602', '0603', '0604',
                         '0701', '0702', '0703', '0704', '0801', '0802', '0803', '0804',
                         '0901', '0902', '0903', '0904', '1001', '1002', '1003', '1004',
                         '1101', '1102', '1103', '1104', '1201', '1202', '1203', '1204',
                         '1301', '1302', '1303', '1304']
        self.playerlist = playerlist
        self.isgameover = False
        self.isStay = False

    def linkPlayer(self):
        if len(self.playerlist) < 2:
            print "ERROR number of players"
        self.playerlist[0].other = self.playerlist[1]
        self.playerlist[1].other = self.playerlist[0]

    def getPlayer(self, sock):
        for player in self.playerlist:
            if sock == player.sock:
                return player


    def randomPickcards(self):
        cards = random.choice(self.allcards)
        self.allcards.remove(cards)
        return cards

    def playercardsstore(self, player, cards):
        player.handcards.append(cards)

    def deal_start_cards(self):
        for i in xrange(2):
            for player in self.playerlist:
                cards = self.randomPickcards()
                self.playercardsstore(player, cards)

    def deal_one_card(self, player):
        card = self.randomPickcards()
        self.playercardsstore(player, card)
        return card


class Player(object):
    def __init__(self, sock, name):
        self.sock = sock
        self.gameover = False
        self.name = name
        self.handcards = []
        self.score = 0
        self.other = None


class PlayerConnection(object):
    def __init__(self, server_sock, readlist, writelist, numPlayers = 2):
        self.readlist = readlist
        self.writelist = writelist
        self.server_sock = server_sock
        self.numPlayers = numPlayers

    def to_close(self):
        print "Close server"
        sys.exit()

    def start(self):
        while True:
            (readable, writable, exceptional) = select.select(self.readlist, [], [])
            for soc in readable:
                if soc == self.server_sock:
                    # A "readable" server socket is ready to accept a connection
                    new_socket, (remhost, remport) = soc.accept()
                    self.readlist.append(new_socket)
                    self.writelist.append(new_socket)
                    self.sendToAll('playernum ' + str(len(self.writelist)))
                    if len(self.writelist) == self.numPlayers:
                        time.sleep(2)
                        name = 'A'
                        playerlist = []
                        for gamesoc in self.writelist:
                            try:
                                gamesoc.send('gamestart ' + name)
                                playerlist.append(Player(gamesoc, name))
                                name = chr(ord(name) + 1)
                            except Exception, e:
                                print e
                                soc.close()
                                self.readlist.remove(soc)
                                self.writelist.remove(soc)
                        gamelogic = Logic(playerlist)
                        gamelogic.linkPlayer()
                        gamelogic.deal_start_cards()
                        time.sleep(0.5)
                        for player in playerlist:
                            player.sock.send('dealcard ' +'2 ' + ' '.join(player.handcards))
                        time.sleep(0.5)
                else:
                    try:
                        recvdata = soc.recv(1024)
                        if not recvdata:
                            continue
                        player = gamelogic.getPlayer(soc)
                        command_list = recvdata.strip().split(" ")
                        if len(command_list) < 1:
                            continue
                        command_name = command_list.pop(0)
                        if command_name == "hit":  # player ask for another card
                            card = gamelogic.deal_one_card(player)
                            player.sock.send('dealcard ' + '1 ' + card)
                        elif command_name == "stay":  # player ask to stay
                            cards = Utilities.translate_cards(player.handcards)
                            score = Utilities.calculate_score(cards)
                            player.score = score
                            if gamelogic.isgameover:  # other player busted
                                player.sock.send("notbusted")
                                self.to_close()
                            elif gamelogic.isStay:  # other player stay
                                score_other = player.other.score
                                if score > score_other:
                                    player.sock.send("win")
                                    player.other.sock.send("lose")
                                    self.to_close()
                                elif score < score_other:
                                    player.other.sock.send("win")
                                    player.sock.send("lose")
                                    self.to_close()
                                else:
                                    self.sendToAll("tie")
                                    self.to_close()
                            else:
                                gamelogic.isStay = True
                        elif command_name == "gameover":  # player busted
                            cards = Utilities.translate_cards(player.handcards)
                            score = Utilities.calculate_score(cards)
                            if score > 21:
                                player.sock.send('gameover')
                                player.other.sock.send("notbusted")
                                self.to_close()
                                player.gameover = True
                                gamelogic.isgameover = True
                    except Exception, e:
                        print e
                        self.to_close()

    def sendToAll(self, senddata):
        for soc in self.writelist:
            soc.send(senddata)


class Server(object):
    def run(self):
        TCP1_IP = '' # listen to everyone
        TCP1_PORT = 50001 # my port
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind((TCP1_IP, TCP1_PORT))
        server_sock.listen(5)
        readlist = [server_sock]
        writelist = []
        self.server_commu = PlayerConnection(server_sock, readlist, writelist)
        self.server_commu.start()

if __name__ == "__main__":
    Server().run()

