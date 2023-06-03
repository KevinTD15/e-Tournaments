class sd: #server down
    def __init__(self) -> None:
        self.active = False
        self.server_down = []
        self.sender = None
        self.sender_id = None
        self.already_sent = False
    
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

class gr: #game replica
    def __init__(self) -> None:
        self.active = False
        self.update = []
        self.already_sent = False

class rep:
    def __init__(self) -> None:
        self.replica = None
    
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