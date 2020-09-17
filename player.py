import pandas as pd
import math
import random
import os

class Player:
    def __init__(self, index, cards, initposition, game, typeAgent):
        self.index = index
        self.type = typeAgent
        self.cardsBefore = cards
        self.cards = {}
        for card in cards:
            self.cards[card.name] = card #{'name': card}
        self.cardsFound = {}
        self.hiddenCards = {}
        self.changeSuspi = {}
        self.position = initposition
        self.game = game
        self.dataframes = {}
        self.suspicions = {}
        self.utils = {"room": {}, "suspect": {}, "weapon": {}} #rewards of player

    def initialize_probs(self):
        rooms = []
        suspects = []
        weapons = []

        #initialize utils
        for card in self.game.cards:
            if card.name not in self.cards:
                self.utils[card.type][card.name] = 1
                if card.type == "room":  
                    rooms.append(card.name)
                if card.type == "suspect":
                    suspects.append(card.name)
                if card.type == "weapon":
                    weapons.append(card.name)
            else:
                self.utils[card.type][card.name] = 0

        players = []
        for player in self.game.players:
            if player != self.index:
                players.append(player)
                self.cardsFound[player] = []
                self.suspicions[player] = []

        self.roomprobs = pd.DataFrame(index=players, columns = rooms, dtype='float64')
        self.suspectprobs = pd.DataFrame(index=players, columns = suspects, dtype='float64')
        self.weaponprobs = pd.DataFrame(index=players, columns = weapons, dtype='float64')

        self.dataframes['room'] = self.roomprobs
        self.dataframes['suspect'] = self.suspectprobs
        self.dataframes['weapon'] = self.weaponprobs


    def suspicion(self, strategy):
        maximumRoom = -100
        maximumSuspect = -100
        maximumWeapon = -100
        reward = 0
        for cardType in self.dataframes:
            if cardType == "room":
                if cardType in self.hiddenCards:
                    cardRoom = self.hiddenCards[cardType]
                    newPos = self.game.divisions[self.hiddenCards[cardType]]
                else:
                    for cardName in self.dataframes[cardType].columns:
                        if strategy == "2":
                            if cardType in self.changeSuspi:
                                if cardName == self.changeSuspi[cardType]:
                                    continue
                        util = self.utils[cardType][cardName]
                        divPosition = self.game.divisions[cardName]
                        distance = abs(math.sqrt((self.position[0]- divPosition[0])**2 
                        + (self.position[1] - divPosition[1])**2))

                        reward = util - (distance / 10)
                        if reward > maximumRoom:
                            maximumRoom = reward
                            cardRoom = cardName
                            newPos = divPosition

            elif cardType == "suspect":
                if cardType in self.hiddenCards:
                    cardSuspect = self.hiddenCards[cardType]
                else:
                    for cardName in self.dataframes[cardType].columns:
                        if strategy == "2":
                            if cardType in self.changeSuspi:
                                if cardName == self.changeSuspi[cardType]:
                                    continue
                        util = self.utils[cardType][cardName]
                        if util >= maximumSuspect:
                            maximumSuspect = reward
                            cardSuspect = cardName

            elif cardType == "weapon":
                if cardType in self.hiddenCards:
                    cardWeapon = self.hiddenCards[cardType]
                else:
                    for cardName in self.dataframes[cardType].columns:
                        if strategy == "2":
                            if cardType in self.changeSuspi:
                                if cardName == self.changeSuspi[cardType]:
                                    continue
                        util = self.utils[cardType][cardName]
                        if util > maximumWeapon:
                            maximumWeapon = reward
                            cardWeapon = cardName

        self.changeSuspi = {}
        self.position = newPos
        suspicion = "Name: " + cardSuspect + "\nWeapon: " + cardWeapon + "\nRoom: " + cardRoom

        return suspicion

    
    def checks_cards(self, suspicion, player):
        suspect, weapon, division = get_cards(suspicion)
        give = []

        for card in self.cards:
            if suspect == card or weapon == card or division == card:
                give.append(self.cards[card])
        
        if len(give) == 0:
            return False
        else:
            player.update_cards(self, random.choice(give))
            return True

    def update_cards(self, playerGaveCard, card):
        if card.name in self.dataframes[card.type].columns:
            self.dataframes[card.type].drop([card.name], axis=1, inplace = True)
            # for bold player
            if card.type in self.hiddenCards and card.name in self.hiddenCards[card.type]:
                #delete card from hiddenCards
                del self.hiddenCards[card.type]

        #update util --> reward is 0
        self.utils[card.type][card.name] = 0

        if card.name not in self.cardsFound[str(playerGaveCard.index)]:
            self.cardsFound[str(playerGaveCard.index)].append(card.name)

        #if the number of cards he gave me is the total he has --> 
        # he does not have the other cards in the game
        if (len(self.cardsFound[str(playerGaveCard.index)])==len(self.cards)):
            for col in self.dataframes[card.type].columns:
                self.dataframes[card.type].loc[str(playerGaveCard.index), col] = 0.0

    def update_probs(self, suspicion, player_has_card):
        suspect, weapon, division = get_cards(suspicion)
        suspect_cards = {'suspect': suspect, 'weapon': weapon, 'room': division}
        #stores card types
        combs = {"True": [], "False": []} #True if player has/knows cards
        
        if suspect in self.cardsFound[player_has_card] or weapon in self.cardsFound[player_has_card] or division in self.cardsFound[player_has_card]:
            # player that gave card already gave one of these to me before
            #check cards that I have
            combs[str(division in self.cards)].append("room")
            combs[str(suspect in self.cards)].append("suspect")
            combs[str(weapon in self.cards)].append("weapon")
        else:
            #What he has/knows
            combs[str(division not in self.dataframes['room'].columns)].append('room')
            combs[str(suspect not in self.dataframes['suspect'].columns)].append('suspect')
            combs[str(weapon not in self.dataframes['weapon'].columns)].append('weapon')
        
        if len(combs["True"]) == 0: #player has/knows no cards
            for cardType in combs["False"]: # comb is type of card
                if suspect_cards[cardType] in self.dataframes[cardType].columns:
                    probCard = self.dataframes[cardType].loc[player_has_card, suspect_cards[cardType]]
                    if (probCard != 0 and probCard < 0.33) or math.isnan(float(probCard)):
                        self.dataframes[cardType].loc[player_has_card, suspect_cards[cardType]] = 0.33


        elif len(combs["True"]) == 1: # player has/knows  1 card
            for cardType in combs["False"]:
                if suspect_cards[cardType] in self.dataframes[cardType].columns:
                    probCard = self.dataframes[cardType].loc[player_has_card, suspect_cards[cardType]]
                    if (probCard != 0 and probCard < 0.5) or math.isnan(float(probCard)):
                        self.dataframes[cardType].loc[player_has_card, suspect_cards[cardType]] = 0.5

        elif len(combs["True"]) == 2: # player has/knows  2 cards
            if suspect_cards[combs["False"][0]] in self.dataframes[combs["False"][0]].columns:
                self.dataframes[combs["False"][0]].drop([suspect_cards[combs["False"][0]]], axis=1, inplace = False)
                #upadte util --> reward is 0
                self.utils[combs["False"][0]][suspect_cards[combs["False"][0]]] = 0
                #add card to found cards
                self.cardsFound[player_has_card].append(suspect_cards[combs["False"][0]])

    def update_suspicions(self, suspicion, player_has_card):
        self.suspicions[player_has_card].append(suspicion)
    
    def update_probs_no_card(self, suspicion, player_no_card):
        suspect, weapon, division = get_cards(suspicion)
        suspect_cards = {'suspect': suspect, 'weapon': weapon, 'room': division}
        if len(self.suspicions[player_no_card]) != 0:
            for suspicion in self.suspicions[player_no_card]:
                #stores card types
                combs = {"True": [], "False": []} #True if cards are the same

                suspect2, weapon2, division2 = get_cards(suspicion)
                suspect_cards2 = {'suspect': suspect2, 'weapon': weapon2, 'room': division2}

                combs[str(suspect==suspect2)].append("suspect")
                combs[str(weapon==weapon2)].append("weapon")
                combs[str(division==division2)].append("room")

                if len(combs["True"]) == 2: # two cards in common
                    # player that gave card in previous suspicion (suspect_cards2) 
                    # has card that is in "False"
                    if suspect_cards2[combs["False"][0]] in self.dataframes[combs["False"][0]].columns:
                        #remove card from prob table
                        self.dataframes[combs["False"][0]].drop([suspect_cards2[combs["False"][0]]], axis=1, inplace = True)
                        #upadte util --> reward is 0
                        self.utils[combs["False"][0]][suspect_cards[combs["False"][0]]] = 0
                        #add card to found cards
                        self.cardsFound[player_no_card].append(suspect_cards[combs["False"][0]])

                elif len(combs["True"]) == 1: # one card in common
                    #player that gave card in previous suspicion (suspect_cards2) 
                    # does not have card in "True" so there is 50%/50% chance of having
                    # the cards in "False"
                    index = 1
                    for cardType in combs["False"]:
                        # if I have one of these cards --> the player has the other
                        if suspect_cards2[cardType] in self.cards:
                            if suspect_cards2[combs["False"][index]] in self.dataframes[cardType]:
                                self.dataframes[cardType].drop([suspect_cards2[combs["False"][index]]], axis=1, inplace = True)
                                 #upadte util --> reward is 0
                                self.utils[cardType][suspect_cards[combs["False"][index]]] = 0
                                #add card to found cards
                                self.cardsFound[player_no_card].append(suspect_cards[combs["False"][index]])
                                break
                        # if I do not have one of these cards, the player has 50%/50%
                        else:
                            if suspect_cards2[cardType] in self.dataframes[cardType].columns:
                                probCard = self.dataframes[cardType].loc[player_no_card, suspect_cards2[cardType]]
                                if probCard != 0 and probCard < 0.5:
                                    self.dataframes[cardType].loc[player_no_card, suspect_cards2[cardType]] = 0.5
                        index = index - 1


        #change prob of player having all of the cards in the suspicion to 0
        for card in suspect_cards:
            if suspect_cards[card] in self.dataframes[card].columns:
                self.dataframes[card].loc[player_no_card, suspect_cards[card]] = 0.0

    def checkIfWon(self):
        return len(self.hiddenCards) == 3

    def update_utils(self, strategy, has_card, suspicion):
        suspect, weapon, division = get_cards(suspicion)
        suspect_cards = {'suspect': suspect, 'weapon': weapon, 'room': division}
        #update utils
        for cardType in self.dataframes:
            if strategy == "2":
                # if bold and naive strategy --> pick card out of two columns --> 50% chance
                if (len(self.dataframes[cardType].columns) == 2) and (self.type == "bold"):
                    random_col = random.choice(self.dataframes[cardType].columns)
                    self.hiddenCards[cardType] =  random_col
                    self.utils[cardType][ random_col] = 1
                # if cautious and naive strategy --> pick card when there is only one column
                elif (len(self.dataframes[cardType].columns) == 1) and (self.type == "cautious" or self.type == "bold"):
                    self.hiddenCards[cardType] = self.dataframes[cardType].columns[0]
                    self.utils[cardType][self.dataframes[cardType].columns[0]] = 1
                # if no one gave card and naive strategy --> player needs to change suspicion for the next round
                if not has_card:
                    self.changeSuspi[cardType] = suspect_cards[cardType]
            # strategy is dynamic
            if strategy == "1":
                if (len(self.dataframes[cardType].columns) == 1):
                    self.hiddenCards[cardType] = self.dataframes[cardType].columns[0]
                    self.utils[cardType][self.dataframes[cardType].columns[0]] = 1
                else:
                    for col in self.dataframes[cardType].columns:
                        num_zeros = (self.dataframes[cardType][col] == 0).sum()
                        # if bold agent --> has 50% or higher chance of guessing the hidden cards 
                        if ((num_zeros / self.dataframes[cardType].shape[0]) >= 0.5) and (self.type == "bold"):
                            self.hiddenCards[cardType] = col
                            self.utils[cardType][col] = 1
                        # if cautious agent --> all values in collumn are 0 --> hidden card
                        elif ((self.dataframes[cardType][col] == 0).all()) and (self.type=="cautious"):
                            self.hiddenCards[cardType] = col
                            self.utils[cardType][col] = 1
                        # update util depending on probs --> get highest prob of each column --> util = 1 - prob
                        else:
                            maximum = self.dataframes[cardType][col].max()
                            if not math.isnan(float(maximum)) and maximum != 0:
                                self.utils[cardType][col] = 1 - maximum

def get_cards(suspicion):
    suspect = suspicion.split("\n")[0]
    suspect = suspect.replace("Name: ", "")
    weapon = suspicion.split("\n")[1]
    weapon = weapon.replace("Weapon: ", "")
    division = suspicion.split("\n")[2]
    division = division.replace("Room: ", "")

    return suspect, weapon, division        