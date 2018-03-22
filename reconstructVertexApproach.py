import time
import re
import random
def rotateList(l, n):
    return l[n:] + l[:n]

def varToKey(varStr,pos):
    return re.split("[_#]",varStr)[pos]

def pathHasArc(path,arc):
    for i in range(len(path)-1):
        if path[i]== arc[0] and path[i+1]==arc[1]:
            return 1

#testFunction for SolToPaths
def testSolToPaths(n,m):
    for k in range(m):
        stringList=["y#0_1"]
        oldNum=1
    
        for i in range(n):
            newNum=random.randint(0,9)
            while (newNum==oldNum):
                newNum=random.randint(0,9)
            stringList+=["y#%d_%d" % (oldNum,newNum)]
            oldNum=newNum
        random.shuffle(stringList)

        if len(solToPaths(stringList))!=1:
            print("Failure Alert")
    for k in range(m):
        stringList=["y#0_1"]
        oldNum=1
    
        for i in range(n):
            newNum=random.randint(1,9)
            while (newNum==oldNum):
                newNum=random.randint(1,9)
            stringList+=["y#%d_%d" % (oldNum,newNum)]
            oldNum=newNum
        stringList.append(stringList[-1])
        #stringList+=["y#N_P","y#P_N"]
        random.shuffle(stringList)
        print(solToPaths(stringList))
        if len(solToPaths(stringList))==1:
            print("Failure Alert")


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


#changes dividers so that the not fully expanded model cannot find the infeasible path path anymore
def breakPath(path,start_time,end_time,breakX = 0):
    pathLength=0
    for i in range(len(path)-1):
        pathLength+=turnover_travel_timesteps[path[i],path[i+1],p]
    prevPath=start_time
    for i in range(len(path)):
        iters=1
        breakPoint=prevPath+iters*pathLength - 1
        
        while (breakPoint < end_time):
            yDividers[path[i],p].addDivider([breakPoint])
            zDividers[path[i],p].addDivider([breakPoint])
            
            if breakX:
                xDividers[path[i],p].addDivider([breakPoint])
            iters += 1
            breakPoint=prevPath+iters*pathLength - 1
               
        if i < len(path)-1:
            prevPath+=turnover_travel_timesteps[path[i],path[i+1],p]



#grab the old solution values
solutionValues = model.solution.get_values()
name2idx = { n : j for j, n in enumerate(model.variables.get_names()) }
name2solutionValue = { n : solutionValues[j] for j, n in enumerate(model.variables.get_names()) }


paths = {}
flyTime = {}
xPaths = {}
assignedRequests = {}


for p in PLANE:
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
    
    
    
    #find the earliest time the plane could departure
    earliestDep=0
    for ID in yDividers[PLANE[p].origin,p].ids:
        if name2solutionValue["y_dep#" + p + "_" + ID] > 0.1:
            earliestDep=max([min(yDividers[PLANE[p].origin,p].ids[ID]),min_timestep])
            startIndex=(p,ID)
    
    #find the latest time the plane could arrive
    latestArr=0
    for ID in yDividers[PLANE[p].destination,p].ids:
        if name2solutionValue["y_arr#" + p + "_" + ID] > 0.1:
            latestArr=min([max(yDividers[PLANE[p].destination,p].ids[ID]),max_timestep])
            goalIndex=(p,ID)

    
    
    #converts the analyzed y variables to a set of longest paths
    #A time dependent solution can be recovered if this path can be flown in
    #the respective time and there are no disconnected cycles.
    paths[p]=solToPaths(yString)


    #Break the disconnected cycles
    if len(paths[p])>1:#cycle check
        for path in paths[p]:
            if path[0]!=PLANE[p].origin and path[0]==path[-1]:#condition for a disconnected cycle
                breakPath(path,tP[p][0],tP[p][-1])
        
    #Check if path can be flown in time
    if flyTime[p] > latestArr-earliestDep-0.0001:
        for path in paths[p]:
            pathLength=0
            for i in range(len(path)-1):
                pathLength+=turnover_travel_timesteps[path[i],path[i+1],p]
                
            prevPath=earliestDep
            for i in range(len(path)):
                LOP=[prevPath-1+m*pathLength for m in range(int(number_of_timesteps) % int(pathLength)) 
                if prevPath-1+m*pathLength <= number_of_timesteps and prevPath-1+m*pathLength>0]
                if LOP != []:
                    yDividers[path[i],p].addDivider(LOP,number_of_timesteps)
                    yDividers[path[i],p].addDivider([1],number_of_timesteps)
                    for r in REQUEST:
                        xDividers[path[i],r,p].addDivider(LOP,number_of_timesteps)
                        xDividers[path[i],r,p].addDivider([1],number_of_timesteps)
                if i < len(path)-1:
                    prevPath+=turnover_travel_timesteps[path[i],path[i+1],p]
        break#This break is to go back to timefree
    
    

    if paths[p] == []:
        continue
    for i,j in TRIP0:
        if pathHasArc(paths[p][0],[i,j]):
            pathModels[p].variables.set_upper_bounds( [(y2[i,j,p,t],1.0) for t in tP[p]] )
            requestModels[p].variables.set_upper_bounds( [(y2[i,j,p,t],1.0) for t in tP[p]] )
            fullModels[p].variables.set_upper_bounds( [(y2[i,j,p,t],1.0) for t in tP[p]] )
        else:
            pathModels[p].variables.set_upper_bounds( [(y2[i,j,p,t],0.0) for t in tP[p]] )
            requestModels[p].variables.set_upper_bounds( [(y2[i,j,p,t],0.0) for t in tP[p]] )
            fullModels[p].variables.set_upper_bounds( [(y2[i,j,p,t],0.0) for t in tP[p]] )
    
     
    pathModels[p].solve()
    continue
    if not pathModels[p].solution.is_primal_feasible():
        breakPath(paths[p][0],tP[p][0],tP[p][-1])
        break
    
    
    time_start = time.clock()
    #check if the requests can be assigned to the tours
    
    
    requestArcs = {}
    for i,j in TRIP:
        requestArcs[i,j] = 0
        
    for r in REQUEST:
        assignedRequests[p][r] = 0
        
    #find assigned requests and set arcs
    for key,val in x.iteritems():
        if key[3]==p:
            valStore=solutionValues[name2idx[val]]
            if valStore > 0.1:
                assignedRequests[p][r] = 1
                requestArcs[key[0],key[1]] = 1
    
    
    for r,assigned in assignedRequests[p].iteritems():
        for i,j in TRIP0:
            requestModels[p].variables.set_upper_bounds( [(x2[i,j,r,p,t],requestArcs[i,j] * assigned) for t in tR[r]])
            fullModels[p].variables.set_upper_bounds( [(x2[i,j,r,p,t],requestArcs[i,j] * assigned) for t in tR[r]])
            
            requestModels[p].variables.set_lower_bounds( [(x2[i,j,r,p,t],requestArcs[i,j] * assigned) for t in tR[r]])
            fullModels[p].variables.set_lower_bounds( [(x2[i,j,r,p,t],requestArcs[i,j] * assigned) for t in tR[r]])
        requestModels[p].variables.set_upper_bounds( [(r2[r,p], assigned)])
        fullModels[p].variables.set_upper_bounds( [(r2[r,p], assigned)])
    
    
    requestModels[p].solve()
    if not pathModels[p].solution.is_primal_feasible():
        for r,assigned in assignedRequests[p].iteritems():
            if assigned:
                breakPath(xPaths[p][0],tR[r][0],tR[r][1],breakX=1)
        break
    
    
    
    fullModels[p].solve()
    if not fullModels[p].solution.is_primal_feasible():
        for r,assigned in assignedRequests[p].iteritems():
            if assigned:
                breakPath(xPaths[p][0])
        break       
    
    
print(flyTime)
print(paths)