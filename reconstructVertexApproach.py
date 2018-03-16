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
                            cyc=pathList[j][0]
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


#print(solToPaths(["y#HA_BE","y_H_QO","y_QO_BUT","y_BUT_H", "y_BE_IC","y_IC_H","y_H_EU", "y_EU_SE","y_SE_NER","y_NER_EU","y#EU_TE","y_TE_GUT"  ]))
#testSolToPaths(10,3)
#number_of_timesteps=200
tS=range(number_of_timesteps)
tSString=[str(t) for t in tS]
solutionValues=model.solution.get_values()
name2idx = { n : j for j, n in enumerate(model.variables.get_names()) }
name2solutionValue = { n : solutionValues[j] for j, n in enumerate(model.variables.get_names()) }
paths={}
flyTime={}
xPaths={}
for p in Airplane:
    print('Checking airplane ' + p)
    print("Old Tour:")
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
    yString=[]
    flyTime[p]=0
    for key,val in y.iteritems():
        if key[2]==p:
            valStore=solutionValues[name2idx[val]]
            for k in range(10):
                if valStore > 0.1+k: 
                    yString+=[val]
                    flyTime[p]+=Traveltime[key[0],key[1],key[2]]
                else:
                    break
    
    
    earliestDep=0
    for ID in yDividers[Airplane[p].origin,p].ids:
        if name2solutionValue["y_dep#" + p + "_" + ID] > 0.1:
            earliestDep=max([min(yDividers[Airplane[p].origin,p].ids[ID]),0])
            startIndex=(p,ID)
    latestArr=0

    for ID in yDividers[Airplane[p].destination,p].ids:
        if name2solutionValue["y_arr#" + p + "_" + ID] > 0.1:
            latestArr=min([max(yDividers[Airplane[p].destination,p].ids[ID]),number_of_timesteps])
            goalIndex=(p,ID)

    
    #Check for cycles
    
    paths[p]=solToPaths(yString)
    print(paths[p])
    if len(paths[p])>1:
        for path in paths[p]:
            if path[0]!=Airplane[p].origin and path[0]==path[-1]:
                cycleLength=0
                for i in range(1,len(path)):
                    cycleLength+=Traveltime[path[i-1],path[i],p]
                prevPath=earliestDep
                for i in range(0,len(path)):
                    LOP=[prevPath-1+m*cycleLength for m in range(1+int(number_of_timesteps) % int(cycleLength)) if prevPath-1+m*cycleLength <= number_of_timesteps and prevPath-1+m*cycleLength>0]
                    if LOP != []:
                        print("Cycle Divider added")
                        yDividers[path[i],p].addDivider(LOP,number_of_timesteps)
                        yDividers[path[i],p].addDivider([1],number_of_timesteps)
                        for r in Request:
                            xDividers[path[i],r,p].addDivider(LOP,number_of_timesteps)
                            xDividers[path[i],r,p].addDivider([1],number_of_timesteps)
                        #yDepDividers[p].addDivider(LOP,number_of_timesteps)
                        #yArrDividers[p].addDivider(LOP,number_of_timesteps)
                    if i < len(path)-1:
                        prevPath+=Traveltime[path[i],path[i+1],p]
        break #This break is to go back to timefree                
    while paths[p][0][0] != Airplane[p].origin:
        paths[p][0].pop(0)
        paths[p][0].append(paths[p][0][0])
        
    #Check if path can be flown in time
    if flyTime[p] > latestArr-earliestDep-0.0001:
        for path in paths[p]:
            pathLength=0
            for i in range(len(path)-1):
                pathLength+=Traveltime[path[i],path[i+1],p]
                
            prevPath=earliestDep
            for i in range(len(path)):
                LOP=[prevPath-1+m*pathLength for m in range(int(number_of_timesteps) % int(pathLength)) if prevPath-1+m*pathLength <= number_of_timesteps and prevPath-1+m*pathLength>0]
                if LOP != []:
                    yDividers[path[i],p].addDivider(LOP,number_of_timesteps)
                    yDividers[path[i],p].addDivider([1],number_of_timesteps)
                    for r in Request:
                        xDividers[path[i],r,p].addDivider(LOP,number_of_timesteps)
                        xDividers[path[i],r,p].addDivider([1],number_of_timesteps)
                if i < len(path)-1:
                    prevPath+=Traveltime[path[i],path[i+1],p]
        break#This break is to go back to timefree
    
    #continue
    model2 = cplex.Cplex()
    y2 = {}
    model2.set_results_stream('reconst.rlog')
    if paths[p] == []:
        continue
    for i,j in Distance:
        for t in tS:
            if pathHasArc(paths[p][0],[i,j]):
                y2[i,j,p,t] = "y#" + i + "_" + j + "_" + p + "_" + str(t)
                model2.variables.add(obj = [0.0], names = [y2[i,j,p,t]], lb = [0], ub=[1.0],types = ["B"])
            else:
                y2[i,j,p,t] = "y#" + i + "_" + j + "_" + p + "_" + str(t)
                model2.variables.add(obj = [0.0], names = [y2[i,j,p,t]], lb = [0],ub=[0.0], types = ["B"])
    
    y_arr2 = {}
    y_dep2 = {}
    for t in tS:
        y_dep2[p,t] = "y_dep#" + p + "_" + str(t)
        model2.variables.add(names = [y_dep2[p,t]], lb = [0.0], ub = [0.0], types = ["B"])
        y_arr2[p,t] = "y_arr#" + p + "_" + str(t)
        model2.variables.add(names = [y_arr2[p,t]], lb = [0.0], ub = [0.0], types = ["B"])
    
    for key,val in y_arr.iteritems():
        if key[0]!=p:
            continue
        valStore=solutionValues[name2idx[val]]
        if valStore >0.5:
            for t in tS:
                model2.variables.set_upper_bounds(y_arr2[key[0],t],1.0 )
    for key,val in y_dep.iteritems():
        if key[0]!=p:
            continue
        valStore=solutionValues[name2idx[val]]
        if valStore >0.5:
            for t in tS:
                model2.variables.set_upper_bounds(y_dep2[key[0],t],1.0 )   
    """
    ySlack = {}
    for i,j in Distance:
        for ID in yDividers[i,j,p].ids:
            ySlack[i,j,p,ID] = "ySlack#" + i + "_" + j + "_" + p + "_" + ID
            model2.variables.add(obj = [1.0], names = [ySlack[i,j,p,ID]], lb = [0.0], types = ["I"])
    
    y_depSlack = {}
    
    for ID in yDepDividers[p].ids:
        y_depSlack[p,ID] = "y_depSlack#" + p  + "_" + ID
        model2.variables.add(obj = [1000.0], names = [y_depSlack[p,ID]], lb = [0.0], types = ["I"])
    
    y_arrSlack = {}
    
    for ID in yArrDividers[p].ids:
        y_arrSlack[p,ID] = "y_arrSlack#" + p  + "_" + ID
        model2.variables.add(obj = [1000.0], names = [y_arrSlack[p,ID]], lb = [0.0], types = ["I"])
    
    ySlack2 = {}
    for i,j in Distance:
            for ID in yDividers[i,j,p].ids:
                ySlack2[i,j,p,ID] = "ySlack2#" + i + "_" + j + "_" + p + "_" + ID
                model2.variables.add(obj = [1.0], names = [ySlack2[i,j,p,ID]], lb = [0.0],ub=[0.0], types = ["I"])
     
    y_depSlack2 = {}
    
    for ID in yDepDividers[p].ids:
        y_depSlack2[p,ID] = "y_depSlack2#" + p  + "_" + ID
        model2.variables.add(obj = [1.0], names = [y_depSlack2[p,ID]], lb = [0.0], types = ["I"])
    
    y_arrSlack2 = {}

    for ID in yArrDividers[p].ids:
        y_arrSlack2[p,ID] = "y_arrSlack2#" + p  + "_" + ID
        model2.variables.add(obj = [1.0], names = [y_arrSlack2[p,ID]], lb = [0.0], types = ["I"])
    """
    
    
    # CONSTRAINTS
      
    #each plane must depart and arrive
    

    thevars=[y_dep2[p,t] for t in tS]
    thecoefs=[1.0 for t in tS]
    model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
    thevars=[y_arr2[p,t] for t in tS]
    thecoefs=[1.0 for t in tS]
    model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
    
    #airplane flow
    
    
    for j in Airport:
        for t in tS:
            thevars=[]
            thecoefs=[]
            for i in Airport:
                if i!=j and (i,j) in Distance:
                    thevars += [y2[i,j,p,t]]
                    thecoefs += [1.0]
            thevars+= [y2[j,k,p,t+Traveltime[j,k,p]] for k in Airport  
                       if k!=j and (j,k) in Distance and t+Traveltime[j,k,p] < number_of_timesteps]
            thecoefs += [-1.0  for k in Airport  
                       if k!=j and (j,k) in Distance and t+Traveltime[j,k,p] < number_of_timesteps]
            
            rhs_value = 0.0
            if (j == Airplane[p].origin):
                thevars.append(y_dep2[p,t])
                thecoefs.append(1.0)
            if (j == Airplane[p].destination):
                thevars.append(y_arr2[p,t])
                thecoefs.append(-1.0)
            
            model2.linear_constraints.add(names=["flow at " + j +", time %d" %t],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [rhs_value])
    
    if (Airplane[p].origin == Airplane[p].destination):
        i = Airplane[p].origin
        
        thevars = [y2[i,j,p,t] for j in Airport if i!=j for t in tS]
        thecoefs = [1.0]*len(thevars)
        
        model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["G"], rhs = [1.0])
    
    #old setting of variables according to timefree tour
    """
    for i in Airport:
        for j in Airport:
            if (i!=j):
                idToTimeSteps={}
                for ID in yDividers[i,j,p].ids:
                    idToTimeSteps[ID]=[]
            
                for t in tS:
                    idToTimeSteps[yDividers[i,j,p].findId(t)].append(t)
                
                for ID in yDividers[i,j,p].ids:
                    thevars=[y2[i,j,p,t] for t in idToTimeSteps[ID]]
                    
                    #thecoefs=[1.0]*len(thevars)+[-1.0,1.0]
                    #thevars+=[ySlack[i,j,p,ID],ySlack2[i,j,p,ID]]
                    thecoefs=[1.0]*len(thevars)+[-1.0,1.0]
                    thevars+=[ySlack[i,j,p,ID],ySlack2[i,j,p,ID]]
                    rhs=solutionValues[name2idx[y[i,j,p,ID]]]
                    model2.linear_constraints.add(names=["slack"+i+j+str(ID)],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [rhs])

    
    
    idToTimeSteps={}
    for ID in yArrDividers[p].ids:
        idToTimeSteps[ID]=[]

    for t in tS:
        idToTimeSteps[yArrDividers[p].findId(t)].append(t)
    
    for ID in yArrDividers[p].ids:
        thevars=[y_arr2[p,t] for t in idToTimeSteps[ID]]
        thecoefs=[1.0]*len(thevars)+[-1.0]
        thevars+=[y_arrSlack[p,ID]]
        rhs=solutionValues[name2idx[y_arr[p,ID]]]
        model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [rhs])

    idToTimeSteps={}
    for ID in yDepDividers[p].ids:
        idToTimeSteps[ID]=[]

    for t in tS:
        idToTimeSteps[yDepDividers[p].findId(t)].append(t)
    
    for ID in yDepDividers[p].ids:
        thevars=[y_dep2[p,t] for t in idToTimeSteps[ID]]
        thecoefs=[1.0]*len(thevars)+[-1.0]
        thevars+=[y_depSlack[p,ID]]
        rhs=solutionValues[name2idx[y_dep[p,ID]]]
        model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [rhs])
    """  
    model2.objective.set_sense(model2.objective.sense.minimize)
    model2.solve()
    time_start = time.clock()
    
    
    """

    #TODO: test if tours can be reconstructed. Use old model2 but set slacks for y variables to 0 try warm start for y variables
        
    #model2.variables.add(XVARS)
    
    """
    print(model2.solution.get_objective_value())
    #continue
    solutionValues2=model2.solution.get_values()
    name2idx2 = { n : j for j, n in enumerate(model2.variables.get_names()) }
    idx2name = { j : n for j, n in enumerate(model2.variables.get_names()) }
    
    

    print("New tour")
    for key,val in y2.iteritems():
        valStore=solutionValues2[name2idx2[val]]
        if valStore > 0.5:
            print(val +" %f" %valStore)
    for key,val in y_dep2.iteritems():
        valStore=solutionValues2[name2idx2[val]]
        if valStore > 0.5:
            print(val +" %f" %valStore)

    
    
    #continue
    assignedRequests={}
    x2 = {}
    
    xString={}
    for i,j in Distance:
        for r in Request:
            xString[r]=[]
            for t in tS:
                x2[i,j,r,p,t]="x#" + i + "_" + j + "_" + r + "_" + p + "_"+str(t)
                model2.variables.add(names = [x2[i,j,r,p,t]], lb = [0.0], ub = [0.0], types = ["B"])
    
    for key,val in x.iteritems():
        if key[3]!=p:
            continue
        valStore=solutionValues[name2idx[val]]
        if valStore >0.5:
            xString[key[2]]+=["x#" + key[0] + "_" + key[1] + "_" + key[2] + "_" + key[3]]
            assignedRequests[key[2]]=Request[key[2]]
            for t in tS:
                model2.variables.set_upper_bounds(x2[key[0],key[1],key[2],key[3],t],1.0 )

    xPaths[p]=[]
    for r in assignedRequests:
        xPaths[p]+=solToPaths(xString[r])
    x_arr2 = {}
    x_dep2 = {}
    for r in assignedRequests:
        for t in tS:
            x_dep2[r,p,t] = "x_dep#" + r + "_" + p + "_" + str(t)
            model2.variables.add(names = [x_dep2[r,p,t]], lb = [0.0], ub = [0.0], types = ["B"])
            x_arr2[r,p,t] = "x_arr#" + r + "_" + p + "_" + str(t)
            model2.variables.add(names = [x_arr2[r,p,t]], lb = [0.0], ub = [0.0], types = ["B"])
    
    for key,val in x_arr.iteritems():
        if key[1]!=p:
            continue
        valStore=solutionValues[name2idx[val]]
        if valStore >0.5:
            for t in tS:
                model2.variables.set_upper_bounds(x_arr2[key[0],key[1],t],1.0 )
    
    for key,val in x_dep.iteritems():
        if key[1]!=p:
            continue
        valStore=solutionValues[name2idx[val]]
        if valStore >0.5:
            for t in tS:
                model2.variables.set_upper_bounds(x_dep2[key[0],key[1],t],1.0 )       
    #continue

    """    
    xSlack = {}
    for i,j in Distance:
        for r in Request:
            for ID in xDividers[i,j,r,p].ids:
                xSlack[i,j,r,p,ID] = "xSlack#" + i + "_" + j + "_" + r + "_" + p + "_"+ID
                model2.variables.add(obj = [1.0], names = [xSlack[i,j,r,p,ID]], lb = [0],  types = ["I"])
    
    x_depSlack = {}
    
    for r in Request:
        for ID in xDepDividers[r,p].ids:
            x_depSlack[r,p,ID] = "x_depSlack#" + r + "_" + p + "_" + ID
            model2.variables.add(obj = [1.0],names = [x_depSlack[r,p,ID]], lb = [0],  types = ["I"])
    
    x_arrSlack = {}
    
    for r in Request:
        for ID in xArrDividers[r,p].ids:
            x_arrSlack[r,p,ID] = "x_arrSlack#" + r + "_" + p + "_" + ID
            model2.variables.add(obj = [1.0],names = [x_arrSlack[r,p,ID]], lb = [0], types = ["I"])
    
    xSlack2 = {}
    for i,j in Distance:
        for r in Request:
            for ID in xDividers[i,j,r,p].ids:
                xSlack2[i,j,r,p,ID] = "xSlack2#" + i + "_" + j + "_" + r + "_" + p + "_"+ID
                model2.variables.add(obj = [1.0], names = [xSlack2[i,j,r,p,ID]], lb = [0],  ub = [1.0], types = ["I"])
    
    x_depSlack2 = {}
    
    for r in Request:
        for ID in xDepDividers[r,p].ids:
            x_depSlack2[r,p,ID] = "x_depSlack2#" + r + "_" + p + "_" + ID
            model2.variables.add(obj = [1.0],names = [x_depSlack2[r,p,ID]], lb = [0],  ub = [1.0],types = ["I"])
    
    x_arrSlack2 = {}
    
    for r in Request:
        for ID in xArrDividers[r,p].ids:
            x_arrSlack2[r,p,ID] = "x_arrSlack2#" + r + "_" + p + "_" + ID
            model2.variables.add(obj = [1.0],names = [x_arrSlack2[r,p,ID]], lb = [0], ub = [1.0],types = ["I"])
    """            
    seatSlack = {}
    for i,j in Distance:
        seatSlack[i,j] = "seatSlack#" + i + "_" + j 
        model2.variables.add(obj = [0.01],names = [seatSlack[i,j]], lb = [0], types = ["I"])
    stopSlack = {}
    for r in assignedRequests:
        stopSlack[r] = "stopSlack#" + r
        model2.variables.add(obj = [1], names = [stopSlack[r]], lb = [0], types = ["I"])    
    print("Finished adding additional variables, time passed: %f" % (time.clock() - time_start))
    
    # each request must depart and arrive
    
    for r in assignedRequests:
        thevars = [x_dep2[r,p,t] for t in tS]
        thecoefs = [1.0  for t in tS]
        model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
        thevars = [x_arr2[r,p,t]  for t in tS]
        thecoefs = [1.0  for t in tS]
        model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [1.0])
    
    print("Each request must depart, time passed: %f" % (time.clock() - time_start))
    
    #TODO: Check if restriction to in Distance has to be added
    # request flow departure
    
    for r in assignedRequests:
        for t in tS:
        #for t in xrange(Request[r].earliest_departure,Request[r].latest_arrival):
            thevars = [x_dep2[r,p,t]]
            thecoefs = [-1.0]
            ori=Request[r].origin
            thevars += [x2[ori,j,r,p,t+Traveltime[ori,j,p]]
                            for j in Airport if j != ori and t+Traveltime[ori,j,p]< number_of_timesteps]
            thecoefs += [1.0 for j in Airport if j != ori and t+Traveltime[ori,j,p]< number_of_timesteps]
            
            
            model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])

    # request flow arrival
    
    for r in assignedRequests:
        for t in tS:
        #for t in xrange(Request[r].earliest_departure,Request[r].latest_arrival):
            desti=Request[r].destination
            thevars = [x_arr2[r,p,t]]
            thecoefs = [-1.0]
            #thevars += [x2[j,desti,r,p,t+Traveltime[j,desti,p]]  for j in Airport if j != desti and t+Traveltime[j,desti,p]< number_of_timesteps]
            thevars += [x2[j,desti,r,p,t]  for j in Airport if j != desti]
            #thecoefs += [1.0 for j in Airport if j != desti and t+Traveltime[j,desti,p]< number_of_timesteps]
            thecoefs += [1.0 for j in Airport if j != desti ]

            model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])

     # request flow (other than departure and arrival)
    print("Flow at destination and orgin added, time passed: %f" % (time.clock() - time_start))    
    for r in assignedRequests:
        for j in Airport:
            if (j != Request[r].origin and j != Request[r].destination):
                for t in tS:
                #for t in xrange(Request[r].earliest_departure,Request[r].latest_arrival):
                    thevars=[]
                    thecoefs=[]
                    thevars += [x2[i,j,r,p,t] for i in Airport if (j!= i)]
                    thecoefs += [1.0  for i in Airport if (j!= i)]
                    
                    thevars += [x2[j,k,r,p,t+Traveltime[j,k,p]] for k in Airport if j != k and t+Traveltime[j,k,p] < number_of_timesteps]
                    
                    thecoefs += [-1.0 for k in Airport if j != k and t+Traveltime[j,k,p] < number_of_timesteps];
                           
                    model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
    print("Flows added, time passed: %f" % (time.clock() - time_start))
    
    #"""
    for i,j in Distance:
        for t in tS:
            #print i,j,p
            thevars = [y2[i,j,p,t],seatSlack[i,j]]
            thecoefs = [-Airplane[p].seats,-1.0]
            thevars += [x2[i,j,r,p,t] for r in assignedRequests]
            thecoefs += [Request[r].passengers for r in assignedRequests]
            model2.linear_constraints.add(names=["seat "+i+j+str(t)],lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
   
    
    # intermediate stops for requests
    
    for r in assignedRequests:
        thevars = [x2[i,j,r,p,t] for i,j in Distance  for t in tS]+[stopSlack[r]]
        thecoefs = [1.0 for i,j in Distance for t in tS ]+[-1.0]
        model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [Request[r].max_stops + 1])
    #"""
    
    model2.solve()
    split=0
    if model2.solution.is_primal_feasible():
        print(model2.solution.get_objective_value())
        solutionValues2=model2.solution.get_values()
        name2idx2 = { n : j for j, n in enumerate(model2.variables.get_names()) }
        idx2name = { j : n for j, n in enumerate(model2.variables.get_names()) }
        if model2.solution.get_objective_value()>0.0001:
            split=1
        else:
            split=0
    else:
        requestsToSplit=assignedRequests
    
    
    if not model2.solution.is_primal_feasible() or split:
        for path in xPaths[p]:
            pathLength=0
            for i in range(len(path)-1):
                pathLength+=Traveltime[path[i],path[i+1],p]
            prevPath=0
            for i in range(len(path)):
                LOP=[prevPath-1+m*pathLength for m in range(int(number_of_timesteps) % int(pathLength)) if prevPath-1+m*pathLength <= number_of_timesteps  and prevPath-1+m*pathLength>0]
                if LOP != []:
                    yDividers[path[i],p].addDivider(LOP,number_of_timesteps)
                    yDividers[path[i],p].addDivider([1],number_of_timesteps)
                    for r in Request:
                        xDividers[path[i],r,p].addDivider(LOP,number_of_timesteps)
                        xDividers[path[i],r,p].addDivider([1],number_of_timesteps)
                    print("Path Divider for X added")
                if i < len(path)-1:
                    prevPath+=Traveltime[path[i],path[i+1],p]
        break
    else:
        continue#This break is to go back to timefree
    
        """
    if flyTime[p] > latestArr-earliestDep-0.0001:
        for path in paths[p]:
            pathLength=0
            for i in range(len(path)-1):
                pathLength+=Traveltime[path[i],path[i+1],p]
            prevPath=earliestDep
            for i in range(len(path)):
                LOP=[prevPath+m*pathLength for m in range(int(number_of_timesteps) % int(pathLength)) if prevPath+m*pathLength <= number_of_timesteps]
                if LOP != []:
                    yDividers[path[i],p].addDivider(LOP,number_of_timesteps)
                    yDividers[path[i],p].addDivider([1],number_of_timesteps)
                    for r in Request:
                        xDividers[path[i],r,p].addDivider(LOP,number_of_timesteps)
                        xDividers[path[i],r,p].addDivider([1],number_of_timesteps)
                if i < len(path)-1:
                    prevPath+=Traveltime[path[i],path[i+1],p]
        break#This break is to go back to timefree
        print(model2.solution.get_objective_value())
        
        solutionValues2=model2.solution.get_values()
        name2idx2 = { n : j for j, n in enumerate(model2.variables.get_names()) }
        
        for key,val in x.iteritems():
            valStore=solutionValues[name2idx[val]]
            if valStore > 0.5:
                print(val+" %f" % valStore)
        
        for key,val in xSlack.iteritems():
            valStore=solutionValues2[name2idx2[val]]
            if valStore > 0.5:
                print(val+" %f" % valStore)
        for key,val in xSlack2.iteritems():
            valStore=solutionValues2[name2idx2[val]]
            if valStore > 0.5:
                print(val+" %f" % valStore)
        print("New tour")
        for key,val in x2.iteritems():
            valStore=solutionValues2[name2idx2[val]]
            if valStore > 0.5:
                print(val +" %f" % valStore)
        for key,val in seatSlack.iteritems():
            valStore=solutionValues2[name2idx2[val]]
            if valStore > 0.0001:
                print(val +" %f" % valStore)
        for key,val in stopSlack.iteritems():
            valStore=solutionValues2[name2idx2[val]]
            if valStore > 0.0001:
                print(val +" %f" % valStore)+"""
    continue      
    """
    time_start=time.clock()
    z2 = {}
        
    for i,j in Distance:
        for ID in tS:
            z2[i,j,p,ID] = "z#" + i + "_" + j + "_" + p  + "_" + str(ID)
            model2.variables.add(names = [z2[i,j,p,ID]], lb = [0], ub = [Airplane[p].max_fuel], types = ["C"])

    z_dep2 = {}
    

    for ID in tS:
        z_dep2[p,ID] = "z_dep#" + p  + "_" + str(ID)
        model2.variables.add(names = [z_dep2[p,ID]], lb = [Airplane[p].departure_min_fuel], ub = [Airplane[p].departure_max_fuel], types = ["C"])

    z_arr2 = {}
    
    for ID in tS:
        z_arr2[p,ID] = "z_arr#" + p  + "_" + str(ID)
        model2.variables.add(names = [z_arr2[p,ID]], lb = [Airplane[p].arrival_min_fuel], ub = [Airplane[p].arrival_max_fuel], types = ["C"])
    
    zSlack = {}
        
    for i,j in Distance:
        for ID in zDividers[i,j,p].ids:
            zSlack[i,j,p,ID] = "zSlack#" + i + "_" + j + "_" + p  + "_" + str(ID)
            model2.variables.add(names = [zSlack[i,j,p,ID]], lb = [0.0], types = ["C"])
    
    z_depSlack = {}
    
    for ID in zDepDividers[p].ids:
        z_depSlack[p,ID] = "z_depSlack#" + p  + "_" + str(ID)
        model2.variables.add(names = [z_depSlack[p,ID]], lb = [0.0], types = ["C"])
    
    z_arrSlack = {}
    
    for ID in zArrDividers[p].ids:
        z_arrSlack[p,ID] = "z_arrSlack#" + p  + "_" + str(ID)
        model2.variables.add(names = [z_arrSlack[p,ID]], lb = [0.0], types = ["C"])
    
    zSlack2 = {}
        
    for i,j in Distance:
        for ID in zDividers[i,j,p].ids:
            zSlack2[i,j,p,ID] = "zSlack2#" + i + "_" + j + "_" + p  + "_" + str(ID)
            model2.variables.add(names = [zSlack2[i,j,p,ID]], lb = [0.0], types = ["C"])
    
    z_depSlack2 = {}
    
    for ID in zDepDividers[p].ids:
        z_depSlack2[p,ID] = "z_depSlack2#" + p  + "_" + str(ID)
        model2.variables.add(names = [z_depSlack2[p,ID]], lb = [0.0], types = ["C"])
    
    z_arrSlack2 = {}
    
    for ID in zArrDividers[p].ids:
        z_arrSlack2[p,ID] = "z_arrSlack2#" + p  + "_" + str(ID)
        model2.variables.add(names = [z_arrSlack2[p,ID]], lb = [0.0], types = ["C"])
    
    
    print("Finished adding additional variables, time passed: %f" % (time.clock() - time_start))
    
    
    
    
    for i,j in Distance:
        for t in tS:
            #print i,j,p
            thevars = [z2[i,j,p,t],y2[i,j,p,t]]
            thecoefs = [1.0,Fuelconsumption[i,j,p] + Airplane[p].reserve_fuel - Airplane[p].max_fuel]
            

            model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
    
    for j in Airport:
        for t in tS:

            thevars = [z2[i,j,p,t] for i in Airport if j!=i]
            thecoefs = [1.0 for i in Airport if j!=i]
                
                
            if j == Airplane[p].origin:
                thevars.append(z_dep2[p,t])
                thecoefs.append(1.0)
            
            thevars += [z2[j,k,p,t+Traveltime[j,k,p]] for k in Airport if (j,k) in Distance and j!=k and t+Traveltime[j,k,p] < number_of_timesteps]    
            thecoefs += [-1.0 for k in Airport if (j,k) in Distance and j!=k and t+Traveltime[j,k,p] < number_of_timesteps]
            thevars += [y2[j,k,p,t+Traveltime[j,k,p]] for k in Airport  if k!=j and (j,k) in Distance and t+Traveltime[j,k,p] < number_of_timesteps]    
            thecoefs += [-Fuelconsumption[j,k,p] for k in Airport  if k!=j and (j,k) in Distance and t+Traveltime[j,k,p] < number_of_timesteps]
            
            
            
            
            if j == Airplane[p].destination:
                thevars.append(z_arr2[p,t])
                thecoefs.append(-1.0)
            
            
            if Airport[j].fuel[str(Airplane[p].required_fueltype)] == '0':
                model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [0.0])
            else:
                model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])
                
    print("Flows added, time passed: %f" % (time.clock() - time_start))
    # weight limit (=max fuel)
    
    for i,j in Distance:
        for t in tS:
            thevars = [x2[i,j,r,p,t] for r in Request ]
            thecoefs = [Request[r].weight for r in Request]
            thevars.append(z2[i,j,p,t])
            thecoefs.append(1.0)
            thevars += [y2[i,j,p,t]]
            thecoefs.append(-min(Weightlimit[i,p].max_takeoff_weight - Airplane[p].reserve_fuel - Airplane[p].empty_weight + Fuelconsumption[i,j,p], Weightlimit[i,p].max_landing_weight - Airplane[p].reserve_fuel - Airplane[p].empty_weight))
            
            model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["L"], rhs = [0.0])



    

    for (i,j) in Distance:
        if (i!=j):
            idToTimeSteps={}
            for ID in zDividers[i,j,p].ids:
                idToTimeSteps[ID]=[]
        
            for t in tS:
                idToTimeSteps[zDividers[i,j,p].findId(t)].append(t)
            
            for ID in zDividers[i,j,p].ids:
                thevars=[z2[i,j,p,t] for t in idToTimeSteps[ID]]
                thecoefs=[1.0]*len(thevars)+[-1.0,1.0]
                thevars+=[zSlack[i,j,p,ID],zSlack2[i,j,p,ID]]
                rhs=solutionValues[name2idx[z[i,j,p,ID]]]
                model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [rhs])

    

    idToTimeSteps={}
    for ID in zArrDividers[p].ids:
        idToTimeSteps[ID]=[]

    for t in tS:
        idToTimeSteps[zArrDividers[p].findId(t)].append(t)
    
    for ID in zArrDividers[p].ids:
        thevars=[z_arr2[p,t] for t in idToTimeSteps[ID]]
        thecoefs=[1.0]*len(thevars)+[-1.0,1.0]
        thevars+=[z_arrSlack[p,ID],z_arrSlack2[p,ID]]
        rhs=solutionValues[name2idx[y_arr[p,ID]]]
        model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [rhs])
    

    idToTimeSteps={}
    for ID in zDepDividers[p].ids:
        idToTimeSteps[ID]=[]

    for t in tS:
        idToTimeSteps[zDepDividers[p].findId(t)].append(t)
    
    for ID in zDepDividers[p].ids:
        thevars=[z_dep2[p,t] for t in idToTimeSteps[ID]]
        thecoefs=[1.0]*len(thevars)+[-1.0,1.0]
        thevars+=[z_depSlack[p,ID],z_depSlack2[p,ID]]
        rhs=solutionValues[name2idx[z_dep[p,ID]]]
        model2.linear_constraints.add(lin_expr = [cplex.SparsePair(thevars,thecoefs)], senses = ["E"], rhs = [rhs])
    
    
    
    
    
    model2.solve()
    """
    """
    print(model2.solution.get_objective_value())
    
    solutionValues2=model2.solution.get_values()
    name2idx2 = { n : j for j, n in enumerate(model2.variables.get_names()) }
    
    for key,val in x.iteritems():
        valStore=solutionValues[name2idx[val]]
        if valStore > 0.5:
            print(val+" %f" % valStore)
    
    for key,val in xSlack.iteritems():
        valStore=solutionValues2[name2idx2[val]]
        if valStore > 0.5:
            print(val+" %f" % valStore)
    for key,val in xSlack2.iteritems():
        valStore=solutionValues2[name2idx2[val]]
        if valStore > 0.5:
            print(val+" %f" % valStore)
    print("New tour")
    for key,val in x2.iteritems():
        valStore=solutionValues2[name2idx2[val]]
        if valStore > 0.5:
            print(val +" %f" % valStore)
    """
print(flyTime)
print(paths)