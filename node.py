from threading import Event, Thread, Timer
from datetime import datetime, timedelta
import time
import math

from nodeServer import NodeServer
from nodeSend import NodeSend
from message import Message
import config
from enums import MSG_TYPE, STATE

class Node():

    CS_INT = 1689
    NEXT_REQ = 3217

    def __init__(self,id):
        Thread.__init__(self)
        self.id = id

        self.port = config.port+id
        self.daemon = True
        self.lamport_ts = 0

        self.curr_state = STATE.INIT

        # Voter attributes
        self.has_voted = False
        self.voted_request = None
        self.request_queue = []

        # Proposer attributes
        self.num_votes_received = 0
        self.has_inquired = False

        # Event signals
        self.signal_request_cs = Event()
        self.signal_request_cs.set()
        self.signal_enter_cs = Event()
        self.signal_exit_cs = Event()

        # Timestamps for next expected request/exit
        self.time_request_cs = None
        self.time_exit_cs = None

        # Thread handling
        self.server = NodeServer(self)
        self.server.start()
        self.client = NodeSend(self)

        # Generating quorum:
        #   With 16 nodes,
        #   Collegues for node 5
        #       0 [ 1]  2   3
        #     [ 4][ 5][ 6][ 7]
        #       8 [ 9] 10  11
        #      12 [13] 14  15

        self.collegues = []
        side = math.ceil(math.sqrt(config.numNodes))

        # Get row index and column index
        row_i = id // side
        col_i = id % side

        # Append row (careful with last row when nodes cannot form a rectangular grid)
        for i in range(side*row_i, min(side*(row_i+1), config.numNodes)):
            self.collegues.append(i)

        # Append column
        for i in range(col_i, config.numNodes, side):
            if i != id:
                self.collegues.append(i)

        self.voting_set = {key: None for key in self.collegues}


    def do_connections(self):
        self.client.build_connection()

    def state(self):
        timer = Timer(1, self.state) #Each 1s the function call itself
        timer.start()

        self.curr_time = datetime.now()
        if   (self.curr_state == STATE.RELEASE and self.time_request_cs <= self.curr_time):
            if not self.signal_request_cs.is_set():
                self.signal_request_cs.set()

        elif (self.curr_state == STATE.REQUEST and self.num_votes_received == len(self.collegues)):
            if not self.signal_enter_cs.is_set():
                self.signal_enter_cs.set()

        elif (self.curr_state == STATE.HELD and self.time_exit_cs <= self.curr_time):
            if not self.signal_exit_cs.is_set():
                self.signal_exit_cs.set()

    def run(self):
        print("Run Node%i with the follows %s"%(self.id,self.collegues))
        self.client.start()
        self.wakeupcounter = 0
        self.state()



    ############################################################################
    # FUNCIONES AUXILIARES AGREGADAS
    ############################################################################

    def request_cs(self, ts):
        self.curr_state = STATE.REQUEST
        self.lamport_ts += 1
        message = Message(msg_type=MSG_TYPE.REQUEST,
                        src=self.id,
                        ts=self.lamport_ts,
                        data="Node_%i wants access to CS"%self.id)
        print(" ? | Node_%i requests CS"%self.id)
        self.client.multicast(message, self.collegues)
        self.signal_request_cs.clear()

    def enter_cs(self, ts):
        self.time_exit_cs = ts + timedelta(milliseconds=type(self).CS_INT)
        self.curr_state = STATE.HELD
        self.lamport_ts += 1
        self.signal_enter_cs.clear()
        print("-->| Node_%i enters CS"%self.id)

    def exit_cs(self, ts):
        self.time_request_cs = ts + timedelta(milliseconds=type(self).NEXT_REQ)
        self.curr_state = STATE.RELEASE
        self.lamport_ts += 1
        self.num_votes_received = 0
        message = Message(msg_type=MSG_TYPE.RELEASE,
                          src=self.id,
                          data="Node_%i releases CS"%self.id)
        print("<--| Node_%i exits CS"%self.id)
        self.client.multicast(message, self.collegues)
        self.signal_exit_cs.clear()


