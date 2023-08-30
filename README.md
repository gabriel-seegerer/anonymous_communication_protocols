# anonymous_communication_protocols
## Python implementation of various anonymous communication protocols in a decentralized p2p network
### About
This projects goal was to implement various anonymous communication protocols found in [Information-Theoretic Security Without An Honest Majority - Broadbent, Tapp 2007](https://arxiv.org/abs/0706.2010) and time them for different group sizes up to 300 participants.

The algebraic manipulation detection code that was used is found in [Experimental implementation of secure anonymous protocols on an eight-user quantum network - Huang, Joshi 2022](https://www.nature.com/articles/s41534-022-00535-1).

A modified version of [Maurice Snoeren - python-p2p-network](https://github.com/macsnoeren/python-p2p-network) is used to create participants in a p2p network who then can execute various protocols with each other.

### Design
Everything revolvs around ParticipantNode. A ParticipantNode is a Participant in the p2p network. After it gets created it can connect to other nodes. Since everything is decentralized the participant has to make sure he is connected to every other participant in the network.

ParticipantNode executes the protocols.

ParticipantNode inherits from Node. Node is the connection manager of the participant.

Node starts a new NodeConnection which is a server socket connection whenever a new participant wants to connect


### Example
In p2p_network/ you find client_example.py which can be used to try out the protocols.

For example message transmission:
- Set print_protocols in Line 183 to True
- Make sure to have only line 220 test_message_transmission active
- Run 2 or more instances of client_example.py
- Client IDs are numbers starting at 1.
- Start with Client 1 and give following Inputs:
  - ID: 1
  - Message Input: Hello 2!
  - Receiver ID: 2
- Continue with client 2, 3, etc.:
  - ID: 2
  - Message Input:
  - Receiver ID:
- Press Enter to start

client_example.py can easily be modified so the participants don't connect to localhost:portXY but to specified IPs and Ports.

### Change Message Length
At the moment the participants have to agree to a fixed message length for message transmission. By default its 64 bits, which means after AMDC encoding with security parameter beta = 5 the length is 99 bits. To change the length there is a script d_gama_calculator.py in p2p_network/ which can be used to calculate the message length.

After calculating the variables message_length and ecoded_message_length in lines 66/67 in participant_node.py have to be changed to the new values.

Make sure to use the corresponding security factor when running execute_message_transmission(security).

### Timing
Timing creates multiple processes using the multiprocessing module to achieve true parallelity. Each process runs one participant_node.

Resulting data is stored as "protocol_name_pickle.pickle" and can be read and visualized with show_graph.py.

Reason behind this is, that the protocols got timed on a vm so the resulting data could easily be copied from one machine to another.


### TODOs
Since this was created during a temporary internship there are a few things which are missing and will be added once I work on it again.

There are no unit test available.
