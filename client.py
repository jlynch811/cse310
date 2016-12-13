#Jonathan Lynch
#109030898
#Client Implementation

from socket import *
import sys
import pickle
import _thread
import os
import datetime
#from Database import *

serverName = 'localhost'
serverPort = 5898
debug=0
connectionStatus = 0
currentCmd = ""
nValue = 5
startRange = 0
endRange = 4

postStart = 0
postEnd = 4
clientSocket = socket(AF_INET, SOCK_STREAM)
name = ""
uid = 0
subPath = r'Subs/'
postCountPath = r'SubPosts/'
readPostsPath = r'ReadPosts/'
currentDisplay = []
currentGroup = ""
currentPost = None
postList = []
idFlag = 0
threadExit = 0
defaultN = 5

#Structures

class Package:
	def __init__(self, protocol, objlist, name):
		self.protocol = protocol
		self.objlist = objlist
		self.name = name
class Group:
	def __init__(self, gid, name):
		self.gid = gid
		self.name = name

class Post: 

	def getTimeStamp(self):
		return format(datetime.datetime.now())

	def __init__(self, pid, subject, body, userid, gname):
		self.pid = pid
		self.subject = subject
		self.body = body
		self.userid = userid
		self.time = self.getTimeStamp()
		self.gname = gname

def byIsRead_key(post):
	return isPostRead(post.subject)

def byTime_key(post):
	return post.time

def nextN():
	global startRange
	global endRange
	global nValue

	startRange = startRange + nValue
	endRange = endRange + nValue

def sendNextN(protocol):
	nextN()
	message = protocol + " " + str(startRange) + " " + str(endRange)
	sendEncoded(clientSocket, message)

def postNextN():
	global postStart
	global postEnd
	global nValue

	postStart = postStart + nValue
	postEnd = postEnd + nValue

def resetPostN():
	global postStart
	global postEnd
	global nValue

	postStart = 0
	postEnd = nValue-1

def subNextN():
	nextN()
	handleSubscribedGroups("")

def resetNValue(n):
	global startRange
	global endRange
	global nValue

	nValue = n
	startRange = 0
	endRange = nValue-1

def handleInput(i):
	global currentCmd
	global nValue
	global defaultN

	cmdList = i.split()
	if cmdList == []:
		return


	try:
		#Check if we're in a command "mode." These return immediately after executing
		#if(connectionStatus ==1):
			#runTests()

		#SUB AG COMMANDS
		if(currentCmd == "ALLGROUPS"):
			handleAllGroupsSubCommand(cmdList)
			return

		elif(currentCmd == "SUBGROUPS"):
			handleSubscribedGroupsSubCommand(cmdList)
			return

		elif(currentCmd == "READGROUP"):
			handleReadGroupSubCommand(cmdList)
			return


		#Login Command
		elif(cmdList[0] == "login" and len(cmdList)==2):
			if(debug): print("Calling Login", cmdList[1])

			handleLogin(cmdList[1])
			return

		elif(cmdList[0] == "help"):
			handleHelp()
			return

		#Disallow other commands if not logged in.
		elif(connectionStatus==0):
			print("Unrecognized Command")
			return

		#Logout Command
		elif(cmdList[0] == "logout"):
			if(debug): print("Calling Logout")
			handleLogout()
			return

		#Exit Command
		elif(cmdList[0] == "exit"):
			print("Exiting...")
			sys.exit()

		#ag Command
		elif(cmdList[0] == "ag" and (len(cmdList)==1 or len(cmdList)==2)):
			#Set the optional nValue
			if(len(cmdList)==2):
				resetNValue(int(cmdList[1]))
				if(debug): print("nValue set: ", nValue)
			else: resetNValue(defaultN)

			handleAllGroups(cmdList)
			return

		#sg Command
		elif(cmdList[0] == "sg" and (len(cmdList)==1 or len(cmdList)==2)):
			#Set the optional nValue
			if(len(cmdList)==2):
				resetNValue(int(cmdList[1]))
				if(debug): print("nValue set: ", nValue)
			else: resetNValue(defaultN)
			print("NVALUE: ", nValue)
			handleSubscribedGroups(cmdList)
			return

		#rg Command
		elif(cmdList[0] == "rg" and (len(cmdList)==2 or len(cmdList)==3)):
			#Set the optional nValue
			if(amSubscribed(cmdList[1])):
				if(len(cmdList)==3):
					resetNValue(int(cmdList[2]))
					if(debug): print("nValue set: ", nValue)
				else: resetNValue(defaultN)
				handleReadGroup(cmdList)
				return
			print("Not subscribed to group.")
			return

		else:
			print("Unrecognized Command, Incorrect Format, Or Command Is Not Available At This Time")
	except:
		print("Formatting returned exception.")

#Multithreading to support stdin and server input
def recvFunc(threadName, val):
	global threadExit

	while True:

		t = clientSocket.recv(10000)
		p  = pickle.loads(t)
		protocol = p.protocol
		list = p.objlist
		gname = p.name
		#print(list)
		handleServerInput(protocol, list, gname)
		if(threadExit==1):
			threadExit=0
			return

def handleServerInput(protocol, list, gname):
	global currentDisplay
	global postList
	global threadExit
	global connectionStatus

	if(debug): print("PROTOCOL: ", protocol)


	if(protocol=="ALLGROUPS"):
		currentDisplay = list
		displayAllGroups()

	if(protocol=="READGROUP"):
		postList = list

		sortPosts()
		displayPosts()

	if(protocol=="NEWPOST"):
		setPostCount(gname.gname, list)
		checkAlert(gname.gname, list)
		#print("POSTCOUNT: ", list)
		#print("GROUP: ", gname)

	if(protocol=="POSTCOUNT"):
		setPostCount(gname, list)
		#print(gname, list)

	if(protocol=="LOGOUT"):
		logout = clientSocket.recv(1024)

		clientSocket.close()
		connectionStatus = 0
		threadExit = 1


def checkAlert(gname, pCount):
	if(amSubscribed==0):
		return
	alert = "\nALERT: NEW POST IN SUBSCRIBED GROUP - " + gname +"\n"
	print(alert)

def displayAllGroups():
	global currentCmd
	count = 0

	if(currentDisplay==[]):
		currentCmd = ""
		print("Quitting All Groups Sub Menu")
		return

	for group in currentDisplay:
		print(str(count+1)+ ". \t("+amSubscribedPrint(group.name)+")\t "+ group.name)
		count+=1
def displaySubGroups():
	global currentDisplay
	global currentCmd

	if(currentDisplay == []):
		currentCmd = ""
		print("Quitting Subscribed Groups Sub Menu")
		return

	count = 0
	for groupname in currentDisplay:
		pCount = getPostCount(groupname)
		c = int(pCount)
		newS =  str(count+1)+ ".\t" + str(c)+"\t"+ groupname.rstrip()
		print(newS)
		count+=1

def displayPosts():
	global postList
	global nValue
	global startRange
	global endRange
	global currentCmd
	global currentGroup
	global idFlag

	c= startRange
	count = 0

	if(startRange>=len(postList)):
		if(idFlag==1):
			markPostReadByName(currentPost)
			idFlag = 0
			resetPostN()
			displayPosts()
			return

		currentCmd = ""
		currentGroup = ""
		postList = []
		print("Quitting Read Group Sub Menu")
		return

	for post in postList:
		if(count>=startRange and count<=endRange):
			print(str(count+1) + ".\t " + displayPostRead(post.subject) + "\t " + str(post.time) + "\t " + post.subject)
		count = count+1
		c = c+1

def sortPosts():
	global postList

	try:
		postList = sorted(postList, key=byTime_key, reverse=True)
		postList = sorted(postList, key=byIsRead_key)
	except:
		return
	#print("TEST")


def stripEndTags(s):
	if(s.endswith('\r')):
		s = s[:2]
	if(s.endswith('\n')):
		s = s[:2]
	if(s.endswith('\r')):
		s = s[:2]

	return s

def stripN(s):
	if(s.endswith('\n')):
		s = s[:2]
	return s

def handleLogin(username):
    global connectionStatus
    global name
    global clientSocket

    #Only attempt to connect if we're not already connected.
    if(connectionStatus==0):
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((serverName,serverPort))

        loginRequest = "LOGIN " + str(username) 
       # print("Waiting to send...")
        sendEncoded(clientSocket, loginRequest)
        #print("Sent...")
        modifiedSentence = clientSocket.recv(1024)
        #print ('From Server:', modifiedSentence)

        name = username
        initSubFile()
        connectionStatus = 1
        print("Logged in as", name+".")
        _thread.start_new_thread(recvFunc, ("recvThread",2,))

        # Check to see if this is a returning user. If not, add a new user to the users.json file

    else:
        print("Already logged in")

def handleHelp():
	print("\n\t\t---COMMAND DIRECTORY---\n")
	print("login <username>\t\tLogs in as <username>")
	print("help\t\t\t\tDisplays this menu")
	print("\n\t\t-COMMANDS REQUIRING LOGIN-\n")
	print("ag [<N>]\t\t\tLists all existing groups, N at a time")
	print("\tSUB COMMANDS")
	print("\ts <1 2 3 ... N>\t\tSubscribes to selected groups")
	print("\tu <1 2 3 ... N>\t\tUnsubscribes from selected groups")
	print("\tn\t\t\tLists next N discussion groups")
	print("\tq\t\t\tExits ag command")
	print("")
	print("sg [<N>]\t\t\tLists all subscribed groups, N at a time")
	print("\tSUB COMMANDS")
	print("\tu <1 2 3 ... N>\t\tUnsubscribes from selected groups")
	print("\tn\t\t\tLists next N subscribed discussion groups")
	print("\tq\t\t\tExits sg command")
	print("")
	print("rg <gname> [<N>]\t\tDisplays status of N posts in group <gname>")
	print("\tSUB COMMANDS")
	print("\t<id>\t\t\tDisplays contents of post <id>")
	print("\t\tSUB COMMANDS")
	print("\t\tn\t\tDisplays next N lines of the post")
	print("\t\tq\t\tQuit displaying post content")
	print("")
	print("\tr <X> | <X-Y>\t\tMarks <X> post, or <X> to <Y> posts as read")
	print("\tn\t\t\tDisplays next N posts")
	print("\tp\t\t\tPosts to the group")
	print("\tq\t\t\tExits rg command")
	print("")
	print("logout\t\t\t\tLogs out user and terminates client")
	print("")


#Set the current Command to ALLGROUPS
def handleAllGroups(cmdList):
	global currentCmd
	global nValue

	currentCmd = "ALLGROUPS"
	message = currentCmd + " " + str(startRange) + " " + str(endRange)
	sendEncoded(clientSocket, message)

#Handle ALLGROUPS sub Commands
def handleAllGroupsSubCommand(cmdList):
	global currentCmd
	global nValue

	if(debug): print("All Groups Sub Command")

	message = ""

	#Ensure less than n sized arguments
	if(cmdList[0] == "s" and len(cmdList)<= nValue+1):
		message = "SUB"
		sCommand(cmdList)
		displayAllGroups()
		return

	elif(cmdList[0] == "u" and len(cmdList)<= nValue+1):
		message = "UNSUB"
		uCommand(cmdList)
		displayAllGroups()
		return

	elif(cmdList[0] == "n"):
		sendNextN("ALLGROUPS")
		return

	elif(cmdList[0] == "q"):
		currentCmd = ""
		print("Quitting All Groups Sub Menu")
		return

	else:
		print("Unrecognized Command, Incorrect Format, Or Command Is Not Available At This Time")


#Set the current Command to SUBGROUPS
def handleSubscribedGroups(cmdList):
    global currentCmd
    global nValue
    global currentDisplay

    currentCmd = "SUBGROUPS"
    #print("RANGE: ", startRange, endRange)
    subList = getSubGroups(startRange, endRange)
    currentDisplay = subList
    #print(subList)
   	#print(currentDisplay)
    displaySubGroups()



    # Get the subscribed groups for the current user and print them up to N
    #discussionGroups = getDiscussionGroups(name)
	#for i in range(0, cmdList):
        #print i + ".\t" + discussionGroups[i]['name']

def getSubGroups(start, end):
	fileName = subPath + name+"sub.txt"
	f = open(fileName,"r+")
	d = f.readlines()
	f.seek(0)

	ret = []
	count = 0
	for i in d:
	    if(count>=start and count <=end):
	    	ret = ret + [i]
	    count+=1

	f.close()

	return ret


#Handle SUBGROUPS sub Commands
def handleSubscribedGroupsSubCommand(cmdList):
	global currentCmd
	global nValue
	global currentDisplay

	if(debug): print("Sub Groups Sub Command")

	message = ""

	#Ensure less than n sized arguments
	if(cmdList[0] == "u" and len(cmdList)<= nValue+1):
		message = "UNSUB"
		uCommandSub(cmdList)

		subList = getSubGroups(startRange, endRange)
		currentDisplay = subList
		displaySubGroups()
		return

	elif(cmdList[0] == "n"):
		subNextN()
		return

	elif(cmdList[0] == "q"):
		currentCmd = ""
		print("Quitting Subscribed Groups Sub Menu")
		return

	print("Unrecognized Command, Incorrect Format, Or Command Is Not Available At This Time")

def uCommand(cmdList):
	for val in cmdList[1:]:
		#print("VAL: ", val)
		try:
			val = int(val)
			val = val - 1
		except:
			print("Incorrect Format")
			return
		try:
			unsubscribeToGroup(currentDisplay[val].name)
		except: print("Unable to unsubscribe from group (Likely out of range index)")

def uCommandSub(cmdList):
	for val in cmdList[1:]:
		#print("VAL: ", val)
		try:
			val = int(val)
			val = val - 1
		except:
			print("Incorrect Format")
			return
		#print("CUR DISPLAY: ", currentDisplay[val])
		unsubscribeToGroup(currentDisplay[val])

def sCommand(cmdList):
	for val in cmdList[1:]:
			try:
				val = int(val)
				val = val - 1
			except:
				print("Incorrect Format")
				return
			try:
				subscribeToGroup(currentDisplay[val].name)
			except: print("Unable to subscribe to group (Likely out of range index)")


#Set the current Command to READGROUP
def handleReadGroup(cmdList):
	global currentCmd
	global nValue
	global currentGroup

	currentCmd = "READGROUP"
	currentGroup = cmdList[1]
	resetNValue(nValue)
	resetPostN()
	message = currentCmd + " " + cmdList[1]
	sendEncoded(clientSocket, message)

#Handle READGROUP sub Commands
def handleReadGroupSubCommand(cmdList):
	global currentCmd
	global nValue
	global currentGroup
	global idFlag

	if(debug): print("Read Groups Sub Command")

	message = ""

	#Mark Read Command
	if(cmdList[0] == "r" and (len(cmdList) == 2)):
		rangeList = cmdList[1].split("-")

		if(debug): print("RANGELIST: ", rangeList)

		#Single Value. Just send
		if(len(rangeList)==1):
			message = "MARKREAD " + str(rangeList[0])
			markPostRead(int(rangeList[0])-1)
			sortPosts()
			resetNValue(nValue)
			displayPosts()
			return

		#Check format of rangelist and [0] < [1]
		elif(len(rangeList)==2 and int(rangeList[0]) < int(rangeList[1])):
			message = "MARKRANGEREAD " + str(rangeList[0]) + " " + str(rangeList[1])
			markPostRangeRead(int(rangeList[0])-1, int(rangeList[1]))
			sortPosts()
			resetNValue(nValue)
			displayPosts()
			return

		else:
			print("Format Error On r Command")
			return

	#List Next N Posts Command
	if(cmdList[0] == "n" and len(cmdList) == 1):

		if(idFlag==1):
			displayPostFile()
			postNextN()
			return
		nextN()
		displayPosts()
		return

	#Post to Group Command
	if(cmdList[0] == "p" and len(cmdList) == 1):
		postBody = ""
		

		subjectStr = input("Enter Post Subject.\n")
		currentStr = input("Enter Post Body followed by a . on its own line.\n")

		while(currentStr != "."):
			postBody = postBody + currentStr+"\n"
			currentStr = input("")

		#print("SUBJECT: \n", subjectStr)
		#print("POST BODY: \n", postBody)

		postList = [subjectStr, postBody]
		sendPost(subjectStr, postBody)
		return

	#Quit RG Command
	if(cmdList[0] == "q"):

		if(idFlag==1):
			markPostReadByName(currentPost)
			idFlag = 0
			resetPostN()
			displayPosts()
			return

		currentCmd = ""
		currentGroup = ""
		postList = []
		print("Quitting Read Group Sub Menu")
		return

	#[id] command
	else:
		try:
			if(int(cmdList[0])):
				message = "ID " + cmdList[0]

				executeId(int(cmdList[0])-1)
				idFlag = 1

			return
		except:
			print("Unrecognized Command, Incorrect Format, Or Command Is Not Available At This Time")
			return

def executeId(idd):
	global currentPost
	global postList

	currentPost = postList[idd]

	writePostToFile()
	print("\n")
	print("Group: " + currentPost.gname)
	print("Subject: " + currentPost.subject)
	print("Author: " + currentPost.userid)
	print("Date: " + str(currentPost.time))
	print("\n")


	#print("CONTENT:",currentPost.body)

def writePostToFile():
	global currentPost

	fileName = "cur.txt"
	f = open(fileName,"a+")
	f.seek(0)
	f.truncate()
	f.seek(0)
	f.write(currentPost.body)
	f.truncate()
	f.close()



def sendPost(subject, content):
	global currentGroup
	global name

	p = Post(None, subject, content, name, currentGroup)
	package = Package("MAKEPOST", p, currentGroup)
	pickledPost = pickle.dumps(package)
	clientSocket.send(pickledPost)


def handleLogout():
	global connectionStatus

	message = "LOGOUT " + str()
	sendEncoded(clientSocket, "LOGOUT " + str(name))
	if(debug): print("SENT COMMAND: ", message)

	clientSocket.shutdown(SHUT_WR)
	print("Logged Out.")
	#Wait for confirmation to close
	#logout = clientSocket.recv(1024)

	#clientSocket.close()
	#connectionStatus = 0


def sendEncoded(socket, message):
	if(debug): print("Sending Message: ", message)
	socket.send(str.encode(message))


def subscribeToGroup(gname):
	initSubFile()
	if(amSubscribed(gname)):
		print("Already Subscribed to ", gname)
		return

	fileName = subPath + name+"sub.txt"
	subFile = open(fileName, 'a+')

	subFile.write(gname+"\n")
	subFile.close()
	initPostCount(gname)
	requestPostCount(gname)

def unsubscribeToGroup(gname):
	fileName = subPath + name+"sub.txt"
	f = open(fileName,"r+")
	d = f.readlines()
	f.seek(0)
	for i in d:
		#print("i: ", i.encode())
		#print("gname: ", gname.encode())
		if (i != gname +"\n" and i!=gname):
			f.write(i)
	f.truncate()
	f.close()

	removePostCount(gname)

def amSubscribed(gname):
	#if(debug): print("Am Subscribed Check: ", gname.encode())

	initSubFile()

	fileName = subPath + name + "sub.txt"
	with open(fileName, 'r+b') as subFile:

		for line in subFile:
			if(line==gname.encode() +b'\r\n'):
				return 1
			elif(line==gname.encode()):
				return 1
	return 0

def amSubscribedPrint(gname):
	if(amSubscribed(gname)):
		return "s"
	return " "

def initSubFile():
	fileName = subPath + name + "sub.txt"
	subFile = open(fileName, 'a+')
	subFile.close()

	fileName = postCountPath + name + "count.txt"
	countFile = open(fileName, 'a+')
	countFile.close()

	fileName = readPostsPath + name + "posts.txt"
	postsFile = open(fileName, 'a+')
	postsFile.close()

def initDirs():
	directory = "Subs"
	if not os.path.exists(directory):
		os.makedirs(directory)

	directory = "SubPosts"
	if not os.path.exists(directory):
		os.makedirs(directory)

	directory = "ReadPosts"
	if not os.path.exists(directory):
		os.makedirs(directory)


def initPostCount(gname):
	if(debug): print("InitPostCount")
	fileName = postCountPath + name + "count.txt"

	countFile = open(fileName, 'a+')

	countFile.write(gname+"\n")
	countFile.write("0\n")
	countFile.close()

def getPostCount(gname):
	fileName = postCountPath + name + "count.txt"
	f = open(fileName,"r+b")
	d = f.readlines()
	f.seek(0)

	#print(gname)
	gname = gname.encode().rstrip()

	g = 0
	for line in d:
		line = line.rstrip()
		#print("LINE: ", line, "GNAME: ", gname)
		l = line.decode()
		#print("LINE: ", line)
		#print("LINE: ",line)
		#print("GNAME: ", gname)
		if(g==1):
			f.close()
			#print("POSTCOUNT: ", l)
			return l
		elif(line==gname):
			#print("FOUND IT")
			g = 1
	f.close()

	return "111"

def setPostCount(gname, countvar):
	fileName = postCountPath + name + "count.txt"
	with open(fileName, 'a+b') as countFile:

		lineNo = -1
		d = countFile.readlines()
		countFile.seek(0)
		count=0
		for line in countFile:
			count = count+1
			if(count%2!=0):
				#print(line, gname.encode())
				if(line==gname.encode() +b'\r\n'):
					lineNo = count
	#print("LINENO: ", lineNo)				
	#Remove the line and the next
	if(lineNo!=-1):
		modLine(fileName,lineNo+1, countvar)

def requestPostCount(gname):
	global clientSocket
	message = "POSTCOUNT " + gname
	sendEncoded(clientSocket, message)

def removePostCount(gname):
	fileName = postCountPath + name + "count.txt"
	with open(fileName, 'a+b') as countFile:

		lineNo = -1
		d = countFile.readlines()
		countFile.seek(0)
		count=0
		for line in countFile:
			count = count+1
			if(count%2!=0):
				if(line==gname.encode() +b'\r\n'):
					lineNo = count

	#Remove the line and the next
	if(lineNo!=-1):
		removeLine(fileName,lineNo)
		removeLine(fileName,lineNo)

def removeLine(fileName, lineNo):
	f = open(fileName,"r+")
	d = f.readlines()
	f.seek(0)
	count = 1
	for i in d:
	    if(lineNo != count):
	    	f.write(i)
	    count = count + 1
	f.truncate()
	f.close()

def modLine(fileName, lineNo, mod):
	f = open(fileName,"r+")
	d = f.readlines()
	f.seek(0)
	count = 1
	for i in d:
	    if(lineNo != count):
	    	f.write(i)
	    else: 
	    	f.write(str(mod) + "\n")
	    	#print("MODDED: ", mod)
	    count = count + 1
	f.truncate()
	f.close()

def markPostRead(postNum):
	global postList

	post = postList[postNum].subject
	if(isPostRead(post)):
		return

	fileName = readPostsPath + name+"posts.txt"
	postsFile = open(fileName, 'a+')

	postsFile.write(post+"\n")
	postsFile.close()

def markPostReadByName(postObj):
	post = postObj.subject
	global postList

	#print("MARKING READ: ", post)

	if(isPostRead(post)):
		return

	fileName = readPostsPath + name+"posts.txt"
	postsFile = open(fileName, 'a+')

	postsFile.write(post+"\n")
	postsFile.close()

def markPostRangeRead(start, end):

	for i in range(start, end):
		markPostRead(i)

def isPostRead(postName):
	initSubFile()

	fileName = readPostsPath + name + "posts.txt"
	with open(fileName, 'r+b') as postsFile:

		for line in postsFile:
			if(line==postName.encode() +b'\r\n'):
				return 1
			elif(line==postName.encode()):
				return 1
	return 0

def displayPostRead(postName):
	if(isPostRead(postName)):
		return " "
	return "N"

def displayPostFile():
	global nValue
	global postStart
	global postEnd
	global idFlag

	pr = ""
	fileName = "cur.txt"
	f = open(fileName,"r+")
	d = f.readlines()
	count = 0
	for i in d:
		if(count>=postStart and count<=postEnd):
			pr = pr + i
		#print("COUNT: ", count)
		count+=1
	#print("START: ", postStart, "COunt: ", count)

	if(count<=postStart):
		if(idFlag==1):
			markPostReadByName(currentPost)
			idFlag = 0
			resetPostN()
			displayPosts()
			return
	f.close()
	print(pr)



def runTests():
	print("RUNNING TESTS: ")
	subscribeToGroup("testgroup");
	subscribeToGroup("testgroup2");
	subscribeToGroup("testgroup3");



	#removePostCount("test2")


#Program loop
initDirs()
while True:
    if sys.version_info >= (3,0):
        readInput = input('Enter command: \n')
    else:
        readInput = raw_input('Enter command: \n')
        
    handleInput(readInput)