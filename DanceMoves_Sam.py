from motor import DRIVE

motor = DRIVE()

def read_file(filename):
    char_list = [ch for ch in open(filename).read()]
    #print(char_list)
    return char_list

def readmove(moves, i):
    move = moves[i]
    return move
