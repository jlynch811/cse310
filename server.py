# CSE 310 Group Project
# Jonathan Lynch 109030898

from socket import *
import select
import sys
import _thread
import pickle

#Structures
class Package:
	def __init__(self, protocol, objlist):
		self.protocol = protocol
		self.list = objlist

class Group:
	def __init__(self, gid, name):
		self.gid = gid
		self.name = name

class Post: 
	def __init__(self, pid, subject, body, userid):
		self.pid = pid
		self.subject = subject
		self.body = body
		self.userid = userid
		self.time = self.getTimeStamp()

	def getTimeStamp():
		return 0.1

#Program
serverPort = 5898
serverSocket = socket(AF_INET,SOCK_STREAM)
debug=1

#Lists
def loadGroups(filePath):
	gp = []
	for i in range(0,10):
		gp.append(Group(11111, "Somesubject"+str(i)))

	return gp
groupList = loadGroups("no current filepath")
socketList = []
outputSocketList = []

#Helper Functions

def acceptFunc(threadName, val):
	print("Accept Func!")

def sendEncoded(socket, message):
	print("Sending Message: ", message)
	socket.send(str.encode(message))

#This is for receiving an array over socket, required for post[subject, body]
def isPickle(s):
	cmdList = s.split()
	print(cmdList[0])
	if(cmdList[0] == b"PICKLE"):
		return 1
	else: return 0

def pickleSend(currsocket, prefix, obj):
	#Pickle is used to send the array over the socket.
	p = Package(prefix, obj)
	pickledObj = pickle.dumps(p)
	currsocket.send(pickledObj)


def handleUserCommand(command, currsocket):
	cmdList = command.split(None, 1)

	if(cmdList[0] == "ALLGROUPS"):
		handleAG(cmdList[1], currsocket)
	elif(cmdList[0] == "LOGIN"):
		currsocket.send(command.encode())

	elif(cmdList[0] == "SUBGROUPS"):
		print("TEST")
		currsocket.send("HELLO".encode())

def handleAG(info, currsocket):
	infoList = info.split()
	indices = groupList[int(infoList[0]):int(infoList[1])]
	pickleSend(currsocket, "ALLGROUPS", indices)

	print("pickle sent AG to client")




#Main Program
serverSocket.setblocking(0)
serverSocket.bind(('',serverPort))
serverSocket.listen(5)

socketList = socketList + [serverSocket]

#_thread.start_new_thread( acceptFunc, ("AcceptThread",2,))
#connectionSocket, addr = serverSocket.accept()
#socketList = socketList + [connectionSocket]

while socketList:
	readSockets, writeSockets, exceptSockets = select.select(socketList, outputSocketList, socketList)

	for s in readSockets:

		#New Connection if serverSocket
		if s is serverSocket:
			connection, client_address = s.accept()
			print("NEW CONNECTION: ", client_address)
			connection.setblocking(0)
			socketList = socketList + [connection]

		#Not server socket. Handle what client sent
		else:
			message = s.recv(1024) 
			print("Received from client: ", message)

			#CHECK FOR EOF
			if(not message):
				print("RECEIVED EOF")
				sendEncoded(s, "LOGOUT")	
				s.close()
				socketList.remove(s)

			elif(isPickle(message)):
				message = message[7:]
				print("PICKLE MESSAGE:\n", pickle.loads(message))
			else:
				#s.send(message)
				handleUserCommand(message.decode(), s)

	
			