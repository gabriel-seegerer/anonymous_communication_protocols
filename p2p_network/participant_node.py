# noinspection SpellCheckingInspection,GrazieInspection
"""
Implementation of multiple anonymous communication protocols based on the following paper:
"Information-Theoretic Security Without an Honest Majority" - Broadbent, Tapp

Implementation is based on a modified version of Maurice Snoerens p2pnet package
https://github.com/macsnoeren/python-p2p-network

The idea is, a network of ParticipantNodes gets created and they can execute various protocols
"""

import itertools
import time
import numpy as np
from p2p_network.node import Node
from secrets import randbits
from p2p_network.amdc_for_p2p import amdc_encode_message, amdc_decode_message


# TODO "Network Manager" - distributes all nodes in network to new participant, ensures no node_ids are used double

class ParticipantNode(Node):
    """
    Implements a participant in a p2p-network. Can do various anonymous communication protocols after connecting to
    other participants
    """
    def __init__(self, host: str, port: int, node_id: str = None, max_connections: int = 1000,
                 print_protocols: bool = False, debug_protocols: bool = False):
        """
        Constructor for ParticipantNode
        :param host: IP address of ParticipantNode in format "XXX.XXX.XXX.XXX" or "localhost"
        :param port: port of ParticipantNode
        :param node_id: if node_id is None, a random id will get created
        :param max_connections: maximum amount of connections the participant can accept
        :param print_protocols: when True methods will print out the various steps of the protocol
        :param debug_protocols: when True some methods will calculate predefined numbers to make it easier to
        understand how the protocol works
        """
        super(ParticipantNode, self).__init__(host, port, node_id, max_connections)
        print(f"{self.node_id}: Started")

        self.debug_protocols = debug_protocols
        self.print_protocols = print_protocols
        self.all_node_ids = []

        self.parity_input = 0
        self.parity_shared_keys = []
        self.parity_broadcasts_last = False
        self.parity_received_broadcast_values = []
        self.parity_result = 0
        self.parity_finished = []

        self.veto_input = 0
        self.veto_result = 0
        self.veto_finished = []

        self.collision_detection_input = 0
        self.collision_detection_result = 0
        self.collision_detection_finished = []

        self.notification_input = ""  # Node ID the participant wants to notify
        self.notification_is_spectator = False
        self.notification_result = 0
        self.notification_finished = []

        self.message_length = 64
        self.encoded_message_length = 99
        self.message_input = []
        self.message_amdc_encoded_input = []
        self.is_message_sender = False
        self.is_message_receiver = False
        self.message_amdc_encoded_received_message = []
        self.message_amdc_decoded_received_message = []
        self.message_received_str = ""
        self.one_time_pad = []
        self.fixed_message_finished = []
        self.message_finished = []

    # Message transmission
    def execute_message_transmission(self, security: int) -> None:
        """
        Executes anonymous message transmission protocol

        If node wants to act as sender:
            * Notification_input needs to be set to receiving node_id.
            * Message_input needs to be a non-empty string.
        :param security: protocol succeeds with probability of at least 1-2**-security
        """
        self.debug_print_protocols("----------Executing message transmission----------")
        self.create_order_in_all_node_ids()
        if self.notification_input != "":
            self.is_message_sender = True
        self.execute_collision_detection(security)
        match self.collision_detection_result:
            case 0:
                self.debug_print_protocols("   Collision Detection: 0 - Nobody wants to send - Abort")
                return
            case 1:
                self.debug_print_protocols("   Collision Detection 1 - Proceeding with notification protocol")
            case 2:
                self.debug_print_protocols("   Collision Detection 2 - Collision detected - Abort")
                self.collision_detection_result = 0
                return
        self.execute_notification(security)
        if self.notification_result == 1:
            self.is_message_receiver = True

        self.execute_fixed_role_message_transmission(security, self.encoded_message_length)

        # TODO if we clear all here, then mp_time_message_transmission can't print output
        # self.clear_all()

        self.send_message_finished()

        self.debug_print_protocols(f"----------Finished message transmission----------")

    def send_message_finished(self) -> None:
        """
        Participant waits until every other participant is also finished with message transmission protocol
        """
        self.send_to_nodes({"message_finished": True})
        self.wait_while_receiving(self.message_finished, len(self.all_nodes))
        self.message_finished = []

    # Fixed role message transmission
    def execute_fixed_role_message_transmission(self, security: int, bit_count: int) -> None:
        """
        Executes fixed role message transmission

        Prerequisites:
            * create_order_in_all_nodes() as to be executed once
            * roles have to be set - is_message_sender and is_message_receiver
        :param security: protocol succeeds with probability of at least 1-2**-security
        :param bit_count: the amount of bits the protocol should transmit
        """
        self.debug_print_protocols("   ----------Executing fixed role message transmission----------")
        self.debug_print_protocols(f"      Roles set: is sender: {self.is_message_sender} - "
                                   f"is receiver: {self.is_message_receiver}")

        if self.is_message_receiver:
            self.create_one_time_pad(bit_count)

        if self.is_message_sender:
            self.message_amdc_encoded_input = amdc_encode_message(self.message_input, security, self.print_protocols)
            if len(self.message_amdc_encoded_input) != self.encoded_message_length:
                raise ValueError(
                    f"Length should be {self.encoded_message_length}, is {len(self.message_amdc_encoded_input)}")

        for round_of_protocol in range(bit_count):
            self.set_parity_input_by_message_role(round_of_protocol)
            self.debug_print_protocols(f"      Executing parity protocol for bit {round_of_protocol + 1}/{bit_count}")
            self.execute_parity()
            self.add_to_received_message(round_of_protocol)

        self.debug_print_protocols(
            f"      Received amdc encoded message is: {self.message_amdc_encoded_received_message}")

        if self.is_message_receiver:
            message_correct, self.message_amdc_decoded_received_message = amdc_decode_message(
                self.message_amdc_encoded_received_message, self.message_length, security, self.print_protocols)
            self.debug_print_protocols(f"      Received message is correct: {message_correct}")
            if not message_correct:
                self.veto_input = 1
            else:
                self.veto_input = 0
        else:
            self.veto_input = 0
            self.message_amdc_decoded_received_message = self.message_amdc_encoded_received_message

        self.execute_veto(security)

        self.received_message_to_string()
        self.debug_print_protocols(f"      Received message is [bits]: {self.message_amdc_decoded_received_message}")
        self.debug_print_protocols(f"      Received message is [string]: {self.message_received_str}")
        self.debug_print_protocols(f"      Veto Result at the end of message transmission is {self.veto_result}")

        self.send_fixed_message_finished()
        self.debug_print_protocols(f"   ----------Finished fixed role message transmission----------\n")

    def set_parity_input_by_message_role(self, round_of_protocol) -> None:
        """
        | Sets parity input by message role
        | if node is message sender: parity input is a bit from amdc encoded message
        | if node is message receiver: parity input is a bit from one time pad

        :param round_of_protocol: which round of fixed message transmission it is - index of used message / one time pad
        """
        if self.is_message_sender:
            self.parity_input = self.message_amdc_encoded_input[round_of_protocol]
        elif self.is_message_receiver:
            self.parity_input = self.one_time_pad[round_of_protocol]

    def create_one_time_pad(self, bit_count) -> None:
        """
        creates a one time pad
        :param bit_count: length of the one time pad
        """
        if self.is_message_receiver:
            self.one_time_pad = [randbits(1) for _ in range(bit_count)]

    def add_to_received_message(self, round_of_protocol) -> None:
        """
        | decodes message bit by xor'ing with used one time pad key
        | just for transparency every other participant also adds their received bit to received_message
        :param round_of_protocol: index of used one time pad bit
        """
        if self.is_message_receiver:
            self.message_amdc_encoded_received_message.append(self.parity_result ^ self.one_time_pad[round_of_protocol])
        else:
            self.message_amdc_encoded_received_message.append(self.parity_result)

    def send_fixed_message_finished(self):
        """
        Participant waits until every other participant is also finished with message transmission protocol
        """
        self.send_to_nodes({"fixed_message_finished": True})
        self.wait_while_receiving(self.fixed_message_finished, len(self.all_nodes))
        self.fixed_message_finished = []

    def received_message_to_string(self) -> None:
        """
        converts amdc decoded received message from a list of bits (8-bit ascii encoded) to a string of characters
        """
        list_to_str = "".join(str(i) for i in self.message_amdc_decoded_received_message)
        self.message_received_str = (
            "".join([chr(int(i, 2)) for i in [list_to_str[i:i + 8] for i in range(0, len(list_to_str), 8)]]))

    # Notification
    def execute_notification(self, notification_security: int) -> None:
        """
        Executes notification protocol

        Prerequisites:
            * is_message_sender set to True for one node
        :param notification_security:
        """
        self.debug_print_protocols(f"   ----------Executing notification----------")

        self.execute_notification_parity(notification_security)

        self.send_notification_finished()
        self.debug_print_protocols(f"   ----------Notification finished - "
                                   f"Notification result is {self.notification_result}----------\n")

    def execute_notification_parity(self, notification_security: int) -> None:
        """
        Executes notification parity

        :param notification_security: protocol succeeds with probability of at least 1-2**-security
        """
        for p, parity_round in itertools.product(self.all_node_ids, range(1, notification_security + 1)):
            self.debug_print_protocols(f"      ----------Starting notification parity round {parity_round} - "
                                       f"Spectator is Participant {p}")
            self.set_notification_parity_by_notification_input(p)

            self.distribute_key_bits()
            self.debug_print_protocols(f"         All keys exchanged: {self.parity_shared_keys}")

            parity_key_xor_result = self.calculate_parity_xor_key_result()
            self.debug_print_protocols(f"         Calculated parity key xor result: {parity_key_xor_result}")

            if p == self.node_id:
                self.wait_while_receiving(self.parity_received_broadcast_values, len(self.all_nodes))
                self.parity_received_broadcast_values.append(parity_key_xor_result)
                self.debug_print_protocols(f"         Spectator received all broadcasts "
                                           f"{self.parity_received_broadcast_values}")
                self.calculate_parity_result()
                self.set_notification_result_by_parity_result()
            else:
                self.send_to_node_by_id(p, {"parity_key_xor_result": parity_key_xor_result})
                self.debug_print_protocols(f"         Non-spectator did nothing")

            self.parity_shared_keys = []
            self.parity_received_broadcast_values = []
            self.parity_input = 0
            self.send_parity_finished()
            self.parity_finished = []

    def set_notification_parity_by_notification_input(self, p: str) -> None:
        """
        If participant wants to notify the spectator of the round, he sets his parity input bit to 1 with a 50% chance
        :param p: node_id of the participant, who doesn't broadcast his result and acts as a spectator
        """
        if p == self.notification_input:
            self.parity_input = randbits(1)
            self.debug_print_protocols(
                f"      Participant sets parity_input by chance, because he wants to notify the spectator")
        else:
            self.parity_input = 0
        self.debug_print_protocols(
            f"      Notification Input = {self.notification_input} -> Parity Input = {self.parity_input}")

    def set_notification_result_by_parity_result(self) -> None:
        """
        if parity_result is 0, notification result stays the same;
        if parity_result is 1, notification result gets set to 1
        """
        self.notification_result = self.notification_result | self.parity_result
        self.debug_print_protocols(f"         Spectator calculated parity result {self.parity_result}")
        self.debug_print_protocols(f"         Spectator notification result is {self.notification_result}")

    def send_notification_finished(self) -> None:
        """
        Participant waits until every other participant is also finished with notification protocol
        """
        self.send_to_nodes({"notification_finished": True})
        self.wait_while_receiving(self.notification_finished, len(self.all_nodes))
        self.notification_finished = []

    # Collision Detection
    def execute_collision_detection(self, collision_detection_security: int) -> None:
        """
        Executes collision detection protocol

        :param collision_detection_security: protocol succeeds with probability of at least 1-2**-security
        """
        self.debug_print_protocols(f"   ----------Executing collision detection----------")
        if self.is_message_sender:
            self.debug_print_protocols("   Set collision detection input to 1, participant is sender")
            self.collision_detection_input = 1
        else:
            self.debug_print_protocols("   Set collision detection input to 0, participant is NOT a sender")
            self.collision_detection_input = 0

        self.veto_input = self.collision_detection_input
        self.debug_print_protocols(f"   Starting Collision Detection Round A")
        self.execute_veto(veto_security=collision_detection_security)
        self.debug_print_protocols(f"   Collision Detection Round A finished - Veto result is {self.veto_result}\n")

        if self.veto_result == 0:
            self.collision_detection_result = 0
            self.debug_print_protocols(f"   Collision Detection finished - Cause: Veto Result Round A was 0")
            self.debug_print_protocols(
                f"   ----------Collision Detection finished with result: {self.collision_detection_result}----------")
            return

        if self.veto_input == 1 and self.parity_input == 0:  # if veto result is 1 but participant didn't input 1
            self.debug_print_protocols(f"   Participant detected a collision in Round A - Set veto input to 1")
            self.veto_input = 1
        else:
            self.debug_print_protocols(f"   Participant didn't detect a collision in Round A - Set veto input to 0")
            self.veto_input = 0

        self.debug_print_protocols(f"   Starting Collision Detection Round B")
        self.execute_veto(veto_security=collision_detection_security)

        if self.veto_result == 0:
            self.collision_detection_result = 1
        else:
            self.collision_detection_result = 2

        self.send_collision_detection_finished()
        self.debug_print_protocols(f"      Collision Detection Round B finished - Veto result is {self.veto_result}")
        self.debug_print_protocols(
            f"   ----------Collision Detection finished with result {self.collision_detection_result}----------\n")

    def send_collision_detection_finished(self) -> None:
        """
        Participant waits until every other participant is also finished with collision detection protocol
        """
        self.send_to_nodes({"collision_detection_finished": True})
        self.wait_while_receiving(self.collision_detection_finished, len(self.all_nodes))
        self.collision_detection_finished = []

    # Veto
    def execute_veto(self, veto_security: int) -> None:
        """
        Executes veto protocol

        :param veto_security: protocol succeeds with probability of at least 1-2**-security
        """
        self.debug_print_protocols(f"      ----------Executing Veto----------")
        for last_broadcaster in self.all_node_ids:
            if last_broadcaster == self.node_id:
                self.parity_broadcasts_last = True
            self.debug_print_protocols(f"      Broadcasts last is {self.parity_broadcasts_last}")
            for i in range(1, veto_security + 1):
                self.debug_print_protocols(
                    f"      Veto Round {self.all_node_ids.index(last_broadcaster) + 1}-{i} started")
                self.set_parity_input_by_veto_input()
                self.execute_parity()
                self.veto_result = self.parity_result
                if self.veto_result == 1:
                    self.parity_broadcasts_last = False
                    self.send_veto_finished()
                    self.debug_print_protocols(f"      ----------Veto abort - Parity Result was 1----------")
                    return
            self.parity_broadcasts_last = False
        self.send_veto_finished()
        self.debug_print_protocols(f"      ----------Veto finished - Veto result = {self.veto_result}----------")

    def set_parity_input_by_veto_input(self) -> None:
        """
        if veto_input is 1, there is a 50/50 chance parity_input gets set to 1
        """
        if self.veto_input == 0:
            self.parity_input = 0
        else:
            self.parity_input = randbits(1)
        self.debug_print_protocols(f"      Veto Input = {self.veto_input} -> Parity Input = {self.parity_input}")

    def send_veto_finished(self) -> None:
        """
        Participant waits until every other participant is also finished with veto protocol
        """
        self.send_to_nodes({"veto_finished": True})
        self.wait_while_receiving(self.veto_finished, len(self.all_nodes))
        self.veto_finished = []

    # Parity
    def execute_parity(self) -> None:
        """
        Executes parity protocol
        """
        self.debug_print_protocols("         ----------Starting Parity----------")
        self.debug_print_protocols(f"         Parity Input is {self.parity_input}")

        self.distribute_key_bits()
        self.debug_print_protocols(f"         All keys exchanged: {self.parity_shared_keys}")

        self.calculate_and_broadcast_keys()
        self.debug_print_protocols(f"         Broadcasting finished: {self.parity_received_broadcast_values}")

        self.calculate_parity_result()
        self.debug_print_protocols(f"         Calculated parity result: {self.parity_result}")

        self.parity_shared_keys = []
        self.parity_received_broadcast_values = []

        self.send_parity_finished()
        self.debug_print_protocols(f"         ----------Finished parity----------")

    def create_bitstring(self) -> list[int]:
        """
        Creates bitstring with length all_nodes + 1, which should be the number of all participants in the network
        """
        number_of_participants = len(self.all_nodes) + 1
        bitstring = [randbits(1) for _ in range(number_of_participants)]
        while bitstring.count(1) % 2 != self.parity_input:
            bitstring = [randbits(1) for _ in range(number_of_participants)]
        return bitstring

    def distribute_key_bits(self) -> None:
        """
        Creates bitstring, adds first bit to own shared_keys list, distributes the rest to other nodes
        """
        bitstring = self.create_bitstring()
        self.debug_print_protocols(f"         Created bitstring {bitstring}")
        self.parity_shared_keys.append(bitstring.pop(0))
        for n in self.all_nodes:
            self.send_to_node(n, {"parity_shared_key": bitstring.pop(0)})
        self.wait_while_receiving(self.parity_shared_keys, len(self.all_nodes) + 1)

    def calculate_and_broadcast_keys(self) -> None:
        """
        | Calculates parity of all shared keys and broadcasts it to other nodes
        | If broadcasts_last is set to True participants waits till everyone broadcast till he broadcasts his bit
        """
        parity_key_xor_result = self.calculate_parity_xor_key_result()
        self.debug_print_protocols(f"         Calculated parity key xor result: {parity_key_xor_result}")

        if self.parity_broadcasts_last:
            self.wait_while_receiving(self.parity_received_broadcast_values, len(self.all_nodes))
            self.send_to_nodes({"parity_key_xor_result": parity_key_xor_result})
            self.debug_print_protocols(f"         Sent his xor result last")
        else:
            self.send_to_nodes({"parity_key_xor_result": parity_key_xor_result})
            self.wait_while_receiving(self.parity_received_broadcast_values, len(self.all_nodes))
        self.parity_received_broadcast_values.append(parity_key_xor_result)

    def calculate_parity_xor_key_result(self) -> int:
        """
        Participant calculates the bit he wants to broadcast by xor'ing all received shared keys and his own parity bit
        :return: xor value of parity_shared_keys
        """
        return int(np.bitwise_xor.reduce(self.parity_shared_keys))

    def calculate_parity_result(self) -> None:
        """
        Participant calculates parity result by xor'ing all received broadcast values and his own calculated xor_result
        """
        self.parity_result = np.bitwise_xor.reduce(self.parity_received_broadcast_values)

    def send_parity_finished(self) -> None:
        """
        Participant waits until every other participant is also finished with parity protocol
        """
        self.send_to_nodes({"parity_finished": True})
        self.wait_while_receiving(self.parity_finished, len(self.all_nodes))
        self.parity_finished = []

    # Getter / Setter
    # TODO remove all getter setter if program is finished and only message transmission should be available
    @property
    def parity_input(self):
        return self._parity_input

    @parity_input.setter
    def parity_input(self, bit):
        if bit != 1 and bit != 0:
            raise ValueError(f"Bit should be 1 or 0, is {bit}")
        self._parity_input = bit

    @property
    def veto_input(self):
        return self._veto_input

    @veto_input.setter
    def veto_input(self, bit):
        if bit != 1 and bit != 0:
            raise ValueError(f"Bit should be 1 or 0, is {bit}")
        self._veto_input = bit

    @property
    def collision_detection_input(self):
        return self._collision_detection_input

    @collision_detection_input.setter
    def collision_detection_input(self, bit):
        if bit != 1 and bit != 0:
            raise ValueError(f"Bit should be 1 or 0, is {bit}")
        self._collision_detection_input = bit

    @property
    def notification_input(self):
        return self._notification_input

    @notification_input.setter
    def notification_input(self, receiver_id):
        if receiver_id == self.node_id:
            raise NameError(f"Cant notify yourself")
        self._notification_input = receiver_id

    @property
    def message_input(self):
        return self._message_input

    @message_input.setter
    def message_input(self, message):
        if not message:
            self._message_input = []
        elif len(message) > self.message_length / 8:
            raise IndexError(f"Maximum message length: {self.message_length / 8} characters")
        else:
            padded_message = message.ljust(int(self.message_length / 8))
            self._message_input = list(map(int, "".join(format(ord(i), '08b') for i in padded_message)))
            self.debug_print_protocols(f"Converting input to 8 bit ascii: {self._message_input}")

    # Utility methods
    def create_order_in_all_node_ids(self) -> None:
        """
        | Participant broadcasts his node_id and receives every other participants node_id.
        | All participants sort node_ids of all network participant the same way, so the order in all_node_ids is the
            same for all participants.
        """
        self.debug_print_protocols("Creating order in all_node_ids")
        self.send_to_nodes({"node_id": self.node_id})
        self.wait_while_receiving(self.all_node_ids, len(self.all_nodes))
        if self.node_id in self.all_node_ids:
            raise NameError("Two Nodes have the same node_id")
        self.all_node_ids.append(self.node_id)
        self.all_node_ids.sort()
        self.debug_print_protocols(f"Order is {self.all_node_ids}")

    @staticmethod
    def wait_while_receiving(element_list: list, amount_of_elements: int) -> None:
        """
        Waits until *element_list* has *amount_of_elements* in it
        :param element_list:
        :param amount_of_elements:
        """
        while len(element_list) != amount_of_elements:
            # TODO time.sleep could be variable..
            #  If there are more participants it could be higher to minimize processor load
            #  If there are less participants it could be lower to minimize latency
            time.sleep(0.01)
            pass

    def sort_incoming_messages(self, message: dict) -> None:
        """
        Sorts messages the node received and appends them to the corresponding lists

        :param message: message received from other nodes
        :raise LookupError:
        """
        (protocol, value), = message.items()
        match protocol:
            case "node_id":
                self.all_node_ids.append(value)
            case "parity_shared_key":
                self.parity_shared_keys.append(value)
            case "parity_key_xor_result":
                self.parity_received_broadcast_values.append(value)
            case "parity_finished":
                self.parity_finished.append(value)
            case "veto_finished":
                self.veto_finished.append(value)
            case "collision_detection_finished":
                self.collision_detection_finished.append(value)
            case "notification_finished":
                self.notification_finished.append(value)
            case "fixed_message_finished":
                self.fixed_message_finished.append(value)
            case "message_finished":
                self.message_finished.append(value)
            case _:
                raise LookupError(f"Can't match message protocol - {message}")

    def clear_all(self) -> None:
        """
        Resets all the class variables to their original state
        """
        self.all_node_ids = []

        self.parity_input = 0
        self.parity_shared_keys = []
        self.parity_broadcasts_last = False
        self.parity_received_broadcast_values = []
        self.parity_result = 0
        self.parity_finished = []

        self.veto_input = 0
        self.veto_result = 0
        self.veto_finished = []

        self.collision_detection_input = 0
        self.collision_detection_result = 0
        self.collision_detection_finished = []

        self.notification_input = ""
        self.notification_is_spectator = False
        self.notification_result = 0
        self.notification_finished = []

        self.message_input = []
        self.is_message_sender = False
        self.is_message_receiver = False
        self.message_amdc_encoded_input = []
        self.message_amdc_encoded_received_message = []
        self.message_amdc_decoded_received_message = []
        self.one_time_pad = []
        self.fixed_message_finished = []

    def debug_print_protocols(self, message: str) -> None:
        """
        Prints message if print_protocols is set to true
        :param message: message that should get printed if print_protocols is true
        """
        if self.print_protocols is True:
            print(f"{self.node_id}: {message}")

    # override network methods
    def outbound_node_connected(self, node):
        # print(f"{self.node_id} connected to {node.connected_node_id}")
        pass

    def inbound_node_connected(self, node):
        # print(f"{self.node_id} connected to {node.connected_node_id}")
        pass

    def inbound_node_disconnected(self, node):
        # print(f"{self.node_id} disconnected from {node.connected_node_id}")
        pass

    def outbound_node_disconnected(self, node):
        # print(f"{self.node_id} disconnected from {node.connected_node_id}")
        pass

    def node_message(self, node, data):
        self.debug_print_network(f"{self.node_id} received message from {node.connected_node_id}: {data}")
        self.sort_incoming_messages(data)

    def node_disconnect_with_outbound_node(self, node):
        # print(f"{self.node_id} wants to disconnect with {node.connected_node_id}")
        pass
