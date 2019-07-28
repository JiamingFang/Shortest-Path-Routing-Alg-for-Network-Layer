from socket import *
import sys
import struct

class pkt_INIT:
    def __init__(self, id):
        self.id = id

    def toByte(self):
        return struct.pack("<I", self.id)

class link_cost:
    def __init__(self, link, cost):
        self.link = link
        self.cost = cost
        self.dest = -1

class circuit_DB:
    def __init__(self, link_num, links):
        self.link_num = link_num
        self.links = links

class pkt_HELLO:
    def __init__(self,routerId, linkId):
        self.routerId = routerId
        self.linkId = linkId
    def toByte(self):
        return struct.pack("<II", self.routerId, self.linkId)

class pkt_LSPDU:
    def __init__(self, sender, routerId, linkId, cost, via):
        self.sender = sender
        self.routerId = routerId
        self.linkId = linkId
        self.cost = cost
        self.via = via
    def toByte(self):
        return struct.pack("<IIIII", self.sender, self.routerId, self.linkId, self.cost, self.via)
class DB:
    def __init__(self, id, links):
        self.id = id
        self.database = {}
        self.database[id] = links 
    def print(self):
        for x in self.database:
            print(str(x) + ": ")
            for i in range(len(self.database[x])):
                print(self.database[x][i].link,self.database[x][i].cost, self.database[x][i].dest)
    def add(self, data):
        unpack = struct.unpack_from("<IIIII", data, 0)
        linkCost = link_cost(unpack[2], unpack[3])
        #find other router in database that is using the same link
        dest = -1
        for i in self.database:
            if i != unpack[1]:
                links = self.database[i]
                for j in links:
                    if j.link == unpack[2]:
                        j.dest = unpack[1]
                        dest = i
                        break
                if dest != -1:
                    break
        linkCost.dest = dest
        #add new lspdu into database
        if unpack[1] in self.database:
            links = self.database[unpack[1]]
            for i in range(len(links)):
                if links[i].link == linkCost.link and links[i].cost == linkCost.cost:
                    return False
            links.append(linkCost)
            self.database[unpack[1]] = links
            return True
        else:
            links = []
            links.append(linkCost)
            self.database[unpack[1]] = links
            return True
    def SPF(self, discovered):
        #init
        N = [self.id]
        cost = [99,99,99,99,99]
        path = [-1,-1,-1,-1,-1]
        cost[self.id-1] = 0
        path[self.id-1] = 0
        for i in discovered:
            for j in self.database[self.id]:
                if i[1] == j.link:
                    cost[i[0]-1] = j.cost
                    path[i[0]-1] = i[0]
                    break
                    
        while len(N) < 5:
            minimum = 99
            node = -1
            for i in range(1,6):
                if i not in N and cost[i-1] < minimum:
                    minimum = cost[i-1]
                    node = i
            N.append(node)
            #update D(v) dor all v adjacent to w and not in N':
            if node not in self.database:
                return cost,path
            for j in self.database[node]:
                if j.dest != -1 and (j.dest not in N):
                    if cost[node-1]+j.cost < cost[j.dest-1] and path[j.dest-1] == -1:
                        path[j.dest-1] = node
                        node2 = node
                        while path[node2-1] != node2:
                            path[j.dest-1] = path[node2-1]
                            node2 = path[node2-1]
                    cost[j.dest-1] = min(cost[j.dest-1], cost[node-1]+j.cost)
                    

        return cost,path
                




def unpack(data):
    num = struct.unpack_from("<I", data, 0)[0]
    index = 4
    links = []
    for i in range(num):
        link = struct.unpack_from("<II", data, index)
        links.append(link_cost(link[0],link[1]))
        index+=8
    return num,links
    

if len(sys.argv) == 5:
    routerIndex = int(sys.argv[1])
    host = sys.argv[2]
    nsePort = int(sys.argv[3])
    port = int(sys.argv[4])

    if routerIndex == 1:
        log = open("router1.log", "w")
    elif routerIndex == 2:
        log = open("router2.log", "w")
    elif routerIndex == 3:
        log = open("router3.log", "w")
    elif routerIndex == 4:
        log = open("router4.log", "w")
    elif routerIndex == 5:
        log = open("router5.log", "w")

    init = pkt_INIT(routerIndex)

    #Create socket
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(('',port))

    #send init and recieve DB
    serverSocket.sendto(init.toByte() ,(host,nsePort))
    log.write("R"+str(routerIndex)+ " sends an INIT: router_id "+ str(routerIndex)+'\n')
    data,clientAddress = serverSocket.recvfrom(2048)
    num, links = unpack(data)
    log.write("R"+str(routerIndex)+ " recieves a CIRCUIT_DB: nbr_link "+ str(num)+'\n')
    db = DB(routerIndex, links)
    # db.print()

    #send HELLO
    for i in range(len(db.database[db.id])):
        hello = pkt_HELLO(db.id, db.database[db.id][i].link)
        serverSocket.sendto(hello.toByte() ,(host,nsePort))
        log.write("R"+str(routerIndex)+ " sends a HELLO: router_id "+ str(hello.routerId)+" link_id "+str(hello.linkId)+'\n')

    #Recieve LSPDU
    discovered = []
    spf = None
    while(True):
        print("new loop:")
        data,clientAddress = serverSocket.recvfrom(2048)
        #If recieved is HELLO
        if len(data) == 8:
            recievedHello = struct.unpack_from("<II", data, 0)
            discovered.append(recievedHello)
            log.write("R"+str(routerIndex)+ " recieves a HELLO: router_id "+ str(recievedHello[0])+" link_id "+str(recievedHello[1])+'\n')
            for i in range(len(db.database[db.id])):
                lspdu = pkt_LSPDU(db.id,db.id,db.database[db.id][i].link,db.database[db.id][i].cost,recievedHello[1])
                serverSocket.sendto(lspdu.toByte() ,(host,nsePort))
                log.write("R"+str(routerIndex)+ " sends a LS PDU: sender "+ str(lspdu.sender)+", router_id "+str(lspdu.routerId)+\
                    ", link_id "+str(lspdu.linkId)+", cost "+str(lspdu.cost)+", via "+str(lspdu.via)+'\n')
        #If recieved is LSPDU
        elif len(data) == 20:
            unpack = struct.unpack_from("<IIIII", data, 0)
            log.write("R"+str(routerIndex)+ " recieves a LS PDU: sender "+ str(unpack[0])+", router_id "+str(unpack[1])+\
                ", link_id "+str(unpack[2])+", cost "+str(unpack[3])+", via "+str(unpack[4])+'\n')
            if(db.add(data)):
                log.write('\n'+"Tropology database:"+'\n')
                for i in db.database:
                    temp = db.database[i]
                    log.write("R"+str(routerIndex)+" -> "+"R"+str(i)+" nbr link "+str(len(temp))+'\n')
                    for j in temp:
                        log.write("R"+str(routerIndex)+" -> "+"R"+str(i)+" link "+str(j.link)+" cost "+str(j.cost)+'\n')
                log.write('\n')
                for i in range(len(discovered)):
                    if discovered[i][0] != unpack[0]:
                        lspdu = pkt_LSPDU(db.id,unpack[1],unpack[2],unpack[3], discovered[i][1])
                        serverSocket.sendto(lspdu.toByte() ,(host,nsePort))
                        log.write("R"+str(routerIndex)+ " sends a LS PDU: sender "+ str(lspdu.sender)+", router_id "+str(lspdu.routerId)+\
                            ", link_id "+str(lspdu.linkId)+", cost "+str(lspdu.cost)+", via "+str(lspdu.via)+'\n')
                spf,path = db.SPF(discovered)
                log.write('\n'+"RIB:"+'\n')
                if path[0] == -1:
                    log.write("R"+str(routerIndex)+" -> "+"R1"+" -> "+"INF"+", "+"INF"+'\n')
                elif path[0] == 0:
                    log.write("R"+str(routerIndex)+" -> "+"R1"+" -> "+"Local"+", "+str(spf[0])+'\n')
                else:
                    log.write("R"+str(routerIndex)+" -> "+"R1"+" -> "+"R"+str(path[0])+", "+str(spf[0])+'\n')

                if path[1] == -1:
                    log.write("R"+str(routerIndex)+" -> "+"R2"+" -> "+"INF"+", "+"INF"+'\n')
                elif path[1] == 0:
                    log.write("R"+str(routerIndex)+" -> "+"R2"+" -> "+"Local"+", "+str(spf[1])+'\n')
                else:
                    log.write("R"+str(routerIndex)+" -> "+"R2"+" -> "+"R"+str(path[1])+", "+str(spf[1])+'\n')

                if path[2] == -1:
                    log.write("R"+str(routerIndex)+" -> "+"R3"+" -> "+"INF"+", "+"INF"+'\n')
                elif path[2] == 0:
                    log.write("R"+str(routerIndex)+" -> "+"R3"+" -> "+"Local"+", "+str(spf[2])+'\n')
                else:
                    log.write("R"+str(routerIndex)+" -> "+"R3"+" -> "+"R"+str(path[2])+", "+str(spf[2])+'\n')

                if path[3] == -1:
                    log.write("R"+str(routerIndex)+" -> "+"R4"+" -> "+"INF"+", "+"INF"+'\n')
                elif path[3] == 0:
                    log.write("R"+str(routerIndex)+" -> "+"R4"+" -> "+"Local"+", "+str(spf[3])+'\n')
                else:
                    log.write("R"+str(routerIndex)+" -> "+"R4"+" -> "+"R"+str(path[3])+", "+str(spf[3])+'\n')

                if path[4] == -1:
                    log.write("R"+str(routerIndex)+" -> "+"R5"+" -> "+"INF"+", "+"INF"+'\n')
                elif path[4] == 0:
                    log.write("R"+str(routerIndex)+" -> "+"R5"+" -> "+"Local"+", "+str(spf[4])+'\n')
                else:
                    log.write("R"+str(routerIndex)+" -> "+"R5"+" -> "+"R"+str(path[4])+", "+str(spf[4])+'\n')
                log.write('\n')
        print(spf)
        db.print()







