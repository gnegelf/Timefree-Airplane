#! /usr/bin/python

import re

import math
import time
import sys
from operator import itemgetter
if not "cplex" in globals():
    import cplex
    from cplex.callbacks import IncumbentCallback
    from cplex.callbacks import LazyConstraintCallback
    from cplex.callbacks import MIPInfoCallback
    from cplex.exceptions import CplexSolverError
from sets import Set
EPSILON = 1e-6

# -------
# classes
# -------

class __PLANE__(object):
  def __init__(self,cost=None,seats=None,plane_departure=None,departure_min_fuel=None,departure_max_fuel=None,plane_arrival=None,arrival_min_fuel=None,arrival_max_fuel=None,required_fueltype=None,fuel=None,speed=None,max_fuel=None,empty_weight=None,add_turnover_time=None,reserve_fuel=None,contigence_ratio=None,pilot_weight=None):
    self.cost = float(cost)
    self.seats = int(seats)
    self.plane_departure = plane_departure
    self.departure_min_fuel = float(departure_min_fuel)
    self.departure_max_fuel = float(departure_max_fuel)
    self.plane_arrival = plane_arrival
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
    self.origin = plane_departure
    self.destination = plane_arrival

class __AIRPORT__(object):
  def __init__(self,turnover_time=None):
    self.turnover_time = int(turnover_time)
    self.fuel = {}

class __REQUEST__(object):
  def __init__(self,request_departure=None,request_arrival=None,earliest_departure_time=None,earliest_departure_day=None,latest_arrival_time=None,latest_arrival_day=None,passengers=None,weight=None,max_stops=None,max_detour=None):
    self.request_departure = request_departure
    self.request_arrival = request_arrival
    self.origin = request_departure
    self.destination = request_arrival
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

class __ARC__(object):
    def __init__(self,distance,fuel,stops,seats,traveltime,s,d,w):
        self.distance=distance
        self.fuel=fuel
        self.stops=stops
        self.seats=seats
        self.traveltime=traveltime
        self.origin=s
        self.destination=d
        self.weight=w

class __VERTEX__(object):
    def __init__(self,name,departure_time,arrival_time,plane,airport):
        self.airport=airport
        self.name=name
        self.arrival_time=arrival_time
        self.departure_time=departure_time
        self.successors = []
        self.predecessors = []
        self.p = plane
# prepare reading and parsing

comment_line = re.compile('#');

#directory = sys.argv[1]
#strategy = sys.argv[2]

restart = 1

directories = {'BUF-AIV':'Testinstances/A2-BUF_A2-AIV',#check
               #'BUF-ANT':'Testinstances/A2-BUF_A2-ANT',#check
               #'BUF-BEE':'Testinstances/A2-BUF_A2-BEE',#check
               #'BUF-BOK':'Testinstances/A2-BUF_A2-BOK',#check
               #'BUF-EGL':'Testinstances/A2-BUF_A2-EGL',#check
               #'BUF-GNU':'Testinstances/A2-BUF_A2-GNU',#check
               #'BUF-JKL':'Testinstances/A2-BUF_A2-JKL',#check
               #'BUF-LEO':'Testinstances/A2-BUF_A2-LEO',#check
               #'BUF-NAS':'Testinstances/A2-BUF_A2-NAS',#check
               #'BUF-OWL':'Testinstances/A2-BUF_A2-OWL',#check
               #'BUF-ZEB':'Testinstances/A2-BUF_A2-ZEB',#check
               #'EGL-BEE':'Testinstances/A2-EGL_A2-BEE',#check
               #'EGL-GNU':'Testinstances/A2-EGL_A2-GNU',#check
               #'EGL-LEO':'Testinstances/A2-EGL_A2-LEO',#check
               #'GNU-BEE':'Testinstances/A2-GNU_A2-BEE',#check
               #'GNU-JKL':'Testinstances/A2-GNU_A2-JKL',#check
               #'GNU-LEO':'Testinstances/A2-GNU_A2-LEO',#check
               #'LEO-AIV':'Testinstances/A2-LEO_A2-AIV',#check
               #'LEO-ANT':'Testinstances/A2-LEO_A2-ANT',#check
               #'LEO-BEE':'Testinstances/A2-LEO_A2-BEE',#check more than og
               #'LEO-BOK':'Testinstances/A2-LEO_A2-BOK',#check
               #'LEO-JKL':'Testinstances/A2-LEO_A2-JKL',#check
               #'LEO-NAS':'Testinstances/A2-LEO_A2-NAS',
               #'LEO-OWL':'Testinstances/A2-LEO_A2-OWL'#check
               }

#file = open("results.txt", "w+")

#file.close()
bestGap = {}
bestSolution = {}
bestDualBound = {}
graphIterations = {}
solutionTime = {}

for instanceName,directory in directories.iteritems():
    bestGap[instanceName] = 10000
    bestSolution[instanceName]  = 10000000
    bestDualBound[instanceName]  = 0
    graphIterations[instanceName] = 0
    if not "oldDirectory" in globals():
        restart = 1
        debugModels = 1
    else:
        if oldDirectory != directory:
            restart = 1
            debugModels = 1
    oldDirectory = directory
    
    
    timeLimit = 10800
    totallySolved = [0]
    # ---------------------
    # reading airplanes.dat
    # ---------------------
    if restart or not "PLANE" in globals():
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
              ID,cost,seats,plane_departure,departure_min_fuel,departure_max_fuel,plane_arrival,arrival_min_fuel,arrival_max_fuel,required_fueltype,fuel,speed,max_fuel,empty_weight,add_turnover_time,reserve_fuel,contigence_ratio,pilot_weight = datas
              PLANE[ID] = __PLANE__(cost,seats,plane_departure,departure_min_fuel,departure_max_fuel,plane_arrival,arrival_min_fuel,arrival_max_fuel,required_fueltype,fuel,speed,max_fuel,empty_weight,add_turnover_time,reserve_fuel,contigence_ratio,pilot_weight)
        
        
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
        
        
        # --------------------------
        # reading columnsolution.dat
        # --------------------------
        
        print "reading '"+directory+"/columnsolution.dat'"
        
        file = open(directory+"/columnsolution.dat", "r")
        columnsolution_data = file.read()
        file.close()
        
        entries = re.split("\n+", columnsolution_data)
        
        COLUMNSOLUTION = Set()
        
        for line in entries:
          if comment_line.search(line) == None:
            datas = re.split("\s+", line)
            if len(datas) == 5:
              plane, origin, destination, hour, minute = datas
              COLUMNSOLUTION.add((plane, origin, destination, hour, minute))
        
        #print Columnsolution
        
        
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
              TRIP[origin,destination] = __TRIP__(distance)
        
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
              ID,origin,destination,earliest_departure_time,earliest_departure_day,latest_arrival_time,latest_arrival_day,passengers,weight,max_stops,max_detour = datas
              REQUEST[ID] = __REQUEST__(origin,destination,earliest_departure_time,earliest_departure_day,latest_arrival_time,latest_arrival_day,passengers,weight,max_stops,max_detour)
        
        
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
        
        
        # --------------------------
        # reading columnsolution.dat
        # --------------------------
        
        print "reading '"+directory+"/columnsolution.dat'"
        
        file = open(directory+"/columnsolution.dat", "r")
        solution_data = file.read()
        file.close()
        
        entries = re.split("\n+", solution_data)
        
        PLANE_SOLUTION = {}
        
        for line in entries:
          if comment_line.search(line) == None:
            datas = re.split("\s+", line)
            if len(datas) == 5:
              plane, origin, destination, hour, minute = datas
              PLANE_SOLUTION[plane, origin, destination, hour, minute] = 1
        
        
        # --------------------------
        # reading columnsolution.dat
        # --------------------------
        
        print "reading '"+directory+"/requestsolution.dat'"
        
        file = open(directory+"/requestsolution.dat", "r")
        solution_data = file.read()
        file.close()
        
        entries = re.split("\n+", solution_data)
        
        REQUEST_SOLUTION = {}
        
        for line in entries:
          if comment_line.search(line) == None:
            datas = re.split("\s+", line)
            if len(datas) == 6:
              plane, request, origin, destination, hour, minute = datas
              REQUEST_SOLUTION[plane, request, origin, destination, hour, minute] = 1
        
        
        # --------------------------------
        # generating further instance data
        # --------------------------------
        
        turnover_timesteps = {}
        
        for i in AIRPORT:
          for p in PLANE:
            turnover_timesteps[i,p] = int(max(1,math.ceil((AIRPORT[i].turnover_time + PLANE[p].add_turnover_time) / timedelta)))
        
        
        travelcost = {}
        
        for p in PLANE:
          for i, j in TRIP:
            travelcost[i,j,p] = TRIP[i,j].distance * PLANE[p].cost
        
        
        travel_time = {}
        
        for p in PLANE:
          for i, j in TRIP:
            travel_time[i,j,p] = int(math.floor(TRIP[i,j].distance / ((PLANE[p].speed / 60) * 5)) * 5)
            #travel_time[i,j,p] = TRIP[i,j].distance / (PLANE[p].speed / 60)
        
        
        travel_timesteps = {}
        
        for p in PLANE:
          for i, j in TRIP:
            travel_timesteps[i,j,p] = int(max(1,math.ceil(travel_time[i,j,p] / timedelta)))
        
        
        turnover_travel_timesteps = {}
        
        for p in PLANE:
          for i, j in TRIP:
            if i == j:
              turnover_travel_timesteps[i,j,p] = 0
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
            max_trip_payload[i,j,p] = min(max_takeoff_payload[i,p]+ fuelconsumption[i,j,p], max_landing_payload[j,p] )
            #max_trip_payload[i,j,p] = min(max_takeoff_payload[i,p], max_landing_payload[j,p] + fuelconsumption[i,j,p])

        
        
        max_trip_fuel = {}
        
        for p in PLANE:
          for i, j in TRIP:
            max_trip_fuel[i,j,p] = PLANE[p].max_fuel - fuelconsumption[i,j,p] - PLANE[p].reserve_fuel
        
        
        earliest_departure_travel_timesteps = {}
        
        for p in PLANE:
          for i, j in TRIP:
            for r in REQUEST:
              earliest_departure_travel_timesteps[i,j,p,r] = math.ceil((REQUEST[r].earliest_departure_time + 60 * TRIP[i,j].distance / PLANE[p].speed) / timedelta)
        
        
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
              aux = earliest_departure_timesteps[r] - turnover_timesteps[REQUEST[r].request_departure,p] - max(direct_flight_timesteps[p,r], max_refuel_flight_timesteps[p,r])
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
        
        
        plane_solution_arrival_time = {}
        plane_solution_arrival_timestep = {}
        
        for p,i,j,hh,mm in PLANE_SOLUTION:
          plane_solution_arrival_time[p,i,j,hh,mm] = 60 * int(hh) + int(mm);
          plane_solution_arrival_timestep[p,i,j,hh,mm] = math.ceil(plane_solution_arrival_time[p,i,j,hh,mm] / timedelta)
        
        
        request_solution_arrival_time = {}
        request_solution_arrival_timestep = {}
        
        for p,r,i,j,hh,mm in REQUEST_SOLUTION:
          request_solution_arrival_time[p,r,i,j,hh,mm] = 60 * int(hh) + int(mm);
          request_solution_arrival_timestep[p,r,i,j,hh,mm] = math.ceil(request_solution_arrival_time[p,r,i,j,hh,mm] / timedelta)
          
          
        PLANE_TIMESTEP = {}
        
        for p in PLANE:
          PLANE_TIMESTEP[p] = {}
          
          for t in range(plane_min_timestep[p], plane_max_timestep[p] + 1):
            PLANE_TIMESTEP[p][t] = 1
            
        
        REQUEST_TIMESTEP = {}
        max_turnover_timesteps = {}
        for r in REQUEST:
          max_turnover_timesteps[r] = 0
          for p in PLANE:
            max_turnover_timesteps[r] = max(max_turnover_timesteps[r], turnover_timesteps[REQUEST[r].request_departure,p])
          
          REQUEST_TIMESTEP[r] = range(earliest_departure_timesteps[r] - max_turnover_timesteps[r], latest_arrival_timesteps[r] + 1)
        
        
        min_timestep = 99999
        max_timestep = 0
        
        for p in PLANE:
          min_timestep = min(min_timestep, plane_min_timestep[p])
          max_timestep = max(max_timestep, plane_max_timestep[p])
          
        TIMESTEP = range(min_timestep, max_timestep + 1)
        
        
        
        
        
        TIMEFREEREQUESTSOLUTION = {}
        
        for p,r,i,j,hh,mm in REQUEST_SOLUTION:
          TIMEFREEREQUESTSOLUTION[p,r,i,j] = 1
          
           
        
        TIMEFREEPLANESOLUTION = {}
        
        for p,i,j,hh,mm in PLANE_SOLUTION:
          if (p,i,j) in TIMEFREEPLANESOLUTION:
            TIMEFREEPLANESOLUTION[p,i,j] += 1
          else:
            TIMEFREEPLANESOLUTION[p,i,j] = 1
        
    REQUESTNEU = {}
    zz=0
    for r in REQUEST:
        REQUESTNEU[r] = REQUEST[r] 
        zz+=1
        if zz>9:
            break
    #REQUEST = REQUESTNEU
    A = {}
    V = {}
    P_s = {}
    P_d = {}
    
    for p in PLANE:
        P_s[p] = __VERTEX__(p + "_" + "ori_" + PLANE[p].origin,plane_min_timestep[p],plane_max_timestep[p],p,PLANE[p].origin)
        P_d[p] = __VERTEX__(p + "_" + "desti_" + PLANE[p].destination,plane_min_timestep[p],plane_max_timestep[p],p,PLANE[p].destination)
        V[P_s[p].name]= P_s[p]
        V[P_d[p].name]= P_d[p]
    
    R_s = {}
    R_d = {}
    
    for p in PLANE:
        R_s[p] = {}
        R_d[p] = {}
        for r in REQUEST:
            R_s[p][r] = __VERTEX__(r + "_" + p + "_" + "ori_" + REQUEST[r].origin,earliest_departure_timesteps[r]-max_turnover_timesteps[r],latest_arrival_timesteps[r],p,REQUEST[r].origin)
            R_d[p][r] = __VERTEX__(r + "_" + p + "_" + "desti_" + REQUEST[r].destination,
               earliest_departure_timesteps[r]-max_turnover_timesteps[r],latest_arrival_timesteps[r],p,REQUEST[r].destination)
            V[R_s[p][r].name] = R_s[p][r]
            V[R_d[p][r].name] = R_d[p][r]
    
    fuelstops=3
    F = {}
    
    for p in PLANE:
        F[p] = {}
        for f in AIRPORT:
            if AIRPORT[f].fuel[PLANE[p].required_fueltype] != '0':
                for i in range(0,fuelstops):
                    F[p][f,str(i)] =  __VERTEX__(p + "_" + "fuel_%d" % i + f,plane_min_timestep[p],plane_max_timestep[p],p,f)
                    V[F[p][f,str(i)].name] = F[p][f,str(i)]
    
    
    for p,vI in P_s.iteritems():
        for f in F[p]:
            v1=PLANE[p].origin
            v2=f[0]
            if v1 != v2:
                vI.successors.append(F[p][f].name)
                A[vI.name,F[p][f].name,p] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1!=v2),0,
                 turnover_travel_timesteps[v1,v2,p],v1,v2,0.0)
        for r in R_s[p]:
            vI.successors.append(R_s[p][r].name)
            v1 = PLANE[p].origin
            v2 = REQUEST[r].origin
            A[vI.name,R_s[p][r].name,p] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1!=v2),0,
             turnover_travel_timesteps[v1,v2,p],v1,v2,0.0)
        vI.successors.append(P_d[p].name)
        v1 = PLANE[p].origin
        v2 = PLANE[p].destination
        A[vI.name,P_d[p].name,p] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1!=v2),0,
             turnover_travel_timesteps[v1,v2,p],v1,v2,0.0)
    
    for p,vI in P_d.iteritems():
        for f in F[p]:
            v1=f[0]
            v2=PLANE[p].destination
            if v1 != v2:
                vI.predecessors.append(F[p][f].name)
                A[F[p][f].name,vI.name,p] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1!=v2),0,
                 turnover_travel_timesteps[v1,v2,p],v1,v2,0.0)
        for r in R_d[p]:
            vI.predecessors.append(R_d[p][r].name)
            v1 = REQUEST[r].destination
            v2 = PLANE[p].destination
            A[R_d[p][r].name,vI.name,p] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1!=v2),-REQUEST[r].passengers,
             turnover_travel_timesteps[v1,v2,p],v1,v2,-REQUEST[r].weight)
        vI.predecessors.append(P_s[p].name)
    
    for p in PLANE:
        for r,vI in R_s[p].iteritems():
            vI.predecessors.append(P_s[p].name)
            for r2 in R_d[p]:
                vI.successors.append(R_d[p][r2].name)#TODO: condition on time windows
                v1 = REQUEST[r].origin
                v2 = REQUEST[r2].destination
                A[vI.name,R_d[p][r2].name,p] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1!=v2),REQUEST[r].passengers,
                     turnover_travel_timesteps[v1,v2,p],v1,v2,REQUEST[r].weight)
                if r2 != r:
                    vI.predecessors.append(R_d[p][r2].name)#TODO: condition on time windows
            for r2 in R_s[p]:
                if r != r2:
                    vI.successors.append(R_s[p][r2].name)#TODO: condition on time windows
                    v1 = REQUEST[r].origin
                    v2 = REQUEST[r2].origin
                    A[vI.name,R_s[p][r2].name,p] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1!=v2),REQUEST[r].passengers,
                         turnover_travel_timesteps[v1,v2,p],v1,v2,REQUEST[r].weight)
                    vI.predecessors.append(R_s[p][r2].name)#TODO: condition on time windows
            for f in F[p]:
                v1 = REQUEST[r].origin
                v2 = f[0]
                if v1 !=v2:
                    vI.successors.append(F[p][f].name)
                    vI.predecessors.append(F[p][f].name)
                    A[vI.name,F[p][f].name,p] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1!=v2),REQUEST[r].passengers,
                             turnover_travel_timesteps[v1,v2,p],v1,v2,REQUEST[r].weight)
                    v2 = REQUEST[r].origin
                    v1 = f[0]
                    A[F[p][f].name,vI.name,p] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1!=v2),0.0,
                             turnover_travel_timesteps[v1,v2,p],v1,v2,0.0)
    
    for p in PLANE:
        for r,vI in R_d[p].iteritems():
            vI.successors.append(P_d[p].name)
            for r2 in R_d[p]:
                if r != r2:
                    vI.successors.append(R_d[p][r2].name)#TODO: condition on time windows
                    v1 = REQUEST[r].destination
                    v2 = REQUEST[r2].destination
                    A[vI.name,R_d[p][r2].name,p] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1!=v2),-REQUEST[r].passengers,
                         turnover_travel_timesteps[v1,v2,p],v1,v2,-REQUEST[r].weight)
                    vI.predecessors.append(R_d[p][r2].name)#TODO: condition on time windows
            for r2 in R_s[p]:
                if r2 != r:
                    vI.successors.append(R_s[p][r2].name)#TODO: condition on time windows
                    v1 = REQUEST[r].destination
                    v2 = REQUEST[r2].origin
                    A[vI.name,R_s[p][r2].name,p] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1!=v2),-REQUEST[r].passengers,
                         turnover_travel_timesteps[v1,v2,p],v1,v2,-REQUEST[r].weight)
                vI.predecessors.append(R_s[p][r2].name)#TODO: condition on time windows
            for f in F[p]:
                v1 = REQUEST[r].destination
                v2 = f[0]
                if v1 != v2:
                    vI.successors.append(F[p][f].name)
                    vI.predecessors.append(F[p][f].name) 
                    A[vI.name,F[p][f].name,p] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1!=v2),-REQUEST[r].passengers,
                             turnover_travel_timesteps[v1,v2,p],v1,v2,-REQUEST[r].weight)
                    v2 = REQUEST[r].destination
                    v1 = f[0]
                    A[F[p][f].name,vI.name,p] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1!=v2),0,
                             turnover_travel_timesteps[v1,v2,p],v1,v2,0.0)
    
    for p in F:
        for f,vI in F[p].iteritems():
            if PLANE[p].origin != f[0]:
                vI.predecessors.append(P_s[p].name)
            if PLANE[p].destination != f[0]:
                vI.successors.append(P_d[p].name)

            for r in R_d[p]:
                if REQUEST[r].destination!=f[0]:
                    vI.successors.append(R_d[p][r].name)
                    vI.predecessors.append(R_d[p][r].name)
            for r in R_s[p]:
                if REQUEST[r].origin != f[0]:
                    vI.successors.append(R_s[p][r].name)
                    vI.predecessors.append(R_s[p][r].name)
            for f2 in F[p]:
                if f[0] != f2[0]:
                    vI.successors.append(F[p][f2].name)
                    v1 = f[0]
                    v2 = f2[0]
                    A[F[p][f].name,F[p][f2].name,p] =  __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1!=v2),0,
                         turnover_travel_timesteps[v1,v2,p],v1,v2,0.0)
                    vI.predecessors.append(F[p][f2].name)
    
    # ----------------
    # MODEL GENERATION
    # ----------------
    
    
    t0 = time.time()
    model = cplex.Cplex()
    
    
    # VARIABLES
    number_of_variables = 0
    y = {}
    seatNum = {}
    t = {}
    stops = {}
    stops2 = {}
    dist = {}
    fuel = {}
    w = {}
    
    
    
    for tup,aI in A.iteritems():
          i = tup[0]
          j = tup[1]
          p = tup[2]
          y[i,j,p] = "y#" + i + "_" + j + '_' + p
          if aI.origin != aI.destination:
              ub=0.0
          else:
              ub=1.0
          model.variables.add(obj = [travelcost[aI.origin,aI.destination,p]], names = [y[i,j,p]]
          , lb = [0],ub = [ub], types = ["B"])
          number_of_variables += 1
    
    for v,vI in V.iteritems():
          seatNum[v] = "s#" + v
          model.variables.add(obj = [0], names = [seatNum[v]]
          , lb = [0], ub = [PLANE[vI.p].seats], types = ["C"])
          number_of_variables += 1
          
          w[v] = "w#" + v
          model.variables.add(obj = [0], names = [w[v]]
          , lb = [0], types = ["C"])
          number_of_variables += 1
          
          t[v] = "t#" + v
          model.variables.add(obj = [0], names = [t[v]]
          , lb = [0], types = ["C"])
          number_of_variables += 1
          
          stops[v] = "st#" + v
          model.variables.add(obj = [0.0], names = [stops[v]]
          , lb = [0], types = ["C"])
          number_of_variables += 1
          
          stops2[v] = "st2#" + v
          model.variables.add(obj = [0], names = [stops2[v]]
          , lb = [0], types = ["C"])
          number_of_variables += 1
          
          dist[v] = "d#" + v
          model.variables.add(obj = [0], names = [dist[v]]
          , lb = [0], types = ["C"])
          number_of_variables += 1
          
          fuel[v] = "f#" + v
          model.variables.add(obj = [0], names = [fuel[v]]
          , lb = [0],ub = [PLANE[p].max_fuel-PLANE[p].reserve_fuel], types = ["C"])
          number_of_variables += 1
    
    for p in PLANE:
        for r,vI in R_d[p].iteritems():
            model.variables.set_upper_bounds([(t[vI.name],latest_arrival_timesteps[r])])
    
    
    
    for p in PLANE:
        for r,vI in R_s[p].iteritems():
            model.variables.set_lower_bounds([(t[vI.name],earliest_departure_timesteps[r]-max_turnover_timesteps[r])])
    
    
    
    
    for v,vI in P_s.iteritems():
        model.variables.set_lower_bounds([(seatNum[vI.name],0.0)])
        model.variables.set_upper_bounds([(seatNum[vI.name],0.0)])
        
        model.variables.set_lower_bounds([(w[vI.name],0.0)])
        model.variables.set_upper_bounds([(w[vI.name],0.0)])
        
        model.variables.set_lower_bounds([(t[vI.name],vI.departure_time)])
        model.variables.set_upper_bounds([(t[vI.name],vI.departure_time)])
        
        model.variables.set_lower_bounds([(dist[vI.name],0.0)])
        model.variables.set_upper_bounds([(dist[vI.name],0.0)])
        
        model.variables.set_lower_bounds([(stops[vI.name],0.0)])
        model.variables.set_upper_bounds([(stops[vI.name],0.0)])
        
        model.variables.set_lower_bounds([(stops2[vI.name],0.0)])
        model.variables.set_upper_bounds([(stops2[vI.name],0.0)])
        
        model.variables.set_lower_bounds([(fuel[vI.name],PLANE[v].departure_min_fuel)])
        model.variables.set_upper_bounds([(fuel[vI.name],PLANE[v].departure_max_fuel)])
    
    for v,vI in P_d.iteritems():
        model.variables.set_lower_bounds([(seatNum[vI.name],0.0)])
        model.variables.set_upper_bounds([(seatNum[vI.name],0.0)])
        
        model.variables.set_lower_bounds([(w[vI.name],0.0)])
        model.variables.set_upper_bounds([(w[vI.name],0.0)])
        
        model.variables.set_upper_bounds([(t[vI.name],vI.arrival_time)])
        
        model.variables.set_lower_bounds([(fuel[vI.name],PLANE[v].arrival_min_fuel)])
        model.variables.set_upper_bounds([(fuel[vI.name],PLANE[v].arrival_max_fuel)])
    
    #plane must start and arrive
    for p in P_s:
        thevars = [y[P_s[p].name,suc,p] for suc in P_s[p].successors]
        thecoefs = [1.0]*len(thevars)
        
        model.linear_constraints.add(names = ["mustleave_" + p], 
                                                       lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
    
    for p in P_d:
        thevars = [y[pred,P_d[p].name,p] for pred in P_d[p].predecessors]
        thecoefs = [1.0]*len(thevars)
        
        model.linear_constraints.add(names = ["mustarrive_" + p], 
                                                       lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
    
    
    #requests must be served by same plane
    for r in REQUEST:
        thevars = [y[pred,R_s[p2][r].name,p2] for p2 in PLANE for pred in R_s[p2][r].predecessors]
        thecoefs = [1.0]*len(thevars)
        model.linear_constraints.add(names = ["mustserve_" + r], 
                                                       lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
    
    for r in REQUEST:
        for p in PLANE:
            thevars = [y[R_s[p][r].name,suc,p] for suc in R_s[p][r].successors]
            thecoefs = [1.0]*len(thevars)
            thevars += [y[R_d[p][r].name,suc,p] for suc in R_d[p][r].successors]
            thecoefs += [-1.0 for suc in R_d[p][r].successors]
            model.linear_constraints.add(names = ["must_be_the_same_" + p + "_" + r], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
    
    #fuel airports can only be visited once
    for p in PLANE:
        for f,vI in F[p].iteritems():
            thevars = [y[pred,vI.name,p] for pred in F[p][f].predecessors]
            thecoefs = [1.0]*len(thevars)
            model.linear_constraints.add(names = ["maxonce_" + p + "_" + f[0]+ "_" + f[1]], 
                                                       lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [1.0])
    
    #planeflow
    for p in PLANE:
        for r,vI in R_s[p].iteritems():
            thevars = [y[pred,vI.name,p] for pred in R_s[p][r].predecessors]
            thecoefs = [1.0 for pred in R_s[p][r].predecessors]
            
            thevars += [y[vI.name,suc,p] for suc in R_s[p][r].successors]
            thecoefs += [-1.0 for suc in R_s[p][r].successors]
            
            model.linear_constraints.add(names = ["flow_req_s_" + p + "_" + r], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
    
    for p in PLANE:
        for r,vI in R_d[p].iteritems():
            thevars = [y[pred,vI.name,p] for pred in R_d[p][r].predecessors]
            thecoefs = [1.0 for pred in R_d[p][r].predecessors]
            
            thevars += [y[vI.name,suc,p] for suc in R_d[p][r].successors]
            thecoefs += [-1.0 for suc in R_d[p][r].successors]
            
            model.linear_constraints.add(names = ["flow_req_d_" + p + "_" + r], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])  
    for p in PLANE:
        for f,vI in F[p].iteritems():
            thevars = [y[pred,vI.name,p] for pred in F[p][f].predecessors]
            thecoefs = [1.0 for pred in F[p][f].predecessors]
            
            thevars += [y[vI.name,suc,p] for suc in F[p][f].successors]
            thecoefs += [-1.0 for suc in F[p][f].successors]
            
            model.linear_constraints.add(names = ["flowat_" + p + "_"  + f[0]+ "_" + f[1]], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])    
    
    
    #set values at vertices
    maxstops=30
    maxdists=30000
    for v,vI in V.iteritems():
        for pred in vI.predecessors:
            
            thevars = [stops[pred],stops[v],y[pred,v,vI.p]]
            thecoefs = [1.0,-1.0,maxstops]
            rhs = -A[pred,v,vI.p].stops+maxstops
            model.linear_constraints.add(names = ["stopsat_" + v + "_" + pred], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs])
            
            thevars = [stops2[pred],stops2[v],y[pred,v,vI.p]]
            thecoefs = [1.0,-1.0,maxstops]
            rhs = -1+maxstops
            model.linear_constraints.add(names = ["stops2at_" + v + "_" + pred], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs])
            
            thevars = [t[pred],t[v],y[pred,v,vI.p]]
            thecoefs = [1.0,-1.0,2*vI.arrival_time]
            rhs = -A[pred,v,vI.p].traveltime+2*vI.arrival_time
            model.linear_constraints.add(names = ["timesat_" + v + "_" + pred], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs])
            
            thevars = [seatNum[pred],seatNum[v],y[pred,v,vI.p]]
            thecoefs = [1.0,-1.0,2*max([PLANE[p].seats for p in PLANE])]
            rhs = -A[pred,v,vI.p].seats+2*max([PLANE[p].seats for p in PLANE])
            model.linear_constraints.add(names = ["seatsmin_" + v + "_" + pred], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs])
            thevars = [seatNum[pred],seatNum[v],y[pred,v,vI.p]]
            thecoefs = [1.0,-1.0,-2*max([PLANE[p].seats for p in PLANE])]
            rhs = -A[pred,v,vI.p].seats-2*max([PLANE[p].seats for p in PLANE])
            model.linear_constraints.add(names = ["seatsmax_" + v + "_" + pred], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [rhs])
            
            thevars = [w[pred],w[v],y[pred,v,vI.p]]
            thecoefs = [1.0,-1.0,4*max(max_landing_payload.values())]
            rhs = -A[pred,v,vI.p].weight+4*max(max_landing_payload.values())
            model.linear_constraints.add(names = ["weightat_" + v + "_" + pred], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs])
            
            thevars = [w[pred],w[v],y[pred,v,vI.p]]
            thecoefs = [1.0,-1.0,-4*max(max_landing_payload.values())]
            rhs = -A[pred,v,vI.p].weight-4*max(max_landing_payload.values())
            model.linear_constraints.add(names = ["weightat_" + v + "_" + pred], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [rhs])
            thevars = [dist[pred],dist[v],y[pred,v,vI.p]]
            thecoefs = [1.0,-1.0,maxdists]
            rhs = -A[pred,v,vI.p].stops+maxdists
            model.linear_constraints.add(names = ["distat_" + v + "_" + pred], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs])
            
            if AIRPORT[A[pred,v,vI.p].origin].fuel[PLANE[p].required_fueltype] == '0':
                thevars = [fuel[pred],fuel[v],y[pred,v,vI.p]]
                thecoefs = [1.0,-1.0,-2*max(max_trip_fuel.values())]
                rhs = A[pred,v,vI.p].fuel-2*max(max_trip_fuel.values())
                model.linear_constraints.add(names = ["fuelminat_" + v + "_" + pred], 
                                                               lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [rhs])
                
                thevars = [fuel[pred],fuel[v],y[pred,v,vI.p]]
                thecoefs = [1.0,-1.0,2*max(max_trip_fuel.values())]
                rhs = A[pred,v,vI.p].fuel+2*max(max_trip_fuel.values())
                model.linear_constraints.add(names = ["fuelmaxat_" + v + "_" + pred], 
                                                               lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs])
            else:
                thevars = [fuel[v],y[pred,v,vI.p]]
                thecoefs = [1.0,A[pred,v,vI.p].fuel]
                rhs = PLANE[p].max_fuel - PLANE[p].reserve_fuel
                model.linear_constraints.add(names = ["fuelmaxat_" + v + "_" + pred], 
                                                               lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs])
               
                
    
      
    #max_weight
    for v,vI in V.iteritems():
        for pred in vI.predecessors:
            thevars = [fuel[pred],w[pred],y[pred,v,vI.p]]
            
            thecoefs = [1.0,1.0,A[pred,v,vI.p].weight]
            rhs = max_trip_payload[A[pred,v,vI.p].origin,A[pred,v,vI.p].destination,vI.p]#+A[pred,v,vI.p].fuel
            #rhs = max_takeoff_payload[A[pred,v,vI.p].origin,vI.p]
            model.linear_constraints.add(names = ["maxweighttakeoff_" + v + "_" + pred], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs])
    
    
    for v,vI in V.iteritems():
        thevars = [fuel[v],w[v]]
        thecoefs = [1.0,1.0]
        rhs = max_landing_payload[vI.airport,vI.p]
        model.linear_constraints.add(names = ["maxweightlanding_" + v + "_" + pred], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs])
    
            
        
    #max_detour
    for p in PLANE:
        for r in REQUEST:
            thevars = [dist[R_s[p][r].name],dist[R_d[p][r].name]]
            thecoefs = [-1.0,1.0]
            rhs = (1 + REQUEST[r].max_detour) * TRIP0[REQUEST[r].request_departure,REQUEST[r].request_arrival].distance
            model.linear_constraints.add(names = ["maxdetour_" + p + "_" + r], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs])
           
    #max_stops
    for p in PLANE:
        for r in REQUEST:
            thevars = [stops[R_s[p][r].name],stops[R_d[p][r].name]]
            thecoefs = [-1.0,1.0]
            rhs = REQUEST[r].max_stops+1
            model.linear_constraints.add(names = ["maxstops_" + p + "_" + r], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs])
       
    #max_fuel
    for v,vI in V.iteritems():
        for pred in vI.predecessors:
            thevars = [fuel[pred],y[pred,v,vI.p]]
            thecoefs = [1.0,A[pred,v,vI.p].fuel]
            rhs = max_trip_fuel[A[pred,v,vI.p].origin,A[pred,v,vI.p].destination,vI.p]#A[pred,v,vI.p].fuel
            model.linear_constraints.add(names = ["maxtripfuel_" + v + "_" + pred], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs])
    
    for p,i,j in TIMEFREEPLANESOLUTION:
        for a,aI in A.iteritems():
            if a[2]==p and aI.origin == i and aI.destination == j:
                model.variables.set_upper_bounds([(y[a[0],a[1],a[2]],1.0)])
    
    # set time limit
    model.parameters.timelimit.set(10800) # 10800 = 3h, 86400 = one day (24h)
    #model.parameters.workmem.set(4096.0) # working memory
    
    
    # solve again
    
    model.write("model.lp")
    name2idx = { n : j for j, n in enumerate(model.variables.get_names()) }
    
    printy=1
    model.solve()
    solution=model.solution
    if solution.is_primal_feasible():
        print "Solution value = ", solution.get_objective_value()
    for a,aI in A.iteritems():
        model.variables.set_upper_bounds([(y[a[0],a[1],a[2]],1.0)])
    
    model.solve()
    solution=model.solution
    if solution.is_primal_feasible():
        print "Solution value = ", solution.get_objective_value()
        if printy:
            solutionValues=model.solution.get_values()
            idx2name = { j : n for j, n in enumerate(model.variables.get_names()) }
            name2idx = { n : j for j, n in enumerate(model.variables.get_names()) }
            name2solutionValue = { n : solutionValues[j] for j, n in enumerate(model.variables.get_names()) }
            for key,val in seatNum.iteritems():
                valStore=solutionValues[name2idx[val]]
                if valStore > 0.5 or valStore < -0.5:
                    print(val+" %f" %valStore)
    else:
        print "No solution available."

    # report solution
    solutionTime[instanceName] = time.time() - t0
    print "total time: ",time.time() - t0
    
    file = open("results.txt", "a")
    lineToAdd = instanceName + ", " + str(int(bestDualBound[instanceName]))+ ", " + str(int(bestSolution[instanceName]))
    lineToAdd += ", " + str(bestGap[instanceName]*100) + "%, " +str(int(solutionTime[instanceName]))+ "\n"
    file.write(lineToAdd)
    file.close()
    
