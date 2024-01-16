
#### TODO

* Thoroughly testing ACK's (for now it seems to work reasonably.)
* Thoroughly testing splitting bigger messages (for now it seems to work reasonably.)


#### Done
* Implementing ACK's using STOP-AND-WAIT protocol for all messages except routing and broadcasts.
* Base code implemented for splitting messages and assembling them.
* Some basic testing
* Make a simple test function to test (all) scenarios in reliable transport with ACK's and big messages.
* Implementing full code for splitting messages + refine.

Below simulation of node 3 sending to node 4 where big message got split up in multiple smaller messages using reliable transport.

<code>
[+] Adding session
{6553: {'type': 1, 'data': b'1-TEST-', 'destination_address': 4, 'ttl': 20, 'source_address': 3, 'ses_num': 6553, 'frame_num': 3}}
Sending ACK to node 3 from node 4
[+] Done sending ACK node 4->3
[+] Appending data to session
{6553: {'type': 1, 'data': b'1-TEST-2-TEST-', 'destination_address': 4, 'ttl': 20, 'source_address': 3, 'ses_num': 6553, 'frame_num': 3}}
Sending ACK to node 3 from node 4
[+] Done sending ACK node 4->3
Sending ACK to node 3 from node 4
[+] Done sending ACK node 4->3
[+] Complete packet is:
{'type': 1, 'data': b'1-TEST-2-TEST-3-TEST', 'destination_address': 4, 'ttl': 20, 'source_address': 3, 'ses_num': 6553, 'frame_num': 3}
Sending ACK to node 3 from node 4
[+] Done sending ACK node 4->3
received a message of type 1 from node 3 for node 4

</code>
