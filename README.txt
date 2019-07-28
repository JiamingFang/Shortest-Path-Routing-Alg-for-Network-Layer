This is a program that runs the shortest path routing algorithm

first run the Emulator:
./nse-linux386 <host of routers> <port>

Then run the five routers:
python3  router.py <id of router> <host of emulator> <port of emulator> <router port>

Run the five routers in order
The routers must be on the same host
The Emulator can be on a different host than the routers

After all operations done, press <ctrl+c> to end program and get log files



FLOW:
- When a router comes online, it sends an INIT packet (struct pkt_INIT) to the network (aka, Network
Environment aka, nse).

- The router receives a packet back from the nse that contain the circuit database (struct circuit_DB), which essentially lists all the links/edges attached to this router.

- This information about links from circuit_DB is put into router's internal database called Link State Database (aka LSDB, also called Topology Database or the Network Map). A Link State Database gives the overall picture of the network known to that specific router.
Initially this Database looks different for each router but converges to a same database as routers exchange information.

- Each router then sends a HELLO_PDU to tell its neighbour. This means that a HELLO packet (struct pkt_HELLO) is sent on all the links that the router discovered in the previous step.

- Each router receiving a HELLO packet from its neighbour, sends a set of LS_PDU packets (struct pkt_LSPDU) to that neighbour, representing its current Topology Database state

- LS_PDU stands for Link State Protocol Data Unit, and each LS_PDU corresponds to a (router_id, link_id) pair in the network. Each unique LS_PDU (unique (link_id, router_id) pair) forms an entry inside the router's Link State Database.

- Receiving a HELLO packet from a neighbour also indicates that this neighbouring router is now
'discovered', and hence will be included in all future communications.

- Whenever a router receives an LS_PDU from one of its neighbours, it does the following steps:

-- Add this (unique) LS_PDU information to the router's Link State Database.
-- Inform each of the rest of neighbours by forwarding/rebroadcasting this LS_PDU to them. Note that a router sending LS_PDUs should set the 'sender' and 'via' fields of the LS_PDU packet to appropriate values.
(To avoid loops, only send this message once per neighbouring router, and do not forward duplicates packets in the future)
-- The router runs a Shortest Path First (SPF) algorithm on the Link State Database. This calculates the path (links to be used) from this router to each of the routers in the network. The result of this algorithm is converted to a 'next-hop database/table' called the Routing Information Base (RIB).
-- The Link State Database and the Routing Information Base (RIB) are printed to a log file.

- This process continues until each router has a complete list of the links and their costs in their Link State
Database. At this point, no packets remain transient in the network.
