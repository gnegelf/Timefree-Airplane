#! /usr/bin/python

import re
import cplex
import math
import time
import sys
from operator import itemgetter
from cplex.callbacks import IncumbentCallback
from cplex.callbacks import LazyConstraintCallback
from cplex.exceptions import CplexSolverError
from sets import Set 

EPSILON = 1e-6

        
# -------
# classes
# -------


class ARC(object):
    def __init__(self,tail=None,head=None,visited=None):
        self.tail = tail
        self.head = head
        self.visited = visited                        
        
# ---------
# callbacks
# ---------

class AIRPLANE(object):
    def __init__(self,cost=None,seats=None,origin=None,departure_min_fuel=None,departure_max_fuel=None,destination=None,arrival_min_fuel=None,arrival_max_fuel=None,required_fueltype=None,fuel=None,speed=None,max_fuel=None,empty_weight=None,add_turnover_time=None,reserve_fuel=None,contigence_ratio=None):
        self.cost = float(cost)
        self.seats = int(seats)
        self.origin = origin
        self.departure_min_fuel = float(departure_min_fuel)
        self.departure_max_fuel = float(departure_max_fuel)
        self.destination = destination
        self.arrival_min_fuel = float(arrival_min_fuel)
        self.arrival_max_fuel = float(arrival_max_fuel)
        self.required_fueltype = int(required_fueltype)
        self.fuel = float(fuel)
        self.speed = float(speed)
        self.max_fuel = float(max_fuel)
        self.empty_weight = float(empty_weight)
        self.add_turnover_time = int(add_turnover_time) / 5
        self.reserve_fuel = float(reserve_fuel)
        self.contigence_ratio = float(contigence_ratio)
    def printMe(self):
        print("Going from " + str(self.origin) + " to "+ str(self.destination))
        

class AIRPORT(object):
    def __init__(self,turnover_time=None,maintenance=None):
        self.turnover_time = int(turnover_time) /5
        self.maintenance = int(maintenance)
        self.fuel = {}

class REQUEST(object):
    def __init__(self,origin=None,destination=None,earliest_departure_time=None,earliest_departure_day=None,latest_arrival_time=None,latest_arrival_day=None,passengers=None,weight=None):
        self.origin = origin
        self.destination = destination
        self.earliest_departure_time = int(earliest_departure_time) / 5
        self.earliest_departure_day = int(earliest_departure_day)
        self.latest_arrival_time = int(latest_arrival_time) / 5
        self.latest_arrival_day = int(latest_arrival_day)
        self.passengers = int(passengers)
        self.weight = float(weight)

        self.earliest_departure = 1440 /5 * (self.earliest_departure_day - 1) + self.earliest_departure_time
        self.latest_arrival = 1440 / 5 * (self.latest_arrival_day - 1) + self.latest_arrival_time
    def printMe(self):
        print("Request going from " + str(self.origin) + " to "+ str(self.destination))
        print("Earliest departure: %d" % (self.earliest_departure))
        print("Latest Arrival: %d" % (self.latest_arrival))

class WEIGHTLIMIT(object):
    def __init__(self,max_takeoff_weight=None,max_landing_weight=None):
        self.max_takeoff_weight = float(max_takeoff_weight)
        self.max_landing_weight = float(max_landing_weight)

class DIVIDERCOLLECTION(object):
    def __init__(self,T):
        self.dividers=[Divider([T+1])]
        #self.dividers=[Divider([i+1 for i in range(T)])]
        self.ids=self.generateIds(T)
    def addDivider(self,listOfPoints,T):
        if listOfPoints == []:
            print("Error Empty list added")
        else:
            if self.changesIntervals(T,listOfPoints):
                self.dividers.append(Divider(listOfPoints))
                print("Intervals changed")
            self.ids=self.generateIds(T)
    def generateIds(self,T,lOP=None):
        tol = 0.000001
        ids={}
        intervalbarriers=[-1]
        newDiv=[]
        if not lOP == None:
            newDiv=[Divider(lOP)]
        for divider in self.dividers+newDiv:
            for point in divider.listOfPoints:
                for count in range(len(intervalbarriers)):
                    if abs(point -intervalbarriers[-count-1])< tol:
                        break
                    if point -intervalbarriers[-count-1] > 0:
                        intervalbarriers.insert(len(intervalbarriers)-count,point)
                        break
        #prev=-1
        for j,i in enumerate(intervalbarriers):
            if j!=0:
                idstore=self.findId(i-1,lOP)
                if ids.has_key(idstore):
                    ids[idstore]+=[prev,i]
                else:
                    ids[idstore]=[prev,i]
            prev=i
        return ids
    def findId(self,t,listOfPoints=None):
        idString=""
        if listOfPoints!=None:
            for divider in self.dividers+[Divider(listOfPoints)]:
                idString+=str(divider.evaluate(t))
        else:
            for divider in self.dividers:
                idString+=str(divider.evaluate(t))
        return idString
    def changesIntervals(self,T,listOfPoints):
        if len(self.ids)==len(self.generateIds(T,listOfPoints)):
            return 0
        else:
            return 1
        
class Divider():
    def __init__(self,listOfPoints):
        self.listOfPoints=listOfPoints
    def evaluate(self,t):
        #return t
        for i,val in enumerate(self.listOfPoints):
            if t < val:
                return i % 2
        return (i+1) % 2
# prepare reading and parsing

def doTheyIntersect(lon1i,lon2i,tol=0.00000001):
    if lon1i[0] >= lon2i[0]:
        lon1=lon1i
        lon2=lon2i
    else:
        lon2=lon1i
        lon1=lon2i
    i=0
    j=0
    while i < len(lon1) and j < len(lon2):
        #print("i: %d" %i)
        #print("j: %d" % j)
        if i % 2 == 0:
            if lon1[i] - lon2[j]<-tol:
                i+=1
            else:
                if lon1[i] - lon2[j+1]<-tol:
                    return 1
                else: j+=2
        else:
            if lon1[i] - lon2[j]<=tol:
                i+=1
            else:
                if lon1[i] - lon2[j+1]<=tol:
                    return 1
                else: j+=2 
    return 0

def joinIntervalLists(l1,l2):
    newList=[]
    i=0
    j=0
    if len(l1) == 0 or len(l2)==0:
        return l1+l2
    if l1[0]>=l2[0]:
        jopen=1
        newList.append(l2[j])
    else:
        jopen=0
        newList.append(l1[i])   
    while i < len(l1) and j < len(l2):
        if jopen:
            #print( "last boundary from l2" )
            if  l1[i] <= l2[j+1]:
                i+=1
            else:
                if i % 2 == 1:
                    j+=1
                    i-=1
                    jopen=0
                else:
                    newList.append(l2[j+1])
                    j+=2
                    if j < len(l2):
                        if l1[i]>=l2[j]:
                            newList.append(l2[j])
                            #j+=1
                        else:
                            newList.append(l1[i])
                            jopen=0
                            #i+=1
        else:
            #print( "last boundary from l1" )
            if l1[i+1] >= l2[j]:
                j+=1
            else:
                if j % 2 == 1:
                    i+=1
                    j-=1
                    jopen=1
                else:
                    newList.append(l1[i+1])
                    i+=2
                    if i < len(l1):
                        if l1[i] <= l2[j]:
                            newList.append(l1[i])
                            #i+=1
                        else:
                            newList.append(l2[j])
                            jopen=1
                            #j+=1
    if jopen:
        j+=1
    else:
        i+=1
    while i < (len(l1)):
        newList.append(l1[i])
        i+=1
    while j < len(l2):
        newList.append(l2[j])
        j+=1
    return newList
        
                

def shiftList(l,shift):
    lnew=[]
    for i in range(len(l)):
        lnew.append(l[i]+shift)
    return lnew

comment_line = re.compile('#');

def printRequests(Request):
    for key,request in Request.iteritems():
        request.printMe()
            
#directory = sys.argv[1]
directory='Data'

# ---------------------
# reading airplanes.dat
# ---------------------

print "reading '"+directory+"/airplanes.dat'"

file = open(directory+"/airplanes.dat", "r")
airplanes_data = file.read()
file.close()

entries = re.split("\n+", airplanes_data)

Airplane = {}

for line in entries:
    if comment_line.search(line) == None:
        datas = re.split("\s+", line)
        if len(datas) == 17:
            #print datas
            ID,cost,seats,origin,departure_min_fuel,departure_max_fuel,destination,arrival_min_fuel,arrival_max_fuel,required_fueltype,fuel,speed,max_fuel,empty_weight,add_turnover_time,reserve_fuel,contigence_ratio = datas
            Airplane[ID] = AIRPLANE(cost,seats,origin,departure_min_fuel,departure_max_fuel,destination,arrival_min_fuel,arrival_max_fuel,required_fueltype,fuel,speed,max_fuel,empty_weight,add_turnover_time,reserve_fuel,contigence_ratio)


# --------------------
# reading airports.dat
# --------------------

print "reading '"+directory+"/airports.dat'"

file = open(directory+"/airports.dat", "r")
airports_data = file.read()
file.close()

entries = re.split("\n+", airports_data)

Airport = {}

for line in entries:
    if comment_line.search(line) == None:
        datas = re.split("\s+", line)
        if len(datas) == 3:
            #print datas
            ID, turnover_time, maintenance = datas
            Airport[ID] = AIRPORT(turnover_time,maintenance)


# --------------------
# reading controls.dat
# --------------------

print "reading '"+directory+"/controls.dat'"

file = open(directory+"/controls.dat", "r")
controls_data = file.read()
file.close()

entries = re.split("\n+", controls_data)

for line in entries:
    if comment_line.search(line) == None:
        datas = re.split("\s+", line)
        if len(datas) == 2:
            #print datas
            ID, value = datas
            if ID == "1":
                max_stops = int(value)
            if ID == "2":
                delta_time = int(value) / 5


# ---------------------
# reading distances.dat
# ---------------------

print "reading '"+directory+"/distances.dat'"

file = open(directory+"/distances.dat", "r")
distances_data = file.read()
file.close()

entries = re.split("\n+", distances_data)

Distance = {}

for line in entries:
    if comment_line.search(line) == None:
        datas = re.split("\s+", line)
        if len(datas) == 3:
            #print datas
            origin, destination, dist = datas
            Distance[origin,destination] = float(dist)


# -----------------
# reading fuels.dat
# -----------------

print "reading '"+directory+"/fuels.dat'"

file = open(directory+"/fuels.dat", "r")
fuels_data = file.read()
file.close()

entries = re.split("\n+", fuels_data)

for line in entries:
    if comment_line.search(line) == None:
        datas = re.split("\s+", line)
        if len(datas) == 3:
            #print datas
            airport, fuelID, isAvailable = datas
            Airport[airport].fuel[fuelID] = isAvailable


# --------------------
# reading requests.dat
# --------------------

print "reading '"+directory+"/requests.dat'"

file = open(directory+"/requests.dat", "r")
requests_data = file.read()
file.close()

entries = re.split("\n+", requests_data)

Request = {}

for line in entries:
    if comment_line.search(line) == None:
        datas = re.split("\s+", line)
        if len(datas) == 9:
            #print datas
            ID,origin,destination,earliest_departure_time,earliest_departure_day,latest_arrival_time,latest_arrival_day,passengers,weight = datas
            Request[ID] = REQUEST(origin,destination,earliest_departure_time,earliest_departure_day,latest_arrival_time,latest_arrival_day,passengers,weight)


# ------------------------
# reading weightlimits.dat
# ------------------------

print "reading '"+directory+"/weightlimits.dat'"

file = open(directory+"/weightlimits.dat", "r")
weightlimits_data = file.read()
file.close()

entries = re.split("\n+", weightlimits_data)

Weightlimit = {}

for line in entries:
    if comment_line.search(line) == None:
        datas = re.split("\s+", line)
        if len(datas) == 4:
            #print datas
            airport, airplane, max_takeoff_weight, max_landing_weight = datas
            Weightlimit[airport,airplane] = WEIGHTLIMIT(max_takeoff_weight,max_landing_weight)


# --------------------------------
# generating further instance data
# --------------------------------

# travelcost

Travelcost = {}

for p in Airplane:
    for i, j in Distance:
        Travelcost[i,j,p] = math.ceil(Distance[i,j] * Airplane[p].cost)

Traveltime = {}

for p in Airplane:
    for i, j in Distance:
        Traveltime[i,j,p] = int(math.floor(Distance[i,j] / ((Airplane[p].speed / 60) * 5)) )

Fuelconsumption = {}

for p in Airplane:
    for i, j in Distance:
        Fuelconsumption[i,j,p] = math.ceil(Distance[i,j] * Airplane[p].fuel * Airplane[p].contigence_ratio);


# ----------------
# MODEL GENERATION
# ----------------



number_of_timesteps=20
# VARIABLES

#"""
xDividers={}
for i,j in Distance:
    for r in Request:
        for p in Airplane:
            xDividers[i,j,r,p]=DIVIDERCOLLECTION(number_of_timesteps)

xDepDividers={}
xArrDividers={}
for r in Request:
    for p in Airplane:
        xArrDividers[r,p]=DIVIDERCOLLECTION(number_of_timesteps)
        xDepDividers[r,p]=DIVIDERCOLLECTION(number_of_timesteps)

yDividers={}
for i,j in Distance:
    for p in Airplane:
        yDividers[i,j,p]=DIVIDERCOLLECTION(number_of_timesteps)

yDepDividers={}
yArrDividers={}
for p in Airplane:
    yDepDividers[p]=DIVIDERCOLLECTION(number_of_timesteps)
    yArrDividers[p]=DIVIDERCOLLECTION(number_of_timesteps)
    #for t in range(1,number_of_timesteps):
    #    yDepDividers[p].addDivider([t],number_of_timesteps)
    #    yArrDividers[p].addDivider([t],number_of_timesteps)

zDividers={}

for i,j in Distance:
    for p in Airplane:
        zDividers[i,j,p]=DIVIDERCOLLECTION(number_of_timesteps)


zDepDividers={}
zArrDividers={}
for p in Airplane:
    zDepDividers[p]=DIVIDERCOLLECTION(number_of_timesteps)
    zArrDividers[p]=DIVIDERCOLLECTION(number_of_timesteps)
#"""

#main loop for creating sequence of loops
mipSolved=0

while(mipSolved==0):
    model = cplex.Cplex()
    x = {}
    for i,j in Distance:
        for r in Request:
            for p in Airplane:
                for ID in xDividers[i,j,r,p].ids:
                    x[i,j,r,p,ID] = "x#" + i + "_" + j + "_" + r + "_" + p + "_"+ID
                    model.variables.add(obj = [0.01 * Distance[i,j]], names = [x[i,j,r,p,ID]], lb = [0], ub = [1], types = ["B"])
    
    x_dep = {}
    
    for r in Request:
        for p in Airplane:
            for ID in xDepDividers[r,p].ids:
                x_dep[r,p,ID] = "x_dep#" + r + "_" + p + "_" + ID
                model.variables.add(names = [x_dep[r,p,ID]], lb = [0], ub = [1], types = ["B"])
    
    x_arr = {}
    
    for r in Request:
        for p in Airplane:
            for ID in xArrDividers[r,p].ids:
                x_arr[r,p,ID] = "x_arr#" + r + "_" + p + "_" + ID
                model.variables.add(names = [x_arr[r,p,ID]], lb = [0], ub = [1], types = ["B"])
        
    y = {}
    for i,j in Distance:
        for p in Airplane:
            for ID in yDividers[i,j,p].ids:
                y[i,j,p,ID] = "y#" + i + "_" + j + "_" + p + "_" + ID
                model.variables.add(obj = [Travelcost[i,j,p]], names = [y[i,j,p,ID]], lb = [0], types = ["I"])
    
    y_dep = {}
    
    for p in Airplane:
        for ID in yDepDividers[p].ids:
            y_dep[p,ID] = "y_dep#" + p  + "_" + ID
            model.variables.add(names = [y_dep[p,ID]], lb = [0.0], ub = [1.0], types = ["B"])
    
    y_arr = {}
    
    for p in Airplane:
        for ID in yArrDividers[p].ids:
            y_arr[p,ID] = "y_arr#" + p  + "_" + ID
            model.variables.add(names = [y_arr[p,ID]], lb = [0.0], ub = [1.0], types = ["B"])
    
    z = {}
    
    for i,j in Distance:
        for p in Airplane:
            for ID in zDividers[i,j,p].ids:
                z[i,j,p,ID] = "z#" + i + "_" + j + "_" + p  + "_" + ID
                model.variables.add(names = [z[i,j,p,ID]], lb = [0], ub = [Airplane[p].max_fuel], types = ["C"])
    
    z_dep = {}
    
    for p in Airplane:
        for ID in zDepDividers[p].ids:
            z_dep[p,ID] = "z_dep#" + p  + "_" + ID
            model.variables.add(names = [z_dep[p,ID]], lb = [Airplane[p].departure_min_fuel], ub = [Airplane[p].departure_max_fuel], types = ["C"])

    z_arr = {}
    
    for p in Airplane:
        for ID in zArrDividers[p].ids:
            z_arr[p,ID] = "z_arr#" + p  + "_" + ID
            model.variables.add(names = [z_arr[p,ID]], lb = [Airplane[p].arrival_min_fuel], ub = [Airplane[p].arrival_max_fuel], types = ["C"])
    """
    w = {}
    
    for i,j in Distance:
        for p in Airplane:
            w[i,j,p] = "w#" + i + "_" + j + "_" + p
            model.variables.add(names = [w[i,j,p]], lb = [0], types = ["C"])
    """
    # CONSTRAINTS
    #TODO: Change constraints so that they are defined for each time variable,
    # to avoid unneccessary constraints track which constraints have been added and only add new ones

    
    #each plane must depart and arrive
    
    for p in Airplane:
        thevars=[y_dep[p,ID] for ID in yDepDividers[p].ids]
        thecoefs=[1.0 for ID in yDepDividers[p].ids]
        model.linear_constraints.add(names=[p+' departure'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
        thevars=[y_arr[p,ID] for ID in yArrDividers[p].ids]
        thecoefs=[1.0 for ID in yArrDividers[p].ids]
        model.linear_constraints.add(names=[p+' arrival'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
    
    #airplane flow
    #TODO: Check if restriction to in Distance is neccessary
    for i,j in Distance:
        for p in Airplane:
            thevars=[y[i,j,p,ID] for ID,intervalIter in yDividers[i,j,p].ids.iteritems() if not(doTheyIntersect(intervalIter,[Traveltime[i,j,p],number_of_timesteps+1]))]
            if thevars!=[]:
                print(thevars)
                thecoefs=[1.0]*len(thevars)
                #model.linear_constraints.add(names=[i+'_'+j+'_'+p+ ' not reachable'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
    #model.variables.set_upper_bounds('y_dep#10_01',0.0)
    for j in Airport:
        for p in Airplane:
            constrCodes=[]
            for t in xrange(number_of_timesteps):
                thevars=[]
                thecoefs=[]
                intervals=[]
                for i in Airport:
                    if i!=j and (i,j) in Distance:
                        ID1=yDividers[i,j,p].findId(t)
                        thevars += [y[i,j,p,ID1]]
                        thecoefs += [1.0]
                        intervals = joinIntervalLists(intervals,yDividers[i,j,p].ids[ID1])

                rhs_value = 0.0
                
                if (j == Airplane[p].origin):
                    ID1=yDepDividers[p].findId(t)
                    #thevars+=[y_dep[p,ID] for ID,intervalIter in yDepDividers[p].ids.iteritems() if doTheyIntersect(intervals2,intervalIter)]
                    thevars.append(y_dep[p,ID1])
                    #thecoefs+=[1.0 for ID,intervalIter in yDepDividers[p].ids.iteritems() if doTheyIntersect(intervals2,intervalIter)]
                    thecoefs+=[1.0]
                    intervals = joinIntervalLists(intervals,yDepDividers[p].ids[ID1])
                """
                if (j == Airplane[p].origin):
                    for ID1,intervalIter in yDepDividers[p].ids.iteritems():
                        if doTheyIntersect(intervalIter,intervals):
                            #thevars+=[y_dep[p,ID] for ID,intervalIter in yDepDividers[p].ids.iteritems() if doTheyIntersect(intervals2,intervalIter)]
                            thevars.append(y_dep[p,ID1])
                            #thecoefs+=[1.0 for ID,intervalIter in yDepDividers[p].ids.iteritems() if doTheyIntersect(intervals2,intervalIter)]
                            thecoefs+=[1.0]
                            intervals = joinIntervalLists(intervals,yDepDividers[p].ids[ID1])
                
                """
                for k in Airport:
                    if k!=j and (j,k) in Distance:
                        for ID ,intervalIter in yDividers[j,k,p].ids.iteritems():
                            if doTheyIntersect(shiftList(intervals,Traveltime[j,k,p]),intervalIter):
                                thevars += [y[j,k,p,ID]]
                                thecoefs += [-1.0]
                                intervals2=joinIntervalLists(intervals,intervalIter)
                """
                thevars+= [y[j,k,p,ID] for k in Airport  if k!=j and (j,k) in Distance for ID ,intervalIter in yDividers[j,k,p].ids.iteritems()
                             if doTheyIntersect(shiftList(intervals,Traveltime[j,k,p]),intervalIter)]

                thecoefs += [-1.0  for k in Airport  if k!=j and (j,k) in Distance for ID ,intervalIter in yDividers[j,k,p].ids.iteritems()
                             if doTheyIntersect(shiftList(intervals,Traveltime[j,k,p]),intervalIter)]
                
                if (j == Airplane[p].destination):
                    #thevars.append(y_arr[p,yArrDividers[p].findId(t)])
                    #thecoefs.append(-1.0)
                    thevars+=[y_arr[p,ID] for ID,intervalIter in yArrDividers[p].ids.iteritems() if doTheyIntersect(intervals,intervalIter)]
                    thecoefs+=[-1.0 for ID,intervalIter in yArrDividers[p].ids.iteritems() if doTheyIntersect(intervals,intervalIter)]
                constrCode=''
                for name in thevars:
                    constrCode+=name
                if not (constrCode in constrCodes):
                    #print(j)
                    #print(constrCode)
                    if  j+'_'+p+'_'+str(t)+ ' flow'=='ABU_10_0 flow' or j+'_'+p+'_'+str(t)+ ' flow'=='MOM_10_0 flow':
                        print(thevars)
                    model.linear_constraints.add(names=[ j+'_'+p+'_'+str(t)+ ' flow'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [rhs_value])
                    constrCodes.append(constrCode)
                
    #"""
    #"""
    for p in Airplane:
        if (Airplane[p].origin == Airplane[p].destination):
            i = Airplane[p].origin
            
            thevars = [y[i,j,p,ID] for j in Airport if i!=j for ID in yDividers[i,j,p].ids]
            thecoefs = [1.0]*len(thevars)
            
            model.linear_constraints.add(names=[p+' must depart'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])
    #"""
    # each request must depart and arrive
    #"""
    for r in Request:
        thevars = [x_dep[r,p,ID] for p in Airplane for ID in xDepDividers[r,p].ids]
        thecoefs = [1.0 for p in Airplane for ID in xDepDividers[r,p].ids]
        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
        thevars = [x_arr[r,p,ID] for p in Airplane for ID in xArrDividers[r,p].ids]
        thecoefs = [1.0 for p in Airplane for ID in xArrDividers[r,p].ids]
        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
    
    
    #TODO: Check if restriction to in Distance has to be added
    # request flow departure
    
    """
    for r in Request:
        for p in Airplane:
            constrCodes=[]
            for t in xrange(number_of_timesteps):
                thevars=[]
                thecoefs=[]
                intervals=[]
                ori=Request[r].origin
                for j in Airport:
                    if (j!= ori):
                        ID1=xDividers[ori,j,r,p].findId(t)
                        thevars += [x[ori,j,r,p,ID1]]
                        thecoefs += [1.0]
                        intervals = joinIntervalLists(intervals,xDividers[ori,j,r,p].ids[ID1])
                thevars += [x_dep[r,p,ID] for ID,intervalIter in xDepDividers[r,p].ids.iteritems() if doTheyIntersect(intervals,intervalIter)]
                thecoefs += [-1.0 for ID,intervalIter in xDepDividers[r,p].ids.iteritems() if doTheyIntersect(intervals,intervalIter)]
                

                
                constrCode=''
                for name in thevars:
                    constrCode+=name
                if not (constrCode in constrCodes):
                    model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
                    constrCodes.append(constrCode)
    
    # request flow arrival
    
    for r in Request:
        for p in Airplane:
            constrCodes=[]
            for t in xrange(number_of_timesteps):
                thevars=[]
                thecoefs=[]
                intervals=[]
                desti=Request[r].destination
                for i in Airport:
                    if (i!= desti):
                        ID1=xDividers[i,desti,r,p].findId(t)
                        thevars += [x[i,desti,r,p,ID1]]
                        thecoefs += [1.0]
                        intervals = joinIntervalLists(intervals,xDividers[i,desti,r,p].ids[ID1])
                thevars += [x_arr[r,p,ID] for ID,intervalIter in xArrDividers[r,p].ids.iteritems() if doTheyIntersect(intervals,intervalIter)]
                thecoefs += [-1.0 for ID,intervalIter in xArrDividers[r,p].ids.iteritems() if doTheyIntersect(intervals,intervalIter)]
                
                #desti=Request[r].destination
                #thevars = [x_arr[r,p,xArrDividers[r,p].findId(t)]]
                #thecoefs = [-1.0]
                #thevars += [x[j,desti,r,p,ID]
                #                for j in Airport if j != desti for ID,intervals in xDividers[j,desti,r,p].ids.iteritems() 
                #                if doTheyIntersect(shiftList(xArrDividers[r,p].ids[xArrDividers[r,p].findId(t)],Traveltime[j,desti,p]),intervals)]
                #thecoefs += [1.0 for j in Airport if j != desti for ID,intervals in xDividers[j,desti,r,p].ids.iteritems() 
                #                if doTheyIntersect(shiftList(xArrDividers[r,p].ids[xArrDividers[r,p].findId(t)],Traveltime[j,desti,p]),intervals)]
                
                
                constrCode=''
                for name in thevars:
                    constrCode+=name
                if not (constrCode in constrCodes):
                    model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
                    constrCodes.append(constrCode)
    
    
    # request flow (other than departure and arrival)
    """
    #"""
    for r in Request:
        for p in Airplane:
            for j in Airport:
                constrCodes=[]
                #if (j != Request[r].origin and j != Request[r].destination):
                if 1:
                    for t in xrange(number_of_timesteps):
                    #for t in xrange(Request[r].earliest_departure,Request[r].latest_arrival):
                        thevars=[]
                        thecoefs=[]
                        intervals=[]
                        for i in Airport:
                            if (j!= i):
                                ID1=xDividers[i,j,r,p].findId(t)
                                thevars += [x[i,j,r,p,ID1]]
                                thecoefs += [1.0]
                                intervals = joinIntervalLists(intervals,xDividers[i,j,r,p].ids[ID1])
                        #thevars = [x[j,i,r,p,xDividers[j,i,r,p].findId(t)]
                        #            for j in Airport if j != i]
                        #thecoefs = [1.0 for j in Airport if j != i];
                        if (j == Request[r].origin):
                            ID1=xDepDividers[r,p].findId(t)
                            thevars.append(x_dep[r,p,ID1])
                            thecoefs+=[1.0]
                            intervals = joinIntervalLists(intervals,xDepDividers[r,p].ids[ID1])
                        thevars += [x[j,k,r,p,ID] 
                                    for k in Airport if j != k for ID,intervalsiter in xDividers[j,k,r,p].ids.iteritems()
                                    if doTheyIntersect(shiftList(intervals,Traveltime[j,k,p]),intervalsiter)]
                        
                        thecoefs += [-1.0 for k in Airport if j != k for ID,intervalsiter in xDividers[j,k,r,p].ids.iteritems()
                                    if doTheyIntersect(shiftList(intervals,Traveltime[j,k,p]),intervalsiter)];
                               
                        if (j == Request[r].destination):

                            thevars+=[x_arr[r,p,ID] for ID,intervalIter in xArrDividers[r,p].ids.iteritems() if doTheyIntersect(intervals,intervalIter)]
                            thecoefs+=[-1.0 for ID,intervalIter in xArrDividers[r,p].ids.iteritems() if doTheyIntersect(intervals,intervalIter)]
                        
                        constrCode=''
                        for name in thevars:
                            constrCode+=name
                        if not (constrCode in constrCodes):
                            model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
                            constrCodes.append(constrCode)
    
    
    # airplane departure/arrival in case origin equals destination
    #TODO: Make sure this is unneccessary in the time expanded case
    
                    
    # seat limit
    
    for i,j in Distance:
        for p in Airplane:
            constrCodes=[]
            for t in range(number_of_timesteps):
                #print i,j,p
                thevars=[]
                thecoefs=[]
                intervals=[]
                for r in Request:
                    ID1=xDividers[i,j,r,p].findId(t)
                    thevars += [x[i,j,r,p,ID1]]
                    thecoefs += [Request[r].passengers]
                    intervals = joinIntervalLists(intervals,xDividers[i,j,r,p].ids[ID1])
                
                #thevars += [y[i,j,p, yDividers[i,j,p].findId(t)]]
                #thecoefs += [-Airplane[p].seats]

                
                thevars += [y[i,j,p,ID] for ID,intervalIter in yDividers[i,j,p].ids.iteritems() 
                             if doTheyIntersect(intervals,intervalIter)]
                thecoefs += [-Airplane[p].seats for ID,intervalIter in yDividers[i,j,p].ids.iteritems() 
                             if doTheyIntersect(intervals,intervalIter)]
                #thevars += [x[i,j,r,p,xDividers[i,j,r,p].findId(t)] for r in Request]
                #thecoefs += [Request[r].passengers for r in Request]
                
                constrCode=''
                for name in thevars:
                    constrCode+=name
                if not (constrCode in constrCodes):
                    model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                    constrCodes.append(constrCode)
    
    
    # intermediate stops for requests
    
    for r in Request:
        thevars = [x[i,j,r,p,ID] for i,j in Distance for p in Airplane for ID in xDividers[i,j,r,p].ids]
        thecoefs = [1.0 for i,j in Distance for p in Airplane for ID in xDividers[i,j,r,p].ids ]
        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [max_stops + 1])
    
    #TODO: Check fi the the max detour length is included
    #"""
    # fueling constraints
    """
    for i,j in Distance:
        for p in Airplane:
            constrCodes=[]
            for t in xrange(number_of_timesteps):
                #print i,j,p
                thevars = [z[i,j,p,zDividers[i,j,p].findId(t)],y[i,j,p,yDividers[i,j,p].findId(t)]]
                thecoefs = [1.0,Fuelconsumption[i,j,p] + Airplane[p].reserve_fuel - Airplane[p].max_fuel]
                
                constrCode=''
                for name in thevars:
                    constrCode+=name
                if not (constrCode in constrCodes):
                    model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                    constrCodes.append(constrCode)
    
    for j in Airport:
        for p in Airplane:
            constrCodes=[]
            for t in xrange(number_of_timesteps):
                #print j,p
                thevars=[]
                thecoefs=[]
                intervals=[]
                for i in Airport:
                    if (j!= i):
                        ID1=zDividers[i,j,p].findId(t)
                        thevars += [z[i,j,p,ID1]]
                        thecoefs += [1.0]
                        intervals = joinIntervalLists(intervals,zDividers[i,j,p].ids[ID1])
                #thevars = [z[i,j,p,zDividers[i,j,p].findId(t)] for i in Airport if (i,j) in Distance]
                #thecoefs = [1.0 for i in Airport if (i,j) in Distance]
                    
                    
                if j == Airplane[p].origin:
                    thevars.append(z_dep[p,zDepDividers[p].findId(t)])
                    #thevars.append(z_dep[p])
                    thecoefs.append(1.0)
                thevars += [z[j,k,p,ID] for k in Airport if (j,k) in Distance for ID,intervalsiter in zDividers[j,k,p].ids.iteritems() 
                                if doTheyIntersect(shiftList(intervals,Traveltime[j,k,p]),intervalsiter) ]    
                thecoefs += [-1.0 for k in Airport if (j,k) in Distance for ID,intervalsiter in zDividers[j,k,p].ids.iteritems() 
                                if doTheyIntersect(shiftList(intervals,Traveltime[j,k,p]),intervalsiter)]
                thevars += [y[j,k,p,ID] for k in Airport  if k!=j and (j,k) in Distance for ID ,intervalIter in yDividers[j,k,p].ids.iteritems()
                             if doTheyIntersect(shiftList(intervals,Traveltime[j,k,p]),intervalIter)]    
                thecoefs += [-Fuelconsumption[j,k,p] for k in Airport  if k!=j and (j,k) in Distance for ID ,intervalIter in yDividers[j,k,p].ids.iteritems()
                             if doTheyIntersect(shiftList(intervals,Traveltime[j,k,p]),intervalIter)]
                
                #for k in Airport:
                #    if (j,k) in Distance:
                #        thevars.append(z[j,k,p])
                #        thecoefs.append(-1.0)
                #        thevars.append(y[j,k,p])
                #        thecoefs.append(-Fuelconsumption[j,k,p])
                
                
                
                if j == Airplane[p].destination:
                    thevars.append(z_arr[p,zArrDividers[p].findId(t)])
                    thecoefs.append(-1.0)
                
                
                constrCode=''
                for name in thevars:
                    constrCode+=name
                if not (constrCode in constrCodes):  
                    constrCodes.append(constrCode)
                    if Airport[j].fuel[str(Airplane[p].required_fueltype)] == '0':
                        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
                    else:
                        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                    
    
    # weight limit (=max fuel)

    for i,j in Distance:
        for p in Airplane:
            constrCodes=[]
            for t in xrange(number_of_timesteps):
                #thevars = [x[i,j,r,p,xDividers[i,j,r,p].findId(t)] for r in Request if t >= Request[r].earliest_departure and t <=Request[r].latest_arrival]
                #thecoefs = [Request[r].weight for r in Request if t >= Request[r].earliest_departure and t <=Request[r].latest_arrival]
                thevars = [x[i,j,r,p,xDividers[i,j,r,p].findId(t)] for r in Request]
                thecoefs = [Request[r].weight for r in Request ]
                
                
                thevars.append(z[i,j,p,zDividers[i,j,p].findId(t)])
                thecoefs.append(1.0)
                thevars += [y[i,j,p,yDividers[i,j,p].findId(t)]]
                thecoefs.append(-min(Weightlimit[i,p].max_takeoff_weight - Airplane[p].reserve_fuel - Airplane[p].empty_weight + Fuelconsumption[i,j,p], Weightlimit[i,p].max_landing_weight - Airplane[p].reserve_fuel - Airplane[p].empty_weight))
                
                
                constrCode=''
                for name in thevars:
                    constrCode+=name
                if not (constrCode in constrCodes):  
                    constrCodes.append(constrCode)
                    model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                
    """
    # minimum number of fuelstops
    
    # objective function 
    
    model.objective.set_sense(model.objective.sense.minimize)
    
    
    # output model
    
    model.write("model.lp")
    
    
    # set callbacks
    
    #incumbent_cb = model.register_callback(CheckSolutuionCallback)
    #lazyconstraint_cb = model.register_callback(SubtourEliminationCallback)
    
    #incumbent_cb = model.register_callback(CheckSolutuionMIPCallback)
    #incumbent_cb.number_of_calls = 0
    
    
    # set parameters
    
    model.parameters.mip.strategy.heuristicfreq.set(-1)
    model.parameters.emphasis.mip.set(3) 
     
    # solve model
           
    try:
        model.solve()
        mipSolved=1
    except CplexSolverError, exc:
        print "** Exception: ",exc
    #TODO: 
    #Use solution to create mips for checking existence of timefree solution
        #1: Check if y-variables can be reconstructed.
         #If not: Adjust them and continue
        #2: Check if x-variables can be reconstructed
         #If not: Adjust them and continue
        #3: Check if f-variables can be reconstructed
         #If not: Adjust them and continue
        #4: Check if x-variables and f-variables can be reconstructed at the same time
        #If not: Adjust them and continue
    #If timefree solution exists mipSolve=1
    #else: add at least one Divider that changes number of variables

#model.write("model.sol")

# solution interpretation

solution = model.solution

print "Solution status = ", solution.get_status()

if solution.is_primal_feasible():
    print "Solution value = ", solution.get_objective_value()
else:
    print "No solution available."
solutionValues=model.solution.get_values()
idx2name = { j : n for j, n in enumerate(model.variables.get_names()) }
name2idx = { n : j for j, n in enumerate(model.variables.get_names()) }
name2solutionValue = { n : solutionValues[j] for j, n in enumerate(model.variables.get_names()) }
for key,val in y.iteritems():
    valStore=solutionValues[name2idx[val]]
    if valStore > 0.5:
        print(val+" %f" %valStore)
for key,val in y_arr.iteritems():
    valStore=solutionValues[name2idx[val]]
    if valStore > 0.5:
        print(val +" %f" %valStore)
for key,val in y_dep.iteritems():
    valStore=solutionValues[name2idx[val]]
    if valStore > 0.5:
        print(val +" %f" %valStore)
#print "calls of incumbent callback:",incumbent_cb.number_of_calls
for key,val in x.iteritems():
    valStore=solutionValues[name2idx[val]]
    if valStore > 0.5:
        print(val+" %f" % valStore)

