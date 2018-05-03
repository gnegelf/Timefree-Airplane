#! /usr/bin/python

import re
if not 'cplex' in globals():
    print 'Loading cplex'
    import cplex
    from cplex.callbacks import IncumbentCallback
    from cplex.callbacks import LazyConstraintCallback
    from cplex.exceptions import CplexSolverError
import math
import time





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

class __PLANE__(object):
  def __init__(self,cost=None,seats=None,plane_departure=None,departure_min_fuel=None,
               departure_max_fuel=None,plane_arrival=None,arrival_min_fuel=None,
               arrival_max_fuel=None,required_fueltype=None,fuel=None,speed=None,
               max_fuel=None,empty_weight=None,add_turnover_time=None,reserve_fuel=None,
               contigence_ratio=None,pilot_weight=None):
    self.cost = float(cost)
    self.seats = int(seats)
    self.plane_departure = plane_departure
    self.origin = self.plane_departure
    self.departure_min_fuel = float(departure_min_fuel)
    self.departure_max_fuel = float(departure_max_fuel)
    self.plane_arrival = plane_arrival
    self.destination = self.plane_arrival
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
    self.pilot_weight = float(pilot_weight)

class __AIRPORT__(object):
  def __init__(self,turnover_time=None):
    self.turnover_time = int(turnover_time)
    self.fuel = {}

class __REQUEST__(object):
  def __init__(self,request_departure=None,request_arrival=None,earliest_departure_time=None,
               earliest_departure_day=None,latest_arrival_time=None,latest_arrival_day=None,
               passengers=None,weight=None,max_stops=None,max_detour=None):
    self.request_departure = request_departure
    self.request_arrival = request_arrival
    self.origin=self.request_departure
    self.destination=self.request_arrival
    self.earliest_departure_time = int(earliest_departure_time)
    self.earliest_departure_day = int(earliest_departure_day)
    self.latest_arrival_time = int(latest_arrival_time)
    self.latest_arrival_day = int(latest_arrival_day)
    self.passengers = int(passengers)
    self.weight = float(weight)
    self.max_stops = int(max_stops)
    self.max_detour = float(max_detour) 

    self.earliest_departure = 1440 * (self.earliest_departure_day - 1) + self.earliest_departure_time
    self.latest_arrival = 1440 * (self.latest_arrival_day - 1) + self.latest_arrival_time

class __WEIGHTLIMIT__(object):
  def __init__(self,max_takeoff_weight=None,max_landing_weight=None):
    self.max_takeoff_weight = float(max_takeoff_weight)
    self.max_landing_weight = float(max_landing_weight)

class __TRIP__(object):
  def __init__(self,distance=None):
    self.distance = float(distance)

class DIVIDERCOLLECTION(object):
    def __init__(self,min_time,max_time):
        self.min_time=min_time
        self.max_time=max_time
        self.dividers=[Divider([max_time])]
        #self.dividers=[Divider([i+1 for i in range(min_time,max_time)])]
        self.ids=self.generateIds()
    def addDivider(self,listOfPoints):
        LOP=[]
        for i in listOfPoints:
            if i>self.min_time and i<self.max_time:
                LOP+=[i]
        if LOP == []:
            print listOfPoints
            print("List out of divider range")
        else:
            if self.changesIntervals(LOP):
                self.dividers.append(Divider(LOP))
                print("Intervals changed")
            self.ids=self.generateIds()
    def generateIds(self,lOP=None):
        tol = 0.000001
        ids={}
        intervalbarriers=[self.min_time]
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
        prev=self.min_time
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
    def changesIntervals(self,listOfPoints):
        if len(self.ids)==len(self.generateIds(listOfPoints)):
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
directory='Testinstances/A2-LEO_A2-NAS'


debugModels=0
restart=0
useObjective=0



# ---------------------
# reading airplanes.dat
# ---------------------

print "reading '"+directory+"/airplanes.dat'"

file = open(directory+"/airplanes.dat", "r")
airplanes_data = file.read()
file.close()

entries = re.split("\n+", airplanes_data)

PLANE = {}

for line in entries:
  if comment_line.search(line) == None:
    datas = re.split("\s+", line)
    if len(datas) == 18:
      ID,cost,seats,plane_departure,departure_min_fuel,departure_max_fuel,plane_arrival,arrival_min_fuel,\
      arrival_max_fuel,required_fueltype,fuel,speed,max_fuel,empty_weight,add_turnover_time,reserve_fuel,\
      contigence_ratio,pilot_weight = datas
      PLANE[ID] = __PLANE__(cost,seats,plane_departure,departure_min_fuel,departure_max_fuel,plane_arrival,
           arrival_min_fuel,arrival_max_fuel,required_fueltype,fuel,speed,max_fuel,empty_weight,add_turnover_time,
           reserve_fuel,contigence_ratio,pilot_weight)


# --------------------
# reading airports.dat
# --------------------

print "reading '"+directory+"/airports.dat'"

file = open(directory+"/airports.dat", "r")
airports_data = file.read()
file.close()

entries = re.split("\n+", airports_data)

AIRPORT = {}

for line in entries:
  if comment_line.search(line) == None:
    datas = re.split("\s+", line)
    if len(datas) == 2:
      ID, turnover_time = datas
      AIRPORT[ID] = __AIRPORT__(turnover_time)




# ---------------------
# reading distances.dat
# ---------------------

print "reading '"+directory+"/distances.dat'"

file = open(directory+"/distances.dat", "r")
distances_data = file.read()
file.close()

entries = re.split("\n+", distances_data)

TRIP = {}

for line in entries:
  if comment_line.search(line) == None:
    datas = re.split("\s+", line)
    if len(datas) == 3:
      origin, destination, distance = datas
      TRIP[origin,destination] = float(distance)


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
      airport, fuelID, isAvailable = datas
      AIRPORT[airport].fuel[int(fuelID)] = isAvailable


# --------------------
# reading requests.dat
# --------------------

print "reading '"+directory+"/requests.dat'"

file = open(directory+"/requests.dat", "r")
requests_data = file.read()
file.close()

entries = re.split("\n+", requests_data)

REQUEST = {}

for line in entries:
  if comment_line.search(line) == None:
    datas = re.split("\s+", line)
    if len(datas) == 11:
      ID,origin,destination,earliest_departure_time,earliest_departure_day,\
      latest_arrival_time,latest_arrival_day,passengers,weight,max_stops,max_detour = datas
      REQUEST[ID] = __REQUEST__(origin,destination,earliest_departure_time,earliest_departure_day,latest_arrival_time,\
             latest_arrival_day,passengers,weight,max_stops,max_detour)


# ------------------------
# reading timedelta.dat
# ------------------------

print "reading '"+directory+"/timedelta.dat'"

file = open(directory+"/timedelta.dat", "r")
timedelta_data = file.read()
file.close()

entries = re.split("\n+", timedelta_data)

timedelta = 1

for line in entries:
  if comment_line.search(line) == None:
    datas = re.split("\s+", line)
    if len(datas) == 2:
      ID,timedelta = datas
      timedelta = int(timedelta) # conversion from string to int


# ------------------------
# reading weightlimits.dat
# ------------------------

print "reading '"+directory+"/weightlimits.dat'"

file = open(directory+"/weightlimits.dat", "r")
weightlimits_data = file.read()
file.close()

entries = re.split("\n+", weightlimits_data)

WEIGHTLIMIT = {}

for line in entries:
  if comment_line.search(line) == None:
    datas = re.split("\s+", line)
    if len(datas) == 4:
      airport, airplane, max_takeoff_weight, max_landing_weight = datas
      WEIGHTLIMIT[airport,airplane] = __WEIGHTLIMIT__(max_takeoff_weight,max_landing_weight)

# --------------------------------
# generating further instance data
# --------------------------------


#intermediate
turnover_timesteps = {}

for i in AIRPORT:
  for p in PLANE:
    turnover_timesteps[i,p] = int(max(1,math.ceil((AIRPORT[i].turnover_time + PLANE[p].add_turnover_time) / timedelta)))

# travelcost
travelcost = {}

for p in PLANE:
  for i, j in TRIP:
      if i == j:
          travelcost[i,j,p]=0.0001
      else:
          travelcost[i,j,p] = TRIP[i,j] * PLANE[p].cost
      


#intermediate
travel_time = {}

for p in PLANE:
  for i, j in TRIP:
    #travel_time[i,j,p] = int(math.floor(TRIP[i,j] / ((PLANE[p].speed / 60) * 5)) * 5)#TODO: why not ceil?
    travel_time[i,j,p] = TRIP[i,j] / (PLANE[p].speed / 60.0) 

#intermediate
travel_timesteps = {}

for p in PLANE:
  for i, j in TRIP:
    travel_timesteps[i,j,p] = int(max(1,math.ceil(travel_time[i,j,p] / timedelta)))




#actual delta
turnover_travel_timesteps = {}

for p in PLANE:
  for i, j in TRIP:
    if i == j:
      turnover_travel_timesteps[i,j,p] = 1
    else:
      turnover_travel_timesteps[i,j,p] = int(travel_timesteps[i,j,p] + turnover_timesteps[i,p])


max_takeoff_payload = {}

for p in PLANE:
  for i in AIRPORT:
    max_takeoff_payload[i,p] = WEIGHTLIMIT[i,p].max_takeoff_weight - PLANE[p].empty_weight - PLANE[p].reserve_fuel - PLANE[p].pilot_weight


max_landing_payload = {}

for p in PLANE:
  for i in AIRPORT:
    max_landing_payload[i,p] = WEIGHTLIMIT[i,p].max_landing_weight - PLANE[p].empty_weight - PLANE[p].reserve_fuel - PLANE[p].pilot_weight


fuelconsumption = {}

for p in PLANE:
  for i, j in TRIP:
    fuelconsumption[i,j,p] = math.ceil(travel_time[i,j,p] * PLANE[p].fuel * PLANE[p].speed * PLANE[p].contigence_ratio / 60.0);


max_trip_payload = {}

for p in PLANE:
  for i, j in TRIP:
    max_trip_payload[i,j,p] = min(max_takeoff_payload[i,p] + fuelconsumption[i,j,p], max_landing_payload[j,p])


max_trip_fuel = {}

for p in PLANE:
  for i, j in TRIP:
    max_trip_fuel[i,j,p] = PLANE[p].max_fuel - fuelconsumption[i,j,p] - PLANE[p].reserve_fuel


earliest_departure_travel_timesteps = {}

for p in PLANE:
  for i, j in TRIP:
    for r in REQUEST:
      earliest_departure_travel_timesteps[i,j,p,r] = math.ceil((REQUEST[r].earliest_departure_time + 60 * TRIP[i,j] / PLANE[p].speed) / timedelta)


earliest_departure_timesteps = {}

for r in REQUEST:
  earliest_departure_timesteps[r] = int(math.ceil((REQUEST[r].earliest_departure_time + 1440 * (REQUEST[r].earliest_departure_day - 1)) / timedelta))
  

latest_arrival_timesteps = {}

for r in REQUEST:
  latest_arrival_timesteps[r] = int(math.floor((REQUEST[r].latest_arrival_time + 1440 * (REQUEST[r].latest_arrival_day - 1)) / timedelta))

direct_flight_timesteps = {}

for p in PLANE:
  for r in REQUEST:
    if PLANE[p].plane_departure == REQUEST[r].request_departure:
      direct_flight_timesteps[p,r] = 0
    else:
      direct_flight_timesteps[p,r] = turnover_travel_timesteps[PLANE[p].plane_departure,REQUEST[r].request_departure,p]

    #print "direct_flight_timesteps plane ",p,", request ",r,": ",direct_flight_timesteps[p,r]

max_refuel_flight_timesteps = {}

for p in PLANE:
  for r in REQUEST:
    max_refuel_flight_timesteps[p,r] = 0
    
    for i in AIRPORT:
      if (AIRPORT[i].fuel[PLANE[p].required_fueltype] == '1' and i != PLANE[p].plane_departure and i != REQUEST[r].request_departure):
        aux = turnover_travel_timesteps[PLANE[p].plane_departure,i,p] + turnover_travel_timesteps[i,REQUEST[r].request_departure,p]
        max_refuel_flight_timesteps[p,r] = max(max_refuel_flight_timesteps[p,r],aux)

    #print "max_refuel_flight_timesteps plane ",p,", request ",r,": ",max_refuel_flight_timesteps[p,r]

plane_min_timestep = {}

for p in PLANE:
  plane_min_timestep[p] = 99999
  
  for r in REQUEST:
    if REQUEST[r].passengers <= PLANE[p].seats:
      aux = earliest_departure_timesteps[r] - turnover_timesteps[REQUEST[r].request_departure,p] - max(direct_flight_timesteps[p,r],
                                        max_refuel_flight_timesteps[p,r])
      plane_min_timestep[p] = int(min(plane_min_timestep[p],aux))

  #print "plane ",p," min timestep: ",plane_min_timestep[p]

plane_max_timestep = {}

for p in PLANE:
  plane_max_timestep[p] = 0
  
  for r in REQUEST:
    if REQUEST[r].passengers <= PLANE[p].seats:
      aux = latest_arrival_timesteps[r] + max(direct_flight_timesteps[p,r],max_refuel_flight_timesteps[p,r])
      plane_max_timestep[p] = int(max(plane_max_timestep[p],aux))

  #print "plane ",p," max timestep: ",plane_max_timestep[p]


TRIP0 = {}

for i,j in TRIP:
  if i != j:
    TRIP0[i,j] = TRIP[i,j]


REQUEST_TRIP = {}

for r in REQUEST:
  REQUEST_TRIP[r] = {}

  for i,j in TRIP:
    if i != REQUEST[r].request_arrival and j != REQUEST[r].request_departure:
      REQUEST_TRIP[r][i,j] = TRIP[i,j]


REQUEST_TRIP0 = {}

for r in REQUEST:
  REQUEST_TRIP0[r] = {}

  for i,j in TRIP0:
    if i != REQUEST[r].request_arrival and j != REQUEST[r].request_departure:
      REQUEST_TRIP0[r][i,j] = TRIP0[i,j]


min_refuel_trip = {}

for i in AIRPORT:
  for p in PLANE:
    min_refuel_trip[i,p] = 99999
    for j in AIRPORT:
      if (i,j) in TRIP:
        if AIRPORT[j].fuel[PLANE[p].required_fueltype] == '1':
          min_refuel_trip[i,p] = min(min_refuel_trip[i,p], fuelconsumption[i,j,p])

  
PLANE_TIMESTEP = {}

for p in PLANE:
  PLANE_TIMESTEP[p] = {}
  
  for t in range(plane_min_timestep[p], plane_max_timestep[p] + 1):
    PLANE_TIMESTEP[p][t] = 1
    

REQUEST_TIMESTEP = {}

for r in REQUEST:
  max_turnover_timesteps = 0
  for p in PLANE:
    max_turnover_timesteps = max(max_turnover_timesteps, turnover_timesteps[REQUEST[r].request_departure,p])
  
  REQUEST_TIMESTEP[r] = range(earliest_departure_timesteps[r] - max_turnover_timesteps, latest_arrival_timesteps[r] + 1)


min_timestep = 99999
max_timestep = 0

for p in PLANE:
  min_timestep = min(min_timestep, plane_min_timestep[p])
  max_timestep = max(max_timestep, plane_max_timestep[p])
  
TIMESTEP = range(min_timestep, max_timestep + 1)




# ----------------
# MODEL GENERATION
# ----------------
startTimes = {}
for i in AIRPORT:
    startTimes[i] = []
    for r in REQUEST:
        if REQUEST[r].origin == i:
            if not earliest_departure_timesteps[r] in startTimes[i]:
                startTimes[i].append(earliest_departure_timesteps[r])
    startTimes[i] = sorted(startTimes[i])
    


#"""
if not "yDividers" in globals() or restart:
    xDividers={}
    for i in AIRPORT:
        for p in PLANE:
            xDividers[i,p]=DIVIDERCOLLECTION(plane_min_timestep[p],plane_max_timestep[p]+1)
            for t in startTimes[i]:
                xDividers[i,p].addDivider([t])
    
    
    yDividers={}
    for i in AIRPORT:
        for p in PLANE:
            yDividers[i,p]=DIVIDERCOLLECTION(plane_min_timestep[p],plane_max_timestep[p]+1)
            for t in startTimes[i]:
                yDividers[i,p].addDivider([t])
    
    
    zDividers={}
    
    for i in AIRPORT:
        for p in PLANE:
            zDividers[i,p]=DIVIDERCOLLECTION(plane_min_timestep[p],plane_max_timestep[p]+1)
            for t in startTimes[i]:
                zDividers[i,p].addDivider([t])
#"""

    



if not ("pathModels" in globals()) or debugModels:
    pathModels = {}
    requestModels = {}
    fullModels = {}
    tR = {}
    tP = {}
    x2 = {}
    x_dep2 = {}
    x_arr2 = {}
    r2 = {}
    y2 = {}
    y_dep2 = {}
    y_arr2 = {}
    z2 = {}
    z_dep2 = {}
    z_arr2 = {}

    for p in PLANE:
        for r in REQUEST:
            tR[r,p] =  range(earliest_departure_timesteps[r],latest_arrival_timesteps[r]+turnover_timesteps[REQUEST[r].destination,p])
    

    
    for p in PLANE:    
        pathModels[p] = cplex.Cplex()
        requestModels[p] = cplex.Cplex()
        fullModels[p] = cplex.Cplex()
        #pathModels[p].set_results_stream('reconst.rlog')
        #requestModels[p].set_results_stream('reconst.rlog')
        #fullModels[p].set_results_stream('reconst.rlog')
        
        pathLines = []
        pathNames = []
        pathRhs = []
        pathSenses = []
        
        requestLines = []
        requestNames = []
        requestRhs = []
        requestSenses = []
        
        fullLines = []
        fullNames = []
        fullRhs = []
        fullSenses = []
        
        tP[p] = range(plane_min_timestep[p],plane_max_timestep[p]+1)
        
        
        #adding variables
        
        #request variables
        for i,j in TRIP:
            for r in REQUEST:
                for t in tR[r,p]:
                    x2[i,j,r,p,t] = "x#" + i + "_" + j + "_" + r + "_" + p + "_"+str(t)
                    requestModels[p].variables.add( names = [x2[i,j,r,p,t]], types = ["B"])
                    fullModels[p].variables.add( names = [x2[i,j,r,p,t]], types = ["B"])
        for r in REQUEST:
            for t in tR[r,p]:
                x_dep2[r,p,t] = "x_dep#" + r + "_" + p + "_" + str(t)
                requestModels[p].variables.add(names = [x_dep2[r,p,t]],  types = ["B"])
                fullModels[p].variables.add(names = [x_dep2[r,p,t]],  types = ["B"])
        for r in REQUEST:
            for t in tR[r,p]:
                x_arr2[r,p,t] = "x_arr#" + r + "_" + p + "_" + str(t)
                requestModels[p].variables.add(names = [x_arr2[r,p,t]], types = ["B"])
                fullModels[p].variables.add(names = [x_arr2[r,p,t]], types = ["B"])
        for r in REQUEST:
            r2[r,p] = "r_ass" + r + "_" + p
            requestModels[p].variables.add(names = [r2[r,p]], types = ["B"])
            fullModels[p].variables.add(names = [r2[r,p]], types = ["B"])
        
        
        
        #plane tour variables
        for i,j in TRIP:
            for t in tP[p]:
                y2[i,j,p,t] = "y#" + i + "_" + j + "_" + p + "_"+ str(t)
                pathModels[p].variables.add(names = [y2[i,j,p,t]], types = ["B"])
                requestModels[p].variables.add(names = [y2[i,j,p,t]], types = ["B"])
                fullModels[p].variables.add(names = [y2[i,j,p,t]], types = ["B"])
            y2[i,j,p] = "y#" + i + "_" + j + "_" + p
            pathModels[p].variables.add(names = [y2[i,j,p]], types = ["B"])
            requestModels[p].variables.add(names = [y2[i,j,p]], types = ["B"])
            fullModels[p].variables.add(names = [y2[i,j,p]], types = ["B"])
        for t in tP[p]:
            y_dep2[p,t] = "y_dep#" + p  + "_" + str(t)
            pathModels[p].variables.add(names = [y_dep2[p,t]], types = ["B"])
            requestModels[p].variables.add(names = [y_dep2[p,t]], types = ["B"])
            fullModels[p].variables.add(names = [y_dep2[p,t]], types = ["B"])
        for t in tP[p]:
            y_arr2[p,t] = "y_arr#" + p  + "_" + str(t)
            pathModels[p].variables.add(names = [y_arr2[p,t]], types = ["B"])
            requestModels[p].variables.add(names = [y_arr2[p,t]], types = ["B"])
            fullModels[p].variables.add(names = [y_arr2[p,t]], types = ["B"])
            
        
        
        
        #fuel variables
        for i,j in TRIP:
            for t in tP[p]:
                z2[i,j,p,t] = "z#" + i + "_" + j + "_" + p  + "_" + str(t)
                pathModels[p].variables.add(names = [z2[i,j,p,t]], lb = [0], ub = [PLANE[p].max_fuel], types = ["C"])
                fullModels[p].variables.add(names = [z2[i,j,p,t]], lb = [0], ub = [PLANE[p].max_fuel], types = ["C"])
        for t in tP[p]:
            z_dep2[p,t] = "z_dep#" + p  + "_" + str(t)
            pathModels[p].variables.add(names = [z_dep2[p,t]], lb = [0.0], ub = [PLANE[p].departure_max_fuel], types = ["C"])
            fullModels[p].variables.add(names = [z_dep2[p,t]], lb = [0.0], ub = [PLANE[p].departure_max_fuel], types = ["C"])
        for t in tP[p]:
            z_arr2[p,t] = "z_arr#" + p  + "_" +str(t)
            #pathModels[p].variables.add(names = [z_arr2[p,t]], lb = [PLANE[p].arrival_min_fuel], ub = [PLANE[p].arrival_max_fuel], types = ["C"])
            pathModels[p].variables.add(names = [z_arr2[p,t]], lb = [0.0], ub = [PLANE[p].arrival_max_fuel], types = ["C"])
            fullModels[p].variables.add(names = [z_arr2[p,t]], lb = [0.0], ub = [PLANE[p].arrival_max_fuel], types = ["C"])
        
        
        
        
        
        #Plane must depart
        thevars = [y_dep2[p,t] for t in tP[p]]
        thecoefs = [1.0 for t in tP[p]]

        
        #pathModels[p].linear_constraints.add(names = [p+' departure'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
        #requestModels[p].linear_constraints.add(names = [p+' departure'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
        #fullModels[p].linear_constraints.add(names = [p+' departure'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
        
        pathLines.append(cplex.SparsePair(thevars,thecoefs))
        pathSenses.append("E")
        pathRhs.append(1.0)
        pathNames.append(p+' departure')
        requestLines.append(cplex.SparsePair(thevars,thecoefs))
        requestSenses.append("E")
        requestRhs.append(1.0)
        requestNames.append(p+' departure')
        fullLines.append(cplex.SparsePair(thevars,thecoefs))
        fullSenses.append("E")
        fullRhs.append(1.0)
        fullNames.append(p+' departure')
        
        
        
        #Plane must arrive
        thevars = [y_arr2[p,t] for t in tP[p]]
        thecoefs = [1.0 for t in tP[p]]
        
        #pathModels[p].linear_constraints.add(names = [p+' arrival'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
        #requestModels[p].linear_constraints.add(names = [p+' arrival'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
        #fullModels[p].linear_constraints.add(names = [p+' arrival'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses=["E"], rhs=[1.0])
        
        pathLines.append(cplex.SparsePair(thevars,thecoefs))
        pathSenses.append("E")
        pathRhs.append(1.0)
        pathNames.append(p+' arrival')
        requestLines.append(cplex.SparsePair(thevars,thecoefs))
        requestSenses.append("E")
        requestRhs.append(1.0)
        requestNames.append(p+' arrival')
        fullLines.append(cplex.SparsePair(thevars,thecoefs))
        fullSenses.append("E")
        fullRhs.append(1.0)
        fullNames.append(p+' arrival')
        
   
        
        #Flow constraints for the planes
        for j in AIRPORT:
            for t in tP[p]:
                thevars=[]
                thecoefs=[]
                
                if (j  ==  PLANE[p].origin):
                    thevars.append(y_dep2[p,t])
                    thecoefs += [1.0]
                
                thevars += [y2[i,j,p,t] for i in AIRPORT ]
                thecoefs += [1.0 for i in AIRPORT ]
                
                thevars += [y2[j,k,p,t+turnover_travel_timesteps[j,k,p]] for k in AIRPORT
                                if t+turnover_travel_timesteps[j,k,p] <=  tP[p][-1]]
                
                thecoefs += [-1.0 for k in AIRPORT
                                if t+turnover_travel_timesteps[j,k,p] <=  tP[p][-1]]
        
                
                if (j  ==  PLANE[p].destination):
                    thevars.append(y_arr2[p,t])
                    thecoefs += [-1.0]
                    
                #pathModels[p].linear_constraints.add(names = [ j+'_'+p+'_'+str(t)+ ' flow'],
                #                                 lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
                #requestModels[p].linear_constraints.add(names = [ j+'_'+p+'_'+str(t)+ ' flow'],
                #                                 lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
                #fullModels[p].linear_constraints.add(names = [ j+'_'+p+'_'+str(t)+ ' flow'],
                #                                 lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
                pathLines.append(cplex.SparsePair(thevars,thecoefs))
                pathSenses.append("E")
                pathRhs.append(0.0)
                pathNames.append( j+'_'+p+'_'+str(t)+ ' flow')
                requestLines.append(cplex.SparsePair(thevars,thecoefs))
                requestSenses.append("E")
                requestRhs.append(0.0)
                requestNames.append( j+'_'+p+'_'+str(t)+ ' flow')
                fullLines.append(cplex.SparsePair(thevars,thecoefs))
                fullSenses.append("E")
                fullRhs.append(0.0)
                fullNames.append( j+'_'+p+'_'+str(t)+ ' flow')
        
        
        
        # each assigned REQUEST must depart and arrive
        for r in REQUEST:
            thevars = [ x_dep2[r,p,t] for t in tR[r,p] ]
            thecoefs = [ 1.0 for t in tR[r,p] ]
            
            thevars += [ r2[r,p] ]
            thecoefs += [ -1.0 ]
            
            #requestModels[p].linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
            #fullModels[p].linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
            
            requestLines.append(cplex.SparsePair(thevars,thecoefs))
            requestSenses.append("E")
            requestRhs.append(0.0)
            requestNames.append( r + 'request departure')
            fullLines.append(cplex.SparsePair(thevars,thecoefs))
            fullSenses.append("E")
            fullRhs.append(0.0)
            fullNames.append( r+'request departure')
            
            thevars = [ x_arr2[r,p,t] for t in tR[r,p] ]
            thecoefs = [ 1.0 for t in tR[r,p] ]
            
            thevars += [ r2[r,p] ]
            thecoefs += [ -1.0 ]
            
            #requestModels[p].linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
            #fullModels[p].linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
        
            requestLines.append(cplex.SparsePair(thevars,thecoefs))
            requestSenses.append("E")
            requestRhs.append(0.0)
            requestNames.append( r + ' request arrival')
            fullLines.append(cplex.SparsePair(thevars,thecoefs))
            fullSenses.append("E")
            fullRhs.append(0.0)
            fullNames.append( r+'request arrival')
        
        
        
        
        #REQUEST flow
        for r in REQUEST:
            for j in AIRPORT:
                for t in tR[r,p]:
                    thevars = []
                    thecoefs = []
        
                    if (j  ==  REQUEST[r].origin):
                        thevars.append(x_dep2[r,p,t])
                        thecoefs += [1.0]
                    
                    thevars += [x2[i,j,r,p,t] for i in AIRPORT ]
                    thecoefs += [1.0 for i in AIRPORT ]
                    
                    thevars += [x2[j,k,r,p,t+turnover_travel_timesteps[j,k,p]] for k in AIRPORT 
                                    if t+turnover_travel_timesteps[j,k,p] <=  tR[r,p][-1]]
                    thecoefs += [-1.0 for k in AIRPORT 
                                    if t+turnover_travel_timesteps[j,k,p] <=  tR[r,p][-1]]
        
                    if (j  ==  REQUEST[r].destination):
                        thevars.append(x_arr2[r,p,t])
                        thecoefs += [-1.0]
                    
                    #requestModels[p].linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
                    #fullModels[p].linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
    
                    requestLines.append(cplex.SparsePair(thevars,thecoefs))
                    requestSenses.append("E")
                    requestRhs.append(0.0)
                    requestNames.append( r+'_'+j+'_'+str(t)+' flow')
                    fullLines.append(cplex.SparsePair(thevars,thecoefs))
                    fullSenses.append("E")
                    fullRhs.append(0.0)
                    fullNames.append( r+'_'+j+'_'+str(t)+' flow')
        
        
        """
        #max detour
        for r in REQUEST:
            thevars = [ x2[i,j,r,p,t] for i,j in TRIP0 for t in tR[r,p] ]
            thecoefs = [ TRIP0[i,j]  for i,j in TRIP0 for t in tR[r,p] ]
            
            #requestModels[p].linear_constraints.add(names = [r+' max detour'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"],
            #                             rhs = [(1 + REQUEST[r].max_detour) * TRIP0[REQUEST[r].request_departure,REQUEST[r].request_arrival]])
            #fullModels[p].linear_constraints.add(names = [r+' max detour'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"],
            #                             rhs = [(1 + REQUEST[r].max_detour) * TRIP0[REQUEST[r].request_departure,REQUEST[r].request_arrival]])
            
            requestLines.append(cplex.SparsePair(thevars,thecoefs))
            requestSenses.append("L")
            requestRhs.append((1 + REQUEST[r].max_detour) * TRIP0[REQUEST[r].request_departure,REQUEST[r].request_arrival])
            requestNames.append( r+' detour')
            fullLines.append(cplex.SparsePair(thevars,thecoefs))
            fullSenses.append("L")
            fullRhs.append((1 + REQUEST[r].max_detour) * TRIP0[REQUEST[r].request_departure,REQUEST[r].request_arrival])
            fullNames.append( r+' detour')
        
        
        
        
        # seat limit
        for i,j in TRIP:
            for t in tP[p]:
                thevars = [ y2[i,j,p,t] ]
                thecoefs = [ -PLANE[p].seats ]
                
                thevars += [ x2[i,j,r,p,t] for r in REQUEST if t >= tR[r,p][0] and t <= tR[r,p][-1] ]
                thecoefs += [ REQUEST[r].passengers  for r in REQUEST if t >= tR[r,p][0] and t <= tR[r,p][-1] ]
                
                #requestModels[p].linear_constraints.add( lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                #fullModels[p].linear_constraints.add( lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
        
                requestLines.append(cplex.SparsePair(thevars,thecoefs))
                requestSenses.append("L")
                requestRhs.append(0.0)
                requestNames.append( i+'_'+j+'_'+str(t)+' seat limit')
                fullLines.append(cplex.SparsePair(thevars,thecoefs))
                fullSenses.append("L")
                fullRhs.append(0.0)
                fullNames.append( i+'_'+j+'_'+str(t)+' seat limit')
        
        
        
        
        # intermediate stops for REQUESTs
        for r in REQUEST:
            thevars = [ x2[i,j,r,p,t] for i,j in TRIP0 for t in tR[r,p] ]
            thecoefs = [ 1.0 for i,j in TRIP0 for t in tR[r,p] ]
            
            #requestModels[p].linear_constraints.add(names = [r+' stop limit'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], 
            #            senses = ["L"], rhs = [REQUEST[r].max_stops + 1])
            #fullModels[p].linear_constraints.add(names = [r+' stop limit'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], 
            #            senses = ["L"], rhs = [REQUEST[r].max_stops + 1])
            
            requestLines.append(cplex.SparsePair(thevars,thecoefs))
            requestSenses.append("L")
            requestRhs.append(REQUEST[r].max_stops + 1)
            requestNames.append( r+' stop limit')
            fullLines.append(cplex.SparsePair(thevars,thecoefs))
            fullSenses.append("L")
            fullRhs.append(REQUEST[r].max_stops + 1)
            fullNames.append( r+' stop limit')
        
        
        
        """
        # no flight no fuel
        for i,j in TRIP:
            for t in tP[p]:   
                thevars = [ y2[i,j,p,t]]
                thecoefs = [ -max_trip_fuel[i,j,p] ]
                
                thevars += [ z2[i,j,p,t] ]
                thecoefs += [ 1.0 ]
                
                #pathModels[p].linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                #fullModels[p].linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
        
                pathLines.append(cplex.SparsePair(thevars,thecoefs))
                pathSenses.append("L")
                pathRhs.append(0.0)
                pathNames.append( i+'_'+j+'_'+str(t)+ ' fuel bound')

                fullLines.append(cplex.SparsePair(thevars,thecoefs))
                fullSenses.append("L")
                fullRhs.append(0.0)
                fullNames.append( i+'_'+j+'_'+str(t)+ ' fuel bound')
        
        #no arrival no fuel
        for t in tP[p]:        
            thevars = [y_arr2[p,t],z_arr2[p,t]]
            thecoefs = [-PLANE[p].arrival_min_fuel,1.0]
            
            pathLines.append(cplex.SparsePair(thevars,thecoefs))
            pathSenses.append("G")
            pathRhs.append(0.0)
            pathNames.append(p+' arrival fuel bound')
            fullLines.append(cplex.SparsePair(thevars,thecoefs))
            fullSenses.append("G")
            fullRhs.append(0.0)
            fullNames.append(p+' arrival fuel bound')
            
            thevars = [y_arr2[p,t],z_arr2[p,t]]
            thecoefs = [-PLANE[p].arrival_max_fuel,1.0]
            
            pathLines.append(cplex.SparsePair(thevars,thecoefs))
            pathSenses.append("L")
            pathRhs.append(0.0)
            pathNames.append(p+' arrival fuel bound2')
            fullLines.append(cplex.SparsePair(thevars,thecoefs))
            fullSenses.append("L")
            fullRhs.append(0.0)
            fullNames.append(p+' arrival fuel bound2')
        #no departure no fuel
        for t in tP[p]:        
            thevars = [y_dep2[p,t],z_dep2[p,t]]
            thecoefs = [-PLANE[p].departure_min_fuel,1.0]
            
            pathLines.append(cplex.SparsePair(thevars,thecoefs))
            pathSenses.append("G")
            pathRhs.append(0.0)
            pathNames.append(p+' departure fuel bound')
            fullLines.append(cplex.SparsePair(thevars,thecoefs))
            fullSenses.append("G")
            fullRhs.append(0.0)
            fullNames.append(p+' departure fuel bound') 
            
            thevars = [y_dep2[p,t],z_dep2[p,t]]
            thecoefs = [-PLANE[p].departure_max_fuel,1.0]
            
            pathLines.append(cplex.SparsePair(thevars,thecoefs))
            pathSenses.append("L")
            pathRhs.append(0.0)
            pathNames.append(p+' departure fuel bound2')
            fullLines.append(cplex.SparsePair(thevars,thecoefs))
            fullSenses.append("L")
            fullRhs.append(0.0)
            fullNames.append(p+' departure fuel bound2') 
        
        
        
        
        #fuel flow constraints
        for j in AIRPORT:
            for t in tP[p]:
                thevars=[]
                thecoefs=[]
                
                if (j  ==  PLANE[p].origin):
                    thevars.append(z_dep2[p,t])
                    thecoefs += [1.0]
                
                thevars += [ z2[i,j,p,t] for i in AIRPORT ]
                thecoefs += [ 1.0 for i in AIRPORT ]
                
                thevars += [ z2[j,k,p,t+turnover_travel_timesteps[j,k,p]] for k in AIRPORT 
                                if t+turnover_travel_timesteps[j,k,p] <=  tP[p][-1] ]
                thecoefs += [ -1.0 for k in AIRPORT 
                                if t+turnover_travel_timesteps[j,k,p] <=  tP[p][-1] ]
                
                thevars += [ y2[j,k,p,t+turnover_travel_timesteps[j,k,p]] for k in AIRPORT 
                                if t+turnover_travel_timesteps[j,k,p] <=  tP[p][-1] ]
                thecoefs += [ -fuelconsumption[j,k,p] for k in AIRPORT 
                                if t+turnover_travel_timesteps[j,k,p] <=  tP[p][-1] ]
                
                if (j  ==  PLANE[p].destination):
                    thevars.append(z_arr2[p,t])
                    thecoefs += [-1.0]
                
                if AIRPORT[j].fuel[PLANE[p].required_fueltype] == '0':    
                    #pathModels[p].linear_constraints.add(names = [ j+'_'+p+'_'+str(t)+ 'fuel flow'],
                    #                                 lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
                    #fullModels[p].linear_constraints.add(names = [ j+'_'+p+'_'+str(t)+ 'fuel flow'],
                    #                                 lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
                    
                    pathLines.append(cplex.SparsePair(thevars,thecoefs))
                    pathSenses.append("E")
                    pathRhs.append(0.0)
                    pathNames.append( j+'_'+str(t)+ ' fuel flow')
    
                    fullLines.append(cplex.SparsePair(thevars,thecoefs))
                    fullSenses.append("E")
                    fullRhs.append(0.0)
                    fullNames.append( j+'_'+str(t)+ ' fuel flow')
                else:
                    #pathModels[p].linear_constraints.add(names = [ j+'_'+p+'_'+str(t)+ 'fuel flow'],
                    #                                 lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                    #fullModels[p].linear_constraints.add(names = [ j+'_'+p+'_'+str(t)+ 'fuel flow'],
                    #                                 lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                    
                    pathLines.append(cplex.SparsePair(thevars,thecoefs))
                    pathSenses.append("L")
                    pathRhs.append(0.0)
                    pathNames.append( j+'_'+str(t)+ ' fuel flow refuel')
    
                    fullLines.append(cplex.SparsePair(thevars,thecoefs))
                    fullSenses.append("L")
                    fullRhs.append(0.0)
                    fullNames.append( j+'_'+str(t)+ ' fuel flow refuel')
                    
        
        
        
        #weight limit constraints
        for i,j in TRIP:
            for t in tP[p]:
                
                thevars = [ y2[i,j,p,t] ]
                thecoefs = [ -max_trip_payload[i,j,p] ]
                
                thevars += [ z2[i,j,p,t] ]
                thecoefs += [ 1.0 ]
                
                thevars += [x2[i,j,r,p,t] for r in REQUEST if t >= tR[r,p][0] and t <= tR[r,p][-1] ]
                thecoefs += [REQUEST[r].weight for r in REQUEST if t >= tR[r,p][0] and t <= tR[r,p][-1] ]
                
    
                #fullModels[p].linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])  
                
                fullLines.append(cplex.SparsePair(thevars,thecoefs))
                fullSenses.append("L")
                fullRhs.append(0.0)
                fullNames.append( i+'_'+j+'_'+str(t)+ ' weight limit')
       
        
        
        
        #set arcs from timefree
        for i,j in TRIP:
            thevars = [ y2[i,j,p,t] for t in tP[p] ]+[ y2[i,j,p] ]
            thecoefs = [ 1.0 for t in tP[p] ] + [ -1.0 ]
            
            pathLines.append(cplex.SparsePair(thevars,thecoefs))
            pathSenses.append("E")
            pathRhs.append(0.0)
            pathNames.append( i+'_'+j+ ' set arc to val')
            requestLines.append(cplex.SparsePair(thevars,thecoefs))
            requestSenses.append("E")
            requestRhs.append(0.0)
            requestNames.append( i+'_'+j+ ' set arc to val')
            fullLines.append(cplex.SparsePair(thevars,thecoefs))
            fullSenses.append("E")
            fullRhs.append(0.0)
            fullNames.append( i+'_'+j+ ' set arc to val')
        
        
        print "Adding constraints to the fully expanded models"         
        pathModels[p].linear_constraints.add(names=pathNames,lin_expr = pathLines,senses = pathSenses, rhs = pathRhs)
        requestModels[p].linear_constraints.add(names=requestNames,lin_expr = requestLines,senses = requestSenses, rhs = requestRhs)
        fullModels[p].linear_constraints.add(names=fullNames,lin_expr = fullLines,senses = fullSenses, rhs = fullRhs)

time_finished = time.clock()



if restart:
    oldObjective=0



#main loop for creating sequence of loops
mipSolved = 0
while(mipSolved == 0):
    
    model = cplex.Cplex()
    xStartTimeIds = {}
    yStartTimeIds = {}
    zStartTimeIds = {}
    for p in PLANE:
        for i in AIRPORT:
            xStartTimeIds[i,p] = { t:xDividers[i,p].findId(t) for t in startTimes[i] }
            yStartTimeIds[i,p] = { t:yDividers[i,p].findId(t) for t in startTimes[i] }
            zStartTimeIds[i,p] = { t:zDividers[i,p].findId(t) for t in startTimes[i] }
    
    #request variables
    x = {}
    for i,j in TRIP0:
        for r in REQUEST:
            for p in PLANE:
                for ID1,intervalIter1 in xDividers[i,p].ids.iteritems():
                    for ID2,intervalIter2 in xDividers[j,p].ids.iteritems():
                        if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p])):
                            x[i,j,r,p,ID1,ID2] = "x#" + i + "_" + j + "_" + r + "_" + p + "_"+ID1+ "_"+ID2
                            ub=1
                            if (max(intervalIter1) < earliest_departure_timesteps[r] 
                                 or min(intervalIter2) > latest_arrival_timesteps[r]):
                                ub=0
                            model.variables.add(obj = [0.0001], names = [x[i,j,r,p,ID1,ID2]], lb = [0], ub = [ub], types = ["B"])
    xPredecessorIds = {}
    xSuccessorIds = {}
    for i in AIRPORT:
        for p in PLANE:
            xSuccessorIds[i,p] = {}
            xPredecessorIds[i,p] = { ID:[] for t,ID in xStartTimeIds[i,p].iteritems() }
            for ID1,intervalIter1 in xDividers[i,p].ids.iteritems():
                ID2=-1
                for depTime in startTimes[i]:
                    if min(intervalIter1) < depTime:
                        ID2 = xDividers[i,p].findId(depTime)
                if ID2 == -1:
                    continue
                xSuccessorIds[i,p][ID1] = ID2
                xPredecessorIds[i,p][ID2].append(ID1)
                for r in REQUEST:
                    x[i,i,r,p,ID1,ID2] = "x#" + i +  "_" + i + "_" + r + "_" + p + "_"+ID1+ "_"+ID2
                    
                    ub=1
                    model.variables.add(obj = [0.0001], names = [x[i,i,r,p,ID1,ID2]], lb = [0], ub = [ub], types = ["B"])
                            
    x_dep = {}
    for r in REQUEST:
        for p in PLANE:
            for ID in xDividers[REQUEST[r].origin,p].ids:
                x_dep[r,p,ID] = "x_dep#" + r + "_" + p + "_" + ID
                model.variables.add(names = [x_dep[r,p,ID]], lb = [0], ub = [1], types = ["B"])
    x_arr = {}
    for r in REQUEST:
        for p in PLANE:
            for ID in xDividers[REQUEST[r].destination,p].ids:
                x_arr[r,p,ID] = "x_arr#" + r + "_" + p + "_" + ID
                model.variables.add(names = [x_arr[r,p,ID]], lb = [0], ub = [1], types = ["B"])
    
    
    
    
    #plane tour variables
    y = {}
    for i,j in TRIP0:
        for p in PLANE:
            for ID1,intervalIter1 in yDividers[i,p].ids.iteritems():
                for ID2,intervalIter2 in yDividers[j,p].ids.iteritems():
                    if not(i == j and ID1 ==ID2):
                        if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p])):
                            y[i,j,p,ID1,ID2] = "y#" + i + "_" + j + "_" + p + "_"+ ID1+ "_"+ID2
                            model.variables.add(obj = [travelcost[i,j,p]], names = [y[i,j,p,ID1,ID2]], lb = [0], types = ["I"])
    yPredecessorIds = {}
    ySuccessorIds = { }
    for i in AIRPORT:
        for p in PLANE:
            ySuccessorIds[i,p] = {}
            yPredecessorIds[i,p] = { ID:[] for t,ID in yStartTimeIds[i,p].iteritems() }
            for ID1,intervalIter1 in yDividers[i,p].ids.iteritems():
                ID2=-1
                for depTime in startTimes[i]:
                    if min(intervalIter1) < depTime:
                        ID2=yDividers[i,p].findId(depTime)
                if ID2 == -1:
                    continue
                ySuccessorIds[i,p][ID1] = ID2
                yPredecessorIds[i,p][ID2].append(ID1)
                y[i,i,p,ID1,ID2] = "y#" + i + "_" + i + "_" + p + "_"+ ID1+ "_"+ID2
                model.variables.add(obj = [travelcost[i,i,p]], names = [y[i,i,p,ID1,ID2]], lb = [0], types = ["I"])
                
    y_dep = {}
    for p in PLANE:
        for ID in yDividers[PLANE[p].origin,p].ids:
            y_dep[p,ID] = "y_dep#" + p  + "_" + ID
            model.variables.add(names = [y_dep[p,ID]], lb = [0.0], ub = [1.0], types = ["B"])
    y_arr = {}
    for p in PLANE:
        for ID in yDividers[PLANE[p].destination,p].ids:
            y_arr[p,ID] = "y_arr#" + p  + "_" + ID
            model.variables.add(names = [y_arr[p,ID]], lb = [0.0], ub = [1.0], types = ["B"])

    
    
    
    #fuel variables
    z = {}
    for i,j in TRIP0:
        for p in PLANE:
            for ID1,intervalIter1 in zDividers[i,p].ids.iteritems():
                for ID2,intervalIter2 in zDividers[j,p].ids.iteritems():
                    if not(i == j and ID1 ==ID2):
                        if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p])):
                            z[i,j,p,ID1,ID2] = "z#" + i + "_" + j + "_" + p  + "_" + ID1+ "_"+ID2
                            model.variables.add(names = [z[i,j,p,ID1,ID2]], lb = [0], ub = [PLANE[p].max_fuel], types = ["C"])
    zPredecessorIds = {}
    zSuccessorIds = { }
    for i in AIRPORT:
        for p in PLANE:
            zSuccessorIds[i,p] = {}
            zPredecessorIds[i,p] = { ID:[] for t,ID in zStartTimeIds[i,p].iteritems() }
            for ID1,intervalIter1 in zDividers[i,p].ids.iteritems():
                ID = -1
                for depTime in startTimes[i]:
                    if min(intervalIter1) < depTime:
                        ID = zDividers[i,p].findId(depTime)
                if ID == -1 or ID == ID1:
                    continue
                zSuccessorIds[i,p][ID1] = ID
                zPredecessorIds[i,p][ID].append(ID1)
                z[i,i,p,ID1,ID] = "z#" + i + "_" + i + "_" + p  + "_" + ID1+ "_"+ID2
                model.variables.add(names = [z[i,i,p,ID1,ID]], lb = [0], ub = [PLANE[p].max_fuel], types = ["C"])
    z_dep = {}
    for p in PLANE:
        for ID in zDividers[PLANE[p].origin,p].ids:
            z_dep[p,ID] = "z_dep#" + p  + "_" + ID
            model.variables.add(names = [z_dep[p,ID]], lb = [0.0], ub = [PLANE[p].departure_max_fuel], types = ["C"])
    z_arr = {}
    for p in PLANE:
        for ID in zDividers[PLANE[p].destination,p].ids:
            z_arr[p,ID] = "z_arr#" + p  + "_" + ID
            model.variables.add(names = [z_arr[p,ID]], lb = [0.0], ub = [PLANE[p].arrival_max_fuel], types = ["C"])
    
        
    
    
    
    #lower bound for old objective
    if useObjective:
        thevars = [ y[i,j,p,ID1,ID2] for i,j in TRIP0 for p in PLANE for ID1,intervalIter1 in yDividers[i,p].ids.iteritems()
                    for ID2,intervalIter2 in yDividers[j,p].ids.iteritems()
                         if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p]))]
        thecoefs = [ travelcost[i,j,p] for i,j in TRIP0 for p in PLANE for ID1,intervalIter1 in yDividers[i,p].ids.iteritems()
                    for ID2,intervalIter2 in yDividers[j,p].ids.iteritems()
                        if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p]))]
        for i in AIRPORT:
            for p in PLANE:
                for ID1,intervalIter1 in yDividers[i,p].ids.iteritems():
                     for ID2 in ySuccessorIds[i,p][ID1]:
                         thevars += [ y[i,i,p,ID1,ID2] ]
                         thecoefs += [ travelcost[i,i,p] ]
       
        model.linear_constraints.add(names = ['lower bound from last run'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], 
                                     senses = ["G"], rhs = [oldObjective-0.5])
    
    
    
    
    #each plane must depart and arrive
    for p in PLANE:
        thevars = [ y_dep[p,ID] for ID in yDividers[PLANE[p].origin,p].ids ]
        thecoefs = [ 1.0 for ID in yDividers[PLANE[p].origin,p].ids ]
        model.linear_constraints.add(names = [p+' departure'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
        thevars = [ y_arr[p,ID] for ID in yDividers[PLANE[p].destination,p].ids ]
        thecoefs = [ 1.0 for ID in yDividers[PLANE[p].destination,p].ids ]
        
        model.linear_constraints.add(names = [p+' arrival'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
    
    
    
    
    #not too long tours cutting plane
    for p in PLANE:
        thevars = [y[i,j,p,ID1,ID2] for i,j in TRIP0 for ID1,intervalIter1 in yDividers[i,p].ids.iteritems() 
                    for ID2,intervalIter2 in yDividers[j,p].ids.iteritems() if 
                    doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p]))]
        thecoefs = [turnover_travel_timesteps[i,j,p] for i,j in TRIP0 for ID1,intervalIter1 in yDividers[i,p].ids.iteritems()  
                    for ID2,intervalIter2 in yDividers[j,p].ids.iteritems() if 
                    doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p]))]
        for i in AIRPORT:
            for p in PLANE:
                for ID1,intervalIter1 in yDividers[i,p].ids.iteritems():
                    if ySuccessorIds[i,p].has_key(ID1):
                        ID2 = ySuccessorIds[i,p][ID1]
                        thevars += [ y[i,i,p,ID1,ID2] ]
                        thecoefs += [ turnover_travel_timesteps[i,i,p] ]
        
        model.linear_constraints.add(names = [p+' length cutting plane'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"],
                                     rhs = [plane_max_timestep[p]-plane_min_timestep[p]])
        
    
    
    
    #PLANE flow
    for j in AIRPORT:
        for p in PLANE:
            for ID1,intervalIter1 in yDividers[j,p].ids.iteritems():
                thevars = []
                thecoefs = []

                if (j == PLANE[p].origin):
                    thevars.append(y_dep[p,ID1])
                    thecoefs += [1.0]
                
                thevars += [y[i,j,p,ID2,ID1] for i in AIRPORT  for ID2,intervalIter2 in yDividers[i,p].ids.iteritems() 
                                if not(i==j)
                                and doTheyIntersect(intervalIter2,shiftList(intervalIter1,-turnover_travel_timesteps[i,j,p]))]
                thecoefs += [1.0 for i in AIRPORT for ID2,intervalIter2 in yDividers[i,p].ids.iteritems() if not(i==j)
                                and doTheyIntersect(intervalIter2,shiftList(intervalIter1,-turnover_travel_timesteps[i,j,p]))]
                
                thevars += [y[j,k,p,ID1,ID2] for k in AIRPORT for ID2,intervalIter2 in yDividers[k,p].ids.iteritems() 
                                if not(k==j)
                                and doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[j,k,p]))]
                thecoefs += [-1.0 for k in AIRPORT for ID2,intervalIter2 in yDividers[k,p].ids.iteritems() if not(k==j)
                                and doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[j,k,p]))]

                if ID1 in yStartTimeIds[j,p].values():
                    for ID2 in yPredecessorIds[j,p][ID1]:
                        thevars += [ y[j,j,p,ID2,ID1] ]
                        thecoefs += [ 1.0 ]
                
                if ySuccessorIds[j,p].has_key(ID1):
                    thevars += [ y[j,j,p,ID1,ySuccessorIds[j,p][ID1]] ]
                    thecoefs += [ -1.0 ]
                    
                if (j == PLANE[p].destination):
                    thevars.append(y_arr[p,ID1])
                    thecoefs += [-1.0]

                model.linear_constraints.add(names = [ j+'_'+p+'_'+ID1+ ' flow'],
                                                 lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
    
    
    
    
    #even if origin and destination are the same does the plane have to depart
    for p in PLANE:
        if (PLANE[p].origin == PLANE[p].destination):
            ori = PLANE[p].origin
            
            thevars = [y[ori,j,p,ID1,ID2] for j in AIRPORT if ori!=j for ID1,intervalIter1 in yDividers[ori,p].ids.iteritems()
                                          for ID2,intervalIter2 in yDividers[j,p].ids.iteritems()
                                           if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[ori,j,p]))]
            thecoefs = [1.0]*len(thevars)
            
            model.linear_constraints.add(names = [p+' must depart'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])
    
    
    
    
    # each REQUEST must depart and arrive
    for r in REQUEST:
        thevars = [x_dep[r,p,ID] for p in PLANE for ID in xDividers[REQUEST[r].origin,p].ids]
        thecoefs = [1.0 for p in PLANE for ID in xDividers[REQUEST[r].origin,p].ids]
        
        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
        
        thevars = [x_arr[r,p,ID] for p in PLANE for ID in xDividers[REQUEST[r].destination,p].ids]
        thecoefs = [1.0 for p in PLANE for ID in xDividers[REQUEST[r].destination,p].ids]
        
        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
    
    
    
    
    #request flow constraints
    for r in REQUEST:
        for p in PLANE:
            for j in AIRPORT:
                for ID1,intervalIter1 in xDividers[j,p].ids.iteritems():
                    thevars = []
                    thecoefs = []
                    
                    if (j == REQUEST[r].origin):
                        thevars.append(x_dep[r,p,ID1])
                        thecoefs += [1.0]
                    
                    thevars += [ x[i,j,r,p,ID2,ID1] for i in AIRPORT for ID2,intervalIter2 in xDividers[i,p].ids.iteritems() if not(i==j)
                                    and doTheyIntersect(intervalIter2,shiftList(intervalIter1,-turnover_travel_timesteps[i,j,p]))]
                    thecoefs += [ 1.0 for i in AIRPORT for ID2,intervalIter2 in xDividers[i,p].ids.iteritems() if not(i==j)
                                    and doTheyIntersect(intervalIter2,shiftList(intervalIter1,-turnover_travel_timesteps[i,j,p]))]
                    
                    thevars +=[ x[j,k,r,p,ID1,ID2] for k in AIRPORT  for ID2,intervalIter2 in xDividers[k,p].ids.iteritems()if not(j==k)
                                    and doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[j,k,p]))]
                    
                    thecoefs += [ -1.0 for k in AIRPORT for ID2,intervalIter2 in xDividers[k,p].ids.iteritems()if not(j==k)
                                    and doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[j,k,p]))]
    
                    if (j == REQUEST[r].destination):
                        thevars.append(x_arr[r,p,ID1])
                        thecoefs += [-1.0]
                    
                    if ID1 in xStartTimeIds[j,p].values():
                        for ID2 in xPredecessorIds[j,p][ID1]:
                            thevars += [ x[j,j,r,p,ID2,ID1] ]
                            thecoefs += [ 1.0 ]
                    if xSuccessorIds[j,p].has_key(ID1):
                        thevars += [ x[j,j,r,p,ID1,xSuccessorIds[j,p][ID1]] ]
                        thecoefs += [ -1.0 ]

                    model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
    
    
    
    
    #max detour
    for r in REQUEST:
        thevars = [x[i,j,r,p,ID1,ID2] for p in PLANE for i,j in TRIP0 for ID1,intervalIter1 in xDividers[i,p].ids.iteritems() 
                    for ID2,intervalIter2 in xDividers[j,p].ids.iteritems()  
                    if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p]))]
        thecoefs = [TRIP0[i,j]  for p in PLANE for i,j in TRIP0 for ID1,intervalIter1 in xDividers[i,p].ids.iteritems()  
                    for ID2,intervalIter2 in xDividers[j,p].ids.iteritems()  
                    if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p]))]
        
        model.linear_constraints.add(names = [r+' max detour'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"],
                                     rhs = [(1 + REQUEST[r].max_detour) * TRIP0[REQUEST[r].request_departure,REQUEST[r].request_arrival]])
    
    
    
    
    # seat limit
    for i,j in TRIP0:
        for p in PLANE:
            for ID1,intervalIter1 in xDividers[i,p].ids.iteritems():
                for ID2,intervalIter2 in xDividers[j,p].ids.iteritems():
                    if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p])):    
                        
                        thevars = [y[i,j,p,ID3,ID4] for ID3,intervalIter3 in yDividers[i,p].ids.iteritems() 
                                                    for ID4,intervalIter4 in yDividers[j,p].ids.iteritems()
                                                        if doTheyIntersect(intervalIter1,intervalIter3) and doTheyIntersect(intervalIter2,intervalIter4)
                                                        and doTheyIntersect(intervalIter3,shiftList(intervalIter4,-turnover_travel_timesteps[i,j,p]))]
                        thecoefs = [-PLANE[p].seats for ID3,intervalIter3 in yDividers[i,p].ids.iteritems() 
                                                    for ID4,intervalIter4 in yDividers[j,p].ids.iteritems()
                                                        if doTheyIntersect(intervalIter1,intervalIter3) and doTheyIntersect(intervalIter2,intervalIter4)
                                                        and doTheyIntersect(intervalIter3,shiftList(intervalIter4,-turnover_travel_timesteps[i,j,p]))]
                        thevars += [x[i,j,r,p,ID1,ID2] for r in REQUEST ]
                        thecoefs += [REQUEST[r].passengers for r in REQUEST]
                        
                        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
    #TODO: Pruefe, ob die seat capacity constraints auch fuer Wartekanten eingefuehrt werden muessen
    
    
    
    # intermediate stops for REQUESTs
    for r in REQUEST:
        thevars = [x[i,j,r,p,ID1,ID2] for i,j in TRIP0 for p in PLANE 
                   for ID1,intervalIter1 in xDividers[i,p].ids.iteritems() for ID2,intervalIter2 in xDividers[j,p].ids.iteritems()
                   if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p]))]
        thecoefs = [ 1.0 ]*len(thevars)
        
        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [REQUEST[r].max_stops + 1])
    
    
    
    
    
    # no flight no fuel
    for i,j in TRIP0:
        for p in PLANE:
            for ID1,intervalIter1 in yDividers[i,p].ids.iteritems():
                for ID2,intervalIter2 in yDividers[j,p].ids.iteritems():
                    if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p])):   
                        thevars = [y[i,j,p,ID1,ID2]]
                        thecoefs = [-max_trip_fuel[i,j,p] ]
                        #TODO: Wenn z und y gleich geteilt werden ist die Ueberpruefung mit ID3 und ID4 ueberfluessig?
                        thevars += [z[i,j,p,ID1,ID2] for ID3,intervalIter3 in zDividers[i,p].ids.iteritems() 
                                            for ID4,intervalIter4 in zDividers[j,p].ids.iteritems()
                                                        if doTheyIntersect(intervalIter1,intervalIter3) and doTheyIntersect(intervalIter2,intervalIter4)]
                        thecoefs += [1.0 for ID3,intervalIter3 in zDividers[i,p].ids.iteritems() for ID4,intervalIter4 in zDividers[j,p].ids.iteritems()
                                                        if doTheyIntersect(intervalIter1,intervalIter3) and doTheyIntersect(intervalIter2,intervalIter4)]
                        
                        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
    for i in AIRPORT:
        for p in PLANE:
            for ID1,intervalIter1 in yDividers[i,p].ids.iteritems():
                if ySuccessorIds[i,p].has_key(ID1): 
                    thevars = [y[i,i,p,ID1,ySuccessorIds[i,p][ID1]]]
                    thecoefs = [-max_trip_fuel[i,i,p] ]
                    
                    thevars += [z[i,i,p,ID1,ySuccessorIds[i,p][ID1]] ]
                    thecoefs += [1.0 ]
                    
                    model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
    
    #no plane no fuel
    #arrival
    for p in PLANE:
        for ID in zDividers[PLANE[p].destination,p].ids:
            thevars = [ z_arr[p,ID], y_arr[p,ID] ]
            thecoefs = [ 1.0, -PLANE[p].arrival_min_fuel]
            model.linear_constraints.add(names = [p+' arrival fuel bound'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])
            thecoefs = [ 1.0, -PLANE[p].arrival_max_fuel]
            model.linear_constraints.add(names = [p+' arrival fuel bound2'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
    #departure
    for p in PLANE:
        for ID in zDividers[PLANE[p].origin,p].ids:
            thevars = [ z_dep[p,ID], y_dep[p,ID] ]
            thecoefs = [ 1.0, -PLANE[p].departure_min_fuel]
            model.linear_constraints.add(names = [p+' departure fuel bound'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])
            thecoefs = [ 1.0, -PLANE[p].departure_max_fuel]
            model.linear_constraints.add(names = [p+' departure fuel bound2'],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0]) 
    
    
    
    
    #fuel flow constraints
    for p in PLANE:
        for j in AIRPORT:
            for ID1,intervalIter1 in zDividers[j,p].ids.iteritems():
                thevars = []
                thecoefs = []
                
                for i in AIRPORT:
                    for ID2,intervalIter2 in zDividers[i,p].ids.iteritems():
                        if doTheyIntersect(intervalIter2,shiftList(intervalIter1,-turnover_travel_timesteps[i,j,p])): 
                            if not(i == j):
                                thevars.append(z[i,j,p,ID2,ID1])
                                thecoefs.append(1.0)
                
                if j == PLANE[p].plane_departure:
                    thevars.append(z_dep[p,ID1])
                    thecoefs.append(1.0)
    
                for k in AIRPORT:
                    for ID2,intervalIter2 in zDividers[k,p].ids.iteritems():
                        if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[j,k,p])):  
                            if not(j == k):
                                thevars.append(z[j,k,p,ID1,ID2])
                                thecoefs.append(-1.0)
    
                                thevars.append(y[j,k,p,ID1,ID2])
                                thecoefs.append(-fuelconsumption[j,k,p])
                
                if ID1 in zStartTimeIds[j,p].values():
                    for ID2 in zPredecessorIds[j,p][ID1]:
                        thevars += [ z[j,j,p,ID2,ID1] ]
                        thecoefs += [ 1.0 ]
                if zSuccessorIds[j,p].has_key(ID1):
                    thevars += [ z[j,j,p,ID1,zSuccessorIds[j,p][ID1]],y[j,j,p,ID1,ySuccessorIds[j,p][ID1]] ]
                    thecoefs += [ -1.0, -fuelconsumption[j,j,p]]
                    
                
                if j == PLANE[p].plane_arrival:
                    thevars.append(z_arr[p,ID1])
                    thecoefs.append(-1.0)
                
                if AIRPORT[j].fuel[PLANE[p].required_fueltype] == '0':
                    model.linear_constraints.add(names = ["fuelconsumption_" + j + "_" + p], 
                                                 lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
                else:
                    model.linear_constraints.add(names = ["refueling_" + j + "_" + p], 
                                                 lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
    
    
    
    
    # weight limit (=max fuel)
    #TODO:Pruefe, ob Gewichtsschranke auch auf Wartekanten definiert werden muss
    for i,j in TRIP0:
        for p in PLANE:
            for ID1,intervalIter1 in xDividers[i,p].ids.iteritems():
                for ID2,intervalIter2 in xDividers[j,p].ids.iteritems():
                    if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p])):    
                        thevars = [y[i,j,p,ID3,ID4] for ID3,intervalIter3 in yDividers[i,p].ids.iteritems() 
                                                    for ID4,intervalIter4 in yDividers[j,p].ids.iteritems()
                                                        if doTheyIntersect(intervalIter1,intervalIter3) and doTheyIntersect(intervalIter2,intervalIter4)
                                                        and doTheyIntersect(intervalIter3,shiftList(intervalIter4,-turnover_travel_timesteps[i,j,p]))]
                        thecoefs = [-max_trip_payload[i,j,p] for ID3,intervalIter3 in yDividers[i,p].ids.iteritems() 
                                                    for ID4,intervalIter4 in yDividers[j,p].ids.iteritems()
                                                        if doTheyIntersect(intervalIter1,intervalIter3) and doTheyIntersect(intervalIter2,intervalIter4)
                                                        and doTheyIntersect(intervalIter3,shiftList(intervalIter4,-turnover_travel_timesteps[i,j,p]))]
                        
                        thevars += [z[i,j,p,ID3,ID4] for ID3,intervalIter3 in yDividers[i,p].ids.iteritems() 
                                                     for ID4,intervalIter4 in yDividers[j,p].ids.iteritems()
                                                        if doTheyIntersect(intervalIter1,intervalIter3) and doTheyIntersect(intervalIter2,intervalIter4)
                                                        and doTheyIntersect(intervalIter3,shiftList(intervalIter4,-turnover_travel_timesteps[i,j,p]))]
                        thecoefs += [1.0 for ID3,intervalIter3 in yDividers[i,p].ids.iteritems() for ID4,intervalIter4 in yDividers[j,p].ids.iteritems()
                                                        if doTheyIntersect(intervalIter1,intervalIter3) and doTheyIntersect(intervalIter2,intervalIter4)
                                                        and doTheyIntersect(intervalIter3,shiftList(intervalIter4,-turnover_travel_timesteps[i,j,p]))]
                        
                        thevars += [x[i,j,r,p,ID1,ID2] for r in REQUEST]
                        thecoefs += [REQUEST[r].weight for r in REQUEST]
                        
                        model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])           
    
    
    
    # minimum number of fuelstops
    for p in PLANE:
        if PLANE[p].departure_max_fuel - fuelconsumption[PLANE[p].plane_departure,PLANE[p].plane_arrival,p] < PLANE[p].arrival_min_fuel:
            #print p
            thevars = []
            thecoefs = []
            
            for i,j in TRIP0:
                if AIRPORT[j].fuel[PLANE[p].required_fueltype] == '1':
                    for ID1,intervalIter1 in yDividers[i,p].ids.iteritems():
                        for ID2,intervalIter2 in yDividers[j,p].ids.iteritems():
                            if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p])):
                                thevars.append(y[i,j,p,ID1,ID2])
                                thecoefs.append(1.0)
            
            model.linear_constraints.add(names = ["minfuelstops_in_" + p], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])
        
        if PLANE[p].departure_max_fuel - fuelconsumption[PLANE[p].plane_departure,PLANE[p].plane_arrival,p] < PLANE[p].arrival_min_fuel:
            #print p
            thevars = []
            thecoefs = []
            
            for i,j in TRIP0:
                if AIRPORT[i].fuel[PLANE[p].required_fueltype] == '1':
                    for ID1,intervalIter1 in yDividers[i,p].ids.iteritems():
                        for ID2,intervalIter2 in yDividers[j,p].ids.iteritems():
                            if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p])):
                                thevars.append(y[i,j,p,ID1,ID2])
                                thecoefs.append(1.0)
            
            model.linear_constraints.add(names = ["minfuelstops_in_" + p], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])
    
    
    
    
    # maximum number of arrivals/departures per airport
    
    for i in AIRPORT:
        anyfuel = 0
        for ft in AIRPORT[i].fuel:
            if AIRPORT[i].fuel[ft] == '1':
                anyfuel += 1
          
        if anyfuel == 0:
            thevars = []
            thecoefs = []
          
            for j in AIRPORT:
                if (i,j) in TRIP0:
                    for p in PLANE:
                        for ID1,intervalIter1 in yDividers[i,p].ids.iteritems():
                            for ID2,intervalIter2 in yDividers[j,p].ids.iteritems():
                                if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p])):
                                    thevars.append(y[i,j,p,ID1,ID2])
                                    thecoefs.append(1.0)
            
            rhs_value = 0
            
            for r in REQUEST:
                if REQUEST[r].request_departure == i or REQUEST[r].request_arrival == i:
                    rhs_value += 1
            
            for p in PLANE:
                if PLANE[p].plane_departure == i:
                    rhs_value += 1
                
            model.linear_constraints.add(names = ["maxpickup_out_" + i], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs_value])
    
    
    for j in AIRPORT:
        anyfuel = 0
        for ft in AIRPORT[j].fuel:
            if AIRPORT[j].fuel[ft] == '1':
                anyfuel += 1
          
        if anyfuel == 0:
            thevars = []
            thecoefs = []
              
            for i in AIRPORT:
                if (i,j) in TRIP0:
                    for p in PLANE:
                        for ID1,intervalIter1 in yDividers[i,p].ids.iteritems():
                            for ID2,intervalIter2 in yDividers[j,p].ids.iteritems():
                                if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p])):
                                    thevars.append(y[i,j,p,ID1,ID2])
                                    thecoefs.append(1.0)
            
            rhs_value = 0
            
            for r in REQUEST:
                if REQUEST[r].request_departure == j or REQUEST[r].request_arrival == j:
                    rhs_value += 1
            
            for p in PLANE:
                if PLANE[p].plane_arrival == j:
                    rhs_value += 1
            
            model.linear_constraints.add(names = ["maxpickup_in_" + j], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs_value])
    
    
    
    
    
    # minimum amount of fuel for detour to refueling airport
    for i,j in TRIP0:
        for p in PLANE:
            for ID1,intervalIter1 in yDividers[i,p].ids.iteritems():
                for ID2,intervalIter2 in yDividers[j,p].ids.iteritems():
                    if doTheyIntersect(intervalIter1,shiftList(intervalIter2,-turnover_travel_timesteps[i,j,p])):
                        thevars = [y[i,j,p,ID1,ID2],z[i,j,p,ID1,ID2]]
                        thecoefs = [min_refuel_trip[j,p],-1.0]
                        
                        model.linear_constraints.add(names = ["minfuel_" + i + "_" + j + "_" + p], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0])

    

    
    
    #set sense
    model.objective.set_sense(model.objective.sense.minimize)
    

    # output model
    model.write("model.lp")
    

    #set parameters    
    model.parameters.mip.strategy.heuristicfreq.set(-1)
    model.parameters.emphasis.mip.set(3) 
     
    # solve model       
    try:
        model.solve()
        if model.solution.is_primal_feasible():
            oldObjective = model.solution.get_objective_value()
        
        mipSolved=1
    except CplexSolverError, exc:
        print "** Exception: ",exc
    


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
for key,val in x_dep.iteritems():
    valStore=solutionValues[name2idx[val]]
    if valStore > 0.5:
        print(val+" %f" % valStore)
for key,val in x_arr.iteritems():
    valStore=solutionValues[name2idx[val]]
    if valStore > 0.5:
        print(val+" %f" % valStore)
for key,val in z.iteritems():
    valStore=solutionValues[name2idx[val]]
    if valStore > 0.5:
        print(val+" %f" % valStore)
for key,val in z_arr.iteritems():
    valStore=solutionValues[name2idx[val]]
    if valStore > 0.5:
        print(val+" %f" % valStore)
for key,val in z_dep.iteritems():
    valStore=solutionValues[name2idx[val]]
    if valStore > 0.5:
        print(val+" %f" % valStore)
