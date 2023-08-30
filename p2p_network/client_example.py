import time
from p2p_network.participant_node import ParticipantNode

PORT = 20000


def test_parity():
    print_protocols = True
    debug_protocols = False
    debug_network = False
    port = PORT
    node_id = input("ID: ")
    # port = input("Port: ")

    node = ParticipantNode("localhost", int(node_id) + port, node_id,
                           print_protocols=print_protocols, debug_protocols=debug_protocols)

    node.start()
    time.sleep(0.5)

    node.debug = debug_network

    connect = input("Connect to: ")
    if connect != "":
        connect = connect.split(sep=",")
        for p in connect:
            node.connect_with_node("localhost", int(p) + port)

    time.sleep(0.5)
    node.parity_input = int(input("Parity input: "))

    input("Press Enter to start.")

    node.execute_parity()

    node.stop()
    print('end test')


def test_veto():
    print_protocols = True
    debug_protocols = False
    debug_network = False
    port = PORT

    node_id = input("ID: ")
    # port = input("Port: ")

    node = ParticipantNode("localhost", int(node_id) + port, node_id,
                           print_protocols=print_protocols, debug_protocols=debug_protocols)

    node.start()
    time.sleep(0.5)

    node.debug = debug_network

    connect = input("Connect to: ")
    if connect != "":
        connect = connect.split(sep=",")
        for p in connect:
            # node.connect_with_node("localhost", int(port))
            node.connect_with_node("localhost", int(p) + port)

    time.sleep(0.5)
    node.veto_input = int(input("Veto input: "))

    input("Press Enter to start.")

    node.execute_veto(veto_security=3)

    node.stop()
    print('end test')


def test_collision_detection():
    print_protocols = True
    debug_protocols = False
    debug_network = False
    port = PORT

    node_id = input("ID: ")
    # port = input("Port: ")

    node = ParticipantNode("localhost", int(node_id) + port, node_id,
                           print_protocols=print_protocols, debug_protocols=debug_protocols)

    node.start()
    time.sleep(0.5)

    node.debug = debug_network

    connect = input("Connect to: ")
    if connect != "":
        connect = connect.split(sep=",")
        for p in connect:
            # node.connect_with_node("localhost", int(port))
            node.connect_with_node("localhost", int(p) + port)

    time.sleep(0.5)
    node.collision_detection_input = int(input("Collision Detection input: "))

    input("Press Enter to start.")

    node.execute_collision_detection(collision_detection_security=3)

    node.stop()
    print('end test')


def test_notification():
    print_protocols = True
    debug_protocols = False
    debug_network = False
    port = PORT

    node_id = input("ID: ")
    # port = input("Port: ")

    node = ParticipantNode("localhost", int(node_id) + port, node_id,
                           print_protocols=print_protocols, debug_protocols=debug_protocols)

    node.start()
    time.sleep(0.5)

    node.debug = debug_network

    """
    connect = input("Connect to: ")
    if connect != "":
        connect = connect.split(sep=",")
        for port in connect:
            # node.connect_with_node("localhost", int(port))
            node.connect_with_node("localhost", int(port) + 8000)
    """
    for p in range(1, int(node_id)):
        node.connect_with_node("localhost", int(p) + port)

    time.sleep(0.5)
    node.notification_input = input("Notification input: ")

    input("Press Enter to start.")

    node.execute_notification(notification_security=4)

    node.stop()
    print('end test')


def test_fixed_role_message_transmission():
    print_protocols = True
    debug_protocols = False
    debug_network = False
    port = PORT

    node_id = input("ID: ")
    # port = input("Port: ")

    node = ParticipantNode("localhost", int(node_id) + port, node_id,
                           print_protocols=print_protocols, debug_protocols=debug_protocols)

    node.start()
    time.sleep(0.5)

    node.debug = debug_network

    for p in range(1, int(node_id)):
        node.connect_with_node("localhost", int(p) + port)

    time.sleep(0.5)
    node.message_input = input("Message input: ")
    node.is_message_sender = True if input("Is message sender? (y/n)") == "y" else False
    node.is_message_receiver = True if input("Is message receiver? (y/n)") == "y" else False

    input("Press Enter to start.")

    node.execute_fixed_role_message_transmission(5, 16)

    node.stop()
    print('end test')


def test_message_transmission():
    print_protocols = True
    debug_protocols = False
    debug_network = False
    port = PORT

    node_id = input("ID: ")
    # port = input("Port: ")

    node = ParticipantNode("localhost", int(node_id) + port, node_id,
                           print_protocols=print_protocols, debug_protocols=debug_protocols)

    node.start()
    time.sleep(0.5)

    node.debug = debug_network

    for p in range(1, int(node_id)):
        node.connect_with_node("localhost", int(p) + port)

    time.sleep(0.5)
    node.message_input = input("Message input: ")
    node.notification_input = input("Receiver ID: ")

    input("Press Enter to start.")

    node.execute_message_transmission(5)

    node.stop()
    print('end test')


if __name__ == "__main__":
    # test_parity()
    # test_veto()
    # test_collision_detection()
    # test_notification()
    # test_fixed_role_message_transmission()
    test_message_transmission()
