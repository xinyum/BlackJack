#!/usr/bin/env python
class Utilities(object):
    @staticmethod
    def translate_cards(raw_cards):
        cards = []
        suitmap = {"01":'Diamonds', "02":'Clubs',"03":"Hearts", "04":"Spades"}
        rankmap = {"13":'King', "11":"Jack", "12":"Queen", "01":"Ace"}
        for card in raw_cards:
            info = {}
            rank = card[:2]
            suit = card[2:]
            info['rank'] = int(rank)
            info['string'] = suitmap[suit]
            if info['rank'] > 1 and info['rank'] <= 10:
                info['string'] += " " + str(info['rank'])
                info['score'] = info['rank']
            elif info['rank'] > 10 and info['rank'] <= 13:
                info['string'] += " " + rankmap[rank]
                info['score'] = 10
            elif info['rank'] == 1:
                info['score'] = 1
                info['string'] += " " + rankmap[rank]
            else:
                continue
            cards.append(info)
        return cards

    @staticmethod
    def calculate_score(cards):
        total = 0
        numAce = 0
        for card in cards:
            if card["rank"] == 1:
                numAce += 1
                total += 1
            else:
                total += card["score"]
        if total < 11 and numAce > 0:
            total += 10
        return total
