import sys
import collections
import numpy as np
import heapq
import time
import numpy as np
global posWalls, posGoals
class PriorityQueue:
    """Define a PriorityQueue data structure that will be used"""
    def  __init__(self):
        self.Heap = []
        self.Count = 0
        self.len = 0

    def push(self, item, priority):
        entry = (priority, self.Count, item)
        heapq.heappush(self.Heap, entry)
        self.Count += 1

    def pop(self):
        (_, _, item) = heapq.heappop(self.Heap)
        return item

    def isEmpty(self):
        return len(self.Heap) == 0

"""Load puzzles and define the rules of sokoban"""

def transferToGameState(layout):
    """Transfer the layout of initial puzzle"""
    layout = [x.replace('\n','') for x in layout]
    layout = [','.join(layout[i]) for i in range(len(layout))]
    layout = [x.split(',') for x in layout]
    maxColsNum = max([len(x) for x in layout])
    for irow in range(len(layout)):
        for icol in range(len(layout[irow])):
            if layout[irow][icol] == ' ': layout[irow][icol] = 0   # free space
            elif layout[irow][icol] == '#': layout[irow][icol] = 1 # wall
            elif layout[irow][icol] == '&': layout[irow][icol] = 2 # player
            elif layout[irow][icol] == 'B': layout[irow][icol] = 3 # box
            elif layout[irow][icol] == '.': layout[irow][icol] = 4 # goal
            elif layout[irow][icol] == 'X': layout[irow][icol] = 5 # box on goal
        colsNum = len(layout[irow])
        if colsNum < maxColsNum:
            layout[irow].extend([1 for _ in range(maxColsNum-colsNum)]) 

    # print(layout)
    return np.array(layout)
def transferToGameState2(layout, player_pos):
    """Transfer the layout of initial puzzle"""
    maxColsNum = max([len(x) for x in layout])
    temp = np.ones((len(layout), maxColsNum))
    for i, row in enumerate(layout):
        for j, val in enumerate(row):
            temp[i][j] = layout[i][j]

    temp[player_pos[1]][player_pos[0]] = 2
    return temp

def PosOfPlayer(gameState):
    """Return the position of agent"""
    return tuple(np.argwhere(gameState == 2)[0]) # e.g. (2, 2)

def PosOfBoxes(gameState):
    """Return the positions of boxes"""
    return tuple(tuple(x) for x in np.argwhere((gameState == 3) | (gameState == 5))) # e.g. ((2, 3), (3, 4), (4, 4), (6, 1), (6, 4), (6, 5))

def PosOfWalls(gameState):
    """Return the positions of walls"""
    return tuple(tuple(x) for x in np.argwhere(gameState == 1)) # e.g. like those above

def PosOfGoals(gameState):
    """Return the positions of goals"""
    return tuple(tuple(x) for x in np.argwhere((gameState == 4) | (gameState == 5))) # e.g. like those above

def isEndState(posBox):
    """Check if all boxes are on the goals (i.e. pass the game)"""
    return sorted(posBox) == sorted(posGoals)#ki???m tra c??c h???p ???? v??o ????ng v??? tr?? hay ch??a

def isLegalAction(action, posPlayer, posBox):#ki???m tra h??nh ?????ng di chuy???n c?? ????ng hay kh??ng
    """Check if the given action is legal"""
    xPlayer, yPlayer = posPlayer#v??? tr?? ng?????i ch??i
    if action[-1].isupper(): # the move was a push,ki???m tra h??nh ?????ng v???a m???i th???c hi???n
        x1, y1 = xPlayer + 2 * action[0], yPlayer + 2 * action[1]
    else:
        x1, y1 = xPlayer + action[0], yPlayer + action[1]
    return (x1, y1) not in posBox + posWalls #vi tri hop khac voi vi tri Wall sau khi di chuyen

def legalActions(posPlayer, posBox):
    """Return all legal actions for the agent in the current game state"""
    allActions = [[-1,0,'u','U'],[1,0,'d','D'],[0,-1,'l','L'],[0,1,'r','R']]
    xPlayer, yPlayer = posPlayer
    legalActions = []
    for action in allActions:
        x1, y1 = xPlayer + action[0], yPlayer + action[1]
        if (x1, y1) in posBox: # the move was a push
            action.pop(2) # drop the little letter
        else:
            action.pop(3) # drop the upper letter
        if isLegalAction(action, posPlayer, posBox):
            legalActions.append(action)
        else: 
            continue     
    return tuple(tuple(x) for x in legalActions) # e.g. ((0, -1, 'l'), (0, 1, 'R'))

def updateState(posPlayer, posBox, action):
    """Return updated game state after an action is taken"""
    xPlayer, yPlayer = posPlayer # the previous position of player
    newPosPlayer = [xPlayer + action[0], yPlayer + action[1]] # the current position of player
    posBox = [list(x) for x in posBox]
    if action[-1].isupper(): # if pushing, update the position of box
        posBox.remove(newPosPlayer)
        posBox.append([xPlayer + 2 * action[0], yPlayer + 2 * action[1]])
    posBox = tuple(tuple(x) for x in posBox)
    newPosPlayer = tuple(newPosPlayer)
    return newPosPlayer, posBox

def isFailed(posBox):
    """This function used to observe if the state is potentially failed, then prune the search"""
    rotatePattern = [[0,1,2,3,4,5,6,7,8],
                    [2,5,8,1,4,7,0,3,6],
                    [0,1,2,3,4,5,6,7,8][::-1],
                    [2,5,8,1,4,7,0,3,6][::-1]]
    flipPattern = [[2,1,0,5,4,3,8,7,6],
                    [0,3,6,1,4,7,2,5,8],
                    [2,1,0,5,4,3,8,7,6][::-1],
                    [0,3,6,1,4,7,2,5,8][::-1]]
    allPattern = rotatePattern + flipPattern

    for box in posBox:
        if box not in posGoals:
            board = [(box[0] - 1, box[1] - 1), (box[0] - 1, box[1]), (box[0] - 1, box[1] + 1), 
                    (box[0], box[1] - 1), (box[0], box[1]), (box[0], box[1] + 1), 
                    (box[0] + 1, box[1] - 1), (box[0] + 1, box[1]), (box[0] + 1, box[1] + 1)]
            for pattern in allPattern:
                newBoard = [board[i] for i in pattern]
                if newBoard[1] in posWalls and newBoard[5] in posWalls: return True
                elif newBoard[1] in posBox and newBoard[2] in posWalls and newBoard[5] in posWalls: return True
                elif newBoard[1] in posBox and newBoard[2] in posWalls and newBoard[5] in posBox: return True
                elif newBoard[1] in posBox and newBoard[2] in posBox and newBoard[5] in posBox: return True
                elif newBoard[1] in posBox and newBoard[6] in posBox and newBoard[2] in posWalls and newBoard[3] in posWalls and newBoard[8] in posWalls: return True
    return False

"""Implement all approcahes"""

def depthFirstSearch(gameState):
    """Implement depthFirstSearch approach"""
    beginBox = PosOfBoxes(gameState)# v??? tr?? c???a c??c h???p
    beginPlayer = PosOfPlayer(gameState)#v??? tr?? c???a ng?????i ch??i

    startState = (beginPlayer, beginBox)# tr???ng th??i c???a b???n ????? (l??u tr??? c??c th??? thay ?????i beginPlayer,beginBox)
    frontier = collections.deque([[startState]])# store states,t???o h??ng ?????i frontier v???i ??i???m ban ?????u trong h??ng ?????i l?? tr???ng th??i c???a tr?? choi
    exploredSet = set()# t???p l??u tr??? c??c ??i???m ???? kh??m ph?? (???? ???????c th??m v??o ???????ng ??i)
    actions = [[0]] # ??i ti???p ???????ng ??i n??n s??? l??u d?????i d???ng m???ng ????? d??? truy xu???t ph???n t???
    temp = []
    while frontier:# ki???m tra frontier c?? r???ng hay kh??ng
        node = frontier.pop()#l???y ph???n t??? cu???i ra trong m???ng v?? x??a n?? kh???i m???ng f
        node_action = actions.pop()# l???y h??nh ?????ng cu???i trong m???ng v?? x??a n?? kh???i m???ng
        if isEndState(node[-1][-1]):# n???u tr???ng th??i hi???n th???i (???ng v???i node cu???i) gi???ng v???i goalState th?? ta s??? c???ng v??o temp c??c action ???? ??i qua
            temp += node_action[1:]# c???ng v??o ???????ng ??i ???? t??m ???????c
            break
        if node[-1] not in exploredSet:# n???u node cu???i kh??ng n???m trong t???p ???? ??i qua
            exploredSet.add(node[-1])# th??m n?? v??o
            for action in legalActions(node[-1][0], node[-1][1]):# ???ng v???i c??c tr???ng th??i
                newPosPlayer, newPosBox = updateState(node[-1][0], node[-1][1], action)# c???p nh???t tr???ng th??i tr?? ch??i
                if isFailed(newPosBox):#ki???m tra k???t qu??? tr?? ch??i,
                    continue
                frontier.append(node + [(newPosPlayer, newPosBox)])# th??m v??? tr?? m???i v??o m???ng frontier
                actions.append(node_action + [action[-1]])#th??m  h??nh ?????ng ???? ??i v??o m???ng action
    return temp

def breadthFirstSearch(gameState):
    """Implement breadthFirstSearch approach"""
    beginBox = PosOfBoxes(gameState)#v??? tr?? c???a c??c h???p hi???n t???i(array)
    beginPlayer = PosOfPlayer(gameState)# v??? tr?? ?????ng c???a ng?????i ch??i

    startState = (beginPlayer, beginBox)  # e.g. ((2, 2), ((2, 3), (3, 4), (4, 4), (6, 1), (6, 4), (6, 5)))#tr???ng th??i c???a b???n ?????
    frontier = collections.deque([[startState]])  # store states,t???o h??ng ?????i frontier v???i ??i???m ban ?????u trong h??ng ?????i l?? v??? tr?? ng?????i ch??i
    actions = collections.deque([[0]])  # store actions ,ta xem v??? tr?? ban ?????u l?? tr???ng th??i 0(t?????ng tr??ng cho node ban ?????u)
    exploredSet = set()# t???p c??c gi?? tr??? ??i???m ???? ??i qua ,d??? th???y r???ng n???u ???????ng ??i c?? s??? l???p l???i s??? d???n ?????n c??y t??m ki???m d??i v?? h???n
    #t??? ???? ta s??? s??? d???ng set ????? l??u tr??? c??c ??i???m ???? ??i qua(set l?? m???t hashtable c?? th??? thay ?????i nh??ng kh??ng l??u ch??? m???c v?? kh??ng ch???p nh???n s??? tr??ng l???p)
    temp=[]# l??u tr??? ???????ng ??i ????ng (trace-back)
    while frontier:
        node = frontier.popleft()#l???y ??i???m ?????u ti??n b??n tr??i  trong frontier v?? x??a n?? ??i(BFS t??m ki???m t??? tr??i tr??n ph???i)
        node_action = actions.popleft()#l???y action ?????u ti??n b??n tr??i trong action v?? x??a action ???? ??i
        if isEndState(node[-1][-1]):# n???u node cu???i c??ng gi???ng v???i goal th?? ta l???y c???ng v??o temp ???????ng ??i ????
            temp += node_action[1:] # c???ng array l??u tr??? ???????ng ??i
            print('BFS done')
            break
        if node[-1] not in exploredSet:#n???u node  kh??ng t???n t???i trong t???p ??i???m ???? ??i th?? th??m v??o
            exploredSet.add(node[-1])#th??m node[-1] v??o ?????u exploredSet
            for action in legalActions(node[-1][0], node[-1][1]):# t???o ra t???p c??c ???????ng ??i (left,right,top,bottom)
                newPosPlayer, newPosBox = updateState(node[-1][0], node[-1][1], action)#c???p nh???t t???a ????? c???a H???p v?? ng?????i ch??i( ?????i l?????ng thay ?????i )
                if isFailed(newPosBox):# n???u v??? tr??  chi???c h???p ????ng
                    continue
                frontier.append(node + [(newPosPlayer, newPosBox)])#th??m v??? tr?? c???a game( ) v??o frontier(kh??i ph???c v??? tr?? c???a node sau v??? tr?? m???i)
                actions.append(node_action + [action[-1]]) #th??m h??nh ?????ng v??o action (kh??i ph???c h??nh ?????ng ???? lo???i b???)
    return temp
    
def cost(actions):
    """A cost function"""
    return len([str(x) for x in actions if x.islower()])#chi phi di chuyen bang so luong cac phep di chuyen hop le

def uniformCostSearch(gameState):
    """Implement uniformCostSearch approach"""
    beginBox = PosOfBoxes(gameState)  # v??? tr?? c???a h???p
    beginPlayer = PosOfPlayer(gameState)  # v??? tr?? c???a player

    startState = (beginPlayer, beginBox)  # tr???ng th??i game
    frontier = PriorityQueue()  # t???o h??ng ?????i ??u ti??n v?? ?? t?????ng c???a ucs l?? ??i d???a tr??n vi???c x???p theo gi?? tr??? Cost
    frontier.push([startState], 0)  # chi ph?? ban ?????u l?? 0(ch??a ??i)
    exploredSet = set()  # t???p c??c ??i???m ???? ??i qua (kh??ng  l???p l???i trong su???t ???????ng ??i)
    actions = PriorityQueue()  # t???o h??ng ?????i h??nh ?????ng
    actions.push([0], 0)  # b???t ?????u node 0 v???i chi ph?? 0
    temp = []
    ### Implement uniform cost search here
    while frontier:
        node = frontier.pop()  # l???y ra kh???i h??ng ?????i ??i???m cu???i  v?? x??a n??
        node_action = actions.pop()  # l???y ra kh???i h??ng ?????i action cu???i  v?? x??a n??
        if isEndState(node[-1][-1]):  # n???u node cu???i c?? cost=0
            temp += node_action[1:]  # th??m c??c h??nh ?????ng ???? ??i c???a ???????ng ??i ???? v??o temp
            print('UCS Done')
            break
        if node[-1] not in exploredSet:  # n???u node cu???i ch??a n???m trong t???p ???? ??i
            exploredSet.add(node[-1])  # th??m n?? v??o tap duong di
            Cost = cost(node_action[1:])# chi ph?? t??nh t??? ban ?????u ?????n node hi???n t???i
            for action in legalActions(node[-1][0], node[-1][1]):
                newPosPlayer, newPosBox = updateState(node[-1][0], node[-1][1], action)#cap nhat vi ti nguoi choi va box
                if isFailed(newPosBox):
                    continue
                frontier.push(node + [(newPosPlayer, newPosBox)],Cost)#them vao hang doi frontier chi phi di va node do
                actions.push(node_action + [action[-1]],Cost)#them action ,cost action vao
    return temp
"""Read command"""
def readCommand(argv):
    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option('-l', '--level', dest='sokobanLevels',
                      help='level of game to play', default='level6.txt')
    parser.add_option('-m', '--method', dest='agentMethod',
                      help='research method', default='bfs')
    args = dict()
    options, _ = parser.parse_args(argv)
    with open('assets/levels/' + options.sokobanLevels,"r") as f: 
        layout = f.readlines()
    args['layout'] = layout
    args['method'] = options.agentMethod
    return args

def get_move(layout, player_pos, method):
    time_start = time.time()
    global posWalls, posGoals
    # layout, method = readCommand(sys.argv[1:]).values()
    gameState = transferToGameState2(layout, player_pos)
    posWalls = PosOfWalls(gameState)
    posGoals = PosOfGoals(gameState)
    if method == 'dfs':
        result = depthFirstSearch(gameState)
    elif method == 'bfs':
        result = breadthFirstSearch(gameState)    
    elif method == 'ucs':
        result = uniformCostSearch(gameState)
    else:
        raise ValueError('Invalid method.')
    time_end=time.time()
    print('Runtime of %s: %.2f second.' %(method, time_end-time_start))
    print(result)
    return result
