#!/usr/bin/python3
"""
PowerBeacon Flask Application
This module defines a Flask web application for managing PowerBeacon implants and listening posts.
It provides various routes for interacting with the implants, tasks, and settings.
Classes:
    MySQLConnection: A context manager for managing MySQL database connections.
Routes:
    /: Redirects to the implants page.
    /selectImplant: Allows selection of an implant.
    /listeningPosts: Displays and manages listening posts.
    /implants: Displays details and tasks for a selected implant.
    /addTask: Adds a new task for an implant.
    /deleteTask: Deletes a task for an implant.
    /updateSettings: Updates settings for an implant.
    /uninstallImplant: Uninstalls an implant.
    /changeTime: Changes the beacon interval for an implant.
    /taskSurvey: Adds a survey task for an implant.
    /displaySurvey: Displays survey data for an implant.
    /addImplant: Adds a new implant.
    /deleteImplant: Deletes an implant.
    /addListeningPost: Adds a new listening post.
    /deleteListeningPost: Deletes a listening post.
    /tools: Provides tools for encoding and decoding data.
Environment Variables:
    DB_HOST: The hostname of the MySQL database (default: 'localhost').
    DB_USER: The username for the MySQL database (default: 'root').
    DB_PASSWD: The password for the MySQL database (default: 't00r').
    DB_NAME: The name of the MySQL database (default: 'powerbeacon').
    SECRET_KEY: The secret key for the Flask application (default: '1234').
Main:
    Parses command-line arguments for host and port, and runs the Flask application.
"""

import argparse
import MySQLdb
from flask import Flask, render_template, request, redirect, url_for, flash, make_response
import os
import lib.pbLibrary as pb

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

app = Flask(__name__,template_folder='html')
app.secret_key = os.getenv('SECRET_KEY', '1234')

#Routes
@app.route('/',methods=['GET','POST'])
def index():
    return redirect(url_for('implants'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/selectImplant',methods=['GET','POST'])
def selectImplant():
    with MySQLConnection(connection_settings) as myConnection:
        error=None
        if request.method == 'POST':
            try:
                cookie = request.form['UUID']
                resp = make_response(redirect('/implants'))
                resp.set_cookie('implant_id',cookie)
                return resp
            except:
                error = "Failed to set implant"
                c2list = pb.getC2List(myConnection)
                implantList = pb.getImplantList(myConnection)
                return render_template('selectImplant.html',c2list=c2list,implantList=implantList, error=error)
        else:
            implantList = pb.getImplantList(myConnection)
            c2list = pb.getC2List(myConnection)
            return render_template('selectImplant.html',c2list=c2list,implantList=implantList,error=error)

@app.route('/listeningPosts',methods=['GET','POST'])
def listeningPosts():
    with MySQLConnection(connection_settings) as myConnection:
        error=None
        if request.method == 'POST':
            listeningposts = pb.getListeningPosts(myConnection)
            return render_template('listeningposts.html',listeningposts=listeningposts,error=error)
        else:
            listeningPosts = pb.getListeningPosts(myConnection)
            return render_template('listeningposts.html',listeningPosts=listeningPosts,error=error)

@app.route('/implants',methods=['GET','POST'])
def implants():
    with MySQLConnection(connection_settings) as myConnection:
        error=None
        cookie = request.cookies.get("implant_id")
        #cookie = "NewTest"
        
        try:
            if cookie:  #check if a cookie exists, otherwise send to implant selection screen
                UUID = cookie

                
                callbacks=pb.getCallbacks(myConnection,UUID,"10")
                pendingTasks=pb.getTasks(myConnection,UUID,"0")
                completedTasks=pb.getTasks(myConnection,UUID,"1")
                surveyData = pb.getSurveyList(myConnection,UUID) 
                C2List = pb.getListeningPosts(myConnection)
                implant = pb.getImplant(myConnection,UUID)
                #Get all the install lines to send to the page
                zeroInstall = pb.generateInstall(myConnection,UUID,0)[0]
                oneInstall = pb.generateInstall(myConnection,UUID,1)[0]
                twoInstall = pb.generateInstall(myConnection,UUID,2)[0]
                threeInstall = pb.generateInstall(myConnection,UUID,3)[0]
                fourInstall = pb.generateInstall(myConnection,UUID,4)[0]
                fiveInstall = pb.generateInstall(myConnection,UUID,5)[0]
                uninstall = pb.generateInstall(myConnection,UUID,0)[1]
                installLines = [zeroInstall,oneInstall,twoInstall,threeInstall,fourInstall,fiveInstall,uninstall]
                return render_template('implants.html',implant=implant,pendingTasks=pendingTasks,surveyData=surveyData,completedTasks=completedTasks,C2List=C2List,callbacks=callbacks,installLines=installLines,error=error)
        except Exception as e:
            print(e)
            error = f"Error accessing implant \"{UUID}.\"  Please select a new implant."
            c2list = pb.getC2List(myConnection)
            implantList = pb.getImplantList(myConnection)
            return render_template('selectImplant.html',c2list=c2list,implantList=implantList, error=error)
        else:
            return redirect('/selectImplant') 

@app.route('/addTask',methods=['GET','POST'])
def addTask():
    with MySQLConnection(connection_settings) as myConnection:
        error = None
        if request.method == 'POST':
            UUID = request.form['UUID']
            task = request.form['task']
            notes = request.form['notes']
            
            try:
                pb.addTask(myConnection,UUID,task,notes)
                flash('Task Added')
                return redirect(url_for('implants'))
            except:
                error = "Failed to add task."
                return redirect(url_for('implants'))

        return redirect(url_for('implants'))

@app.route('/deleteTask',methods=['GET','POST'])
def deleteTask():
    with MySQLConnection(connection_settings) as myConnection:
        error=None
        if request.method=="POST":
            try:
                id=request.form['taskID']
                pb.deleteTask(myConnection,id)
                flash('Task Deleted')
                
                return redirect(url_for('implants'))
            except:
                error = "Error deleting task.  Task may have already completed."
                flash(error)
                return redirect(url_for('implants'))
            return redirect(url_for('implants'))

@app.route('/updateSettings',methods=['GET','POST'])
def updateSettings():
    with MySQLConnection(connection_settings) as myConnection:
        error=None
        if request.method=="POST":
            notes = request.form['updateNotes']
            UUID = request.form['UUID']
            if 'updateSettings' in request.form:
                C2 = request.form['updateC2']
                filter = request.form['updateFilter']
                consumer = request.form['updateConsumer']
                interval = request.form['interval']
                pb.updateSettings(myConnection,UUID,notes,C2,filter,consumer,interval)
            else:
                pb.updateNotes(myConnection,UUID,notes)
            return redirect(url_for('implants'))
        return redirect(url_for('implants'))

@app.route('/uninstallImplant',methods=['GET','POST'])
def uninstallImplant():
    with MySQLConnection(connection_settings) as myConnection:
        error=None
        if request.method=="POST":
            UUID = request.form['UUID']
            pb.uninstallImplant(myConnection,UUID)
            return redirect(url_for('implants'))
        return redirect(url_for('implants'))

@app.route('/changeTime',methods=['GET','POST'])
def changeTime():
    with MySQLConnection(connection_settings) as myConnection:
        if request.method=="POST":
            UUID=request.form['UUID']
            interval=int(request.form['interval'])
            
            newTimingTask=pb.generateInstall(myConnection,UUID,interval)[0]
            intervalText=["15 seconds","1 minute","15 minutes","30 minutes","1 hour","4 hours"]  #For crafting the note
            taskNotes="Change interval timing to " + intervalText[interval]                     #And make the note
            pb.addTask(myConnection,UUID,newTimingTask,taskNotes)                               #create the task
            flash("Beacon timing tasked to " + intervalText[interval])
            return redirect(url_for('implants'))
        return redirect(url_for('implants'))

@app.route('/taskSurvey',methods=['GET','POST'])
def taskSurvey():
    with MySQLConnection(connection_settings) as myConnection:
        if request.method=="POST":
            UUID=request.form['UUID']
            notes=request.form['notes']
            options=[False,False,False]
            if "dirs" in request.form:
                options[0]=True
            if "firewall" in request.form:
                options[1]=True
            if "mppref" in request.form:
                options[2]=True         
            task=pb.generateSurvey(myConnection,UUID,options,notes)
            pb.addTask(myConnection,UUID,task,notes)
            flash("Survey Tasked")
            return redirect(url_for('implants'))
        return redirect(url_for('implants'))

@app.route('/displaySurvey',methods=['GET','POST'])
def getData():
    with MySQLConnection(connection_settings) as myConnection:
        error = None
        if request.method == 'POST':
            id=request.form['ID']
            cur = myConnection.cursor()
            cur.execute("SELECT data from datastore where (id="+id+")")
            dataDetails=cur.fetchall()
            cur.close()
            return render_template('displaySurvey.html',error=error,dataDetails=dataDetails)
            
        return redirect(url_for('implants'))

@app.route('/addImplant',methods=['GET','POST'])
def addImplant():
    with MySQLConnection(connection_settings) as myConnection:
        error = None
        if request.method == 'POST':
            try:
                UUID = request.form['UUID']
                key = request.form['key']
                c2 = request.form['c2']
                filter = request.form['filter']
                notes = request.form['notes']
                consumer = request.form['consumer']
                pb.addImplant(myConnection,UUID,key,notes,c2,filter,consumer)
                flash("Implant Added")
                return redirect(url_for('selectImplant'))
            except Exception as e:
                error = f"Error adding implant: {e}"
                c2list = pb.getC2List(myConnection)
                implantList = pb.getImplantList(myConnection)
                return render_template('selectImplant.html',c2list=c2list,implantList=implantList, error=error)

        return redirect(url_for('implants'))
        
@app.route('/deleteImplant',methods=['GET','POST'])
def deleteImplant():
    with MySQLConnection(connection_settings) as myConnection:
        error = None
        if request.method == 'POST':
            UUID=request.form['deleteImplantID']
            pb.deleteImplant(myConnection,UUID)
            flash("Implant Deleted")
            resp = make_response(redirect('/implants'))
            resp.set_cookie('implant_id','', expires=0)
            return resp
        return redirect(url_for('implants'))

@app.route('/addListeningPost',methods=['GET','POST'])
def addListeningPost():
    with MySQLConnection(connection_settings) as myConnection:
        error = None
        if request.method == 'POST':
            try:
                name = request.form['name']
                address = request.form['address']
                pb.addListeningPost(myConnection,name,address)
                flash("Listening Post Added")
                return redirect(url_for('listeningPosts'))
            except Exception as e:
                error = f"Error adding listening post: {e}"
                listeningPosts = pb.getListeningPosts(myConnection)
                return render_template('listeningposts.html',listeningPosts=listeningPosts,error=error)
        return redirect(url_for('listeningPosts'))

@app.route('/deleteListeningPost',methods=['GET','POST'])
def deleteListeningPost():
    with MySQLConnection(connection_settings) as myConnection:
        error = None
        if request.method == 'POST':
            ID=request.form['lpID']
            pb.deleteListeningPost(myConnection,ID)
            flash("Listening Post Deleted")
            return redirect(url_for('listeningPosts'))
        return redirect(url_for('listeningPosts'))

@app.route('/tools',methods=['GET','POST'])
def tools():
    with MySQLConnection(connection_settings) as myConnection:
        error = None
        if request.method == 'POST':
            if 'encodedData' in request.form:
                encodedData = request.form['encodedData']
                decodedData = pb.base64Decode(encodedData)
                if decodedData == "Error decoding data":
                    error = "Error decoding data.  Please check the data and try again."
                return render_template('tools.html',encodedData=encodedData,decodedData=decodedData,error=error)
            elif 'decodedData' in request.form:
                decodedData = request.form['decodedData']
                encodedData=pb.base64Encode(decodedData)
                if 'powershellify' in request.form:
                    encodedData = f"powershell -e {encodedData}"
                return render_template('tools.html',encodedData=encodedData,decodedData=decodedData,error=error)

        encodedData = ""
        decodedData = ""
        return render_template('tools.html',encodedData=encodedData,decodedData=decodedData,error=error)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=int, required=False)
    parser.add_argument('-b', type=str, required=False)
    args = parser.parse_args()
    
    if args.b:
        host = args.b
    else:
        host = '0.0.0.0'
    if args.p:
        port = args.p
    else:
        port = 5000
    app.run(host,port,debug=True)
