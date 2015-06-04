from dream.plugins.Enumeration import Enumeration
from pprint import pformat
from copy import copy, deepcopy
import json
import time
import random
import operator
import xmlrpclib
import signal
from multiprocessing import Pool

# # run an ant in a subrocess. Can be parrallelized.
# def runAntInSubProcess(ant):
#   ant['result'] = plugin.ExecutionPlugin.runOneScenario(ant['input'])['result']
#   return ant

# enumeration in order to search for the optimal threshold
class CapacityStationsEnumeration(Enumeration):
    def calculateScenarioScore(self, scenario):
        return 1
        
    # creates the collated scenarios, i.e. the list 
    # of options collated into a dictionary for ease of referencing in ManPy
    def createScenarioList(self,data):
        scenarioList=[]
        step=data['general'].get('thresholdStep',7)
        dueDates=[]
        for project in data['input']['BOM']['productionOrders']:
            dueDates.append(project['dueDate'])
        minimum=min(dueDates)
        maximum=max(dueDates)
        thresholds=[]
        for i in range(0,int(maximum-minimum),step):
            thresholds.append(i)
        thresholds.append(int(maximum-minimum)+1)
        for threshold in thresholds:
            scenarioList.append({'key':str(threshold),'threshold':threshold})
        return scenarioList
    
    # creates the ant scenario based on what ACO randomly selected
    def createScenarioData(self,data,scenario): 
        scenarioData=deepcopy(data)
        scenarioData['graph']['node']['CSC']['dueDateThreshold']=scenario['threshold']     
        return scenarioData   
    
    # checks if the algorithm should terminate. Default is set to False so that the algorithm 
    # terminates only when all scenarios are considered
    def checkIfShouldTerminate(self,data,scenarioList): 
        return False