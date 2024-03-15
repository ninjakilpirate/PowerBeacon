#!/usr/bin/python3

from flask import Flask,render_template,request,redirect,url_for,flash,make_response
import time
from base64 import b64encode
import MySQLdb
import pbLibrary as pb


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

        checkIns=pb.getCheckIns(myConnection,UUID,"20")    #getting data to send to page
        implantDetails=pb.getDetails(myConnection,UUID)
        pendingTasks=pb.getTasks(myConnection,UUID,"0")
          
        return render_template('implants.html',implantDetails=implantDetails,checkIns=checkIns,UUID=implantDetails[0][0],pendingTasks=pendingTasks,error=error)
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
            print("added task")
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
            error = "Error deleting task"
            return redirect(url_for('implants'))
        return redirect(url_for('implants'))



if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000,debug=True)
