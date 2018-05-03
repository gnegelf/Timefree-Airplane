import time
import re

def rotateList(l, n):
    return l[n:] + l[:n]

def varToKey(varStr,pos):
    return re.split("[_#]",varStr)[pos]

def arcAmount(path,arc):
    res = 0
    for i in range(len(path)-1):
        if path[i] == arc[0] and path[i+1]==arc[1]:
            res += 1
    
    return res

infeasible = 0

#turns a list of strings with variable names into a list of paths
def solToAirports(solutionStringList,p):
    airportList=[]
    for string in solutionStringList:
        airportList.append((re.split("[_#]",string)[1]))
    airportList2=[]
    for string in solutionStringList:
        airportList2.append((re.split("[_#]",string)[2]))
    airportDict = {}
    airportDict1 = {}
    airportDict2 = {}
    for s in airportList:
        airportDict1[s] = 0
        airportDict2[s] = 0
    for s in airportList2:
        airportDict1[s] = 0
        airportDict2[s] = 0
    for s in airportList:
        airportDict1[s] += 1
    
    

    for s in airportList2:
        airportDict2[s] += 1
    
    for s in airportDict1:
        airportDict[s] = max([airportDict1[s],airportDict2[s]])  
        if s == PLANE[p].origin:
            airportDict[s] += 1                              
    
    return airportDict



#turns a list of strings with variable names into a list of paths
def solToPaths(solutionStringList):
    pathList=[]
    for string in solutionStringList:
        pathList.append([(re.split("[_#]",string)[1]),(re.split("[_#]",string)[2])])
    prevLength=0
    curLength=len(pathList)
    while (prevLength!=curLength):
        prevLength=len(pathList)
        for i,path in enumerate(pathList):
            for j in range(len(pathList)):
                if i!=j:
                    if path[-1]==pathList[j][0]:
                        pathList[j].pop(0)
                        path+=pathList.pop(j)
                        break
                    else:
                        if pathList[j][0] == pathList[j][-1] : 
                            breaker=0
                            for num,vert in enumerate(path):
                                for num2,vert2 in enumerate(pathList[j]):
                                    if vert2==vert:
                                        tempPath=pathList.pop(j)
                                        tempPath.pop(-1)
                                        tempPath=rotateList(tempPath,num2)
                                        path[num:num]=tempPath
                                        
                                        breaker=1
                                        break
                                if breaker:
                                    break
                            if breaker:
                                break
                        
            curLength=len(pathList)
            if (curLength!=prevLength):
                break
    return pathList    


#grab the old solution values
solutionValues = model.solution.get_values()
name2idx = { n : j for j, n in enumerate(model.variables.get_names()) }
name2solutionValue = { n : solutionValues[j] for j, n in enumerate(model.variables.get_names()) }


paths = {}
flyTime = {}
xPaths = {}
assignedRequests = {}


for p in PLANE:
#for p in ['1']:    
    print('Checking PLANE ' + p)
    
    assignedRequests[p] = {}
    
    #Print the timefree tour of the plane for debugging
    print("Timefree Tour:")
    for key,val in y.iteritems():
        if key[2]!=p:
            continue
        valStore=solutionValues[name2idx[val]]
        if valStore > 0.5:
            print(val+" %f" %valStore)
    for key,val in d.iteritems():
        if key[2]!=p:
            continue
        valStore=solutionValues[name2idx[val]]
        if valStore > 0.5:
            print(val+" %f" %valStore)
    for key,val in y_arr.iteritems():
        if key[0]!=p:
            continue
        valStore=solutionValues[name2idx[val]]
        if valStore > 0.5:
            print(val +" %f" %valStore)
    
    for key,val in y_dep.iteritems():
        if key[0]!=p:
            continue
        valStore=solutionValues[name2idx[val]]
        if valStore > 0.5:
            print(val +" %f" %valStore)
    for key,val in d_arr.iteritems():
        if key[0]!=p:
            continue
        valStore=solutionValues[name2idx[val]]
        if valStore > 0.5:
            print(val +" %f" %valStore)
    
    for key,val in d_dep.iteritems():
        if key[0]!=p:
            continue
        valStore=solutionValues[name2idx[val]]
        if valStore > 0.5:
            print(val +" %f" %valStore)
    
    #read the y-variables that are set for p
    yString=[]
    flyTime[p]=0
    for key,val in y.iteritems():
        if key[2]==p:
            valStore=solutionValues[name2idx[val]]
            for k in range(10): #account for y variables that are not binary
                if valStore > 0.1+k: 
                    yString+=[val]
                    flyTime[p]+=turnover_travel_timesteps[key[0],key[1],key[2]]
                else:
                    break
    
    
    paths[p]=solToPaths(yString)


        
    if paths[p] == []:
        continue
    
    for i,j in TRIP0:
        fullModel[p].variables.set_upper_bounds( [(y2[i,j,p],arcAmount(paths[p][0],[i,j])) ] )
        fullModel[p].variables.set_lower_bounds( [(y2[i,j,p],arcAmount(paths[p][0],[i,j])) ] )
    
    
    requestArcs = {}
    for i,j in TRIP:
        requestArcs[i,j] = 0
        
    for r in REQUEST:
        assignedRequests[p][r] = 0
    
    xString = {}
    #find assigned requests and set arcs
    for key,val in x.iteritems():
        if key[3]==p:
            valStore=solutionValues[name2idx[val]]
            if valStore > 0.1:
                if assignedRequests[p][key[2]] == 0:
                    xString[key[2]]=[]
                assignedRequests[p][key[2]] = 1
                requestArcs[key[0],key[1]] = 1
                if key[0]!=key[1]:
                    xString[key[2]]+=["x#" + key[0] + "_" + key[1] + "_" + key[2] + "_" + key[3]]
    
    for r in assignedRequests[p]:
        if assignedRequests[p][r]:
            xPaths[p,r]=solToPaths(xString[r])
    
    for r,assigned in assignedRequests[p].iteritems():
        fullModel[p].variables.set_upper_bounds( [(r2[r,p], assigned)])
        fullModel[p].variables.set_lower_bounds( [(r2[r,p], assigned)])
    
    #converts the analyzed y variables to a set of longest paths
    airports=solToAirports(yString,p)
    
    
    
    fullModel[p].solve()
    if not fullModel[p].solution.is_primal_feasible():
        print "plane " + p + " infeasible"
        infeasible = 1
        for s in airports:
            if AirportNum[p,s][-1] < airports[s]:
                AirportNum[p,s].append(AirportNum[p,s][-1]+1)
        #break  
    
if infeasible:
    print("Solution infeasible")    
print(flyTime)
print(paths)