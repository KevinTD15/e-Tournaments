from abc import ABC

class protocol(ABC):
    def __init__(self):
        self.sms = None
        self.active = False
        self.count = 0

class CR(protocol): #close ring
    def __init__(self):
        self.sms = None
        self.active = False
        self.count = 0

class EM(protocol): #election message
    def __init__(self):
        self.sms = None
        self.active = False
        self.count = 0

class BS(protocol): #boss
    def __init__(self):
        self.sms = None
        self.active = False
        self.count = 0

class CR2(protocol): #boss
    def __init__(self):
        self.sms = None
        self.active = False
        self.count = 0