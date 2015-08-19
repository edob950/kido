from copy import copy
import json
import time
import random
import operator
import datetime

from dream.plugins import plugin

class BatchesWIPShort(plugin.InputPreparationPlugin):
    """ Input preparation 
        reads the WIP from the short format
    """

    def preprocess(self, data):
        nodes=data['graph']['node']
        WIPData=data['input'].get(self.configuration_dict['input_id'], {})
        batchCounter=0
        
        from pprint import pprint
               
        # get the number of units for a standard batch
        standardBatchUnits=0
        for node_id, node in nodes.iteritems():
            if node['_class']=='Dream.BatchSource':
                standardBatchUnits=int(node['batchNumberOfUnits']) 
            node['wip']=[]

        # remove the titles
        WIPData.pop(0)

        # group the stations that may share sub-batches
        groups=[]
        alreadyGrouped=[]
        for row in WIPData:
            # on the first empty row break
            if not row[0]:
                break
            stationId=row[0]
            if stationId in alreadyGrouped:
                continue
            
            workingBatchSize=nodes[stationId]['workingBatchSize']

            # get a list with the stations that the station might share batches with (if any)           
            sharingStations=[]
            if workingBatchSize!=standardBatchUnits:
                sharingStations=self.findSharingStations(data,stationId)
                self.checkIfDefinitionIsValid(data, WIPData, stationId, sharingStations,standardBatchUnits)
            if sharingStations:
                groups.append([stationId]+sharingStations)
                alreadyGrouped.extend(sharingStations)
            else:
                groups.append([stationId])
        
        # set the WIP for every group
        for group in groups:
            # if we have stations that may share sub-batches
            if len(group)>1:
                currentBatchId='Batch_'+str(batchCounter)+'_WIP'
                unitsToCompleteBatch=standardBatchUnits
                group.sort(key=lambda x: self.getDistanceFromSource(data, x))
                for stationId in group:
                    stationWIPData=[element for element in WIPData if element[0] == stationId][0]
                    print stationWIPData
                    awaiting=stationWIPData[1]
                    complete=stationWIPData[2]
                    if not awaiting:
                        awaiting=0
                    awaiting=int(awaiting)
                    if not complete:
                        complete=0                    
                    complete=int(complete)
                    
                    buffered=awaiting - (awaiting % workingBatchSize)
                    proceeded=complete - (complete % workingBatchSize)
                    currentCompleted=awaiting % workingBatchSize
                    print buffered,proceeded,currentCompleted
            # for stations that do not share sub-batches with others
            else:
                pass
                    
        return data
    

    
    # gets the data and a station id and returns a list with all the stations that the station may share batches
    def findSharingStations(self,data,stationId):
        nodes=data['graph']['node']
        sharingStations=[]
        current=stationId
        # find all the predecessors that may share batches
        while 1:
            previous=self.getPredecessors(data, current)[0]
            # when a decomposition is reached break
            if 'Decomposition' in nodes[previous]['_class']:
                break
            # when a station is reach add it
            if 'Machine' in nodes[previous]['_class'] or 'M3' in nodes[previous]['_class']:
                sharingStations.append(previous)
                # append also the parallel stations (this implies a symmetry)
                parallelStations=self.getParallelStations(data, previous)
                sharingStations.extend(parallelStations)
            current=previous
        current=stationId
        # find all the successors that may share batches
        while 1:
            next=self.getSuccessors(data, current)[0]
            # when a reassembly is reached break
            if 'Reassembly' in nodes[next]['_class']:
                break
            # when a station is reach add it
            if 'Machine' in nodes[next]['_class'] or 'M3' in nodes[next]['_class']:
                sharingStations.append(next)
                # append also the parallel stations (this implies a symmetry)
                parallelStations=self.getParallelStations(data, next)
                sharingStations.extend(parallelStations)
            current=next
        return sharingStations
        
    # validates the definition of WIP and throws an error message in case it is not valid, i.e. not full batches are formed
    def checkIfDefinitionIsValid(self,data,WIPData,stationId,sharingStations,standardBatchUnits):
        # find all the stations in the group. For example PackagingA may not share batches with PackagingB. 
        # but carding does share with both so the group should contain all 3 stations
        allStations=[stationId]+sharingStations
        stationsToAdd=[]
        for station in allStations:
            parallelStations=self.getParallelStations(data, station)
            for id in parallelStations:
                if id not in allStations:
                    stationsToAdd.append(id)
        allStations.extend(stationsToAdd)
        totalUnits=0
        for row in WIPData:
            if row[0] in allStations:
                if row[1]:
                    totalUnits+=int(row[1])
                if row[2]:
                    totalUnits+=int(row[2])
        assert totalUnits % standardBatchUnits == 0, 'wrong wip definition in group '+str(allStations)+'. Not full batches.'
                
    # returns how far a station is from source. Useful for sorting
    def getDistanceFromSource(self,data,stationId):
        distance=0
        nodes=data['graph']['node']
        current=stationId
        # find all the predecessors that may share batches
        while 1:
            previous=self.getPredecessors(data, current)[0]      
            if 'Source' in nodes[previous]['_class']:
                break
            distance+=1
            current=previous  
        return distance
        
        
    