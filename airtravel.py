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
        self.add_turnover_time = int(add_turnover_time)
        self.reserve_fuel = float(reserve_fuel)
        self.contigence_ratio = float(contigence_ratio)

class AIRPORT(object):
    def __init__(self,turnover_time=None,maintenance=None):
        self.turnover_time = int(turnover_time)
        self.maintenance = int(maintenance)
        self.fuel = {}

class REQUEST(object):
    def __init__(self,origin=None,destination=None,earliest_departure_time=None,earliest_departure_day=None,latest_arrival_time=None,latest_arrival_day=None,passengers=None,weight=None):
        self.origin = origin
        self.destination = destination
        self.earliest_departure_time = int(earliest_departure_time)
        self.earliest_departure_day = int(earliest_departure_day)
        self.latest_arrival_time = int(latest_arrival_time)
        self.latest_arrival_day = int(latest_arrival_day)
        self.passengers = int(passengers)
        self.weight = float(weight)

        self.earliest_departure = 1440 * (self.earliest_departure_day - 1) + self.earliest_departure_time
        self.latest_arrival = 1440 * (self.latest_arrival_day - 1) + self.latest_arrival_time

class WEIGHTLIMIT(object):
    def __init__(self,max_takeoff_weight=None,max_landing_weight=None):
        self.max_takeoff_weight = float(max_takeoff_weight)
        self.max_landing_weight = float(max_landing_weight)

class DIVIDERCOLLECTION(object):
    def __init__(self,data,T):
        self.dividers=[Divider([T+1])]
        self.ids=self.generateIds()
    def addDivider(self,listOfPoints):
        if self.changesIntervals(listOfPoints):
            self.dividers.append(Divider(listOfPoints))
        self.ids=self.generateIds()
    def generateIds(self,T,lOP=None):
        ids={}
        for i in range(T):
            ids[self.findID(i,lOP)]=1
        return ids
    def findID(self,t,listOfPoints=None):
        idString=""
        if listOfPoints!=None:
            for divider in self.dividers+Divider(listOfPoints):
                idString+=str(divider.evaluate(t))
        else:
            for divider in self.dividers:
                idString+=str(divider.evaluate(t))
        return idString
    def changesIntervals(self,listOfPoints):
        if len(self.ids==len(self.generateIds(listOfPoints))):
            return 0
        else:
            return 1
        
class Divider():
    def __init__(self,listOfPoints):
        self.listOfPoints=listOfPoints
    def evaluate(self,t):
        for i,val in enumerate(self.listOfPoints):
            if t < val:
                return i % 2
        return (i+1) % 2
# prepare reading and parsing

comment_line = re.compile('#');

directory = sys.argv[1]


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
                delta_time = int(value)


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
        Traveltime[i,j,p] = int(math.floor(Distance[i,j] / ((Airplane[p].speed / 60) * 5)) * 5)

Fuelconsumption = {}

for p in Airplane:
    for i, j in Distance:
        Fuelconsumption[i,j,p] = math.ceil(Distance[i,j] * Airplane[p].fuel * Airplane[p].contigence_ratio);


# ----------------
# MODEL GENERATION
# ----------------



number_of_timesteps=100
# VARIABLES


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


zDividers={}

for i,j in Distance:
    for p in Airplane:
        zDividers[i,j,p]=DIVIDERCOLLECTION(number_of_timesteps)


zDepDividers={}
zArrDividers={}
for p in Airplane:
    zDepDividers[p]=DIVIDERCOLLECTION(number_of_timesteps)
    zArrDividers[p]=DIVIDERCOLLECTION(number_of_timesteps)

#main loop for creating sequence of loops
mipSolved=0

while(mipSolved==0):
    model = cplex.Cplex()
    x = {}
    for i,j in Distance:
        for r in Request:
            for p in Airplane:
                for ID in xDividers[i,j,r,p].ids:
                    x[i,j,r,p] = "x#" + i + "_" + j + "_" + r + "_" + p + "_"+ID
                    model.variables.add(obj = [0.01 * Distance[i,j]], names = [x[i,j,r,p]], lb = [0], ub = [1], types = ["B"])
    
    x_dep = {}
    
    for r in Request:
        for p in Airplane:
            x_dep[r,p] = "x_dep#" + r + "_" + p
            model.variables.add(names = [x_dep[r,p]], lb = [0], ub = [1], types = ["B"])
    
    x_arr = {}
    
    for r in Request:
        for p in Airplane:
            x_arr[r,p] = "x_arr#" + r + "_" + p
            model.variables.add(names = [x_arr[r,p]], lb = [0], ub = [1], types = ["B"])
    
    y = {}
    for i,j in Distance:
        for p in Airplane:
            y[i,j,p] = "y#" + i + "_" + j + "_" + p
            model.variables.add(obj = [Travelcost[i,j,p]], names = [y[i,j,p]], lb = [0], types = ["I"])
    
    z = {}
    
    for i,j in Distance:
        for p in Airplane:
            z[i,j,p] = "z#" + i + "_" + j + "_" + p
            model.variables.add(names = [z[i,j,p]], lb = [0], ub = [Airplane[p].max_fuel], types = ["C"])
    
    z_dep = {}
    
    for p in Airplane:
        
        z_dep[p] = "z_dep#" + p
        model.variables.add(names = [z_dep[p]], lb = [Airplane[p].departure_min_fuel], ub = [Airplane[p].departure_max_fuel], types = ["C"])
    
    z_arr = {}
    
    for p in Airplane:
        z_arr[p] = "z_arr#" + p
        model.variables.add(names = [z_arr[p]], lb = [Airplane[p].arrival_min_fuel], ub = [Airplane[p].arrival_max_fuel], types = ["C"])
    
    w = {}
    
    for i,j in Distance:
        for p in Airplane:
            w[i,j,p] = "w#" + i + "_" + j + "_" + p
            model.variables.add(names = [w[i,j,p]], lb = [0], types = ["C"])
    
    # CONSTRAINTS
    #TODO: Change constraints so that they are defined for each time variable,
    # to avoid unneccessary constraints track which constraints have been added and only add new ones
    # each request must depart
    
    for r in Request:
        thevars = []
        thecoefs = []
        for p in Airplane:
            thevars.append(x_dep[r,p])
            thecoefs.append(1.0);
        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
    
    
    # each request must arrive
    
    for r in Request:
        thevars = []
        thecoefs = []
        for p in Airplane:
            thevars.append(x_arr[r,p])
            thecoefs.append(1.0);
        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
    
    
    # request flow departure
    
    for r in Request:
        for p in Airplane:
            #print r,p
            thevars = [x_dep[r,p]]
            thecoefs = [-1.0]
            for j in Airport:
                if (j != Request[r].origin):
                    thevars.append(x[Request[r].origin,j,r,p])
                    thecoefs.append(1.0)
            model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
    
    
    # request flow arrival
    
    for r in Request:
        for p in Airplane:
            #print r,p
            thevars = [x_arr[r,p]]
            thecoefs = [-1.0]
            for i in Airport:
                if (i != Request[r].destination):
                    thevars.append(x[i,Request[r].destination,r,p])
                    thecoefs.append(1.0)
            model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
    
    
    # request flow (other than departure and arrival)
    
    for r in Request:
        for p in Airplane:
            for i in Airport:
                if (i != Request[r].origin and i != Request[r].destination):
                    #print r,p,i
                    thevars = [];
                    thecoefs = [];
                    for j in Airport:
                        if (i != j):
                            thevars.append(x[j,i,r,p])
                            thecoefs.append(-1.0)  
                            thevars.append(x[i,j,r,p])
                            thecoefs.append(1.0)
                    model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
    
    
    # airplane flow
    
    for p in Airplane:
        for i in Airport:
            #print p,i
            thevars = []
            thecoefs = []
            for j in Airport:
                if (i != j):
                    thevars.append(y[j,i,p])
                    thecoefs.append(-1.0);
                    thevars.append(y[i,j,p])
                    thecoefs.append(1.0);
            
            rhs_value = 0.0
            if (i == Airplane[p].origin):
                rhs_value += 1.0
            if (i == Airplane[p].destination):
                rhs_value -= 1.0
        
            model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [rhs_value])
    
    
    # airplane departure/arrival in case origin equals destination
    
    for p in Airplane:
        if (Airplane[p].origin == Airplane[p].destination):
            i = Airplane[p].origin
            
            thevars = []
            thecoefs = []
            
            for j in Airport:
                if (i != j):
                    thevars.append(y[i,j,p])
                    thecoefs.append(1.0);
            
            model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])
    
                    
    # seat limit
    
    for i,j in Distance:
        for p in Airplane:
            #print i,j,p
            thevars = [y[i,j,p]]
            thecoefs = [-Airplane[p].seats]
            for r in Request:
                thevars.append(x[i,j,r,p])
                thecoefs.append(Request[r].passengers)
            model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
    
    
    # intermediate stops for requests
    
    for r in Request:
        thevars = []
        thecoefs = []
        #print r
        for i,j in Distance:
            for p in Airplane:
                thevars.append(x[i,j,r,p]);
                thecoefs.append(1.0);
        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [max_stops + 1])
    
    
    # fueling constraints
    
    for i,j in Distance:
        for p in Airplane:
            #print i,j,p
            thevars = [z[i,j,p],y[i,j,p]]
            thecoefs = [1.0,Fuelconsumption[i,j,p] + Airplane[p].reserve_fuel - Airplane[p].max_fuel]
            model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
    
    for j in Airport:
        for p in Airplane:
            #print j,p
            thevars = []
            thecoefs = []
                
            for i in Airport:
                if (i,j) in Distance:
                    thevars.append(z[i,j,p])
                    thecoefs.append(1.0)
                
            if j == Airplane[p].origin:
                thevars.append(z_dep[p])
                thecoefs.append(1.0)
                
            for k in Airport:
                if (j,k) in Distance:
                    thevars.append(z[j,k,p])
                    thecoefs.append(-1.0)
                    thevars.append(y[j,k,p])
                    thecoefs.append(-Fuelconsumption[j,k,p])
                
            if j == Airplane[p].destination:
                thevars.append(z_arr[p])
                thecoefs.append(-1.0)
                
            if Airport[j].fuel[str(Airplane[p].required_fueltype)] == '0':
                model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
            else:
                model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
    
    
    # weight limit (=max fuel)
    
    for i,j in Distance:
        for p in Airplane:
            #print i,j,p
            thevars = [w[i,j,p]]
            thecoefs = [1.0]
    
            for r in Request:
                thevars.append(x[i,j,r,p])
                thecoefs.append(-Request[r].weight)
    
            thevars.append(z[i,j,p])
            thecoefs.append(-1.0)
            
            model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
    
    for i,j in Distance:
        for p in Airplane:
            #print i,j,p
            thevars = [w[i,j,p],y[i,j,p]]
            thecoefs = [1.0,-min(Weightlimit[i,p].max_takeoff_weight - Airplane[p].reserve_fuel - Airplane[p].empty_weight + Fuelconsumption[i,j,p], Weightlimit[i,p].max_landing_weight - Airplane[p].reserve_fuel - Airplane[p].empty_weight)]
    
            model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
            
    
    # minimum number of fuelstops
    
    for p in Airplane:
        if Airplane[p].origin == Airplane[p].destination:
            F = 0
        else:
            F = Fuelconsumption[Airplane[p].origin, Airplane[p].destination, p]
            
        if Airplane[p].departure_max_fuel - F < Airplane[p].arrival_min_fuel and Airport[Airplane[p].origin].fuel[str(Airplane[p].required_fueltype)] == '0':
            #print p
            thevars = []
            thecoefs = []
    
            for j in Airport:
                if Airport[j].fuel[str(Airplane[p].required_fueltype)] == '1':
                    for i in Airport:
                        if (i,j) in Distance:
                            thevars.append(y[i,j,p])
                            thecoefs.append(1.0)
            
            model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])
    
    for p in Airplane:
        if Airplane[p].origin == Airplane[p].destination:
            F = 0
        else:
            F = Fuelconsumption[Airplane[p].origin, Airplane[p].destination, p]
        
        if Airplane[p].departure_max_fuel - F < Airplane[p].arrival_min_fuel and Airport[Airplane[p].destination].fuel[str(Airplane[p].required_fueltype)] == '0':
            #print p
            thevars = []
            thecoefs = []
    
            for i in Airport:
                if Airport[i].fuel[str(Airplane[p].required_fueltype)] == '1':
                    for j in Airport:
                        if (i,j) in Distance:
                            thevars.append(y[i,j,p])
                            thecoefs.append(1.0)
            
            model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])
    
    
    # maximum number of arrivals/departures per airport
    
    for p in Airplane:
        for j in Airport:
            if Airport[j].fuel[str(Airplane[p].required_fueltype)] == '0':            
                count = 0
                
                for r in Request:
                    if Request[r].origin == i or Request[r].destination == i:
                        count += 1
    
                if j == Airplane[p].destination:
                    max_arr = count + 1
                else:
                    max_arr = count
                    
                if j == Airplane[p].origin:
                    max_dep = count + 1
                else:
                    max_dep = count
                
                thevars = []
                thecoefs = []
    
                for i in Airport:
                    if (i,j) in Distance:
                        thevars.append(y[i,j,p])
                        thecoefs.append(1.0)
        
                model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [max_arr])
                
                thevars = []
                thecoefs = []
    
                for k in Airport:
                    if (j,k) in Distance:
                        thevars.append(y[j,k,p])
                        thecoefs.append(1.0)
        
                model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [max_dep])
    
    
    
    # objective function 
    
    model.objective.set_sense(model.objective.sense.minimize)
    
    
    # output model
    
    model.write("model.lp")
    
    
    # set callbacks
    
    #incumbent_cb = model.register_callback(CheckSolutuionCallback)
    #lazyconstraint_cb = model.register_callback(SubtourEliminationCallback)
    
    incumbent_cb = model.register_callback(CheckSolutuionMIPCallback)
    incumbent_cb.number_of_calls = 0
    
    
    # set parameters
    
    model.parameters.mip.strategy.heuristicfreq.set(-1)
    model.parameters.emphasis.mip.set(3) 
     
    # solve model
           
    try:
        model.solve()
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

model.write("model.sol")

# solution interpretation

solution = model.solution

print "Solution status = ", solution.get_status()

if solution.is_primal_feasible():
    print "Solution value = ", solution.get_objective_value()
else:
    print "No solution available."

print "calls of incumbent callback:",incumbent_cb.number_of_calls


