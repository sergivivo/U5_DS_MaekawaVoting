import select
from threading import Thread
import json
import traceback

import utils
from message import Message
from enums import *
import heapq

class NodeServer(Thread):
    def __init__(self, node):
        Thread.__init__(self)
        self.node = node

    def run(self):
        self.update()

    def update(self):
        self.connection_list = []
        self.server_socket = utils.create_server_socket(self.node.port)
        self.connection_list.append(self.server_socket)

        while self.node.daemon:
            (read_sockets, write_sockets, error_sockets) = select.select(
                self.connection_list, [], [], 5)
            if not (read_sockets or write_sockets or error_sockets):
                print('NS%i - Timed out'%self.node.id) #force to assert the while condition
            else:
                for read_socket in read_sockets:
                    if read_socket == self.server_socket:
                        (conn, addr) = read_socket.accept()
                        self.connection_list.append(conn)
                    else:
                        try:
                            msg_stream = read_socket.recvfrom(4096)
                            for msg in msg_stream:
                                try:
                                    ms = json.loads(str(msg,"utf-8"))
                                    self.process_message(ms)
                                except:
                                    pass
                        except:
                            read_socket.close()
                            self.connection_list.remove(read_socket)
                            continue

        self.server_socket.close()

    def process_message(self, msg):
        print("Node_%i receive msg: %s"%(self.node.id,msg))

        self.node.lamport_ts = max(self.node.lamport_ts + 1, msg["ts"])

        try:
            if msg["msg_type"] == MSG_TYPE.REQUEST:
                self.on_request(msg)
            elif msg["msg_type"] == MSG_TYPE.RELEASE:
                self.on_release(msg)
            elif msg["msg_type"] == MSG_TYPE.GRANT:
                self.on_grant(msg)
            elif msg["msg_type"] == MSG_TYPE.FAIL:
                self.on_fail(msg)
            elif msg["msg_type"] == MSG_TYPE.INQUIRE:
                self.on_inquire(msg)
            elif msg["msg_type"] == MSG_TYPE.YIELD:
                self.on_yield(msg)
        except Exception as e:
            print(traceback.format_exc())




    ############################################################################
    # FUNCIONES AUXILIARES AGREGADAS
    ############################################################################

    def on_request(self, msg):
        if self.node.curr_state == STATE.HELD:
            heapq.heappush(self.node.request_queue, msg)
        else:
            if self.node.has_voted:
                self.node.request_queue.append(msg)
                response_msg = Message(src=self.node.id)
                if (msg['ts'] < self.node.voted_request['ts'] and not self.node.has_inquired):
                    response_msg.set_type(MSG_TYPE.INQUIRE)
                    response_msg.set_dest(self.node.voted_request.src)
                    self.node.has_inquired = True
                    print("    * Node_%i sends INQUIRE to Node_%i *"%(self.node.id, msg['src']))
                else:
                    response_msg.set_type(MSG_TYPE.FAIL)
                    response_msg.set_dest(msg['src'])
                    print("    * Node_%i sends FAIL for Node_%i *"%(self.node.id, msg['src']))
                self.node.client.send_message(response_msg, response_msg.dest)
            else:
                self.grant_request(msg)

    def on_release(self, msg=None):
        self.node.has_inquired = False
        if self.node.request_queue:
            next_request = min(self.node.request_queue, key=lambda x: x['ts'])
            self.grant_request(next_request)
        else:
            self.node.has_voted = False
            self.node.voted_request = None

    def grant_request(self, request_msg):
        grant_msg = Message(msg_type = MSG_TYPE.GRANT,
                            src = self.node.id,
                            dest = request_msg['src'])
        print("    * Node_%i sends GRANT to Node_%i *"%(self.node.id, request_msg['src']))
        self.node.client.send_message(grant_msg, grant_msg.dest, False)
        self.node.has_voted = True
        self.node.voted_request = request_msg

    def on_grant(self, grant_msg):
        self.node.voting_set[grant_msg['src']] = grant_msg
        self.node.num_votes_received += 1
        print(self.node.id, "increases votes by 1, currently, the value is", self.node.num_votes_received)

    def on_fail(self, fail_msg):
        self.node.voting_set[fail_msg['src']] = fail_msg

    def on_inquire(self, inquire_msg):
        if self.node.state != STATE.HELD:
            self.node.voting_set[inquire_msg['src']] = None
            self.node.num_votes_received -= 1
            yield_msg = Message(msg_type = "YIELD",
                                src = self.node.id,
                                dest = inquire_msg['src'])
            self.node.client.send_message(yield_msg, yield_msg.dest)

    def on_yield(self, msg=None):
        self.node.request_queue.append(self.node.voted_request)
        self.check_release()


