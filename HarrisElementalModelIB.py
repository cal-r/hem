# %% CREATE FUNCTIONS FOR THE MODEL 

# Import libraries
import numpy as np
from re import split,findall
import re
from random import shuffle
import copy
import matplotlib.pyplot as plt

#import matplotlib.ticker as ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg,NavigationToolbar2TkAgg
import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox
import xlsxwriter
import itertools
from PIL import ImageTk
import time 


# Set two different colormaps to alternate after each run
def get_cmap(n,runColor):
    cmapList = ['rainbow','gist_rainbow']    
    name = cmapList[runColor]
    return plt.cm.get_cmap(name, n)


# eachPhase = Separates the text for each phase
# noPhases = number of phases
# stimuli = each stimuli as a string separated in a list
# noStimuli = number of stimuli
def getPhases(text):  
    eachPhase = split('\|', text)
    for i in range(len(eachPhase)):
        tmpEachPres = split('\/',eachPhase[i])
        for j in range(len(tmpEachPres)):
            noTrials = findall('\d+', tmpEachPres[j])
            if noTrials == []:
                tmpEachPres[j] = '1' + tmpEachPres[j]
        eachPhase[i] = '/'.join(tmpEachPres)
            
    noPhases = len(eachPhase)
    stimuli = list(np.unique(np.array(findall('[A-Z]', text)))) # Every presentation with stimuli
    noStimuli = len(stimuli)

    return eachPhase, noPhases,stimuli,noStimuli


# totalElems = total number of elements
# commonElems = total number of common elements
# uncommonElemsList = list of uncommon elements between pairs of stimuli
def giveTotal (similarity,noElems,noStimuli,stimuli) :
    uncommonElemsList = np.ones(len(stimuli)) * noElems
    commonElemsList = np.zeros(len(stimuli))
    commonElems = 0
    for k,v in similarity.items():
        if v>0:
            commonElems += v*noElems
            for i in range(len(k)):
                commonElemsList [stimuli.index(k[i])] += int(v * noElems)
    for i in range(noStimuli):
        uncommonElemsList[i] = uncommonElemsList[i] - commonElemsList[i]
                        
    if commonElems >0:
        totalElems = commonElems + sum(uncommonElemsList)
        totalElems = int(totalElems)           
    else:
        totalElems = noElems * noStimuli
    return totalElems,commonElems,uncommonElemsList


# legendR = legend for Response plot
# legendV = legend for Associative Strength plot
# plotColor_R = colors for each line in Response plot
# plotColor_V = colors for each line in Associative Strength plot
def getLegend(text,noPhases,eachPhase,stimuli,runColor,n):    
    # legendR
    legendR = {}
    for i in range(noPhases):
        tmp = eachPhase[i].replace("^","")
        tmp2 = np.array(findall('[A-Z]+', tmp))
        _,idx = np.unique(tmp2,return_index=True)
        legendR[i] = list(tmp2[np.sort(idx)])
    
    tmp = np.array(findall('[A-Z]+', text.replace("^","")))
    _,idx = np.unique((tmp),return_index=True)  
    allCS = list(tmp[np.sort(idx)])
    probeStimuli = []
    # Add probe stimuli            
    for i in range(noPhases):
        eachPres = split('\/', eachPhase[i])
        for j in range(len(eachPres)):
            tmp = findall('[A-Z]+',eachPres[j].replace("^",""))
            tmp3 = findall('[A-Z]\^',eachPres[j])
            for k in range(len(tmp3)):
                legendR[i].append(tmp3[k] + "{" + tmp[0] + "}")
                probeStimuli.append(tmp3[k] + "{" + tmp[0] + "}")
                
    allCS = allCS + list(np.unique(probeStimuli))
    colors = get_cmap(len(allCS),runColor)      
    plotColor_R = {}
    for i in range(noPhases):
        plotColor_R[i] = []
        for j in range(len(legendR[i])):
            plotColor_R[i].append(tuple(.93**n*x if x == colors(allCS.index(legendR[i][j]))[-1]  \
                       else 0.95**n*x if x == colors(allCS.index(legendR[i][j]))[-2]
                       else 0.85**n*x if x == colors(allCS.index(legendR[i][j]))[-3]                       
                       else 0.60**n*x for x in colors(allCS.index(legendR[i][j]))))
    
    # legendV
    legendV = copy.deepcopy(legendR)
    for i in range(noPhases):
        tmp = eachPhase[i].replace("^","")
        tmp2 = list(np.unique(np.array(findall('[A-Z]', tmp))))
        for j in range(len(tmp2)):
            if not tmp2[j] in legendV[i]:
                legendV[i].append(tmp2[j])
            if not tmp2[j] in allCS:
                allCS = allCS + list(tmp2[j])
    
    colors = get_cmap(len(allCS),runColor)        
    plotColor_V = {}
    for i in range(noPhases):
        plotColor_V[i] = []
        for j in range(len(legendV[i])):
            plotColor_V[i].append(tuple(.93**n*x if x == colors(allCS.index(legendV[i][j]))[-1]  \
                       else 0.95**n*x if x == colors(allCS.index(legendV[i][j]))[-2]
                       else 0.85**n*x if x == colors(allCS.index(legendV[i][j]))[-3]                       
                       else 0.60**n*x for x in colors(allCS.index(legendV[i][j]))))
               
    return legendR,legendV,plotColor_R,plotColor_V


# trialsR = matrix of 0 and 1 to find if stimuli is present for each presentation
# usPres = list of 0 and 1 to find is US is there on presentations
# noTrials = list of trials per presentation
# eachPres = list of presentations as a string
# noPres = number of presentations
def getStimuliMatrixR(eachPhase,stimuli,noStimuli,legendR,p):
    # If US is empty after the stimuli add '-' manually
    tmpEachPres = split('\/',eachPhase[p])
    text = ''
    for i in range(len(tmpEachPres)):
        if not(tmpEachPres[i][-1] == '+' or tmpEachPres[i][-1] == '-'):
            tmpEachPres[i] = tmpEachPres[i] + '-'
        if i < len(tmpEachPres):
            text = text + tmpEachPres[i] + '/'
        else:
            text = text + tmpEachPres[i]
            
    eachPres = split('\+/|\-/|\+|\-', text)
    text = text.replace("^","")
    del eachPres[-1] # Remove last element in list which is empty
       
    noTrials = list(map(int,np.array(findall('\d+', text))))
        
    usPresR = findall('\+|\-', text)
    usPresR = np.array([1 if i == '+' else 0 for i in usPresR])
    
    noPres = len(eachPres) # Number of presentations e.g A+/B+/AB- is 3
    
    dictEachPres = {}
    for i in range(len(legendR[p])):
        dictEachPres[i] = findall('[A-Z]', findall('^[A-Z]+',legendR[p][i])[0])    
    dictStimuliNo = {}
    for i in range(0,noStimuli):
        dictStimuliNo[i] = stimuli[i]            
    dictAlltrials = {}
    for i in range(len(legendR[p])):
        tmp = [0] * noStimuli
        for j in range(0,len(dictEachPres[i])):
            for k in range(0, noStimuli):            
                if dictEachPres[i][j] == dictStimuliNo[k] or tmp[k] == 1 :
                    tmp[k] = 1
            dictAlltrials[i] = tmp
    
#    for i in range(noPres,len(legendR[p])):
#        dictEachPres[i] = findall('^[A-Z]', legendR[p][i])            
#    for i in range(noPres,len(legendR[p])):
#        tmp = [0] * noStimuli
#        for j in range(0,len(dictEachPres[i])):
#            for k in range(0, noStimuli):            
#                if dictEachPres[i][j] == dictStimuliNo[k] or tmp[k] == 1 :
#                    tmp[k] = 1
#            dictAlltrials[i] = tmp
                 
    trialsR = np.zeros((len(legendR[p]),noStimuli))
    for i in range(len(legendR[p])): 
        trialsR[i] = dictAlltrials[i]

    return trialsR,usPresR,noTrials,eachPres,noPres


# trialsV = matrix of 0 and 1 to find if stimuli is present for each presentation
def getStimuliMatrixV(legendV,noStimuli,stimuli,p):
    dictEachPres = {}
    for i in range(len(legendV[p])):
        dictEachPres[i] = findall('^[A-Z]+', legendV[p][i])
        dictEachPres[i] = findall('[A-Z]', dictEachPres[i][0])        
    dictStimuliNo = {}
    for i in range(noStimuli):
        dictStimuliNo[i] = stimuli[i]            
    dictAlltrials = {}
    for i in range(len(legendV[p])):
        tmp = [0] * noStimuli
        for j in range(0,len(dictEachPres[i])):
            for k in range(0, noStimuli):            
                if dictEachPres[i][j] == dictStimuliNo[k] or tmp[k] == 1 :
                    tmp[k] = 1
            dictAlltrials[i] = tmp
                
    trialsV = np.zeros((len(legendV[p]),noStimuli))
    for i in range(len(legendV[p])): 
        trialsV[i] = dictAlltrials[i]
    return trialsV

# stimuliIndexR = index for each presentation that corresponds to legendR. Used for CR.
# presIdx = single number for each presentation. Used in case of repeat trials e.g. 10A+/10B+/10A+
def getStimuliIndexR(legendR,eachPres,p):
    dictAllStimuli = {}
    for i in range(0,len(eachPres)):
        tmp = eachPres[i].replace("^","")
        dictAllStimuli[i]= (findall('[A-Z]+', tmp)[0])
    
    stimuliIndexR = {}
    for i in range(len(dictAllStimuli)):
        stimuliIndexR[i] = []
        stimuliIndexR[i].append(legendR[p].index(dictAllStimuli[i]))
        
    presIdx = copy.deepcopy(stimuliIndexR)
    
    # Add probe trials to index    
    for i in range(len(eachPres)):
       if "^" in eachPres[i]: 
            tmp = eachPres[i].replace("^","")
            tmp2 = findall('[A-Z]\^',eachPres[i]) 
            for j in range(len(tmp2)):
                tmp3 = tmp2[j] + '{' + findall('[A-Z]+',tmp)[0] + '}'
                stimuliIndexR[i].append(legendR[p].index(tmp3))    
    
    return stimuliIndexR,presIdx


# stimuliIndexV = index for each presentation that corresponds to legendV. Used for CR.
def getStimuliIndexV(legendV,eachPres,p):
    # Find index number for each presentation
    dictAllStimuli = {}
    for i in range(0,len(eachPres)):
        tmp = eachPres[i].replace("^","")
        dictAllStimuli[i] = findall('[A-Z]', tmp)
        if len(dictAllStimuli[i])>1:
            dictAllStimuli[i].append(findall('[A-Z]+', tmp)[0])
        
    stimuliIndexV = {}
    for i in range(len(dictAllStimuli)):
        stimuliIndexV[i] = []
        for j in range(len(dictAllStimuli[i])):
            stimuliIndexV[i].append(legendV[p].index(dictAllStimuli[i][j]))
        stimuliIndexV[i] = sorted(stimuliIndexV[i])
                
    # Add probe trials to index    
    for i in range(len(eachPres)):
       if "^" in eachPres[i]: 
            tmp = eachPres[i].replace("^","")
            tmp2 = findall('[A-Z]\^',eachPres[i]) 
            for j in range(len(tmp2)):
                tmp3 = tmp2[j] + '{' + findall('[A-Z]+',tmp)[0] + '}'
                stimuliIndexV[i].append(legendV[p].index(tmp3))
    return stimuliIndexV


# csRep = raw weights for each CS. Common elements and salience are taken into account.
def getCSRepresentation(stimuli,noStimuli,totalElems,commonElems,uncommonElemsList,noElems,salience,similarity):
    csRep = np.zeros([noStimuli,int(totalElems)])
    if commonElems > 0:
        colNo = 0
        for k,v in similarity.items():
            if v>0:
                tmp = []
                for i in range(len(k)):
                    tmp.append(stimuli.index(k[i]))
                commonElems = int(v * noElems)
                for i in range(len(tmp)):
                    csRep[tmp[i],colNo:colNo+commonElems] = abs((np.random.randn(commonElems)+3)/6)
                colNo = colNo + commonElems
                
        for i in range(noStimuli):
            if int(uncommonElemsList[i]) > 0:
                weights = abs((np.random.randn(int(uncommonElemsList[i]))+3)/6)
                csRep[i,colNo:colNo+int(uncommonElemsList[i])] = weights
            colNo = colNo + int(uncommonElemsList[i])
    else:
        for i in range(noStimuli):
            csRep[i,i*noElems:(i+1)*noElems] = abs((np.random.randn(noElems)+3)/6)

    for i in range(0,len(salience)):
        csRep[i] = salience[i] * csRep[i]
    
    return csRep


# capacity = numerical value for buffer capacity.
def getCapacity(allConnections,csRep,totalElems,noElems):
    capacity = 0
    for i in range(len(csRep)):
        tmp = sum(sum(np.multiply(allConnections,np.tile(csRep[i],(totalElems+noElems,1)))))
        if tmp > capacity:
            capacity = tmp
    return capacity


# trialReps = matrix for CS-US connections for each item in either legendR or legendV
# Inspired by HMS
def getTrialReps(noPres,csRep,trials,sparse,capacity,gain,noElems,
                 allConnections,noStimuli,totalElems):
    trialReps = {}
    for i in range(noPres):
        tmp = np.sum(csRep[trials[i,:]==1, :], axis=0)
        connectionsPerTrial = np.multiply(allConnections,np.tile(tmp,(totalElems+noElems,1)))
        sortElems = np.flipud(np.sort(np.array(connectionsPerTrial).flatten()))
        cutoffPres = max(np.multiply((np.cumsum(sortElems) > capacity),sortElems))
        
        csusConnections = np.multiply(allConnections[totalElems:,:],np.tile(tmp,(noElems,1))) # Extract only connections between CS and US
        csusConnectionsGain = np.where(csusConnections > cutoffPres,csusConnections*gain,csusConnections)
         
        trialReps[i] = csusConnectionsGain
    return trialReps    


# sumV = summed V value for weights connecting to each US
# Vs = matrix of V-values for each CS-US connection
# crR = CR for Response (R)
# crV = CR for Associative Strength (V)     
def getCR(usPresR,presNo,presIdx,Vs,gain,L,sumV,cutoff,totalElems,
          trialRepsR,trialRepsV,crR,crV,stimuliIndexV,stimuliIndexR,
          lambdaPlus,lambdaMinus,betaPlus,betaMinus):
    
    idx = presIdx[presNo][0]
    
    # find CR for Response for the presentation
    crRIdx = stimuliIndexR[presNo]
    for i in range(len(crRIdx)):    
        crR[crRIdx[i]].append(np.sum(np.sum(np.multiply(Vs,trialRepsR[crRIdx[i]]), axis=1)))

    # find CR for Associative Strength for the presentation       
    crVIdx = stimuliIndexV[presNo]
    for i in range(len(crVIdx)):                                        
        crV[crVIdx[i]].append(np.sum(np.sum(np.multiply(Vs,trialRepsV[crVIdx[i]]), axis=1))) 

    # Update sumV for the presentation    
    sumV[idx] = np.sum(np.multiply(Vs,trialRepsR[idx]), axis=1)
    
    # Update values of V using update rule which is dependent on US present or absent
    # Update rule setup is the same as HMS    
    if usPresR[presNo] == 1: # US Present
        Vs = Vs + np.multiply(np.tile(np.multiply((gain * betaPlus * (lambdaPlus * L-sumV[idx])), 
                  (lambdaPlus * L-sumV[idx]>=cutoff)),(totalElems,1)).T, trialRepsR[idx]) \
            +  np.multiply(np.tile(np.multiply((-1 * betaPlus * np.abs(lambdaPlus * L-sumV[idx])), 
                   (lambdaPlus * L-sumV[idx]<cutoff)),(totalElems,1)).T, trialRepsR[idx])
    else: # US not present
         Vs = Vs + np.multiply(np.tile(np.multiply((gain * betaMinus * (lambdaMinus * L-sumV[idx])), 
                   (lambdaMinus * L-sumV[idx]>=cutoff)),(totalElems,1)).T, trialRepsR[idx]) \
            +  np.multiply(np.tile(np.multiply((-1 * betaMinus * np.abs(lambdaMinus * L-sumV[idx])), 
                   (lambdaMinus * L-sumV[idx]<cutoff)),(totalElems,1)).T, trialRepsR[idx]) 

    return sumV, Vs, crR, crV


def getAllConnections(totalElems,noElems,noStimuli,density,salience):
    allConnections = np.multiply((abs(np.random.randn(totalElems+noElems,totalElems)+3)/6) < density,
                             (abs(np.random.randn(totalElems+noElems,totalElems)+3)/6))

    return allConnections
   
# %% INITIALISE  VALUES AND SET UP

def trainHEM(groups,randomTrialsValue,noElemsVariableList,gainVariableList,
             densityVariableList,groupRandomise,salienceVariableDict,
             lambdaPlusVariableDict,lambdaMinusVariableDict,betaPlusVariableDict,betaMinusVariableDict,
             similarityDict,capacityVariableList,runColor):

    # Store group CR, legend, stimuli and color in single dictionary    
    groupAveCR_R = {}
    groupAveCR_V = {}
    groupLegend_R = {}
    groupLegend_V = {}
    groupStimuli = {}
    groupPlotColor_R = {}
    groupPlotColor_V = {}

    # Loop through each group   
    for n in range(len(groups)):
        
        text = groups[n] # string of text to represent group
        runs = randomTrialsValue # Number of runs
        noElems = noElemsVariableList[n] # Number of elements per CS
        gain = gainVariableList[n] # Buffer gain
        density = densityVariableList[n] # Connection density from 0-1
        randomise = groupRandomise[n] # randomise trials
        similarity = similarityDict[n] # similarity between pairs of elements
        capacityFactor = capacityVariableList[n] # capacity of buffer
        salience =  salienceVariableDict[n] # salience of each CS
        
        eachPhase,noPhases,stimuli,noStimuli = getPhases(text)
                            
        totalElems,commonElems,uncommonElemsList = giveTotal(similarity,noElems,noStimuli,stimuli)
            
        legendR,legendV,plotColor_R,plotColor_V = getLegend(text,noPhases,eachPhase,stimuli,runColor,n)
             

        # %% FIND V VALUES
        
        totalCRperPhaseR = {} 
        totalCRperPhaseV = {}
        
        # Number of random trials determines runs
        for i in range(runs):
                
            # Representation of CS for each stimuli
            csRep = getCSRepresentation(stimuli,noStimuli,totalElems,commonElems,uncommonElemsList,noElems,salience,similarity)

            allConnections = getAllConnections(totalElems,noElems,noStimuli,density,salience)

            #lambda. Array of US elements with random weights
            L = abs((np.random.randn(noElems)+3)/6)
            L = L/sum(L) 
            
            # Matrix of sparse US-CS connections
            sparse = np.array(np.random.uniform(0,1,(noElems,totalElems))) < density
            
            # If entered group is 0 skip ValueError exception
            try:
                capacity = getCapacity(allConnections,csRep,totalElems,noElems) * capacityFactor
            except ValueError:
                continue
            
            # Cutoff is the value of the threshold in the update rule. (see getCR() function) 
            # Previously set as value according to weight values. Arbitrarily set to zero
            cutoff = 0
            
            # Set up V values
            Vs = np.zeros([noElems,totalElems])
            
            # Loop through each phase
            for p in range(noPhases):
                
                # Exception when group is 0. Skip this 'for' loop
                if eachPhase[p] == '0':
                    continue
                
                trialsR,usPresR,noTrials,eachPres,noPres = getStimuliMatrixR(eachPhase,stimuli,noStimuli,legendR,p) 
                stimuliIndexR,presIdx = getStimuliIndexR(legendR,eachPres,p)               
                                
                trialsV = getStimuliMatrixV(legendV,noStimuli,stimuli,p)
                stimuliIndexV = getStimuliIndexV(legendV,eachPres,p)               
                                
                # Representation of US-CS connections per presentation
                trialRepsR = getTrialReps(len(trialsR),csRep,trialsR,sparse,capacity,gain,noElems,allConnections,noStimuli,totalElems)
                trialRepsV = getTrialReps(len(trialsV),csRep,trialsV,sparse,capacity,gain,noElems,allConnections,noStimuli,totalElems)

                crR={}
                for j in range(len(legendR[p])):
                    crR[j] = []
                    
                crV={}
                for j in range(len(legendV[p])):
                    crV[j] = []
                                
                # Initialise sumV
                sumV = {} 
                for j in range(len(legendR[p])):
                    sumV[j] = np.sum(np.multiply(Vs,trialRepsR[j]), axis=1)

                # Lambda and Beta values for each group and phase                                 
                lambdaPlus = lambdaPlusVariableDict[n][p]
                lambdaMinus = lambdaMinusVariableDict[n][p]
                betaPlus = betaPlusVariableDict[n][p]
                betaMinus = betaMinusVariableDict[n][p]
                                
                # Update V Values and find cr values for R and V
                # If random is True for this phase
                if randomise[p] == 1:            
                    randomTrialsList = []        
                    for k in range(len(noTrials)):
                        randomTrialsList.extend(noTrials[k] * [k])
                    shuffle(randomTrialsList)
                    
                    for k in range(len(randomTrialsList)):
                        presNo = randomTrialsList[k]
                        sumV, Vs, crR, crV = getCR(usPresR,presNo,presIdx,Vs,gain,L,sumV,cutoff,totalElems,
                                                  trialRepsR,trialRepsV,crR,crV,stimuliIndexV,stimuliIndexR,
                                                  lambdaPlus,lambdaMinus,betaPlus,betaMinus)
                # If random is false for phase
                else:                   
                    trialsList = []        
                    for k in range(len(noTrials)):
                        trialsList.extend(noTrials[k] * [k])            
                    for k in range(len(trialsList)):
                        presNo = trialsList[k]
                        sumV, Vs, crR, crV = getCR(usPresR,presNo,presIdx,Vs,gain,L,sumV,cutoff,totalElems,
                                                  trialRepsR,trialRepsV,crR,crV,stimuliIndexV,stimuliIndexR,
                                                  lambdaPlus,lambdaMinus,betaPlus,betaMinus) 
                
                # Convert back to array to perform matrix operations
                for j in range(len(crR)):
                    crR[j] = np.array(crR[j])
                for j in range(len(crV)):
                    crV[j] = np.array(crV[j])
                
                # Total all cr values for R
                if i == 0:
                    totalCRperPhaseR[p] = crR
                else:
                    for k in range(len(legendR[p])):
                        totalCRperPhaseR[p][k] = totalCRperPhaseR[p][k] + crR[k]
                
                # Total all cr values for V
                if i == 0:
                    totalCRperPhaseV[p] = crV
                else:
                    for k in range(len(legendV[p])):
                        totalCRperPhaseV[p][k] = totalCRperPhaseV[p][k] + crV[k]
        
        # Exception when groups are 0
        if not totalCRperPhaseR:
            continue
                         
        # Average the cr values for R over a number of random trials
        aveCR_R = totalCRperPhaseR # Need to set up aveCR with the same dimensions as totalCRperPhase
        for i in range(noPhases):
            try:
                aveCR_R[i]
            except KeyError:
                aveCR_R[i] = {}
            else:
                for j in range(len(aveCR_R[i])):
                    aveCR_R[i][j] = totalCRperPhaseR[i][j]/runs

        # Average the cr values for R over a number of random trials
        aveCR_V = totalCRperPhaseV                    
        for i in range(noPhases):
            try:
                aveCR_V[i]
            except KeyError:
                aveCR_V[i] = {}
            else:
                for j in range(len(aveCR_V[i])):
                    aveCR_V[i][j] = totalCRperPhaseV[i][j]/runs
                
        # Average CR, legend, stimuli and plot colour added to group dictionary
        groupAveCR_R[n] = aveCR_R
        groupAveCR_V[n] = aveCR_V
        groupLegend_R[n] = legendR
        groupLegend_V[n] = legendV
        groupStimuli[n] = stimuli
        groupPlotColor_R[n] = plotColor_R
        groupPlotColor_V[n] = plotColor_V


    return groupAveCR_R,groupAveCR_V,groupLegend_R,groupLegend_V, \
            groupStimuli,groupPlotColor_R,groupPlotColor_V
            
# %% BUILDING GUI FOR THE SIMULATOR

# Main class to open simulator    
class App:        
    def __init__(self,master):
        self.master = master
        # Configure windows to change shape along resize of window
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.master.rowconfigure(2, weight=1)
        self.master.rowconfigure(4, weight=1)
        self.master.columnconfigure(3, weight=1)
        self.master.columnconfigure(7, weight=1)
        self.master.columnconfigure(5, weight=1)
        self.master.columnconfigure(1, weight=1)

        # Setup Menus
        menu = tk.Menu(self.master)
        root.config(menu=menu)
        
        # File menu
        filemenu = tk.Menu(menu, tearoff=0)        
        menuFont = ("Arial", 8)
        menu.add_cascade(label="File", menu=filemenu,font=menuFont)
        filemenu.add_command(label="New", command=self.newExperiment,font=menuFont)
        filemenu.add_command(label="Open Experiment", command=self.file_open,font=menuFont)
        filemenu.add_command(label="Save Experiment", command=self.file_save,font=menuFont)
        filemenu.add_command(label="Export to Excel",command=self.file_export,font=menuFont)
        
        # Settings menu
        settingsmenu = tk.Menu(menu, tearoff=0)        
        self.commonElemsVar = tk.BooleanVar(value=1)
        menu.add_cascade(label="Settings", menu=settingsmenu,font=menuFont)
        settingsmenu.add_checkbutton(label="Common Elements between Paired Stimuli", variable=self.commonElemsVar,
                                     font=menuFont,onvalue=1,offvalue=0)
        self.rPlotsVar = tk.BooleanVar(value=1)        
        settingsmenu.add_checkbutton(label="Plot Response (R) Values", variable=self.rPlotsVar,
                                     font=menuFont,onvalue=1,offvalue=0) 
        self.vPlotsVar = tk.BooleanVar()        
        settingsmenu.add_checkbutton(label="Plot Associative Strength (V) Values", variable=self.vPlotsVar,
                                     font=menuFont,onvalue=1,offvalue=0) 
        settingsmenu.add_command(label="Number of Random Trial Combinations",command=self.randomTrials,font=menuFont)
        self.newExperiment()
    
    # Start a new experiment. Used when simulator starts up and when 'New' is chosen
    # in 'File' menu    
    def newExperiment(self):
        # Exceptions to start a new experiment. If groups have not been initialised
        # then there is no need to delete groups
        try:
            self.groups
            self.noStimuliperGroup
        except AttributeError:
            pass
        else:
            del self.groups
            del self.noStimuliperGroup
        
        # Fonts
        self.headingsFont = ("Arial", 12, 'bold italic')
        buttonFont = ("Arial", 10, 'bold')
        groupsPhasesButtonFont = ("Arial", 8, 'bold')
        self.groupTableHeadingsFont = ("Arial", 9, 'bold')
        
        # Colour and border
        initialiseColour = 'gray80'
        self.setColour = 'gray70'
        runColour = 'gray60'
        buttonFrameColour = '#FBF9ED'
        self.tableColour = '#2B2C0D'
        self.headingsColour = "#CE9D0A"        
        self.labelBorder = 0
        
        # NOTES on GUI
        # tk.Canvas is needed to setup the ability to add scrollbars for each LabelFrame of the GUI
        # tk.LabelFrame is added to the canvas. Widgets are added to the LabelFrame        
        
        # Row and column represent the groups and phases
        self.rowNo = 0
        self.colNo = 0
        
        
        # GROUPS FRAME
        # Group Names, experiment design, random trials, add/remove groups and phases
        self.groupCanvas = tk.Canvas(self.master, borderwidth=0, background=initialiseColour,height=250,width=850)
        self.groupCanvas.grid(row=0,column=0,sticky='NEWS',columnspan=2)        
        self.allGroupFrame = tk.LabelFrame(self.groupCanvas,text='GROUPS',background=self.tableColour,height=250,width=800,font=self.headingsFont,bd=self.labelBorder,foreground=self.headingsColour)
        self.groupVsb = self.AutoScrollbar(self.master, orient="vertical", command=self.groupCanvas.yview)
        self.groupVsb.grid(row=0,column=2,sticky='NS')       
        self.groupHsb = self.AutoScrollbar(self.master, orient="horizontal", command=self.groupCanvas.xview)
        self.groupHsb.grid(row=1,column=0,sticky='WE',columnspan=2)        
        self.groupCanvas.configure(yscrollcommand=self.groupVsb.set)
        self.groupCanvas.configure(xscrollcommand=self.groupHsb.set)                
        self.groupCanvas.create_window((4,4), window=self.allGroupFrame, anchor="nw", 
                                  tags="self.frame")
        self.allGroupFrame.bind("<Configure>", self.onFrameConfigure)

        self.groupsFrame = tk.Frame(master=self.allGroupFrame,background=initialiseColour)
        self.groupsFrame.grid(row=0,column=0)
        self.groupsLabel = tk.Label(master=self.groupsFrame,text='GROUPS',font=groupsPhasesButtonFont)
        self.groupsLabel.grid(row=0,column=0,sticky="nsew")
        self.plusGroup = tk.Button(master=self.groupsFrame,text='+',command=self.addGroups)
        self.plusGroup.grid(row=0,column=2,sticky="nsew")
        self.minusGroup = tk.Button(master=self.groupsFrame,text='-',command=self.minusGroups)
        self.minusGroup.grid(row=0,column=1,sticky="nsew")
        
        self.phasesFrame = tk.Frame(master=self.allGroupFrame)
        self.phasesFrame.grid(row=0,column=1)
        self.phasesLabel = tk.Label(master=self.phasesFrame,text='PHASES',font=groupsPhasesButtonFont)
        self.phasesLabel.grid(row=0,column=0,sticky="nsew", padx=1, pady=1)  
        self.plusPhase = tk.Button(master=self.phasesFrame,text='+',command=self.addPhases)
        self.plusPhase.grid(row=0,column=2)
        self.minusPhase = tk.Button(master=self.phasesFrame,text='-',command=self.minusPhases)
        self.minusPhase.grid(row=0,column=1)
        
        self.groupLabel = tk.Label(master=self.allGroupFrame,text='Group Name',font=self.groupTableHeadingsFont)
        self.groupLabel.grid(row=1,column=0,sticky="nsew", padx=1, pady=1)        
        self.group = {}
        self.groupVariable = {}
        self.groupVariable[self.rowNo] = tk.StringVar(value="Group 1")
        self.group[self.rowNo] = tk.Entry(master=self.allGroupFrame,textvariable=self.groupVariable[self.rowNo])
        self.group[self.rowNo].grid(row=2,column=0,sticky="nsew", padx=1, pady=1)
        
        self.phaseLabel = {}
        self.phaseLabel[self.colNo] = tk.Label(master=self.allGroupFrame,text='Phase 1',font=self.groupTableHeadingsFont)
        self.phaseLabel[self.colNo].grid(row=1,column=1,sticky="nsew", padx=1, pady=1)        
        self.entry = {self.rowNo:{}}
        self.entryVariable = {self.rowNo:{}}
        self.entryVariable[self.rowNo][self.colNo] = tk.StringVar()
        self.entryVariable[self.rowNo][self.colNo].trace("w",self.text_changed)
        self.entry[self.rowNo][self.colNo] = tk.Entry(master=self.allGroupFrame,textvariable=self.entryVariable[self.rowNo][self.colNo],width=30)
        self.entry[self.rowNo][self.colNo].grid(row=2,column=1,sticky="nsew", padx=1, pady=1)
        
        self.randomLabel = {}
        self.randomLabel[self.colNo] = tk.Label(master=self.allGroupFrame,text='Rand 1',font=self.groupTableHeadingsFont)
        self.randomLabel[self.colNo].grid(row=1,column=2,sticky="nsew", padx=1, pady=1) 
        self.check = {self.rowNo:{}}
        self.randomVariable = {self.rowNo:{}}
        self.randomVariable[self.rowNo][self.colNo] = tk.IntVar()
        self.check[self.rowNo][self.colNo] = tk.Checkbutton(master=self.allGroupFrame,variable=self.randomVariable[self.rowNo][self.colNo],command=self.groupInitialiseOff)
        self.check[self.rowNo][self.colNo].grid(row=2,column=2,sticky="nsew",padx=1, pady=1)
        
        
        # PARAMETERS FRAME
        # Number of elements, gain, density, capacity         
        self.paramCanvas = tk.Canvas(self.master,borderwidth=0, background=self.setColour,height=250,width=400)
        self.paramCanvas.grid(row=0,column=3,sticky='NEWS',columnspan=4)
        
        self.paramFrame = tk.LabelFrame(self.paramCanvas,text='PARAMETERS',background=self.tableColour,height=250,width=300,font=self.headingsFont,bd=self.labelBorder,foreground=self.headingsColour)      
        self.paramHsb = self.AutoScrollbar(self.master, orient="horizontal", command=self.paramCanvas.xview)
        self.paramHsb.grid(row=1,column=3,sticky='WE',columnspan=2)        
        self.paramCanvas.configure(xscrollcommand=self.paramHsb.set)                
        self.paramCanvas.create_window((4,4), window=self.paramFrame, anchor="nw", 
                                  tags="self.frame")        
        self.paramFrame.bind("<Configure>", self.onParamFrameConfigure)
     
        self.paramGroupLabel = tk.Label(self.paramFrame,text='Group',font=self.groupTableHeadingsFont)
        self.paramGroupLabel.grid(column=0,row=0,sticky="nsew",padx=1, pady=1)
        
        self.groupOneLabel = {self.rowNo:{}}
        self.groupOneLabel[self.rowNo] = tk.Label(self.paramFrame,text='1',font=self.groupTableHeadingsFont)
        self.groupOneLabel[self.rowNo].grid(column=1,row=0,sticky="nsew",padx=1, pady=1)
        
        self.noElems = {self.rowNo:{}}
        self.noElemsVariable = {self.rowNo:{}}       
        self.noElemsVariable[self.rowNo] = tk.DoubleVar(value=20)
        self.noElemsVariable[self.rowNo].trace('w',self.text_changed_params)
        self.noElems[self.rowNo] = tk.Entry(master=self.paramFrame,textvariable=self.noElemsVariable[self.rowNo],width=5)
        self.noElems[self.rowNo].grid(column=1,row=1,sticky="nsew",padx=1, pady=1)
        self.noElemsLabel = tk.Label(master=self.paramFrame,text = 'Number of Elements',font=self.groupTableHeadingsFont)
        self.noElemsLabel.grid(column=0,row=1,sticky="nsew",padx=1, pady=1)
        
        self.gain = {self.rowNo:{}}  
        self.gainVariable = {self.rowNo:{}}
        self.gainVariable[self.rowNo] = tk.DoubleVar(value=2.0)
        self.gainVariable[self.rowNo].trace('w',self.text_changed_params)
        self.gain[self.rowNo] = tk.Entry(master=self.paramFrame,textvariable=self.gainVariable[self.rowNo],width=5)
        self.gain[self.rowNo].grid(column=1,row=2,sticky="nsew",padx=1, pady=1)
        self.gainLabel = tk.Label(master=self.paramFrame,text = 'Gain',font=self.groupTableHeadingsFont )
        self.gainLabel.grid(column=0,row=2,sticky="nsew",padx=1, pady=1)
     
        self.density = {self.rowNo:{}}
        self.densityVariable = {self.rowNo:{}}
        self.densityVariable[self.rowNo] = tk.DoubleVar(value=0.5)
        self.densityVariable[self.rowNo].trace('w',self.text_changed_params)
        self.density[self.rowNo] = tk.Entry(master=self.paramFrame,textvariable=self.densityVariable[self.rowNo],width=5)
        self.density[self.rowNo].grid(column=1,row=3,sticky="nsew",padx=1, pady=1)
        self.densityLabel = tk.Label(master=self.paramFrame,text = 'Density',font=self.groupTableHeadingsFont)
        self.densityLabel.grid(column=0,row=3,sticky="nsew",padx=1, pady=1)

        self.capacity = {self.rowNo:{}}
        self.capacityVariable = {self.rowNo:{}}
        self.capacityVariable[self.rowNo] = tk.DoubleVar(value=1.0)
        self.capacityVariable[self.rowNo].trace('w',self.text_changed_params)
        self.capacity[self.rowNo] = tk.Entry(master=self.paramFrame,textvariable=self.capacityVariable[self.rowNo],width=5)
        self.capacity[self.rowNo].grid(column=1,row=4,sticky="nsew",padx=1, pady=1)
        self.capacityLabel = tk.Label(master=self.paramFrame,text = 'Capacity',font=self.groupTableHeadingsFont)
        self.capacityLabel.grid(column=0,row=4,sticky="nsew",padx=1, pady=1)
        
        
        # SALIENCE FRAME 
        # Salience of each stimuli                   
        self.salienceCanvas = tk.Canvas(self.master,borderwidth=0, background=self.setColour,height=250,width=300)
        self.salienceCanvas.grid(row=0,column=7,sticky='NEWS')
        
        self.salienceFrame = tk.LabelFrame(self.salienceCanvas,text='SALIENCE',background=self.tableColour,height=20,width=100,font=self.headingsFont,bd=self.labelBorder,foreground=self.headingsColour)      
        self.salienceVsb = self.AutoScrollbar(self.master, orient="vertical", command=self.salienceCanvas.yview)
        self.salienceVsb.grid(row=0,column=8,sticky='NS')
        self.salienceHsb = self.AutoScrollbar(self.master, orient="horizontal", command=self.salienceCanvas.xview)
        self.salienceHsb.grid(row=1,column=7,sticky='WE')         
        self.salienceCanvas.configure(yscrollcommand=self.salienceVsb.set) 
        self.salienceCanvas.configure(xscrollcommand=self.salienceHsb.set)                               
        self.salienceCanvas.create_window((4,4), window=self.salienceFrame, anchor="nw", 
                                  tags="self.frame")        
        self.salienceFrame.bind("<Configure>", self.onSalienceFrameConfigure)
    
    
        # LAMBDA Frame
        # Lambda plus and minus for each group and phase
        self.lambdaPlusCanvas = tk.Canvas(self.master,borderwidth=0, background=self.setColour,height=150,width=200)
        self.lambdaPlusCanvas.grid(row=2,column=3,sticky='NEWS',columnspan=1)
        self.lambdaPlusFrame = tk.LabelFrame(self.lambdaPlusCanvas,text='λ+',background=self.tableColour,height=20,width=100,font=self.headingsFont,bd=self.labelBorder,foreground=self.headingsColour)      
        self.lambdaPlusVsb = self.AutoScrollbar(self.master, orient="vertical", command=self.lambdaPlusCanvas.yview)
        self.lambdaPlusVsb.grid(row=2,column=4,sticky='NS')
        self.lambdaPlusHsb = self.AutoScrollbar(self.master, orient="horizontal", command=self.lambdaPlusCanvas.xview)
        self.lambdaPlusHsb.grid(row=3,column=3,sticky='WE',columnspan=1)         
        self.lambdaPlusCanvas.configure(yscrollcommand=self.lambdaPlusVsb.set) 
        self.lambdaPlusCanvas.configure(xscrollcommand=self.lambdaPlusHsb.set)                               
        self.lambdaPlusCanvas.create_window((4,4), window=self.lambdaPlusFrame, anchor="nw", 
                                  tags="self.frame")        
        self.lambdaPlusFrame.bind("<Configure>", self.onLambdaPlusFrameConfigure)
        
        self.lambdaMinusCanvas = tk.Canvas(self.master,borderwidth=0, background=self.setColour,height=150,width=200)
        self.lambdaMinusCanvas.grid(row=4,column=3,sticky='NEWS',columnspan=1)
        self.lambdaMinusFrame = tk.LabelFrame(self.lambdaMinusCanvas,text='λ-',background=self.tableColour,height=20,width=100,font=self.headingsFont,bd=self.labelBorder,foreground=self.headingsColour)      
        self.lambdaMinusVsb = self.AutoScrollbar(self.master, orient="vertical", command=self.lambdaMinusCanvas.yview)
        self.lambdaMinusVsb.grid(row=4,column=4,sticky='NS')
        self.lambdaMinusHsb = self.AutoScrollbar(self.master, orient="horizontal", command=self.lambdaMinusCanvas.xview)
        self.lambdaMinusHsb.grid(row=5,column=3,sticky='WE',columnspan=1)         
        self.lambdaMinusCanvas.configure(yscrollcommand=self.lambdaMinusVsb.set) 
        self.lambdaMinusCanvas.configure(xscrollcommand=self.lambdaMinusHsb.set)                               
        self.lambdaMinusCanvas.create_window((4,4), window=self.lambdaMinusFrame, anchor="nw", 
                                  tags="self.frame")        
        self.lambdaMinusFrame.bind("<Configure>", self.onlambdaMinusFrameConfigure)
        
        
        # BETA Frames
        # Beta plus and minus for each group and phase        
        self.betaPlusCanvas = tk.Canvas(self.master,borderwidth=0, background=self.setColour,height=150,width=200)
        self.betaPlusCanvas.grid(row=2,column=5,sticky='NEWS',columnspan=1)
        self.betaPlusFrame = tk.LabelFrame(self.betaPlusCanvas,text='β+',background=self.tableColour,height=20,width=100,font=self.headingsFont,bd=self.labelBorder,foreground=self.headingsColour)      
        self.betaPlusVsb = self.AutoScrollbar(self.master, orient="vertical", command=self.betaPlusCanvas.yview)
        self.betaPlusVsb.grid(row=2,column=6,sticky='NS')
        self.betaPlusHsb = self.AutoScrollbar(self.master, orient="horizontal", command=self.betaPlusCanvas.xview)
        self.betaPlusHsb.grid(row=3,column=5,sticky='WE',columnspan=1)         
        self.betaPlusCanvas.configure(yscrollcommand=self.betaPlusVsb.set) 
        self.betaPlusCanvas.configure(xscrollcommand=self.betaPlusHsb.set)                               
        self.betaPlusCanvas.create_window((4,4), window=self.betaPlusFrame, anchor="nw", 
                                  tags="self.frame")        
        self.betaPlusFrame.bind("<Configure>", self.onbetaPlusFrameConfigure)
        
        self.betaMinusCanvas = tk.Canvas(self.master,borderwidth=0, background=self.setColour,height=150,width=200)
        self.betaMinusCanvas.grid(row=4,column=5,sticky='NEWS',columnspan=1)
        self.betaMinusFrame = tk.LabelFrame(self.betaMinusCanvas,text='β-',background=self.tableColour,height=20,width=100,font=self.headingsFont,bd=self.labelBorder,foreground=self.headingsColour)      
        self.betaMinusVsb = self.AutoScrollbar(self.master, orient="vertical", command=self.betaMinusCanvas.yview)
        self.betaMinusVsb.grid(row=4,column=6,sticky='NS')
        self.betaMinusHsb = self.AutoScrollbar(self.master, orient="horizontal", command=self.betaMinusCanvas.xview)
        self.betaMinusHsb.grid(row=5,column=5,sticky='WE',columnspan=1)         
        self.betaMinusCanvas.configure(yscrollcommand=self.betaMinusVsb.set) 
        self.betaMinusCanvas.configure(xscrollcommand=self.betaMinusHsb.set)                               
        self.betaMinusCanvas.create_window((4,4), window=self.betaMinusFrame, anchor="nw", 
                                  tags="self.frame")        
        self.betaMinusFrame.bind("<Configure>", self.onbetaMinusFrameConfigure) 
        
        # COMMON ELEMENTS FRAME
        # Common elements for each pair of stimuli
        self.commonCanvas = tk.Canvas(self.master,borderwidth=0,height=300,width=300,background=self.setColour)
        self.commonCanvas.grid(row=2,column=7,sticky='NEWS',rowspan=4)
        self.commonFrame = tk.LabelFrame(self.commonCanvas,text='COMMON ELEMENTS',background=self.tableColour,height=20,width=200,
                                         font=self.headingsFont,bd=self.labelBorder,foreground=self.headingsColour)      
        self.commonVsb = self.AutoScrollbar(self.master, orient="vertical", command=self.commonCanvas.yview)
        self.commonVsb.grid(row=2,column=8,sticky='NS',rowspan=4)
        self.commonCanvas.configure(yscrollcommand=self.commonVsb.set)
        self.commonHsb = self.AutoScrollbar(self.master, orient="horizontal", command=self.commonCanvas.xview)
        self.commonHsb.grid(row=6,column=7,sticky='WE')
        self.commonCanvas.configure(xscrollcommand=self.commonHsb.set) 
        self.commonCanvas.create_window((4,4), window=self.commonFrame, anchor="nw", 
                                  tags="self.frame")        
        self.commonFrame.bind("<Configure>", self.onCommonFrameConfigure)
            
        # BUTTONS FRAME
        # Initiate, set and run buttons
        buttonFrame = tk.Frame(self.master,background=buttonFrameColour,width=300)    
        buttonFrame.grid(row=2,column=1,sticky='NEWS',rowspan=4)
        self.initiateButton = tk.Button(buttonFrame,text='1. Initialise',font=buttonFont,command=self.initiate,height=2,width=15,bd=4,background=initialiseColour)
        self.initiateButton.grid(row=1,column=1) 
        
        self.setParamsButton = tk.Button(buttonFrame,text='2. Set Parameters',font=buttonFont,command=self.setParams,height=2,width=15,bd=4,background=self.setColour)
        self.setParamsButton.grid(row=2,column=1)   
        
        self.runButton = tk.Button(buttonFrame,text='3. Run',font=buttonFont,command=self.run,height=2,width=15,bd=4,background=runColour)        
        self.runButton.grid(row=3,column=1)

        self.displayButton = tk.Button(buttonFrame,text='Display Figures',font=buttonFont,command=self.display,height=2,width=15,bd=4,background=runColour)
        self.displayButton.grid(row=4,column=1)
        
        # Centre all buttons and labls in middle of buttonFrame
        buttonFrame.grid_rowconfigure(0, weight=1)
        buttonFrame.grid_rowconfigure(4, weight=1)
        buttonFrame.grid_columnconfigure(0, weight=1)
        buttonFrame.grid_columnconfigure(3, weight=1)
        
        
        # Initialise variables. (This is needed to not create errors)
        self.salience = {0:{}}
        self.salienceGroupLabel = {}
        self.salienceLabel = {0:{}}
        
        self.lambdaPlus = {}
        self.lambdaPlusGroupLabel = {}
        self.lambdaPlusPhaseLabel = {}
        
        self.lambdaMinus = {}
        self.lambdaMinusGroupLabel = {}
        self.lambdaMinusPhaseLabel = {}
        
        self.betaPlus = {}
        self.betaPlusGroupLabel = {}
        self.betaPlusPhaseLabel = {}
        
        self.betaMinus = {}
        self.betaMinusGroupLabel = {}
        self.betaMinusPhaseLabel = {}
        
        self.salienceVariable = {0:{}}        
        self.lambdaPlusVariable = {0:{}}
        self.lambdaMinusVariable = {0:{}}
        self.betaPlusVariable = {0:{}} 
        self.betaMinusVariable = {0:{}} 
        
        self.similarityGroupLabel = {}
        self.similarity = {}
        self.similarityLabel = {} 
        self.similarityVariable = {0:{}}
        
        self.commonElementsTitleLabel = tk.Label()
       
        self.initialiseState = tk.IntVar()
        self.initialiseCheck = tk.Checkbutton(buttonFrame,state=tk.DISABLED,background=buttonFrameColour,
                                              variable=self.initialiseState)
        self.initialiseCheck.grid(column=2, row=1,sticky='E')
        
        self.setParamsState = tk.IntVar()
        self.setParamsCheck = tk.Checkbutton(buttonFrame,state=tk.DISABLED,background=buttonFrameColour,
                                             variable=self.setParamsState)
        self.setParamsCheck.grid(column=2, row=2,sticky='W')
        
        self.runState = tk.IntVar()
        self.runCheck = tk.Checkbutton(buttonFrame,state=tk.DISABLED,background=buttonFrameColour,
                                             variable=self.runState)
        self.runCheck.grid(column=2, row=3,sticky='W')
        
        # Icon at bottom left of simulator        
        anImage = ImageTk.PhotoImage(file="Harris-IB-small.png")
        iconLabel = tk.Label(self.master,background="#FBF9ED")
        iconLabel.config(image=anImage)
        iconLabel.image = anImage
        iconLabel.grid(row=2,column=0,sticky='NEWS',rowspan=4)
        
        # Setup number of random trials
        try:
            self.randomTrialsVariable
            self.randomTrialsValue
        except:
            self.randomTrialsVariable = tk.IntVar(value=100)
            self.randomTrialsValue = 100
        
        # Set up the colormap index. Colormap changes after every run
        self.runColor = 0
        self.onRandomTrials = 0

    # Function linked to pressing the Initalise button   
    def initiate(self):
        # Return the groups and random variable
        self.groups = {}
        for i in range(self.rowNo +1):
            self.groups[i] = []
            for j in range(self.colNo +1):
                eachPres = re.split('\/',self.entryVariable[i][j].get())
                for k in range(len(eachPres)):
                    eachPres[k] = eachPres[k].replace("^","")
                    check = re.findall('\d+[A-Z]+\+$|\d+[A-Z]+\-$|\d+[A-Z]+$|[A-Z]+\+$|[A-Z]+\-$|[A-Z]+$|^[0]$',eachPres[k])
                    if not check:
                        tkinter.messagebox.showinfo("Warning", "Error on GROUP %d" %(i+1) + ", PHASE %d" %(j+1) + "\nPlease Enter Representation Correctly")
                        self.initialiseCheck.deselect()                        
                        self.setParamsCheck.deselect()
                        del self.groups
                        return
                if j == 0:
                    self.groups[i].append(self.entryVariable[i][j].get())
                    self.groups[i] = self.groups[i][0]
                else:
                    self.groups[i] = self.groups[i] + '|' + (self.entryVariable[i][j].get())        
        self.groupRandomise = {}
        for i in range(self.rowNo +1):
            self.groupRandomise[i] = []
            for j in range(self.colNo +1):
                self.groupRandomise[i].append(self.randomVariable[i][j].get())

        # PARAMETERS Table
        # Remove widgets from previous experiment
        for i in range(len(self.noElems)):
            self.noElems[i].destroy()
            self.gain[i].destroy()
            self.density[i].destroy()
            self.groupOneLabel[i].destroy()
            self.capacity[i].destroy()
        # Add new widgets according to number of groups
        for i in range(len(self.noElems),self.rowNo+1):
            self.noElemsVariable[i] = tk.DoubleVar(value=20)                
            self.gainVariable[i] = tk.DoubleVar(value=2.0)
            self.densityVariable[i] = tk.DoubleVar(value=0.5)
            self.capacityVariable[i] = tk.DoubleVar(value=1.0)
            self.noElemsVariable[i].trace('w',self.text_changed_params)
            self.gainVariable[i].trace('w',self.text_changed_params)
            self.densityVariable[i].trace('w',self.text_changed_params)
            self.capacityVariable[i].trace('w',self.text_changed_params)                        
        for i in range(self.rowNo+1):
            self.groupOneLabel[i] = tk.Label(self.paramFrame,text= i+1,font=self.groupTableHeadingsFont)
            self.groupOneLabel[i].grid(column=i+1,row=0,sticky="nsew",padx=1, pady=1)            
            self.noElems[i] = tk.Entry(master=self.paramFrame,textvariable=self.noElemsVariable[i],width=5)
            self.noElems[i].grid(column=i+1,row=1,sticky="nsew",padx=1, pady=1)
            self.gain[i] = tk.Entry(master=self.paramFrame,textvariable=self.gainVariable[i],width=5)
            self.gain[i].grid(column=i+1,row=2,sticky="nsew",padx=1, pady=1)  
            self.density[i] = tk.Entry(master=self.paramFrame,textvariable=self.densityVariable[i],width=5)
            self.density[i].grid(column=i+1,row=3,sticky="nsew",padx=1, pady=1) 
            self.capacity[i] = tk.Entry(master=self.paramFrame,textvariable=self.capacityVariable[i],width=5)
            self.capacity[i].grid(column=i+1,row=4,sticky="nsew",padx=1, pady=1) 
        
        # SALIENCE Table
        # Remove widgets from previous experiment
        for i in range(len(self.salience)):
            for j in range(len(self.salience[i])):
                self.salience[i][j].destroy()                
        for i in range(len(self.salienceGroupLabel)):
            self.salienceGroupLabel[i].destroy()
        for i in range(len(self.salienceLabel)):
            for j in range(len(self.salienceLabel[i])):
                self.salienceLabel[i][j].destroy()
        # Add widgets to setup salience table                
        salienceGroupTitleLabel = tk.Label(self.salienceFrame,text="Group",font=self.groupTableHeadingsFont)
        salienceGroupTitleLabel.grid(row=0,column=0,sticky="nsew",padx=1, pady=1)                           
        self.salience = {}
        self.salienceGroupLabel = {}
        self.salienceLabel = {}
        maxCol = 0
        self.noStimuliperGroup = []        
        self.stimuliDict = {}          
        for i in range(len(self.groups)):
            eachPhase, noPhases,stimuli,noStimuli = getPhases(self.groups[i])
            self.salience[i] = {}
            self.salienceLabel[i] = {}
            self.salienceGroupLabel[i] = tk.Label(self.salienceFrame,text=i+1,font=self.groupTableHeadingsFont,width=6)
            self.salienceGroupLabel[i].grid(row=0,column=2*i+1,sticky="nsew",padx=1, pady=1,columnspan=2)
            self.stimuliDict[i] = []
            for j in range(noStimuli):
                try:
                    self.salienceVariable[i][j]
                except KeyError:
                    self.salienceVariable[i][j] = tk.DoubleVar(value=0.5)
                    self.salienceVariable[i][j].trace('w',self.text_changed_params)
                self.salience[i][j] = tk.Entry(self.salienceFrame,textvariable=self.salienceVariable[i][j],width=5)
                self.salience[i][j].grid(row=j+1,column=2*i+2,sticky="nsew",padx=1, pady=1)
                self.salienceLabel[i][j] = tk.Label(self.salienceFrame,text = stimuli[j],font=self.groupTableHeadingsFont)
                self.salienceLabel[i][j].grid(row=j+1,column=2*i+1,sticky="nsew",padx=1, pady=1)
                self.stimuliDict[i].append(stimuli[j])
            if noStimuli > maxCol:
                maxCol = noStimuli            
            self.noStimuliperGroup.append(noStimuli)        
        salienceTitleLabel = tk.Label(self.salienceFrame,text="Salience",font=self.groupTableHeadingsFont)
        if not (maxCol==0):
            salienceTitleLabel.grid(row=1,column=0,rowspan=maxCol,sticky="nsew",padx=1, pady=1)

        # COMMON ELEMENTS Table 
        # Paired Stimuli
        if self.commonElemsVar.get() == 1:
            self.similarityDict = {}
            for i in range(len(self.groups)):
                eachPhase, noPhases,stimuli,noStimuli = getPhases(self.groups[i])                
                self.similarityDict[i] = {}
                for j in range(noStimuli + 1):
                    for subset in itertools.combinations(stimuli, j):
                        if len(list(subset)) == 2:
                            self.similarityDict[i][subset] = 0.0
        # All stimuli                    
        if self.commonElemsVar.get() == 0:
            self.similarityDict = {}
            for i in range(len(self.groups)):
                eachPhase, noPhases,stimuli,noStimuli = getPhases(self.groups[i])                
                self.similarityDict[i] = {}
                for j in range(noStimuli + 1):
                    for subset in itertools.combinations(stimuli, j):
                        if len(list(subset)) == noStimuli & noStimuli > 1:
                            self.similarityDict[i][subset] = 0.0           
        # Remove widgets from previous experiment                            
        for i in range(len(self.similarity)):
            for j in range(len(self.similarity[i])):
                self.similarity[i][j].destroy()          
        for i in range(len(self.similarityGroupLabel)):
            self.similarityGroupLabel[i].destroy()
        for i in range(len(self.similarityLabel)):
            for j in range(len(self.similarityLabel[i])):
                self.similarityLabel[i][j].destroy()
        # Add widgets to setup common elements table                                                        
        similarityGroupTitleLabel = tk.Label(self.commonFrame,text="Group",font=self.groupTableHeadingsFont)
        similarityGroupTitleLabel.grid(row=0,column=0,sticky="nsew",padx=1, pady=1)             
        self.similarityGroupLabel = {}
        self.similarity = {}
        self.similarityLabel = {}
        self.maxColSim = 1
        for i in range(len(self.groups)):
            self.similarity[i] = {}
            self.similarityLabel[i] = {}
            self.similarityGroupLabel[i] = tk.Label(self.commonFrame,text=i+1,font=self.groupTableHeadingsFont,width=6)
            self.similarityGroupLabel[i].grid(row=0,column=2*i+1,sticky="nsew",padx=1, pady=1,columnspan=2)                
            similarityList = []                
            for k,v in self.similarityDict[i].items():
                similarityList.append(k)
            for j in range(len(self.similarityDict[i])):
                try:
                    self.similarityVariable[i][j]
                except KeyError:
                    self.similarityVariable[i][j] = tk.DoubleVar(value=0.0)
                    self.similarityVariable[i][j].trace('w',self.text_changed_params)
                self.similarity[i][j] = tk.Entry(self.commonFrame,textvariable=self.similarityVariable[i][j],width=5)
                self.similarity[i][j].grid(row=j+1,column=2*i+2,sticky="nsew",padx=1,pady=1)
                self.similarityLabel[i][j] = tk.Label(self.commonFrame,text="".join(similarityList[j]),font=self.groupTableHeadingsFont)
                self.similarityLabel[i][j].grid(row=j+1,column=2*i+1,sticky="nsew",padx=1, pady=1)                  
            if len(self.similarityDict[i])>self.maxColSim:
                self.maxColSim = len(self.similarityDict[i])        
        self.nonZeroSimilarityGroups = np.ones(self.rowNo+1)
        for i in range(len(self.similarityDict)):
            if self.similarityDict[i] == {}:
                self.nonZeroSimilarityGroups[i] = 0    
        self.commonElementsTitleLabel.destroy()
        self.commonElementsTitleLabel = tk.Label(self.commonFrame,text="Common",font=self.groupTableHeadingsFont)
        self.commonElementsTitleLabel.grid(row=1,column=0,rowspan=self.maxColSim,sticky="nsew",padx=1, pady=1)
                   
        # LAMBDA Table
        # Remove widgets from previous experiment                            
        for i in range(len(self.lambdaPlus)):
            for j in range(len(self.lambdaPlus[i])):
                self.lambdaPlus[i][j].destroy()
                self.lambdaMinus[i][j].destroy()                
        for i in range(len(self.lambdaPlusGroupLabel)):
            self.lambdaPlusGroupLabel[i].destroy()
            self.lambdaMinusGroupLabel[i].destroy()
        for i in range(len(self.lambdaPlusPhaseLabel)):
            self.lambdaPlusPhaseLabel[i].destroy()
            self.lambdaMinusPhaseLabel[i].destroy()
        # Add widgets to setup lambda plus table                                                        
        lambdaPlusGroupLabel = tk.Label(self.lambdaPlusFrame,text="Group",font=self.groupTableHeadingsFont)
        lambdaPlusGroupLabel.grid(row=1,column=0,rowspan=self.rowNo +1,sticky="nsew",padx=1, pady=1)
        lambdaPlusPhaseTitleLabel = tk.Label(self.lambdaPlusFrame,text="Phase",font=self.groupTableHeadingsFont)
        lambdaPlusPhaseTitleLabel.grid(row=0,column=0,sticky="nsew",padx=1, pady=1,columnspan=2)                                                      
        self.lambdaPlus = {}
        self.lambdaPlusGroupLabel = {}
        self.lambdaPlusPhaseLabel = {}
        for i in range(self.rowNo +1):
            self.lambdaPlus[i] = {}
            self.lambdaPlusGroupLabel[i] = tk.Label(self.lambdaPlusFrame,text=i+1,font=self.groupTableHeadingsFont)
            self.lambdaPlusGroupLabel[i].grid(row=i+1,column=1,sticky="nsew",padx=1, pady=1)
            for j in range(self.colNo +1):
                try:
                    self.lambdaPlusVariable[i][j]
                except KeyError:
                    self.lambdaPlusVariable[i][j] = tk.DoubleVar(value=100.0)
                    self.lambdaPlusVariable[i][j].trace('w',self.text_changed_params)                                    
                self.lambdaPlus[i][j] = tk.Entry(self.lambdaPlusFrame,textvariable=self.lambdaPlusVariable[i][j],width=5)
                self.lambdaPlus[i][j] .grid(row=i+1,column=j+2,sticky="nsew",padx=1, pady=1)                
        for i in range(self.colNo +1) :       
            self.lambdaPlusPhaseLabel[i] = tk.Label(self.lambdaPlusFrame,text = i+1,font=self.groupTableHeadingsFont)
            self.lambdaPlusPhaseLabel[i].grid(row=0,column=i+2,sticky="nsew",padx=1, pady=1)                    
        # Add widgets to setup lambda minus table                                                        
        lambdaMinusGroupLabel = tk.Label(self.lambdaMinusFrame,text="Group",font=self.groupTableHeadingsFont)
        lambdaMinusGroupLabel.grid(row=1,column=0,rowspan=self.rowNo +1,sticky="nsew",padx=1, pady=1) 
        lambdaMinusPhaseTitleLabel = tk.Label(self.lambdaMinusFrame,text="Phase",font=self.groupTableHeadingsFont)
        lambdaMinusPhaseTitleLabel.grid(row=0,column=0,sticky="nsew",padx=1, pady=1,columnspan=2)                           
        self.lambdaMinus = {}
        self.lambdaMinusGroupLabel = {}
        self.lambdaMinusPhaseLabel = {}
        for i in range(self.rowNo +1):
            self.lambdaMinus[i] = {}
            self.lambdaMinusGroupLabel[i] = tk.Label(self.lambdaMinusFrame,text=i+1,font=self.groupTableHeadingsFont)
            self.lambdaMinusGroupLabel[i].grid(row=i+1,column=1,sticky="nsew",padx=1, pady=1)
            for j in range(self.colNo +1):
                try:
                    self.lambdaMinusVariable[i][j]
                except KeyError:
                    self.lambdaMinusVariable[i][j] = tk.DoubleVar(value=0.0)
                    self.lambdaMinusVariable[i][j].trace('w',self.text_changed_params)                    
                self.lambdaMinus[i][j] = tk.Entry(self.lambdaMinusFrame,textvariable=self.lambdaMinusVariable[i][j],width=5)
                self.lambdaMinus[i][j].grid(row=i+1,column=j+2,sticky="nsew",padx=1, pady=1)
        for i in range(self.colNo +1) :                       
            self.lambdaMinusPhaseLabel[i] = tk.Label(self.lambdaMinusFrame,text = i+1,font=self.groupTableHeadingsFont)
            self.lambdaMinusPhaseLabel[i].grid(row=0,column=i+2,sticky="nsew",padx=1, pady=1)                    

        # BETA Table
        # Remove widgets from previous experiment                            
        for i in range(len(self.betaPlus)):
            for j in range(len(self.betaPlus[i])):
                self.betaPlus[i][j].destroy()
                self.betaMinus[i][j].destroy()                
        for i in range(len(self.betaPlusGroupLabel)):
            self.betaPlusGroupLabel[i].destroy()
            self.betaMinusGroupLabel[i].destroy()
        for i in range(len(self.betaPlusPhaseLabel)):
            self.betaPlusPhaseLabel[i].destroy()
            self.betaMinusPhaseLabel[i].destroy()
        # Add widgets to setup beta plus table                                                                         
        betaPlusGroupLabel = tk.Label(self.betaPlusFrame,text="Group",font=self.groupTableHeadingsFont)
        betaPlusGroupLabel.grid(row=1,column=0,rowspan=self.rowNo +1,sticky="nsew",padx=1, pady=1)
        betaPlusPhaseTitleLabel = tk.Label(self.betaPlusFrame,text="Phase",font=self.groupTableHeadingsFont)
        betaPlusPhaseTitleLabel.grid(row=0,column=0,sticky="nsew",padx=1, pady=1,columnspan=2)                                                      
        self.betaPlus = {}
        self.betaPlusGroupLabel = {}
        self.betaPlusPhaseLabel = {}
        for i in range(self.rowNo +1):
            self.betaPlus[i] = {}
            self.betaPlusGroupLabel[i] = tk.Label(self.betaPlusFrame,text=i+1,font=self.groupTableHeadingsFont)
            self.betaPlusGroupLabel[i].grid(row=i+1,column=1,sticky="nsew",padx=1, pady=1)
            for j in range(self.colNo +1):
                try:
                    self.betaPlusVariable[i][j]
                except KeyError:
                    self.betaPlusVariable[i][j] = tk.DoubleVar(value=0.01)
                    self.betaPlusVariable[i][j].trace('w',self.text_changed_params) 
                self.betaPlus[i][j] = tk.Entry(self.betaPlusFrame,textvariable=self.betaPlusVariable[i][j],width=4)
                self.betaPlus[i][j] .grid(row=i+1,column=j+2,sticky="nsew",padx=1, pady=1)                
        for i in range(self.colNo +1) :       
            self.betaPlusPhaseLabel[i] = tk.Label(self.betaPlusFrame,text = i+1,font=self.groupTableHeadingsFont)
            self.betaPlusPhaseLabel[i].grid(row=0,column=i+2,sticky="nsew",padx=1, pady=1)                    
        # Add widgets to setup beta minus table                                                                         
        betaMinusGroupLabel = tk.Label(self.betaMinusFrame,text="Group",font=self.groupTableHeadingsFont)
        betaMinusGroupLabel.grid(row=1,column=0,rowspan=self.rowNo +1,sticky="nsew",padx=1, pady=1) 
        betaMinusPhaseTitleLabel = tk.Label(self.betaMinusFrame,text="Phase",font=self.groupTableHeadingsFont)
        betaMinusPhaseTitleLabel.grid(row=0,column=0,sticky="nsew",padx=1, pady=1,columnspan=2)                           
        self.betaMinus = {}
        self.betaMinusGroupLabel = {}
        self.betaMinusPhaseLabel = {}
        for i in range(self.rowNo +1):
            self.betaMinus[i] = {}
            self.betaMinusGroupLabel[i] = tk.Label(self.betaMinusFrame,text=i+1,font=self.groupTableHeadingsFont)
            self.betaMinusGroupLabel[i].grid(row=i+1,column=1,sticky="nsew",padx=1, pady=1)
            for j in range(self.colNo +1):
                try:
                    self.betaMinusVariable[i][j]
                except KeyError:
                    self.betaMinusVariable[i][j] = tk.DoubleVar(value=0.01) 
                    self.betaMinusVariable[i][j].trace('w',self.text_changed_params)
                self.betaMinus[i][j] = tk.Entry(self.betaMinusFrame,textvariable=self.betaMinusVariable[i][j],width=4)
                self.betaMinus[i][j].grid(row=i+1,column=j+2,sticky="nsew",padx=1, pady=1)
        for i in range(self.colNo +1) :                       
            self.betaMinusPhaseLabel[i] = tk.Label(self.betaMinusFrame,text = i+1,font=self.groupTableHeadingsFont)
            self.betaMinusPhaseLabel[i].grid(row=0,column=i+2,sticky="nsew",padx=1, pady=1) 

        # Check initialise tickbox                        
        self.initialiseCheck.select()
        self.setParamsCheck.deselect()
        self.runCheck.deselect()
     
        
    # Function linked to pressing the Set Parameters button           
    def setParams(self):
        # Error exception if Initialise button not pressed first
        if self.initialiseState.get() == 1:
            pass
        else: 
            tkinter.messagebox.showinfo("Warning","Please INITAILISE GROUPS before SET PARAMETERS")
            return
        
        # Retrieve number of elements, gain, density, capacity, salience, lambda,
        # beta & similarity
        self.noElemsVariableList = []
        for i in range(self.rowNo +1):
            try:
                self.noElemsVariable[i].get()
            except tk.TclError:
                tkinter.messagebox.showinfo("Warning","Error on ELEMENTS parameter in GROUP %d" %(i+1) + "\nNumber of elements takes integer values")
                return  
            check = re.findall('^[0-9]+\.0$',str(self.noElemsVariable[i].get()))
            if not check:
                tkinter.messagebox.showinfo("Warning","Error on ELEMENTS parameter in GROUP %d" %(i+1) + "\nNumber of elements takes integer values")
                return
            self.noElemsVariableList.append(int(self.noElemsVariable[i].get()))
                                       
        self.gainVariableList = []
        for i in range(self.rowNo +1):
            try:
                self.gainVariable[i].get()
            except tk.TclError:
                tkinter.messagebox.showinfo("Warning","Error on GAIN parameter in GROUP %d" %(i+1) + "\nGain takes positive values")
                return 
            check = re.findall('^[0-9]+\.[0-9]+$',str(self.gainVariable[i].get()))
            if not check:
                tkinter.messagebox.showinfo("Warning","Error on GAIN parameter in GROUP %d" %(i+1) + "\nGain takes positive values")
                return            
            self.gainVariableList.append(self.gainVariable[i].get())
        
        self.densityVariableList = []
        for i in range(self.rowNo +1):
            try:
                self.densityVariable[i].get()
            except tk.TclError:
                tkinter.messagebox.showinfo("Warning","Error on DENSITY parameter in GROUP %d" %(i+1) + "\nDensity takes values from 0-1")
                return
            check = re.findall('^0\.[0-9]+$|^1\.0+$|^1$',str(self.densityVariable[i].get()))
            if not check:
                tkinter.messagebox.showinfo("Warning","Error on DENSITY parameter in GROUP %d" %(i+1) + "\nDensity takes values from 0-1")
                return            
            self.densityVariableList.append(self.densityVariable[i].get())

        self.capacityVariableList = []
        for i in range(self.rowNo +1):
            try:
                self.capacityVariable[i].get()
            except tk.TclError:
                tkinter.messagebox.showinfo("Warning","Error on CAPACITY parameter in GROUP %d" %(i+1) + "\nCapacity takes positive values")
                return
            check = re.findall('^[0-9]+\.[0-9]+$',str(self.capacityVariable[i].get()))
            if not check:
                tkinter.messagebox.showinfo("Warning","Error on CAPACITY parameter in GROUP %d" %(i+1) + "\nCapacity takes positive values")
                return 
            self.capacityVariableList.append(self.capacityVariable[i].get())
                    
        self.salienceVariableDict = {}
        for i in range(self.rowNo +1):
            eachPhase, noPhases,stimuli,noStimuli = getPhases(self.groups[i])
            self.salienceVariableDict[i] = []
            for j in range(noStimuli):
                try:
                    self.salienceVariable[i][j].get()
                except tk.TclError:
                    tkinter.messagebox.showinfo("Warning","Error on SALIENCE parameter in GROUP %d" %(i+1) + ", STIMULI %s" % stimuli[j] + "\nSalience takes values from 0-1")
                    return
                check = re.findall('^0\.[0-9]+$|^1\.0+$|^1$',str(self.salienceVariable[i][j].get()))
                if not check:
                    tkinter.messagebox.showinfo("Warning","Error on SALIENCE parameter in GROUP %d" %(i+1) + ", STIMULI %s" % stimuli[j] + "\nSalience takes values from 0-1")
                    return                 
                self.salienceVariableDict[i].append(self.salienceVariable[i][j].get())

        self.lambdaPlusVariableDict = {}
        for i in range(self.rowNo +1):
            self.lambdaPlusVariableDict[i] = []
            for j in range(self.colNo +1):
                try:
                    self.lambdaPlusVariable[i][j].get()
                except tk.TclError:
                    tkinter.messagebox.showinfo("Warning","Error on λ+ parameter in GROUP %d" %(i+1) + ", PHASE %s" % (j+1) + "\nλ+ takes positive values")
                    return
                check = re.findall('^[0-9]+\.[0-9]+$',str(self.lambdaPlusVariable[i][j].get()))
                if not check:
                    tkinter.messagebox.showinfo("Warning","Error on λ+ parameter in GROUP %d" %(i+1) + ", PHASE %s" % (j+1) + "\nλ+ takes positive values")
                    return                
                self.lambdaPlusVariableDict[i].append(self.lambdaPlusVariable[i][j].get())
                
        self.lambdaMinusVariableDict = {}
        for i in range(self.rowNo +1):
            self.lambdaMinusVariableDict[i] = []
            for j in range(self.colNo +1):
                try:
                    self.lambdaMinusVariable[i][j].get()
                except tk.TclError:
                    tkinter.messagebox.showinfo("Warning","Error on λ- parameter in GROUP %d" %(i+1) + ", PHASE %s" % (j+1) + "\nλ- takes positive values")
                    return 
                check = re.findall('^[0-9]+\.[0-9]+$',str(self.lambdaMinusVariable[i][j].get()))
                if not check:
                    tkinter.messagebox.showinfo("Warning","Error on λ- parameter in GROUP %d" %(i+1) + ", PHASE %s" % (j+1) + "\nλ- takes positive values")
                    return 
                self.lambdaMinusVariableDict[i].append(self.lambdaMinusVariable[i][j].get())

        self.betaPlusVariableDict = {}
        for i in range(self.rowNo +1):
            self.betaPlusVariableDict[i] = []
            for j in range(self.colNo +1):
                try:
                    self.betaPlusVariable[i][j].get()
                except tk.TclError:
                    tkinter.messagebox.showinfo("Warning","Error on β+ parameter in GROUP %d" %(i+1) + ", PHASE %s" % (j+1) + "\nβ+ takes positive values")
                    return 
                check = re.findall('^[0-9]+\.[0-9]+$',str(self.betaPlusVariable[i][j].get()))
                if not check:
                    tkinter.messagebox.showinfo("Warning","Error on β+ parameter in GROUP %d" %(i+1) + ", PHASE %s" % (j+1) + "\nβ+ takes positive values")
                    return 
                self.betaPlusVariableDict[i].append(self.betaPlusVariable[i][j].get())
                
        self.betaMinusVariableDict = {}
        for i in range(self.rowNo +1):
            self.betaMinusVariableDict[i] = []
            for j in range(self.colNo +1):
                try:
                    self.betaMinusVariable[i][j].get()
                except tk.TclError:
                    tkinter.messagebox.showinfo("Warning","Error on β- parameter in GROUP %d" %(i+1) + ", PHASE %s" % (j+1) + "\nβ- takes positive values")
                    return
                check = re.findall('^[0-9]+\.[0-9]+$',str(self.betaMinusVariable[i][j].get()))
                if not check:
                    tkinter.messagebox.showinfo("Warning","Error on β- parameter in GROUP %d" %(i+1) + ", PHASE %s" % (j+1) + "\nβ- takes positive values")
                    return                 
                self.betaMinusVariableDict[i].append(self.betaMinusVariable[i][j].get())                
        
        try:
            for i in range(self.rowNo +1):                
                j = 0
                for k,v in self.similarityDict[i].items():
                    self.similarityDict[i][k] = self.similarityVariable[i][j].get()
                    check = re.findall('^0\.[0-9]+$|^1\.0+$|^1$',str(self.similarityVariable[i][j].get()))
                    if not check:
                        tkinter.messagebox.showinfo("Warning","Error on COMMON ELEMENTS parameter in GROUP %d" %(i+1) + "\nCommon Elements between pairs of CSs take values from 0-1")
                        return 
                    j+=1                    
                eachPhase, noPhases,stimuli,noStimuli = getPhases(self.groups[i])
                fractionList = np.zeros(len(stimuli))
                for k,v in self.similarityDict[i].items():
                    for l in range(len(k)):
                        fractionList[stimuli.index(k[l])] += v
                if any(fractionList>1):
                    tkinter.messagebox.showinfo("Warning","The fraction of common elements for each CS cannot exceed 1.0")
                    self.setParamsCheck.deselect()
                    return               
        except:
            pass
        
        # Check Set Parameters box
        self.setParamsCheck.select()
        self.runCheck.deselect()


    # Function linked to pressing the Run button           
    def run(self):
        # Error exception if Initialise and Set button not pressed first        
        if self.setParamsState.get() == 1 and self.initialiseState.get() == 1:
            pass
        else: 
            tkinter.messagebox.showinfo("Warning","Please INITIALISE GROUPS and SET PARAMETERS before RUN")
            return
        
        # Run trainHEM function to find CR, Legend, stimuli, plot colour
        self.groupAveCR_R,self.groupAveCR_V,self.groupLegend_R,self.groupLegend_V,\
          groupStimuli, self.groupPlotColor_R,self.groupPlotColor_V   =    trainHEM(self.groups,
                                                                          self.randomTrialsValue,
                                                                          self.noElemsVariableList,
                                                                          self.gainVariableList,
                                                                          self.densityVariableList,
                                                                          self.groupRandomise,
                                                                          self.salienceVariableDict,
                                                                          self.lambdaPlusVariableDict,
                                                                          self.lambdaMinusVariableDict,
                                                                          self.betaPlusVariableDict,
                                                                          self.betaMinusVariableDict,
                                                                          self.similarityDict,
                                                                          self.capacityVariableList,
                                                                          self.runColor %2)
        self.runColor +=1
        self.runCheck.select()

                                             
    # Function linked to pressing the Display Figures button               
    def display(self):
        try:
            self.groups
        except AttributeError:
            return
        
        subtitlePhasePerGroup = {}
        for i in range(len(self.groups)):
            subtitlePhasePerGroup[i] = {}
            eachPhase, noPhases,stimuli,noStimuli = getPhases(self.groups[i])
            for j in range(len(eachPhase)):
                subtitlePhasePerGroup[i][j] = eachPhase[j]
                
        self.windows = []
        data_R = {}
        data_V = {}
        subtitle = {}
        groupName = {}
        color_R = {}
        color_V = {}
        
        # Exception for only one 0 group
        if not self.groupAveCR_R:
            return

        if self.rPlotsVar.get() == 1:
            for i in range(len(self.groupAveCR_R[0])):  # Each Phase
                data_R[i] = {}
                subtitlePhase = {}
                color_R[i] = {}
                for j in range(len(self.groupAveCR_R)): # Each Group
                    groupName[j] = self.groupVariable[j].get()
                    data_R[i][j] = self.groupAveCR_R[j][i]
                    color_R[i][j] = self.groupPlotColor_R[j][i]
                    subtitlePhase[j] = subtitlePhasePerGroup[j][i]
                for j in range(len(subtitlePhase)):
                    if j == 0:
                        subtitle[i] = '1-' + groupName[j] + ": " + subtitlePhase[j] + "\n"
                    elif j>0 and j<len(subtitlePhase):
                        subtitle[i] += '%d-' %(j+1) + groupName[j] + ": " + subtitlePhase[j] + "\n"
                    else:
                        subtitle[i] += '%d-' %(j+1) + groupName[j] + ": " + subtitlePhase[j]
                title = 'Response (R) Plot\nPhase %d \n' % (i+1) + subtitle[i]
                yTitle = "Response (R)"
                self.windows.append(Plotwindow(self.master,data_R[i], self.groupLegend_R,color_R[i],i,title,groupName,yTitle,len(self.groups)))

        if self.vPlotsVar.get() == 1:
            for i in range(len(self.groupAveCR_V[0])):  # Each Phase
                data_V[i] = {}
                subtitlePhase = {}
                color_V[i] = {}
                for j in range(len(self.groupAveCR_V)): # Each Group
                    groupName[j] = self.groupVariable[j].get()
                    data_V[i][j] = self.groupAveCR_V[j][i]
                    color_V[i][j] = self.groupPlotColor_V[j][i]
                    subtitlePhase[j] = subtitlePhasePerGroup[j][i]
                for j in range(len(subtitlePhase)):
                    if j == 0:
                        subtitle[i] = '1-' + groupName[j] + ": " + subtitlePhase[j] + "\n"
                    elif j>0 and j<len(subtitlePhase):
                        subtitle[i] += '%d-' %(j+1) + groupName[j] + ": " + subtitlePhase[j] + "\n"
                    else:
                        subtitle[i] += '%d-' %(j+1) + groupName[j] + ": " + subtitlePhase[j]
                title = 'Associative Strength (V)\nPhase %d \n' % (i+1) + subtitle[i]
                yTitle = "Associative Strength (V)"
                self.windows.append(Plotwindow(self.master,data_V[i], self.groupLegend_V,color_V[i],i,title,groupName,yTitle,len(self.groups)))


    # Function linked to Save Experiment option in the File menu                              
    def file_save(self):
        # Error exception if Initialise not pressed first therefore unable to save
        try:
            self.noStimuliperGroup
        except AttributeError:
            tkinter.messagebox.showinfo("Warning","Please INITIALISE GROUPS before SAVING experiment")
            return 
        
        # default extension for the file is .hrs
        mask = [("Harris files","*.hrs")]        
        fout = filedialog.asksaveasfile(mode='w', defaultextension=".hrs",filetypes=mask)
        
        if not fout:
            return

        fout.write(str(self.rowNo) + " " + str(self.colNo) + "\n")
        
        for i in range(self.rowNo +1):
            for j in range(self.colNo +1):
                if j < (self.colNo):
                    fout.write(self.entryVariable[i][j].get() + " ")
                else:
                    fout.write(self.entryVariable[i][j].get() + "\n")
        
        for i in range(self.rowNo +1):
            if i < (self.rowNo):
                fout.write(str("'" + self.groupVariable[i].get()) + "'" + " ")
            else:
                fout.write("'" + str(self.groupVariable[i].get()) + "'" + "\n") 
                
        for i in range(self.rowNo +1):
            for j in range(self.colNo +1):
                if j < (self.colNo):
                    fout.write(str(self.randomVariable[i][j].get()) + " ")
                else:
                    fout.write(str(self.randomVariable[i][j].get()) + "\n") 
                
        for i in range(self.rowNo +1):
            if i < (self.rowNo):
                fout.write(str(self.noElemsVariable[i].get()) + " ")
            else:
                fout.write(str(self.noElemsVariable[i].get()) + "\n")
                
        for i in range(self.rowNo +1):
            if i < (self.rowNo):
                fout.write(str(self.gainVariable[i].get()) + " ")
            else:
                fout.write(str(self.gainVariable[i].get()) + "\n")  
                
        for i in range(self.rowNo +1):
            if i < (self.rowNo):
                fout.write(str(self.densityVariable[i].get()) + " ")
            else:
                fout.write(str(self.densityVariable[i].get()) + "\n") 
                
        for i in range(self.rowNo +1):
            if i < (self.rowNo):
                fout.write(str(self.capacityVariable[i].get()) + " ")
            else:
                fout.write(str(self.capacityVariable[i].get()) + "\n")  
                          
        for i in range(self.rowNo +1):
            for j in range(self.noStimuliperGroup[i]):
                if j < (self.noStimuliperGroup[i] -1):
                    fout.write(str(self.salienceVariable[i][j].get()) + " ")
                else:
                    fout.write(str(self.salienceVariable[i][j].get()) + "\n") 
                    
        for i in range(self.rowNo +1):
            for j in range(len(self.similarityDict[i])):
                if j < (len(self.similarityDict[i]) -1):
                    fout.write(str(self.similarityVariable[i][j].get()) + " ")
                else:
                    fout.write(str(self.similarityVariable[i][j].get()) + "\n")
                    
        for i in range(self.rowNo +1):
            for j in range(self.colNo +1):
                if j < (self.colNo):
                    fout.write(str(self.lambdaPlusVariable[i][j].get()) + " ")
                else:
                    fout.write(str(self.lambdaPlusVariable[i][j].get()) + "\n") 
        
        for i in range(self.rowNo +1):
            for j in range(self.colNo +1):
                if j < (self.colNo):
                    fout.write(str(self.lambdaMinusVariable[i][j].get()) + " ")
                else:
                    fout.write(str(self.lambdaMinusVariable[i][j].get()) + "\n")
                    
        for i in range(self.rowNo +1):
            for j in range(self.colNo +1):
                if j < (self.colNo):
                    fout.write(str(self.betaPlusVariable[i][j].get()) + " ")
                else:
                    fout.write(str(self.betaPlusVariable[i][j].get()) + "\n") 

        for i in range(self.rowNo +1):
            for j in range(self.colNo +1):
                if j < (self.colNo):
                    fout.write(str(self.betaMinusVariable[i][j].get()) + " ")
                else:
                    fout.write(str(self.betaMinusVariable[i][j].get()) + "\n") 
            
        fout.close()       

    # Function linked to Open Experiment option in the File menu                                      
    def file_open(self):
        initial_dir = "C:\Temp"
        mask = [("Harris files","*.hrs")]       
        fin = filedialog.askopenfile(initialdir=initial_dir, filetypes=mask, mode='r')
        
        # Return nothing if cancel opening
        if not fin:
            return
        
        self.newExperiment()
        
        rowsCols = re.split('\s+',fin.readline())
        del rowsCols[-1]
        rows = int(rowsCols[0])
        cols = int(rowsCols[1])
                  
        # Load all groups and phases
        loadGroups = []
        for i in range(rows + 1):
            loadGroups.append((fin.readline()).strip('\n'))        
        # Split on spaces and create list for each group
        for i in range(len(loadGroups)):
            loadGroups[i] =  re.split('\s+', loadGroups[i])         
        #Add groups and phases before adding text
        for i in range(rows):
            self.addGroups()
        for i in range(cols):
            self.addPhases()            
        # Add text
        for i in range(rows +1):
            for j in range(cols +1):
                self.entry[i][j].insert(0,loadGroups[i][j])
        
        loadGroupNames =(fin.readline()).strip('\n')
        loadGroupNames = re.split('\'', loadGroupNames) 
        loadGroupNames[:] = [item for item in loadGroupNames if item != ''] #Remove blank and empty items in list
        loadGroupNames[:] = [item for item in loadGroupNames if item != ' ']
        for i in range(rows +1):
            self.group[i].delete(0,'end')
            self.group[i].insert(0,loadGroupNames[i]) 
              
        loadRandom = []
        for i in range(rows + 1):
            loadRandom.append((fin.readline()).strip('\n'))            
        for i in range(len(loadGroups)):
            loadRandom[i] =  re.split('\s+', loadRandom[i])             
        for i in range(rows +1):
            for j in range(cols +1):
                if int(loadRandom[i][j]) == 1:
                    self.check[i][j].select()
                
        self.initiate()
                
        loadNoElems = (fin.readline()).strip('\n')           
        loadNoElems = re.split('\s+', loadNoElems)             
        for i in range(rows +1):
            self.noElems[i].delete(0,'end')
            self.noElems[i].insert(0,loadNoElems[i])
            
        loadGain = (fin.readline()).strip('\n')           
        loadGain = re.split('\s+', loadGain)             
        for i in range(rows +1):
            self.gain[i].delete(0,'end')
            self.gain[i].insert(0,loadGain[i])
            
        loadDensity = (fin.readline()).strip('\n')           
        loadDensity = re.split('\s+', loadDensity)             
        for i in range(rows +1):
            self.density[i].delete(0,'end')
            self.density[i].insert(0,loadDensity[i])
            
        loadCapacity = (fin.readline()).strip('\n')           
        loadCapacity = re.split('\s+', loadCapacity)             
        for i in range(rows +1):
            self.capacity[i].delete(0,'end')
            self.capacity[i].insert(0,loadCapacity[i])
            
        loadSalience = []
        for i in range(rows + 1):
            loadSalience.append((fin.readline()).strip('\n'))        
        # Split on spaces and create list for each group
        for i in range(len(loadGroups)):
            loadSalience[i] =  re.split('\s+', loadSalience[i])         
        # Add text
        for i in range(rows +1):
            for j in range(self.noStimuliperGroup[i]):
                self.salience[i][j].delete(0,'end')               
                self.salience[i][j].insert(0,loadSalience[i][j])
        
        loadSimilarity = []
        for i in range(rows +1):
            if self.nonZeroSimilarityGroups[i] == 1:
                loadSimilarity.append((fin.readline()).strip('\n'))
        for i in range(int(sum(self.nonZeroSimilarityGroups))):
            loadSimilarity[i] =  re.split('\s+', loadSimilarity[i]) 
        for i in range(rows +1):
            if self.nonZeroSimilarityGroups[i] == 1:
                for j in range(len(self.similarityDict[i])):
                    self.similarity[i][j].delete(0,'end')               
                    self.similarity[i][j].insert(0,loadSimilarity[i][j])
            
        loadLambdaPlus = []
        for i in range(rows + 1):
            loadLambdaPlus.append((fin.readline()).strip('\n'))        
        for i in range(len(loadGroups)):            
            loadLambdaPlus[i] = re.split('\s+', loadLambdaPlus[i])             
        for i in range(rows +1):
            for j in range(cols +1):
                self.lambdaPlus[i][j].delete(0,'end')
                self.lambdaPlus[i][j].insert(0,loadLambdaPlus[i][j])
                
        loadLambdaMinus = []
        for i in range(rows + 1):
            loadLambdaMinus.append((fin.readline()).strip('\n'))        
        for i in range(len(loadGroups)):            
            loadLambdaMinus[i] = re.split('\s+', loadLambdaMinus[i])             
        for i in range(rows +1):
            for j in range(cols +1):
                self.lambdaMinus[i][j].delete(0,'end')
                self.lambdaMinus[i][j].insert(0,loadLambdaMinus[i][j])
 
        loadBetaPlus = []
        for i in range(rows + 1):
            loadBetaPlus.append((fin.readline()).strip('\n'))        
        for i in range(len(loadGroups)):            
            loadBetaPlus[i] = re.split('\s+', loadBetaPlus[i])             
        for i in range(rows +1):
            for j in range(cols +1):
                self.betaPlus[i][j].delete(0,'end')
                self.betaPlus[i][j].insert(0,loadBetaPlus[i][j])               
        
        loadBetaMinus = []
        for i in range(rows + 1):
            loadBetaMinus.append((fin.readline()).strip('\n'))        
        for i in range(len(loadGroups)):            
            loadBetaMinus[i] = re.split('\s+', loadBetaMinus[i])             
        for i in range(rows +1):
            for j in range(cols +1):
                self.betaMinus[i][j].delete(0,'end')
                self.betaMinus[i][j].insert(0,loadBetaMinus[i][j])
        
                
    # Function lined to Export to Excel in File menu                
    def file_export(self):
        # Error exception if Run not pressed before trying to export
        try:
            self.groupAveCR_R
        except AttributeError:
            tkinter.messagebox.showinfo("Warning","Please RUN experiment before EXPORT")
            return 
        
        mask = [("Excel files","*.xlsx")]        
        workbookName = filedialog.asksaveasfile(mode='w', defaultextension=".xlsx",filetypes=mask) 
        
        # If cancel dialog box, simply returns as to avoid error
        if not workbookName:
            return
        
        workbook = xlsxwriter.Workbook(workbookName.name)        
        boldAndBorder = workbook.add_format({'bold': True,'border': True})
        border = workbook.add_format({'border': True})
        boldLarge = workbook.add_format({'bold': True,'underline':True})
        
        for group in range(len(self.groupAveCR_R)):            
            rowNo = 0
            worksheet = workbook.add_worksheet(self.groupVariable[group].get())
            
            for j in range(self.colNo +1):
                if j ==0:
                    groupPres = self.entryVariable[group][j].get()
                else:
                    groupPres = groupPres + "|" + self.entryVariable[group][j].get()
            worksheet.write(rowNo, 0, self.groupVariable[group].get() + ": " + groupPres,boldLarge)
            rowNo += 2
            
            worksheet.write(rowNo, 0, "CS Alpha",boldAndBorder)
            
            rowNo+=1
            for i in range(len(self.stimuliDict[group])):
                worksheet.write(rowNo, 0, self.stimuliDict[group][i],boldAndBorder)
                worksheet.write(rowNo, 1, self.salienceVariableDict[group][i],border)
                rowNo+=1
            
            rowNo +=1    
            worksheet.write(rowNo, 0, "Elements",boldAndBorder)
            worksheet.write(rowNo +1, 0, self.noElemsVariable[group].get(),border)
            worksheet.write(rowNo, 1, "Gain",boldAndBorder)
            worksheet.write(rowNo +1, 1, self.gainVariable[group].get(),border)
            worksheet.write(rowNo, 2, "Density",boldAndBorder)
            worksheet.write(rowNo +1, 2, self.densityVariable[group].get(),border)
            worksheet.write(rowNo, 3, "Capacity",boldAndBorder)
            worksheet.write(rowNo +1, 3, self.capacityVariable[group].get(),border)
            
            rowNo +=3
            worksheet.write(rowNo, 0, " ",boldAndBorder)
            worksheet.write(rowNo+1, 0, "λ+",boldAndBorder)
            for phase in range(len(self.groupAveCR_R[0])):
                worksheet.write(rowNo, phase +1, "Phase %d" % (phase +1), boldAndBorder)
                worksheet.write(rowNo +1, phase +1, self.lambdaPlusVariableDict[group][phase], border)                

            rowNo +=3
            worksheet.write(rowNo, 0, " ",boldAndBorder)
            worksheet.write(rowNo+1, 0, "λ-",boldAndBorder)
            for phase in range(len(self.groupAveCR_R[0])):
                worksheet.write(rowNo, phase +1, "Phase %d" % (phase +1), boldAndBorder)
                worksheet.write(rowNo +1, phase +1, self.lambdaMinusVariableDict[group][phase], border) 
            
            rowNo +=3
            worksheet.write(rowNo, 0, " ",boldAndBorder)
            worksheet.write(rowNo+1, 0, "β+",boldAndBorder)
            for phase in range(len(self.groupAveCR_R[0])):
                worksheet.write(rowNo, phase +1, "Phase %d" % (phase +1), boldAndBorder)
                worksheet.write(rowNo +1, phase +1, self.betaPlusVariableDict[group][phase], border)
            
            rowNo +=3
            worksheet.write(rowNo, 0, " ",boldAndBorder)
            worksheet.write(rowNo+1, 0, "β-",boldAndBorder)
            for phase in range(len(self.groupAveCR_R[0])):
                worksheet.write(rowNo, phase +1, "Phase %d" % (phase +1), boldAndBorder)
                worksheet.write(rowNo +1, phase +1, self.betaMinusVariableDict[group][phase], border)
                
            rowNo +=3
            worksheet.write(rowNo, 0, " ",boldAndBorder)
            worksheet.write(rowNo+1, 0, "Common Elements",boldAndBorder)
            j=0
            for k,v in self.similarityDict[group].items():
                worksheet.write(rowNo, j+1, ''.join(k),boldAndBorder)
                worksheet.write(rowNo+1, j+1,v,border)
                j +=1
                
            rowNo +=4
            worksheet.write(rowNo, 0, "Response (R)",boldLarge)
            
            rowNo +=2
            rowNoTrials = rowNo              
            for phase in range(len(self.groupAveCR_R[0])):    
                worksheet.write(rowNoTrials, 0, "Phase %d" %(phase+1),boldAndBorder)

                legend = self.groupLegend_R[group][phase]
                data_R = []
                for pres in range(len(self.groupAveCR_R[group][phase])):
                    data_R.append(list(self.groupAveCR_R[group][phase][pres]))
                    
                
                for row,array in enumerate(data_R):
                    worksheet.write(rowNo+1, 0, legend[row],boldAndBorder)
                    for col, value in enumerate(array):
                        worksheet.write(rowNo+1, col+1, round(value,3),border)
                        worksheet.write(rowNoTrials, col+1, "Trial %d" % (col+1),boldAndBorder)
                    rowNo +=1
                    
                rowNoTrials = rowNo +2
                rowNo = rowNo +2
                
            rowNo +=1
            worksheet.write(rowNo, 0, "Associative Strength (V)",boldLarge)
            
            rowNo +=2            
            rowNoTrials = rowNo            
            for phase in range(len(self.groupAveCR_V[0])):    
                worksheet.write(rowNoTrials, 0, "Phase %d" %(phase+1),boldAndBorder)

                legend = self.groupLegend_V[group][phase]
                data_V = []
                for pres in range(len(self.groupAveCR_V[group][phase])):
                    data_V.append(list(self.groupAveCR_V[group][phase][pres]))
                    
                
                for row,array in enumerate(data_V):
                    worksheet.write(rowNo+1, 0, legend[row],boldAndBorder)
                    for col, value in enumerate(array):
                        worksheet.write(rowNo+1, col+1, round(value,3),border)
                        worksheet.write(rowNoTrials, col+1, "Trial %d" % (col+1),boldAndBorder)
                    rowNo +=1
                    
                rowNoTrials = rowNo +2
                rowNo = rowNo +2
                       
        workbook.close()        


    # Function linked to Number of Random Trial Combinations in Settings menu
    def randomTrials(self):
        
        if self.onRandomTrials == 0:
            self.onRandomTrials = 1
            buttonFont = ("Arial", 10, 'bold')
            self.randomWin = tk.Toplevel(self.master)
            self.randomWin.resizable(0,0)        
            randomTrialsFrame = tk.Frame(self.randomWin)
            randomTrialsFrame.pack()
            randomTrialsLabel = tk.Label(master=randomTrialsFrame,text='Enter number of combinations:')
            randomTrialsLabel.grid(row=0,column=0,sticky="nsew", padx=10, pady=10,columnspan=2)            
            randomTrials = tk.Entry(randomTrialsFrame,textvariable=self.randomTrialsVariable)
            randomTrials.grid(row=1,column=0,sticky="nsew", padx=10, pady=5,columnspan=2)        
            okButton = tk.Button(randomTrialsFrame,text='OK',font=buttonFont,height=1,width=5,command=self.okRandomTrials)
            okButton.grid(row=2,column=0,padx=10, pady=10)         
            cancelButton = tk.Button(randomTrialsFrame,text='Cancel',font=buttonFont,height=1,width=5,command=self.cancelRandomTrials)
            cancelButton.grid(row=2,column=1,padx=10, pady=10)
        
    # OK Button for randomTrials box
    def okRandomTrials(self):
        self.randomTrialsVariable = tk.IntVar(value=self.randomTrialsVariable.get())
        self.randomTrialsValue = self.randomTrialsVariable.get()
        self.randomWin.destroy()
        self.onRandomTrials = 0          
    # Cancel Button for randomTrials box
    def cancelRandomTrials(self):
        self.randomWin.destroy() 
        self.randomTrialsVariable = tk.IntVar(value=self.randomTrialsValue)
        self.onRandomTrials = 0          

    # Function to add groups in Groups Table
    def addGroups(self):
        self.rowNo = self.rowNo + 1
        groupNo = self.rowNo + 1
        self.groupVariable[self.rowNo] = tk.StringVar(value="Group %d" % groupNo)
        self.group[self.rowNo] = tk.Entry(master=self.allGroupFrame,textvariable=self.groupVariable[self.rowNo])
        self.group[self.rowNo].grid(row=self.rowNo+2,column=0,sticky="nsew", padx=1, pady=1)        
        self.entry[self.rowNo] = {}
        self.check[self.rowNo] = {}
        self.entryVariable[self.rowNo] = {}
        self.randomVariable[self.rowNo] = {}        
        for i in range(self.colNo +1):            
            self.entryVariable[self.rowNo][i] = tk.StringVar()
            self.entryVariable[self.rowNo][i].trace('w',self.text_changed)
            self.entry[self.rowNo][i] = tk.Entry(master=self.allGroupFrame,textvariable=self.entryVariable[self.rowNo][i],width=30)
            self.entry[self.rowNo][i].grid(row=self.rowNo+2,column=2*i+1,sticky="nsew", padx=1, pady=1)          
            self.randomVariable[self.rowNo][i] = tk.IntVar()
            self.check[self.rowNo][i] = tk.Checkbutton(master=self.allGroupFrame,variable=self.randomVariable[self.rowNo][i],command=self.groupInitialiseOff)
            self.check[self.rowNo][i].grid(row=self.rowNo+2,column=2*i+2,sticky="nsew",padx=1, pady=1)
            
        self.salienceVariable[self.rowNo] = {}
        self.lambdaPlusVariable[self.rowNo] = {}
        self.lambdaMinusVariable[self.rowNo] = {}
        self.betaPlusVariable[self.rowNo] = {}
        self.betaMinusVariable[self.rowNo] = {}
        self.similarityVariable[self.rowNo] = {}
        
        self.initialiseCheck.deselect()
        self.setParamsCheck.deselect()
        self.runCheck.deselect()

    # Function to remove groups in Groups Table
    def minusGroups(self):
        if self.rowNo > 0:            
            self.group[self.rowNo].destroy()
            for i in range(self.colNo +1):
                self.entry[self.rowNo][i].destroy()
                self.check[self.rowNo][i].destroy()
           
            self.salienceVariable.pop(self.rowNo)
            self.lambdaPlusVariable.pop(self.rowNo)
            self.lambdaMinusVariable.pop(self.rowNo)
            self.betaPlusVariable.pop(self.rowNo)
            self.betaMinusVariable.pop(self.rowNo)    
            self.similarityVariable.pop(self.rowNo)
                                        
            self.rowNo = self.rowNo - 1

        self.initialiseCheck.deselect()
        self.setParamsCheck.deselect()            
        self.runCheck.deselect()

    # Function to add phases in Groups Table   
    def addPhases(self):
        self.colNo = self.colNo + 1                
        self.phaseLabel[self.colNo] = tk.Label(master=self.allGroupFrame,text='Phase %d' % (self.colNo +1),font=self.groupTableHeadingsFont)
        self.phaseLabel[self.colNo].grid(row=1,column=2*self.colNo+1,sticky="nsew", padx=1, pady=1) 
        self.randomLabel[self.colNo] = tk.Label(master=self.allGroupFrame,text='Rand %d' % (self.colNo +1),font=self.groupTableHeadingsFont)
        self.randomLabel[self.colNo].grid(row=1,column=2*self.colNo+2,sticky="nsew", padx=1, pady=1)            
        for i in range(self.rowNo +1):
            self.entryVariable[i][self.colNo] = tk.StringVar()
            self.entryVariable[i][self.colNo].trace('w',self.text_changed)
            self.entry[i][self.colNo] = tk.Entry(master=self.allGroupFrame,textvariable=self.entryVariable[i][self.colNo],width=30)
            self.entry[i][self.colNo].grid(row=i+2,column=2*self.colNo+1,sticky="nsew", padx=1, pady=1)            
            self.randomVariable[i][self.colNo] = tk.IntVar() 
            self.check[i][self.colNo] = tk.Checkbutton(master=self.allGroupFrame,variable=self.randomVariable[i][self.colNo],command=self.groupInitialiseOff)
            self.check[i][self.colNo].grid(row=i+2,column=2*self.colNo+2,sticky="nsew",padx=1, pady=1)

        self.initialiseCheck.deselect()
        self.setParamsCheck.deselect()
        self.runCheck.deselect()

    # Function to remove phases in Groups Table               
    def minusPhases(self):
        if self.colNo > 0:
            self.phaseLabel[self.colNo].destroy()
            self.randomLabel[self.colNo].destroy()                        
            for i in range(self.rowNo +1):
                self.entry[i][self.colNo].destroy()
                self.check[i][self.colNo].destroy()
            self.colNo = self.colNo - 1   

        self.initialiseCheck.deselect()
        self.setParamsCheck.deselect()
        self.runCheck.deselect()
        

    # Add Scrollbars if widgets exceed the space allocated in Frame        
    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.groupCanvas.configure(scrollregion=self.groupCanvas.bbox("all"))  

    def onParamFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.paramCanvas.configure(scrollregion=self.paramCanvas.bbox("all"))
 
    def onSalienceFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.salienceCanvas.configure(scrollregion=self.salienceCanvas.bbox("all"))   
        
    def onLambdaPlusFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.lambdaPlusCanvas.configure(scrollregion=self.lambdaPlusCanvas.bbox("all"))  

    def onlambdaMinusFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.lambdaMinusCanvas.configure(scrollregion=self.lambdaMinusCanvas.bbox("all"))          

    def onbetaPlusFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.betaPlusCanvas.configure(scrollregion=self.betaPlusCanvas.bbox("all"))  

    def onbetaMinusFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.betaMinusCanvas.configure(scrollregion=self.betaMinusCanvas.bbox("all"))   

    def onCommonFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.commonCanvas.configure(scrollregion=self.commonCanvas.bbox("all")) 


    # a scrollbar that hides itself if it's not needed
    class AutoScrollbar(tk.Scrollbar):
        def set(self, lo, hi):
            if float(lo) <= 0.0 and float(hi) >= 1.0:
                # grid_remove is currently missing from Tkinter!
                self.tk.call("grid", "remove", self)
            else:
                self.grid()
            tk.Scrollbar.set(self, lo, hi)
        
    def groupInitialiseOff(self):
        self.initialiseCheck.deselect()
        self.setParamsCheck.deselect()
        self.runCheck.deselect()
        
    def text_changed(self,*args):
        self.initialiseCheck.deselect()
        self.setParamsCheck.deselect()
        self.runCheck.deselect()

    def text_changed_params(self,*args):
        self.setParamsCheck.deselect() 
        self.runCheck.deselect()


# Plot R and V values. Each phase uses new window. 
class Plotwindow():
    def __init__(self, master, data, groupLegend,color,p,title,groupName,yTitle,noGroups):
        t = tk.Toplevel(master)
        t.columnconfigure(0, weight=1)
        t.rowconfigure(0, weight=1) 
        
        # Frame for the plot
        plotFrame = tk.Frame(t)
        plotFrame.grid(row=0,column=0,sticky = 'NESW')
        
        # Size of window
        f = plt.Figure(figsize=(10,6), dpi=100)
        self.ax = f.add_subplot(111)
        
        # Set box position, height and width. Fontsize for x- and y-ticks
        box = self.ax.get_position()
        self.ax.set_position([box.x0, box.y0,box.width*.65, box.height*.98**noGroups])
        self.ax.xaxis.set_tick_params(labelsize=10)
        self.ax.yaxis.set_tick_params(labelsize=10)
#        self.ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        
        # Configure plot to match the shape of the window
        self.ax.format_coord = lambda x, y: ''
        plotFrame.grid_columnconfigure(0, weight=1)
        plotFrame.grid_rowconfigure(1, weight=1)

        # Add plot to tkinter
        self.canvas = FigureCanvasTkAgg(f,master=plotFrame)
        self.canvas.show()
        self.canvas.get_tk_widget().grid(row=1,column=0,sticky = 'NESW')
        self.canvas.mpl_connect('pick_event', self.onpick) # Add functionality to toggle legend
        
        # Add toolbar at top of plot
        navigationFrame = tk.Frame(plotFrame)
        navigationFrame.grid(row=0,column=0)        
        toolbar = NavigationToolbar2TkAgg(self.canvas, navigationFrame )
        toolbar.update()        
        
        # Dictionary of all plots from all groups
        plotDict = {}   
        n = 0 
        for i in range(len(data)):
            for k,v in data[i].items():
                plotDict[n] = data[i][k]
                n +=1 
        
        # Legend from all groups                            
        legend = {}
        n = 0
        for i in range(len(groupLegend)):
            for j in range(len(groupLegend[i][p])):
                legend[n] = "%d" % (i+1) + "-" + groupName[i] + ": " +  groupLegend[i][p][j]
                n +=1
        
        # List of number of plots per group. This is used to change markers and linestyle                        
        idx = []
        n=0
        for i in range(len(color)):
            idx.append(n + len(color[i]))
            n = n + len(color[i])
        
        # Color for each plot line
        plotColor = {}
        n=0
        for i in range(len(color)):
            for j in range(len(color[i])):
                plotColor[n] = color[i][j]
                n +=1        
        
        # Marker types, linestyle and fillstyle of markers
        marker = ['s','v','o','^','D','h','*']
        style = ['-','--','-.','-.','--','-']
        fillstyle = ['none','full','left','right','bottom','top']
        
        # PLOT
        lines = [0] * len(plotDict)
        n = 0 # counts the number of plots. This is used to change the group
        m = 0 # counts the number of plots. This is used to change the markers
        group = 0 # monitors the groups
        if not lines:
            return
        # Loop over plotDict to plot every line
        for (k,v),i in zip(plotDict.items(),range(len(plotDict))):
            if n == idx[group]:
                group += 1
                m=0
            X = range(1,len(v)+1) # Start plot at trial 1
            # Plot for a single line
            lines[i], = self.ax.plot(X,v,color=plotColor[i],label=legend[i],marker=marker[m%7],
                         markersize=6.0,linestyle=style[group%6],fillstyle=fillstyle[group%6],zorder=1)            
            n +=1
            m +=1
        
        # Title, x-label, y-label, plot background style, xlimit of x-axis=0
        self.ax.set_title(title,fontdict={'fontsize':'8','fontweight' : 'bold'})
        self.ax.set_xlabel('Number of Trials')
        self.ax.set_ylabel(yTitle)
        self.ax.grid(True,linestyle='dashed',linewidth=0.25)
        self.ax.set_xlim(left=0)
        
        # Legend style and position. Make legend draggable
        leg = self.ax.legend(loc='right', bbox_to_anchor=(1.7,0.9*.98**noGroups),
                             fancybox=True, shadow=True, ncol=2,prop={'size': 9})
        if leg:
            leg.draggable()
            
        # Set up toggable legend
        self.lined = dict()
        for legline, origline in zip(leg.get_lines(), lines):
            legline.set_picker(5)  # 5 pts tolerance
            self.lined[legline] = origline
    
    # Toggle legend
    # credit to User: https://stackoverflow.com/users/4124317/importanceofbeingernest
    # see https://stackoverflow.com/q/46837752/8770423
    #     https://stackoverflow.com/q/47833071/8770423
    #     https://matplotlib.org/examples/event_handling/legend_picking.html
    def onpick(self, event):
        if event.artist in self.lined.keys():
            # on the pick event, find the orig line corresponding to the
            # legend proxy line, and toggle the visibility
            legline = event.artist
            origline = self.lined[legline]
            vis = not origline.get_visible()
            origline.set_visible(vis)
            # Change the alpha on the line in the legend so we can see what lines
            # have been toggled
            if vis:
                legline.set_alpha(1.0)
            else:
                legline.set_alpha(0.0)
            self.canvas.draw()

# Splash screen
# Credit to http://code.activestate.com/recipes/534124-elegant-tkinter-splash-screen/            
class SplashScreen( object ):
   def __init__( self, tkRoot, imageFilename, minSplashTime=0 ):
      self._root              = tkRoot
      self._image             = tk.PhotoImage( file='Harris-IB-splash.png' )
      self._splash            = None
      self._minSplashTime     = time.time() + minSplashTime
      
   def __enter__( self ):
      # Remove the app window from the display
      self._root.withdraw( )
      
      # Calculate the geometry to center the splash image
      scrnWt = self._root.winfo_screenwidth( )
      scrnHt = self._root.winfo_screenheight( )
      
      imgWt = self._image.width()
      imgHt = self._image.height()
      
      imgXPos = (scrnWt / 2) - (imgWt / 2)
      imgYPos = (scrnHt / 2) - (imgHt / 2)

      # Create the splash screen      
      self._splash = tk.Toplevel()
      self._splash.overrideredirect(1)
      self._splash.geometry( '+%d+%d' % (imgXPos, imgYPos) )
      tk.Label( self._splash, image=self._image, cursor='watch' ).pack( )

      # Force Tk to draw the splash screen outside of mainloop()
      self._splash.update( )
   
   def __exit__( self, exc_type, exc_value, traceback ):
      # Make sure the minimum splash time has elapsed
      timeNow = time.time()
      if timeNow < self._minSplashTime:
         time.sleep( self._minSplashTime - timeNow )
      
      # Destroy the splash window
      self._splash.destroy( )
      
      # Display the application window
      self._root.deiconify( )
  
    
if __name__ == "__main__":
    root = tk.Tk()
    
    with SplashScreen( root, 'splashImage.jpg', 1.0):
        root.title("HEMFULL SIMULATOR ver 1.0")
        root.tk.call('wm', 'iconbitmap', root._w, 'harrisib_icon.ico')
        app = App(root)
    root.mainloop()