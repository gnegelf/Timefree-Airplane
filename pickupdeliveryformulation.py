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
    def __init__(self,distance,fuel,stops,seats,traveltime):
        self.distance=distance
        self.fuel=fuel
        self.stops=stops
        self.seats=seats
        self.traveltime=traveltime

class __VERTEX__(object):
    def __init__(self,name,arrival_time,departure_time):
        self.name=name
        self.arrival_time=arrival_time
        self.departure_time=departure_time
        self.successors = []
        self.predecessors = []
# prepare reading and parsing

comment_line = re.compile('#');

#directory = sys.argv[1]
#strategy = sys.argv[2]

restart = 1

directories = {#'BUF-AIV':'Testinstances/A2-BUF_A2-AIV',#check
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
               'EGL-GNU':'Testinstances/A2-EGL_A2-GNU',#check
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
               #'#LEO-OWL':'Testinstances/A2-LEO_A2-OWL'#check
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
            max_trip_payload[i,j,p] = min(max_takeoff_payload[i,p] + fuelconsumption[i,j,p], max_landing_payload[j,p])
        
        
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
        
        
    A = {}
    V = {}
    P_s = {}
    P_d = {}
    
    for p in PLANE:
        P_s[p] = __VERTEX__(p + "_" + "ori_" + PLANE[p].origin,plane_min_timestep[p],plane_max_timestep[p])
        P_d[p] = __VERTEX__(p + "_" + "desti_" + PLANE[p].destination,plane_min_timestep[p],plane_max_timestep[p])
        V[P_s[p].name]= P_s[p]
        V[P_d[p].name]= P_d[p]
    
    R_s = {}
    R_d = {}
    
    for p in PLANE:
        R_s[p] = {}
        R_s[p] = {}
        for r in REQUEST:
            R_s[p][r] = __VERTEX__(r + "_" + p + "_" + "ori_" + REQUEST[r].origin,min(REQUEST_TIMESTEP[r]),max(REQUEST_TIMESTEP[r]))
            R_d[p][r] = __VERTEX__(r + "_" + p + "_" + "desti_" + REQUEST[r].destination,min(REQUEST_TIMESTEP[r]),max(REQUEST_TIMESTEP[r]))
            V[R_s[p][r].name] = P_s[p][r]
            V[R_d[p][r].name] = P_d[p][r]
    
    fuelstops=3
    F = {}
    
    for p in PLANE:
        F[p] = {}
        for f in AIRPORT:
            if AIRPORT[j].fuel[PLANE[p].required_fueltype] != '0':
                for i in range(0,fuelstops):
                    F[p][f,i] =  __VERTEX__(p + "_" + "fuel_%d" % i + f,plane_min_timestep[p],plane_max_timestep[p])
                    V[F[p][f].name] = F[p][f,i]
    
    
    for p,vI in P_s.iteritems():
        for f in F[p]:
            vI.successors.append(F[p][f].name)
            v1=PLANE[p].origin
            v2=f[0]
            A[vI.name,F[p][f].name] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1==v2),0,
             turnover_travel_timesteps[v1,v2,p])
        for r in R_s[p]:
            vI.successors.append(R_s[p][r].name)
            v1 = PLANE[p].origin
            v2 = REQUEST[r].origin
            A[vI.name,R_s[p][r].name] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1==v2),0,
             turnover_travel_timesteps[v1,v2,p])
        vI.succesors.append(P_d[p].name)
        v1 = PLANE[p].origin
        v2 = PLANE[p].destination
        A[vI.name,P_d[p].name] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1==v2),0,
             turnover_travel_timesteps[v1,v2,p])
    
    for p,vI in P_d.iteritems():
        for f in F[p]:
            vI.predecessors.append(F[p][f].name)
            v1=f[0]
            v2=PLANE[p].destination
            A[F[p][f].name,vI.name] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1==v2),0,
             turnover_travel_timesteps[v1,v2,p])
        for r in R_d[p]:
            vI.predecessors.append(R_d[r].name)
            v1 = REQUEST[r].destination
            v2 = PLANE[p].destination
            A[R_d[p][r].name,vI.name] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1==v2),0,
             turnover_travel_timesteps[v1,v2,p])
        vI.predecesors.append(P_s[p].name)
    
    for p in PLANE:
        for r,vI in R_s[p].iteritems():
            vI.predecessors.append(P_s[p].name)
            for r2 in R_d[p]:
                vI.successors.append(R_d[p][r2].name)#TODO: condition on time windows
                v1 = REQUEST[r].origin
                v2 = REQUEST[r2].destination
                A[vI.name,R_d[p][r2].name] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1==v2),REQUEST[r].seats,
                     turnover_travel_timesteps[v1,v2,p])
                if r2 != r:
                    vI.predecessors.append(R_d[p][r2].name)#TODO: condition on time windows
            for r2 in R_s[p]:
                if r != r2:
                    vI.successors.append(R_s[p][r2].name)#TODO: condition on time windows
                    v1 = REQUEST[r].origin
                    v2 = REQUEST[r2].origin
                    A[vI.name,R_s[p][r2].name] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1==v2),REQUEST[r].seats,
                         turnover_travel_timesteps[v1,v2,p])
                    vI.predecessors.append(R_s[p][r2].name)#TODO: condition on time windows
            for f in F[p]:
                vI.successors.append(F[p][f].name)
                vI.predecessors.append(F[p][f].name)
                v1 = REQUEST[r].origin
                v2 = f[0]
                A[vI.name,F[p][f].name] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1==v2),0,
                         turnover_travel_timesteps[v1,v2,p])
                v2 = REQUEST[r].origin
                v1 = f[0]
                A[F[p][f].name,vI.name] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1==v2),0,
                         turnover_travel_timesteps[v1,v2,p])
    
    for p in PLANE:
        for r,vI in R_d[p].iteritems():
            vI.successors.append(P_d[p].name)
            for r2 in R_d[p]:
                if r != r2:
                    vI.successors.append(R_d[p][r2].name)#TODO: condition on time windows
                    v1 = REQUEST[r].destination
                    v2 = REQUEST[r2].destination
                    A[vI.name,R_d[p][r2].name] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1==v2),0,
                         turnover_travel_timesteps[v1,v2,p])
                    vI.predecessors.append(R_d[p][r2].name)#TODO: condition on time windows
            for r2 in R_s[p]:
                if r2 != r:
                    vI.successors.append(R_s[p][r2].name)#TODO: condition on time windows
                    v1 = REQUEST[r].destination
                    v2 = REQUEST[r2].origin
                    A[vI.name,R_s[p][r2].name] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1==v2),0,
                         turnover_travel_timesteps[v1,v2,p])
                vI.predecessors.append(R_s[p][r2].name)#TODO: condition on time windows
            for f in F[p]:
                vI.successors.append(F[p][f].name)
                vI.predecessors.append(F[p][f].name) 
                v1 = REQUEST[r].destination
                v2 = f[0]
                A[vI.name,F[p][f].name] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1==v2),0,
                         turnover_travel_timesteps[v1,v2,p])
                v2 = REQUEST[r].destination
                v1 = f[0]
                A[F[p][f].name,vI.name] = __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1==v2),0,
                         turnover_travel_timesteps[v1,v2,p])
    
    for p in F:
        for f,vI in F[p].iteritems:
            for p in P_s:
                vI.predecessors.append(P_s[p].name)
            for p in P_d:
                vI.successors.append(P_d[p].name)

            for r in R_d[p]:
                vI.successors.append(R_d[p][r].name)
                vI.predecessors.append(R_d[p][r].name)
            for r in R_s[p]:
                vI.successors.append(R_s[p][r].name)
                vI.predecessors.append(R_s[p][r].name)
            for f2 in F[p]:
                if f[0] != f2[0]:
                    vI.successors.append(F[p][f2].name)
                    v1 = f[0]
                    v2 = f2[0]
                    A[F[p][f].name,F[p][f2].name] =  __ARC__(TRIP[v1,v2].distance,fuelconsumption[v1,v2,p],int(v1==v2),0,
                         turnover_travel_timesteps[v1,v2,p])
                    vI.predecessors.append(F[p][f2].name)
    
    # ----------------
    # MODEL GENERATION
    # ----------------
    
    
    t0 = time.time()
    model = cplex.Cplex()
    
    
    # VARIABLES
    
    y = {}
    
    
    for i,j in TRIP0:
      for p in PLANE:
          for n1 in AirportNum[p,i]:
              for n2 in AirportNum[p,j]:
                  if n1 == AirportNum[p,i][-1] and n2 == AirportNum[p,j][-1]:
                      y[i,j,p,n1,n2] = "y#" + i  + "_" + j  + "_" + p + "_" + str(n1) + "_" + str(n2)
                      model.variables.add(obj = [travelcost[i,j,p]], names = [y[i,j,p,n1,n2]], lb = [0], types = ["I"])
                      number_of_variables += 1
                  else:
                      y[i,j,p,n1,n2] = "y#" + i + "_" + j + "_" + p  + "_" + str(n1) + "_" + str(n2)
                      model.variables.add(obj = [travelcost[i,j,p]], names = [y[i,j,p,n1,n2]], lb = [0], types = ["B"])
                      number_of_variables += 1
    
    y_dep = {}
    
    for p in PLANE:
        for n1 in AirportNum[p,PLANE[p].origin]:
          y_dep[p,n1] = "y_dep#" + p + str(n1)
          model.variables.add(names = [y_dep[p,n1]], lb = [0], ub = [1], types = ["B"])
          number_of_variables += 1
    
    y_arr = {}
    
    for p in PLANE:
        for n1 in AirportNum[p,PLANE[p].destination]:
          y_arr[p,n1] = "y_arr#" + p + str(n1)
          model.variables.add(names = [y_arr[p,n1]], lb = [0], ub = [1],types = ["B"])
          number_of_variables += 1
    
    f = {}
    
    for i,j in TRIP0:
      for p in PLANE:
          for n1 in AirportNum[p,i]:
              for n2 in AirportNum[p,j]:
                f[i,j,p,n1,n2] = "f#" + i + "_" + j + "_" + p + "_" + str(n1) + "_" + str(n2)
                model.variables.add(names = [f[i,j,p,n1,n2]], lb = [0], types = ["C"])
                number_of_variables += 1
    
    f_dep = {}
    
    for p in PLANE:
        for n1 in AirportNum[p,PLANE[p].origin]:
          f_dep[p,n1] = "f_dep#" + p + str(n1)
          #model.variables.add(names = [f_dep[p,n1]], lb = [PLANE[p].departure_min_fuel], ub = [PLANE[p].departure_max_fuel], types = ["C"])
          model.variables.add(names = [f_dep[p,n1]], lb = [0.0], ub = [PLANE[p].departure_max_fuel], types = ["C"])
          number_of_variables += 1
    
    f_arr = {}
    
    for p in PLANE:
        for n1 in AirportNum[p,PLANE[p].destination]:
          f_arr[p,n1] = "f_arr#" + p + str(n1)
          #model.variables.add(names = [f_arr[p,n1]], lb = [PLANE[p].arrival_min_fuel], ub = [PLANE[p].arrival_max_fuel], types = ["C"])
          model.variables.add(names = [f_arr[p,n1]], lb = [0.0], ub = [PLANE[p].arrival_max_fuel], types = ["C"])
          number_of_variables += 1
    
    if timeflow:
        d = {}
        
        for i,j in TRIP0:
          for p in PLANE:
              for n1 in AirportNum[p,i]:
                  for n2 in AirportNum[p,j]:
                    d[i,j,p,n1,n2] = "t#" + i + str(n1) + "_" + j + str(n2) + "_" + p 
                    model.variables.add(names = [d[i,j,p,n1,n2]], lb = [0], types = ["C"])
                    number_of_variables += 1
        
        d_dep = {}
        
        for p in PLANE:
            for n1 in AirportNum[p,PLANE[p].origin]:
              d_dep[p,n1] = "t_dep#" + p + str(n1)
              model.variables.add(names = [d_dep[p,n1]], lb = [0], ub = [plane_min_timestep[p]], types = ["C"])
              number_of_variables += 1
        
        d_arr = {}
        
        for p in PLANE:
            for n1 in AirportNum[p,PLANE[p].destination]:
              d_arr[p,n1] = "t_arr#" + p + str(n1)
              model.variables.add(names = [d_arr[p,n1]], lb = [0], ub = [plane_max_timestep[p]], types = ["C"])
              number_of_variables += 1
    
    w = {}
    
    for i,j in TRIP0:
      for p in PLANE:
          for n1 in AirportNum[p,i]:
              for n2 in AirportNum[p,j]:
                w[i,j,p,n1,n2] = "w#" + i + str(n1) + "_" + j + str(n2) + "_" + p
                model.variables.add(names = [w[i,j,p,n1,n2]], lb = [0], types = ["C"])
                number_of_variables += 1
    
    print "number of variables: ",number_of_variables
    
    name2idx = { n : j for j, n in enumerate(model.variables.get_names()) }
    x_indices = [name2idx[name] for name in x.values()+x_arr.values()+x_dep.values() ]
    y_indices = [ name2idx[name] for name in y.values()]
    cb_indices = x_indices+y_indices
    # OBJECTICE 
    
    model.objective.set_sense(model.objective.sense.minimize)
    
    
    # CONSTRAINTS
    
    number_of_constraints = 0
    number_of_nonzeros = 0
    
    #lower airports first
    for p in PLANE:
        for j in AIRPORT:
             for n1 in AirportNum[p,j]:
                 if n1 != AirportNum[p,j][-1]:
                     thevars = [y[i,j,p,n2,n1] for i in AIRPORT if (i,j) in TRIP0 for n2 in AirportNum[p,i]]
                     thecoefs = [1.0]*len(thevars)
                     
                     model.linear_constraints.add(names = ["max_one_ingoing" + p + "_" + j + str(n1)], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [1.0])
                     number_of_constraints += 1
            
                     thevars = [y[j,i,p,n1,n2] for i in AIRPORT if (j,i) in TRIP0 for n2 in AirportNum[p,i]]
                     thecoefs = [1.0]*len(thevars)
                     
                     model.linear_constraints.add(names = ["max_one_outgoing" + p + "_" + j + str(n1)], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [1.0])
                     number_of_constraints += 1
    
    for p in PLANE:
        for j in AIRPORT:
             for n1ind,n1 in enumerate(AirportNum[p,j]):
                 if n1ind != 0:
                     thevars = [y[i,j,p,n2,n1] for i in AIRPORT if (i,j) in TRIP0 for n2 in AirportNum[p,i]]
                     thecoefs = [1.0]*len(thevars)
                     
                     thevars += [y[j,i,p,AirportNum[p,j][n1ind-1],n2] for i in AIRPORT if (j,i) in TRIP0 for n2 in AirportNum[p,i]]
                     thecoefs += [-5.0 for i in AIRPORT if (j,i) in TRIP0 for n2 in AirportNum[p,i]]
                     
                     model.linear_constraints.add(names = ["bounded by previous outgoing" + p + "_" + j + str(n1)], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                     number_of_constraints += 1
                     
                     thevars = [y[j,i,p,n1,n2] for i in AIRPORT if (i,j) in TRIP0 for n2 in AirportNum[p,i]]
                     thecoefs = [1.0]*len(thevars)
                     
                     thevars += [y[j,i,p,AirportNum[p,j][n1ind-1],n2] for i in AIRPORT if (i,j) in TRIP0 for n2 in AirportNum[p,i]]
                     thecoefs += [-5.0 for i in AIRPORT if (i,j) in TRIP0 for n2 in AirportNum[p,i]]
                     
                     model.linear_constraints.add(names = ["bounded by previous outgoing" + p + "_" + j + str(n1)], 
                                                           lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                     number_of_constraints += 1
                     
    
    for p in PLANE:
        if len(AirportNum[p,PLANE[p].origin]) > 1:
            thevars = [y[i,PLANE[p].origin,p,n2,1] for i in AIRPORT if (i,PLANE[p].origin) in TRIP0 for n2 in AirportNum[p,i]]
            thecoefs = [1.0]*len(thevars)
            
            model.linear_constraints.add(names = ["no return to start" + p ],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
    
    
    for p in PLANE:
        for n1 in AirportNum[p,PLANE[p].origin]:
            thevars = [y_dep[p,n1],f_dep[p,n1]]
            thecoefs = [-PLANE[p].departure_min_fuel,1.0]
            
            model.linear_constraints.add(names = ["plane_fueldep_" + p + str(n1)], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])
            number_of_constraints += 1
            
            thevars = [y_dep[p,n1],f_dep[p,n1]]
            thecoefs = [-PLANE[p].departure_max_fuel,1.0]
            
            model.linear_constraints.add(names = ["plane_fueldep2_" + p + str(n1)], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
            number_of_constraints += 1
            
            if timeflow:
                thevars = [y_dep[p,n1],d_dep[p,n1]]
                thecoefs = [-plane_min_timestep[p],1.0]
                
                model.linear_constraints.add(names = ["plane_timedep_" + p + str(n1)], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])
                number_of_constraints += 1
                
                thevars = [y_dep[p,n1],d_dep[p,n1]]
                thecoefs = [-plane_min_timestep[p],1.0]
                
                model.linear_constraints.add(names = ["plane_timedep2_" + p + str(n1)], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                number_of_constraints += 1
        
        for n1 in AirportNum[p,PLANE[p].destination]:
            thevars = [y_arr[p,n1],f_arr[p,n1]]
            thecoefs = [-PLANE[p].arrival_min_fuel,1.0]
            
            model.linear_constraints.add(names = ["plane_fuelarr_" + p + str(n1)], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])
            number_of_constraints += 1
            
            thevars = [y_arr[p,n1],f_arr[p,n1]]
            thecoefs = [-PLANE[p].arrival_max_fuel,1.0]
            
            model.linear_constraints.add(names = ["plane_fuelarr2_" + p + str(n1)], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
            number_of_constraints += 1
            
            if timeflow:
                thevars = [y_arr[p,n1],d_arr[p,n1]]
                thecoefs = [-plane_max_timestep[p],1.0]
                
                model.linear_constraints.add(names = ["plane_timearr_" + p + str(n1)], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                number_of_constraints += 1
    
    # each request must depart
    
    for r in REQUEST:
          thevars = []
          thecoefs = []
          for p in PLANE:
              for n1 in AirportNum[p,REQUEST[r].origin]:
                thevars.append(x_dep[r,p,n1])
                thecoefs.append(1.0)
                number_of_nonzeros += 1
                
          model.linear_constraints.add(names = ["request_one_dep_" + r], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
          number_of_constraints += 1
    
    
    # each request must arrive
    
    for r in REQUEST:
      thevars = []
      thecoefs = []
      for p in PLANE:
          for n1 in AirportNum[p,REQUEST[r].destination]:
            thevars.append(x_arr[r,p,n1])
            thecoefs.append(1.0)
            number_of_nonzeros += 1
        
      model.linear_constraints.add(names = ["request_one_arr_" + r], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
      number_of_constraints += 1
      
    
    # request flow
    
    for r in REQUEST:
      for p in PLANE:
        for j in AIRPORT:
            for n2 in AirportNum[p,j]:
              thevars = []
              thecoefs = []
        
              for i in AIRPORT:
                if (i,j) in REQUEST_TRIP0[r]:
                    for n1 in AirportNum[p,i]:
                          thevars.append(x[i,j,r,p,n1,n2])
                          thecoefs.append(1.0)
                          number_of_nonzeros += 1
              
              if j == REQUEST[r].request_departure:
                thevars.append(x_dep[r,p,n2])
                thecoefs.append(1.0)
                number_of_nonzeros += 1
                
              for k in AIRPORT:
                if (j,k) in REQUEST_TRIP0[r]:
                    for n1 in AirportNum[p,k]:
                      thevars.append(x[j,k,r,p,n2,n1])
                      thecoefs.append(-1.0)
                      number_of_nonzeros += 1
                  
              if j == REQUEST[r].request_arrival:
                thevars.append(x_arr[r,p,n2])
                thecoefs.append(-1.0)
                number_of_nonzeros += 1
                
              model.linear_constraints.add(names = ["request_flow_" + r + "_" + p + "_" + j + str(n2)],
                                                    lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
              number_of_constraints += 1
             
    
    # airplane flow
    
    
    for p in PLANE:
      thevars = []
      thecoefs = []
      for n1 in AirportNum[p,PLANE[p].origin]:
        thevars.append(y_dep[p,n1])
        thecoefs.append(1.0)
        number_of_nonzeros += 1
            
      model.linear_constraints.add(names = ["plane_one_dep_" + p], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
      number_of_constraints += 1
    
    
    for p in PLANE:
      thevars = []
      thecoefs = []
      for n1 in AirportNum[p,PLANE[p].destination]:
        thevars.append(y_arr[p,n1])
        thecoefs.append(1.0)
        number_of_nonzeros += 1
            
      model.linear_constraints.add(names = ["plane_one_arr_" + p], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
      number_of_constraints += 1
    
    for p in PLANE:
      for j in AIRPORT:
          for n2 in AirportNum[p,j]:
            #print p,i
            rhs_value = 0.0
            thevars = []
            thecoefs = []
                
            for i in AIRPORT:
              if (i,j) in TRIP0:
                  for n1 in AirportNum[p,i]:
                    thevars.append(y[i,j,p,n1,n2])
                    thecoefs.append(1.0)
                    number_of_nonzeros += 1
                
            if j == PLANE[p].plane_departure:
                thevars.append(y_dep[p,n2])
                #rhs_value += -1.0
                thecoefs.append(1.0)
                number_of_nonzeros += 1
              
            for k in AIRPORT:
              if (j,k) in TRIP0:
                  for n1 in AirportNum[p,k]:
                    thevars.append(y[j,k,p,n2,n1])
                    thecoefs.append(-1.0)
                    number_of_nonzeros += 1
            
            if j == PLANE[p].plane_arrival:
              #rhs_value += 1.0
              thevars.append(y_arr[p,n2])
              thecoefs.append(-1.0)
              number_of_nonzeros += 1
            
            model.linear_constraints.add(names = ["plane_flow_" + p + "_" + j + str(n2)], 
                                                  lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [rhs_value])
            number_of_constraints += 1
    
    
    # seat limit
    
    for i,j in TRIP0:
        for p in PLANE:
          for n1 in AirportNum[p,i]:
             for n2 in AirportNum[p,j]:
              
                #print i,j,p
                thevars = [y[i,j,p,n1,n2]]
                thecoefs = [-PLANE[p].seats]
                number_of_nonzeros += 1
                
                for r in REQUEST:
                  if (i,j) in REQUEST_TRIP0[r]:
                    thevars.append(x[i,j,r,p,n1,n2])
                    thecoefs.append(REQUEST[r].passengers)
                    number_of_nonzeros += 1
                  
                model.linear_constraints.add(names = ["seatlimit_" + i + str(n1) + "_" + j + "_" + p + str(n2)], 
                                                      lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                number_of_constraints += 1
    
    
    # intermediate stops for requests
    
    for r in REQUEST:
      thevars = []
      thecoefs = []
      #print r
        
      for i,j in REQUEST_TRIP0[r]:
          for p in PLANE:
              for n1 in AirportNum[p,i]:
                for n2 in AirportNum[p,j]: 
                  thevars.append(x[i,j,r,p,n1,n2])
                  thecoefs.append(1.0)
                  number_of_nonzeros += 1
                
      model.linear_constraints.add(names = ["intermediatestops_" + r], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [REQUEST[r].max_stops + 1])
      number_of_constraints += 1
    
    
    # maximum detour for passengers (compared to direct flight)
    
    for r in REQUEST:
      thevars = []
      thecoefs = []
      
      for i,j in REQUEST_TRIP0[r]:
        for p in PLANE:
            for n1 in AirportNum[p,i]:
                for n2 in AirportNum[p,j]:
                  thevars.append(x[i,j,r,p,n1,n2])
                  thecoefs.append(TRIP0[i,j].distance)
                  number_of_nonzeros += 1
      
      model.linear_constraints.add(names = ["maxdetour_" + r], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [(1 + REQUEST[r].max_detour) * TRIP0[REQUEST[r].request_departure,REQUEST[r].request_arrival].distance])
      number_of_constraints += 1
      
    
    # fueling constraints
    
    for i,j in TRIP0:
        for p in PLANE:
          for n1 in AirportNum[p,i]:
              for n2 in AirportNum[p,j]:
              
                #print i,j,p
                thevars = [f[i,j,p,n1,n2],y[i,j,p,n1,n2]]
                thecoefs = [1.0,-max_trip_fuel[i,j,p]]
                number_of_nonzeros += 2
                
                model.linear_constraints.add(names = ["noflight_nofuel_" + i + str(n1) + "_" + j + "_" + p + str(n2)], 
                                                      lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                number_of_constraints += 1
    
    
    for j in AIRPORT:
        for p in PLANE:
          for n2 in AirportNum[p,j]:
          
            #print j,p
            thevars = []
            thecoefs = []
                    
            for i in AIRPORT:
              if (i,j) in TRIP0:
                  for n1 in AirportNum[p,i]:
                    thevars.append(f[i,j,p,n1,n2])
                    thecoefs.append(1.0)
                    number_of_nonzeros += 1
                    
            if j == PLANE[p].plane_departure:
              thevars.append(f_dep[p,n2])
              thecoefs.append(1.0)
              number_of_nonzeros += 1
                    
            for k in AIRPORT:
              if (j,k) in TRIP0:
                  for n1 in AirportNum[p,k]:
                    thevars.append(f[j,k,p,n2,n1])
                    thecoefs.append(-1.0)
                    number_of_nonzeros += 1
                    
                    thevars.append(y[j,k,p,n2,n1])
                    thecoefs.append(-fuelconsumption[j,k,p])
                    number_of_nonzeros += 1
                    
            if j == PLANE[p].plane_arrival:
              thevars.append(f_arr[p,n2])
              thecoefs.append(-1.0)
              number_of_nonzeros += 1
                    
            if AIRPORT[j].fuel[PLANE[p].required_fueltype] == '0':
              model.linear_constraints.add(names = ["fuelconsumption_" + j + "_" + p + str(n2)], 
                                                    lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
              number_of_constraints += 1
            else:
              model.linear_constraints.add(names = ["refueling_" + j + "_" + p + str(n2)], 
                                                    lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
              number_of_constraints += 1
    
    # time constraints
    
    if timeflow:
        for i,j in TRIP0:
            for p in PLANE:
              for n1 in AirportNum[p,i]:
                  for n2 in AirportNum[p,j]:
                  
                    #print i,j,p
                    thevars = [d[i,j,p,n1,n2],y[i,j,p,n1,n2]]
                    thecoefs = [1.0,-plane_max_timestep[p]]
                    number_of_nonzeros += 2
                    
                    model.linear_constraints.add(names = ["noflight_notime_" + i + str(n1) + "_" + j + str(n2) + "_" + p], 
                                                 lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                    number_of_constraints += 1
        
        for i,j in TRIP0:
            for p in PLANE:
                for n1 in AirportNum[p,i]:
                    for n2 in AirportNum[p,j]:
                      
                        #print i,j,p
                        thevars = [d[i,j,p,n1,n2],y[i,j,p,n1,n2]]
                        thecoefs = [1.0,-plane_min_timestep[p]]
                        
                        model.linear_constraints.add(names = ["aflight_atime_" + i + str(n1) + "_" + j + str(n2) + "_" + p], 
                                                     lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [0.0])
        
        
        for j in AIRPORT:
            for p in PLANE:
              for n2 in AirportNum[p,j]:
              
                #print j,p
                thevars = []
                thecoefs = []
                        
                for i in AIRPORT:
                  if (i,j) in TRIP0:
                      for n1 in AirportNum[p,i]:
                        thevars.append(d[i,j,p,n1,n2])
                        thecoefs.append(1.0)
                        number_of_nonzeros += 1
                        
                        thevars.append(y[i,j,p,n1,n2])
                        thecoefs.append(turnover_travel_timesteps[i,j,p])
                        number_of_nonzeros += 1
                    
                if j == PLANE[p].plane_departure:
                  thevars.append(d_dep[p,n2])
                  thecoefs.append(1.0)
                  number_of_nonzeros += 1
                        
                for k in AIRPORT:
                  if (j,k) in TRIP0:
                      for n1 in AirportNum[p,k]:
                        thevars.append(d[j,k,p,n2,n1])
                        thecoefs.append(-1.0)
                        number_of_nonzeros += 1
                    
                    
                        
                if j == PLANE[p].plane_arrival:
                  thevars.append(d_arr[p,n2])
                  thecoefs.append(-1.0)
                  number_of_nonzeros += 1
                        
                model.linear_constraints.add(names = ["timeconsumption_" + j + str(n2) + "_" + p], 
                                                        lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                number_of_constraints += 1
        
        for r in REQUEST:
            for p in PLANE:
                for i,j in REQUEST_TRIP0[r]:
                    for n1 in AirportNum[p,i]:
                        for n2 in AirportNum[p,j]:
                            if not( n1==AirportNum[p,i][-1] and n2 == AirportNum[p,j][-1] ):
                                thevars = [d[i,j,p,n1,n2],x[i,j,r,p,n1,n2]]
                                thecoefs = [1,plane_max_timestep[p]]
                                rhs = latest_arrival_timesteps[r]+plane_max_timestep[p]-turnover_travel_timesteps[i,j,p]#+turnover_timesteps[i,p]#TODO: Verify this timewindow
                                number_of_nonzeros += 2
                                        
                                model.linear_constraints.add(names = ["timewindow1_" + i + str(n1) + '_' + j + str(n2) + '_' + r + "_" + p], 
                                                             lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs])
                                
                                number_of_constraints += 1
                                thecoefs = [1,-plane_max_timestep[p]]
                                rhs = earliest_departure_timesteps[r]-plane_max_timestep[p]-max_turnover_timesteps[r]
                                number_of_nonzeros += 2
                                        
                                model.linear_constraints.add(names = ["timewindow2_" + i + str(n1) + '_' + j + str(n2) + '_' + r + "_" + p], 
                                                             lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [rhs])
                                
                                number_of_constraints += 1
                            else:
                                m="di"+str(i)+str(j)+str(r)+str(p)+str(n1)+str(n2)
                                model.variables.add( names = [m], lb = [0],  types = ["I"])
                                thevars = [m,y[i,j,p,n1,n2],x[i,j,r,p,n1,n2]]
                                thecoefs = [1,-1,1]
                                number_of_variables += 1
                                model.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                                number_of_constraints += 1
                                
                                thevars = [d[i,j,p,n1,n2],x[i,j,r,p,n1,n2],m]
                                thecoefs = [1,plane_max_timestep[p],-plane_max_timestep[p]]
                                rhs = latest_arrival_timesteps[r]+plane_max_timestep[p]-turnover_travel_timesteps[i,j,p]#+turnover_timesteps[i,p]#TODO: Verify this timewindow
                                number_of_nonzeros += 3
                                        
                                model.linear_constraints.add(names = ["timewindow1_" + i + str(n1) + '_' + j + str(n2) + '_' + r + "_" + p], 
                                                             lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs])
                                
                                number_of_constraints += 1
                                
                                
                                thevars = [d[i,j,p,n1,n2],x[i,j,r,p,n1,n2]]
                                thecoefs = [1,-plane_max_timestep[p]]
                                rhs = earliest_departure_timesteps[r]-plane_max_timestep[p]-max_turnover_timesteps[r]
                                number_of_nonzeros += 3
                                        
                                model.linear_constraints.add(names = ["timewindow2_" + i + str(n1) + '_' + j + str(n2) + '_' + r + "_" + p], 
                                                             lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [rhs])
                                
                                number_of_constraints += 1
        
    # weight limit (=max fuel)
    
    for i,j in TRIP0:
        for p in PLANE:
          for n1 in AirportNum[p,i]:
              for n2 in AirportNum[p,j]:
              
                #print i,j,p
                thevars = [w[i,j,p,n1,n2]]
                thecoefs = [1.0]
                number_of_nonzeros += 1
            
                for r in REQUEST:
                  if (i,j) in REQUEST_TRIP0[r]:
                    thevars.append(x[i,j,r,p,n1,n2])
                    thecoefs.append(-REQUEST[r].weight)
                    number_of_nonzeros += 1
            
                thevars.append(f[i,j,p,n1,n2])
                thecoefs.append(-1.0)
                number_of_nonzeros += 1
                    
                model.linear_constraints.add(names = ["computeweight_" + i + str(n1) + '_' + j + str(n2) + "_" + p], 
                                                      lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
                number_of_constraints += 1
    
    
    for i,j in TRIP0:
        for p in PLANE:
          for n1 in AirportNum[p,i]:
              for n2 in AirportNum[p,j]:
              
                #print i,j,p
                thevars = [w[i,j,p,n1,n2],y[i,j,p,n1,n2]]
                thecoefs = [1.0,-max_trip_payload[i,j,p]]
                number_of_nonzeros += 2
            
                model.linear_constraints.add(names = ["weightlimit_" + i + str(n1) + '_' + j + str(n2) + "_" + p], 
                                             lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                number_of_constraints += 1
    
    
    # minimum number of fuelstops
    
    for p in PLANE:
      if PLANE[p].departure_max_fuel - fuelconsumption[PLANE[p].plane_departure,PLANE[p].plane_arrival,p] < PLANE[p].arrival_min_fuel:
        #print p
        thevars = []
        thecoefs = []
    
        for i,j in TRIP0:
          if AIRPORT[j].fuel[PLANE[p].required_fueltype] == '1':
              for n1 in AirportNum[p,i]:
                  for n2 in AirportNum[p,j]:
                    thevars.append(y[i,j,p,n1,n2])
                    thecoefs.append(1.0)
                    number_of_nonzeros += 1
            
        model.linear_constraints.add(names = ["minfuelstops_in_" + p], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])
        number_of_constraints += 1
    
    for p in PLANE:    
      if PLANE[p].departure_max_fuel - fuelconsumption[PLANE[p].plane_departure,PLANE[p].plane_arrival,p] < PLANE[p].arrival_min_fuel:
        #print p
        thevars = []
        thecoefs = []
    
        for i,j in TRIP0:
          if AIRPORT[i].fuel[PLANE[p].required_fueltype] == '1':
              for n1 in AirportNum[p,i]:
                  for n2 in AirportNum[p,j]:
                    thevars.append(y[i,j,p,n1,n2])
                    thecoefs.append(1.0)
                    number_of_nonzeros += 1
            
        model.linear_constraints.add(names = ["minfuelstops_out_" + p], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])
        number_of_constraints += 1
       
    
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
                for n1 in AirportNum[p,i]:
                    for n2 in AirportNum[p,j]:
                    
                      thevars.append(y[i,j,p,n1,n2])
                      thecoefs.append(1.0)
                      number_of_nonzeros += 1
    
        rhs_value = 0
        
        for r in REQUEST:
          if REQUEST[r].request_departure == i or REQUEST[r].request_arrival == i:
            rhs_value += 1
        
        for p in PLANE:
          if PLANE[p].plane_departure == i:
            rhs_value += 1
        
        model.linear_constraints.add(names = ["maxpickup_out_" + i], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs_value])
        number_of_constraints += 1
    
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
                for n1 in AirportNum[p,i]:
                    for n2 in AirportNum[p,j]:
                    
                      thevars.append(y[i,j,p,n1,n2])
                      thecoefs.append(1.0)
                      number_of_nonzeros += 1
    
        rhs_value = 0
        
        for r in REQUEST:
          if REQUEST[r].request_departure == j or REQUEST[r].request_arrival == j:
            rhs_value += 1
        
        for p in PLANE:
          if PLANE[p].plane_arrival == j:
            rhs_value += 1
            
        model.linear_constraints.add(names = ["maxpickup_in_" + j], lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [rhs_value])
        number_of_constraints += 1
    
    
    # minimum amount of fuel for detour to refueling airport
    
    for i,j in TRIP0:
        for p in PLANE:
          for n1 in AirportNum[p,i]:
              for n2 in AirportNum[p,j]:
              
                thevars = [y[i,j,p,n1,n2],f[i,j,p,n1,n2]]
                thecoefs = [min_refuel_trip[j,p],-1.0]
                number_of_nonzeros += 2
                
                model.linear_constraints.add(names = ["minfuel_" + i + str(n1) + "_" + j + str(n2) + "_" + p], 
                                                      lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0])
                number_of_constraints += 1
    
    print "number of constraints: ",number_of_constraints
    print "number of non-zeros: ",number_of_nonzeros
    
    
    # fix heuristic solution variables
    
    for p,i,j in TIMEFREEPLANESOLUTION:
       thevars = []
       thecoefs = []
       for n1 in AirportNum[p,i]:
           for n2 in AirportNum[p,j]:
              thevars += [y[i,j,p,n1,n2]]
              thecoefs += [1.0]
       model.linear_constraints.add(names = ["fix_airplane_schedule_" + i + "_" + j + "_" + p], 
                                   lin_expr = [cplex.SparsePair(thevars,thecoefs)], 
                                   senses = ["E"], rhs = [TIMEFREEPLANESOLUTION[p,i,j]])
    
    
    for p,r,i,j in TIMEFREEREQUESTSOLUTION:
      if (i,j,r,p) in x and j != REQUEST[r].request_arrival and i != REQUEST[r].request_departure:
        thevars = []
        thecoefs = []
        for n1 in AirportNum[p,i]:
            for n2 in AirportNum[p,j]:
                thevars += [x[i,j,r,p,n1,n2]]
                thecoefs += [1.0]
        
        model.linear_constraints.add(names = ["fix_request_schedule_" + i + "_" + j + "_" + r + "_" + p], 
                                     lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
    
    
    
    # set time limit
    
    model.parameters.timelimit.set(10800) # 10800 = 3h, 86400 = one day (24h)
    #model.parameters.workmem.set(4096.0) # working memory
    
    
    # solve again
    
    model.write("model.lp")
    name2idx = { n : j for j, n in enumerate(model.variables.get_names()) }
    
    
    model.solve()
    
    timeLimit -= time.time()-tOld
    # report solution
    solutionTime[instanceName] = time.time() - t0
    bestGap[instanceName]= 1.0 - bestDualBound[instanceName]/bestSolution[instanceName]
    print "total time: ",time.time() - t0
    
    file = open("results.txt", "a")
    lineToAdd = instanceName + ", " + str(int(bestDualBound[instanceName]))+ ", " + str(int(bestSolution[instanceName]))
    lineToAdd += ", " + str(bestGap[instanceName]*100) + "%, " +str(int(solutionTime[instanceName]))+ "\n"
    file.write(lineToAdd)
    file.close()