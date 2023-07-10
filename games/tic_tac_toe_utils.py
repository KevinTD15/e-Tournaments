def minimax(state, hand):
    x=analyzeboard(state);
    if(x!=0):
        return (x*hand);
    pos=-1;
    value=-2;
    for i in range(0,9):
        if(state[i]==0):
            state[i] = hand;
            score =- minimax(state,(hand*-1));
            if(score>value):
                value=score;
                pos=i;
            state[i]=0;
    if(pos==-1):
        return 0;
    return value;

def analyzeboard(board):
    cb=[[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]];

    for i in range(0,8):
        if(board[cb[i][0]] != 0 and
           board[cb[i][0]] == board[cb[i][1]] and
           board[cb[i][0]] == board[cb[i][2]]):
            return board[cb[i][2]];
    return 0;