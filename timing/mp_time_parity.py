import pickle
import time
import timeit
from multiprocessing import Process, Queue
import numpy as np
from p2p_network.participant_node import ParticipantNode

TIMEIT_REPETITION = 1
PORT = 20000


def create_new_client_instance(node_id, number_of_participants, print_protocol, debug_protocol, debug_network,
                               queue, set_input=0):
    new_participant = ParticipantNode("localhost", PORT + node_id, node_id, print_protocols=print_protocol,
                                      debug_protocols=debug_protocol)
    new_participant.start()
    time.sleep(0.5)
    new_participant.debug = debug_network
    new_participant.parity_input = set_input
    for i in range(1, node_id):
        new_participant.connect_with_node("localhost", PORT + int(i))
    while number_of_participants != len(new_participant.all_nodes) + 1:
        time.sleep(0.1)
        # print(f"{node_id}: Accepted connections: {len(new_participant.all_nodes)}")
    time.sleep(2)
    print(f"{node_id} starting parity")

    timeit_result = []
    for _ in range(TIMEIT_REPETITION):
        result = timeit.timeit(lambda: new_participant.execute_parity(), number=1)
        timeit_result.append(result)
        time.sleep(1)

    print(f"{node_id} finished parity - result: {new_participant.parity_result}")
    queue.put(min(timeit_result), block=False)
    new_participant.stop()
    time.sleep(1)


def get_scale(number_of_participants, number_of_datapoints, log_scale):
    if log_scale:
        return np.unique(
            np.geomspace(start=1, stop=number_of_participants, num=number_of_datapoints, dtype=int))[1:]
    else:
        return np.linspace(start=2, stop=number_of_participants, num=number_of_datapoints, dtype=int)


def main():
    print_protocol = False
    debug_protocol = False
    debug_network = False

    participants = int(input("Number of participants: "))
    datapoints = int(input("Number of datapoints: "))

    scale = get_scale(number_of_participants=participants, number_of_datapoints=datapoints, log_scale=False)
    print(scale)
    # scale = [50, 50, 50, 50, 50]

    results_min = []
    results_mean = []
    process_list = []
    q = Queue()

    for participant_number in scale:
        for participant_id in range(1, participant_number + 1):
            if participant_id == 1:
                p = Process(target=create_new_client_instance,
                            args=(participant_id, participant_number, print_protocol, debug_protocol,
                                  debug_network, q, 1,))
            else:
                p = Process(target=create_new_client_instance,
                            args=(participant_id, participant_number, print_protocol, debug_protocol,
                                  debug_network, q,))
            process_list.append(p)
            p.start()
            time.sleep(0.05)
        for p in process_list:
            p.join()
        time.sleep(0.5)

        process_results = []
        while not q.empty():
            process_results.append(q.get())

        results_min.append(min(process_results))
        results_mean.append(sum(process_results) / len(process_results))

        time.sleep(2)

    pickle_dict = {"protocol": "Parity", "scale": scale, "results_min": results_min, "results_mean": results_mean,
                   "datapoints": datapoints, "participants": participants}
    with open("timing_logs/parity_pickle.pickle", "wb") as f:
        pickle.dump(pickle_dict, f)

    print("Finished")


if __name__ == "__main__":
    main()
