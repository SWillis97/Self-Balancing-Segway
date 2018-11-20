from motor import DRIVE

motor = DRIVE()

def read_file(filename):
    char_list = [ch for ch in open(filename).read() if ch not in ['\r', '\n']]
    return char_list

def readmove(moves, i, pwmValue):
    move = moves[i]
    if move == 'a':
        print('left 45')
        motor.right_forward(pwmValue)
        motor.left_forward(pwmValue/3)
    elif move == 'b':
        print('right 45')
        motor.right_forward(pwmValue/3)
        motor.left_forward(pwmValue)
    elif move == 'c':
        print('backwards')
        motor.right_back(pwmValue)
        motor.left_back(pwmValue)
    elif move == 'd':
        print('forwards')
        motor.right_forward(pwmValue)
        motor.left_forward(pwmValue)
    elif move == 'e':
        print('left 90')
        motor.right_forward(pwmValue/6)
        motor.left_forward(pwmValue)
