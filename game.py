from card import Card
from player import Player
import random
import os
import shutil
import math
import matplotlib.pyplot as plt

def build_graph(cardType, player4, iteration):
    plt.plot(range(len(game.players[player4].utils[cardType])), list(game.players[player4].utils[cardType].values()))
    plt.xlabel('Cards')
    plt.ylabel('Utils')
    plt.show()
    plt.savefig(game.players[player4].index + "/"+ cardType + str(iteration) + ".png")
    plt.clf()

class Game: 
    def __init__(self):
        self.cards = set()
        self.removecards = set()
        self.hiddencards = {}

        self.players = {}
        self.divisions = {}
        
        self.positions = [(1,1), (4,1), (7,1), (1,3), (7,3), (7,5), (1, 7), (4,7), (7,7)]
        self.playerPositions = [(2,1), (1,2), (7,2), (7,6), (2,7), (5,7)]

        self.types = []

    def initialize_cards(self):
        self.cards.add(Card('room', 'Lounge'))
        self.cards.add(Card('room', 'Dining Room'))
        self.cards.add(Card('room', 'Kitchen'))
        self.cards.add(Card('room', 'Ballroom'))
        self.cards.add(Card('room', 'Conservatory'))
        self.cards.add(Card('room', 'Billiard Room'))
        self.cards.add(Card('room', 'Library'))
        self.cards.add(Card('room', 'Study'))
        self.cards.add(Card('room', 'Hall'))

        self.cards.add(Card('suspect', 'Miss Scarlett'))
        self.cards.add(Card('suspect', 'Coloniel Mustard'))
        self.cards.add(Card('suspect', 'Misses White'))
        self.cards.add(Card('suspect', 'Mister Green'))
        self.cards.add(Card('suspect', 'Misses Peacock'))
        self.cards.add(Card('suspect', 'Professor Plumb'))

        self.cards.add(Card('weapon', 'Lead Pipe'))
        self.cards.add(Card('weapon', 'Wrench'))
        self.cards.add(Card('weapon', 'Knife'))
        self.cards.add(Card('weapon', 'Revolver'))
        self.cards.add(Card('weapon', 'Candlestick'))
        self.cards.add(Card('weapon', 'Rope'))

    def initialize_hiddencards(self):     
        rooms = []
        suspects = []
        weapons = []
        n = 0

        for card in self.cards:
            if card.type == "room":
                rooms.append(card)
                self.divisions[card.name] = self.positions[n]
                n += 1
            if card.type == "suspect":
                suspects.append(card)
            if card.type == "weapon":
                weapons.append(card)

        self.removecards = set(self.cards)

        hidden_room = random.choice(rooms)
        self.hiddencards["room"] = hidden_room.name
        self.removecards.remove(hidden_room)
        hidden_suspect = random.choice(suspects)
        self.hiddencards["suspect"] = hidden_suspect.name
        self.removecards.remove(hidden_suspect)
        hidden_weapon = random.choice(weapons)
        self.hiddencards["weapon"] = hidden_weapon.name
        self.removecards.remove(hidden_weapon)

    def initialize_players(self, numPlayers):
        gameCardsSize = len(self.removecards)
        if gameCardsSize % numPlayers == 0:
            n = 1
            while n <= numPlayers:
                randomCards = random.sample(self.removecards, int(math.floor(gameCardsSize/ numPlayers)))
                self.players["player" + str(n)] = Player("player" + str(n), randomCards, self.playerPositions[n-1], game, self.types[n-1])
                self.removecards.difference_update(randomCards)
                n += 1

        else: # if number of players not divisible by 18 (number of cards without hidden cards)
            randomCards = random.sample(self.removecards, int(math.floor(gameCardsSize % numPlayers)))
            self.removecards.difference_update(randomCards)
            gameCardsSize = len(self.removecards)
            self.cards.difference_update(randomCards)
            n = 1
            while n <= numPlayers:
                randomCards = random.sample(self.removecards, int(math.floor(gameCardsSize/ numPlayers)))
                self.players["player" + str(n)] = Player("player" + str(n), randomCards, self.playerPositions[n-1], game, self.types[n-1])
                self.removecards.difference_update(randomCards)
                n += 1


#####################
###     MAIN      ###
#####################
if __name__== "__main__":
    game = Game()
    game.initialize_cards()
    game.initialize_hiddencards()

    print("\nSelect 2 - 6 players\n")
    players = input("How many players do you want: ")

    bold = input("\nHow many bold players do you want (use " + players + " or less): ")

    cautious = str(int(players) - int(bold))
    print("\nRemaining " + cautious + " players are cautious\n")

    x = int(bold)
    while x > 0:
        game.types.append("bold")
        x -= 1
        
    y = int(cautious)
    while y > 0:
        game.types.append("cautious")
        y -= 1

    print(game.types)

    game.initialize_players(int(players))

    delete_players = ["player1", "player2", "player3", "player4", "player5", "player6"]

    for player in delete_players:
        if os.path.isdir(player):
            shutil.rmtree(player)

    for player in game.players:
        # If you want to see the cards each player has --> uncomment these lines
        # print("\n" + player)
        # for card in game.players[player].cards:
        #     print(card)
        os.mkdir(player)

        game.players[player].initialize_probs()

    print("\nSelect: \n1 - Dynamic Strategy\n2 - naive strategy\n")
    strategy = input("Strategy: ")

    iteration = 1
    playing = True
    print("\n################### Game starting ###################")
    while playing:
        for player in game.players:
            print("\n--------------------- Iteration" + str(iteration) + " ---------------------\n") 
            suspicion = game.players[player].suspicion(strategy)
            print(player)
            print("\n--------- Suspicion ---------")
            print(suspicion)
            # if iteration == 1:
            #     build_graph("room", player, iteration-1)
            #     build_graph("suspect", player, iteration-1)
            #     build_graph("weapon", player, iteration-1)
            for player2 in game.players:
                if player2 != player:
                    has_card = False
                    #checks if has card and if yes gives card
                    if game.players[player2].checks_cards(suspicion, game.players[player]):
                        has_card = True
                        print("\n" + player2 + " gives card")
                        if strategy == "1":
                            for player3 in game.players:
                                if player3 != player2:
                                    print(player3 + " updates suspicion")
                                    game.players[player3].update_suspicions(suspicion, player2)
                                
                                if player3 != player and player3 != player2:
                                    print(player3 + " updates probs")
                                    game.players[player3].update_probs(suspicion, player2)
                        break
                    else: #Player2 has none of the cards --> all players, except player 2, update their probs
                        print("\n" + player2 + " has no card")
                        if strategy == "1":
                            for player3 in game.players:
                                if player3 != player2:
                                    print(player3 + " updates probs")
                                    game.players[player3].update_probs_no_card(suspicion, player2)

            for player4 in game.players:
                game.players[player4].update_utils(strategy, has_card, suspicion)
                # build_graph("room", player4, iteration)
                # build_graph("suspect", player4, iteration)
                # build_graph("weapon", player4, iteration)
                game.players[player4].dataframes["room"].to_csv(game.players[player4].index + "/room" + str(iteration) + ".csv")
                game.players[player4].dataframes["suspect"].to_csv(game.players[player4].index + "/suspect" + str(iteration) + ".csv")
                game.players[player4].dataframes["weapon"].to_csv(game.players[player4].index + "/weapon" + str(iteration) + ".csv")

            won = False
            if game.players[player].checkIfWon():
                print("\n------------ " + player + " thinks he/she won ------------\n")
                print("\n-------- player cards --------")
                for card in game.players[player].hiddenCards:
                    print(game.players[player].hiddenCards[card])

                print("\n-------- crime cardsssssssss --------")

                for card in game.hiddencards:
                    print(game.hiddencards[card])

                if game.hiddencards == game.players[player].hiddenCards:
                    print("\n################### " + player + " WON!!!! ###################")
                
                else:
                    print("\n################### " + player + " LOSTT!!!!###################")

                print("\n-------------- I am " + game.players[player].type + " --------------\n")            

                playing = False
                break
                break

            iteration += 1