class sd: #server down
    def __init__(self) -> None:
        self.active = False
        self.server_down = []
        self.sender = None
        self.sender_id = None
        self.already_sent = False
        self.resumed_games = []
        self.rep_leader = []
    
    def default(self):
        self.__init__()
        

class sg: #start game
    def __init__(self) -> None:
        self.active = False
        self.games = None
        self.ip = None
        self.continue_game = False
        

class dg: # distribute games
    def __init__(self) -> None:
        self.active = False
        self.games = None
        self.already_sent = False
        self.client_ip = None

class gr: #game replica
    def __init__(self) -> None:
        self.active = False
        self.update = []
        self.already_sent = False

# class frep: #full replica
#     def __init__(self) -> None:
#         self.play = None
#         self.winner = None
#         self.tournamens = None
#        self.play_count = None
        

class rep: #replica
    def __init__(self) -> None:
        self.play = None
        self.winner = None
        self.tournamens = None
        self.send_leader_rep = []
        self.play_count = None
        self.already_sent = False

class stl: #send to leader
    def __init__(self) -> None:
        self.play = None
        self.repl = None
        self.already_sent = False
        self.send = None
        self.pause = False
        
        
# class clt: #send message game to client
#     def __init__(self) -> None:
#         self.ip = None
#         self.active_ms = False
#         self.msg = None

# class su: #send update
#     def __init__(self) -> None:
#         self.active = False
#         self.update = None
#         self.sender_ip = None
#         self.sender_id = None
#         self.already_sent = False