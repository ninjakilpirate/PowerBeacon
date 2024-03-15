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
    cur.execute("delete from tasks where (id="+taskID+") and (is_complete=0)")
    connection.commit()
    cur.close()


