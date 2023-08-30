# noinspection SpellCheckingInspection,GrazieInspection
"""
Author : Maurice Snoeren <macsnoeren(at)gmail.com>
Version: 0.3 beta (use at your own risk)
Date: 7-5-2020

Python package p2pnet for implementing decentralized peer-to-peer network applications
Modified by Gabriel Seegerer
"""

import json
import pickle
import socket
import threading
import time


class NodeConnection(threading.Thread):
    """
    The class NodeConnection is used by the class Node and represent the TCP/IP socket connection with another node.
    Both inbound (nodes that connect with the server) and outbound (nodes that are connected to) are represented by
    this class. The class contains the client socket and hold the id information of the connecting node.
    Communication is done by this class. When a connecting node sends a message, the message is relayed to the main
    node (that created this NodeConnection in the first place).
       
    Instantiates a new NodeConnection. Do not forget to start the thread. All TCP/IP communication is handled by this
    connection.
        main_node: The Node class that received a connection.
        sock: The socket that is associated with the client connection.
        id: The id of the connected node (at the other side of the TCP/IP connection).
        host: The host/ip of the main node.
        port: The port of the server of the main node.
    """

    def __init__(self, main_node, sock, connected_node_id, host, port):
        """
        Instantiates a new NodeConnection. Do not forget to start the thread. All TCP/IP communication is handled by
        this connection.
            main_node: The Node class that received a connection.
            sock: The socket that is associated with the client connection.
            id: The id of the connected node (at the other side of the TCP/IP connection).
            host: The host/ip of the main node.
            port: The port of the server of the main node.
        """

        self.host = host
        self.port = port
        self.main_node = main_node
        self.sock = sock
        self.terminate_flag = threading.Event()

        # The id of the connected node
        self.connected_node_id = str(connected_node_id)  # Make sure the ID is a string

        # End of transmission character for the network streaming messages.
        self.EOT_CHAR = 0x04.to_bytes(1, 'big')

        # Datastore to store additional information concerning the node.
        self.info = {}

        # Use socket timeout to determine problems with the connection
        self.sock.settimeout(10.0)

        self.main_node.debug_print_network(
            f"NodeConnection: Started with client ({self.connected_node_id}) '{self.host}:{str(self.port)}'")
        super(NodeConnection, self).__init__()

    def send_pickle(self, data):
        """
        Send the data to the connected node. Serialized with pickle
        """
        self.sock.sendall(pickle.dumps(data))

    def send(self, data, encoding_type='utf-8'):
        """
        Send the data to the connected node. The data can be pure text (str), dict object (send as json) and bytes
        object. When sending bytes object, it will be using standard socket communication. An end of transmission
        character 0x04 utf-8/ascii will be used to decode the packets ate the other node. When the socket is corrupted
        the node connection is closed.
        """
        if isinstance(data, str):
            try:
                self.sock.sendall(data.encode(encoding_type) + self.EOT_CHAR)

            except Exception as e:  # Fixed issue #19: When sending is corrupted, close the connection
                self.main_node.debug_print_network(f"Node connection send: Error sending data to node: {str(e)}")
                self.stop()  # Stopping node due to failure

        elif isinstance(data, dict):
            try:
                self.sock.sendall(json.dumps(data).encode(encoding_type) + self.EOT_CHAR)

            except TypeError as type_error:
                self.main_node.debug_print_network('This dict is invalid')
                self.main_node.debug_print_network(type_error)

            except Exception as e:  # Fixed issue #19: When sending is corrupted, close the connection
                self.main_node.debug_print_network(f"Node connection send: Error sending data to node: {str(e)}")
                self.stop()  # Stopping node due to failure

        elif isinstance(data, bytes):
            try:
                self.sock.sendall(data + self.EOT_CHAR)

            except Exception as e:  # Fixed issue #19: When sending is corrupted, close the connection
                self.main_node.debug_print_network(f"Node connection send: Error sending data to node: {str(e)}")
                self.stop()  # Stopping node due to failure

        else:
            self.main_node.debug_print_network(
                "datatype used is not valid please use str, dict (will be send as json) or bytes")

    def stop(self):
        """
        Terminates the connection and the thread is stopped. Stop the node client. Please make sure you join the thread.
        """
        self.main_node.debug_print_network(
            f"{self.main_node.node_id} stopping node connection to {self.connected_node_id}")
        self.terminate_flag.set()

    @staticmethod
    def parse_packet_pickle(packet):
        """
        Parse the packet and determines whether it has been sent in str, json or byte format. It returns the according
        data.
        """
        return pickle.loads(packet)

    @staticmethod
    def parse_packet(packet):
        """
        Parse the packet and determines whether it has been sent in str, json or byte format. It returns the according
        data.
        """
        try:
            packet_decoded = packet.decode('utf-8')

            try:
                return json.loads(packet_decoded)

            except json.decoder.JSONDecodeError:
                return packet_decoded

        except UnicodeDecodeError:
            return packet

    # Required to implement the Thread. This is the main loop of the node client.
    def run(self):
        """
        The main loop of the thread to handle the connection with the node. Within the main loop the thread waits to
        receive data from the node. If data is received the method node_message will be invoked of the main node to be
        processed.
        """
        buffer = b''  # Hold the stream that comes in!

        while not self.terminate_flag.is_set():
            chunk = b''

            try:
                chunk = self.sock.recv(4096)

            except socket.timeout:
                # self.main_node.debug_print("NodeConnection: timeout")
                pass

            except Exception as e:
                self.terminate_flag.set()  # Exception occurred terminating the connection
                self.main_node.debug_print_network('Unexpected error')
                self.main_node.debug_print_network(e)

            if chunk != b'':
                buffer += chunk
                eot_pos = buffer.find(self.EOT_CHAR)

                while eot_pos > 0:
                    packet = buffer[:eot_pos]
                    buffer = buffer[eot_pos + 1:]

                    self.main_node.message_count_recv += 1
                    self.main_node.node_message(self, self.parse_packet(packet))

                    eot_pos = buffer.find(self.EOT_CHAR)

            time.sleep(0.01)

        self.sock.settimeout(None)
        self.sock.close()
        self.main_node.node_disconnected(self)
        self.main_node.debug_print_network("NodeConnection: Stopped")

    def set_info(self, key, value):
        self.info[key] = value

    def get_info(self, key):
        return self.info[key]

    def __str__(self):
        return 'NodeConnection: {}:{} <-> {}:{} ({})'.format(self.main_node.host, self.main_node.port, self.host,
                                                             self.port, self.connected_node_id)

    def __repr__(self):
        return '<NodeConnection: Node {}:{} <-> Connection {}:{}>'.format(self.main_node.host, self.main_node.port,
                                                                          self.host, self.port)

    def __hash__(self):
        return hash(self.main_node.node_id + self.connected_node_id)

    def __eq__(self, other):
        return self.main_node == other.main_node and self.connected_node_id == other.node_id
