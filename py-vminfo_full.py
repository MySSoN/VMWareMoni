#!/usr/bin/env python2.7

from __future__ import print_function
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vmodl, vim
from datetime import timedelta, datetime
from time import clock
from pyVim import connect
from tools import cli
from tools import pchelper
import argparse
import atexit
import getpass
import ssl
import urllib2
import time

#====================================================================================================
#=========================Settings:
#====================================================================================================
# Time Interval:
interval=5

#Host vCphere:
hostVM="HostIP or Name"

#User:
userVM="User"

#Password:
pwdVM="Password"

#Port:
portVM=int(443)

#Sender API:
url='Api To Push message'

#===== API For Sender.mobi
#Necessarily for sender.mobi :
phone1='Api phone1 number'
#If needed 2nd line for sender:
phone2='Api phone2 number'

#CPU Load alarm 1-100%
maxCPL=80

#CPU Ready alarm 1-100%
maxAver=20

#Rerun Script If needed (In seconds)
ReRun=240
#====================================================================================================
#====================================================================================================
#====================================================================================================


# No Fail SSL 
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
context.verify_mode = ssl.CERT_NONE
START = clock()

#=== How long it took for script run ======
def endit():
    end = clock()
    total = end - START
    print("Completion time: {0} seconds.".format(total))

#======BuldQuery
def BuildQuery(content, vchtime, counterId, instance, vm, interval):
    perfManager = content.perfManager
    metricId = vim.PerformanceManager.MetricId(counterId=counterId, instance=instance)
    startTime = vchtime - timedelta(minutes=(interval + 1))
    endTime = vchtime - timedelta(minutes=1)
    query = vim.PerformanceManager.QuerySpec(intervalId=20, entity=vm, metricId=[metricId], startTime=startTime,
                                             endTime=endTime)
    perfResults = perfManager.QueryPerf(querySpec=[query])
    if perfResults:
        return perfResults
    else:
        print('ERROR: Performance results empty.  TIP: Check time drift on source and vCenter server')
        print('Troubleshooting info:')
        print('vCenter/host date and time: {}'.format(vchtime))
        print('Start perf counter time   :  {}'.format(startTime))
        print('End perf counter time     :  {}'.format(endTime))
        print(query)
        exit()

#======Print VM Info
def PrintVmInfo(vm, content, vchtime, interval, perf_dict, VMN, url, phone1, phone2, maxCPL, maxAver, ):
    statInt = interval * 3  # There are 3 20s samples in each minute
    summary = vm.summary
    disk_list = []
    network_list = []

    # Convert limit and reservation values from -1 to None
    if vm.resourceConfig.cpuAllocation.limit == -1:
        vmcpulimit = "None"
    else:
        vmcpulimit = "{} Mhz".format(vm.resourceConfig.cpuAllocation.limit)

##    if vm.resourceConfig.memoryAllocation.limit == -1:
##        vmmemlimit = "None"
##    else:
##        vmmemlimit = "{} MB".format(vm.resourceConfig.cpuAllocation.limit)

    if vm.resourceConfig.cpuAllocation.reservation == 0:
        vmcpures = "None"
    else:
        vmcpures = "{} Mhz".format(vm.resourceConfig.cpuAllocation.reservation)

##    if vm.resourceConfig.memoryAllocation.reservation == 0:
##        vmmemres = "None"
##    else:
##        vmmemres = "{} MB".format(vm.resourceConfig.memoryAllocation.reservation)

##    vm_hardware = vm.config.hardware
##    for each_vm_hardware in vm_hardware.device:
##        if (each_vm_hardware.key >= 2000) and (each_vm_hardware.key < 3000):
##            disk_list.append('{} | {:.1f}GB | Thin: {} | {}'.format(each_vm_hardware.deviceInfo.label,
##                                                         each_vm_hardware.capacityInKB/1024/1024,
##                                                         each_vm_hardware.backing.thinProvisioned,
##                                                         each_vm_hardware.backing.fileName))
##        elif (each_vm_hardware.key >= 4000) and (each_vm_hardware.key < 5000):
##            network_list.append('{} | {} | {}'.format(each_vm_hardware.deviceInfo.label,
##                                                         each_vm_hardware.deviceInfo.summary,
##                                                         each_vm_hardware.macAddress))

    #CPU Ready Average
    statCpuReady = BuildQuery(content, vchtime, (StatCheck(perf_dict, 'cpu.ready.summation')), "", vm, interval)
    cpuReady = (float(sum(statCpuReady[0].value[0].value)) / statInt)

    #CPU Usage Average % - NOTE: values are type LONG so needs divided by 100 for percentage
    statCpuUsage = BuildQuery(content, vchtime, (StatCheck(perf_dict, 'cpu.usage.average')), "", vm, interval)
    cpuUsage = ((float(sum(statCpuUsage[0].value[0].value)) / statInt) / 100)

##    #Memory Active Average MB
##    statMemoryActive = BuildQuery(content, vchtime, (StatCheck(perf_dict, 'mem.active.average')), "", vm, interval)
##    memoryActive = (float(sum(statMemoryActive[0].value[0].value) / 1024) / statInt)

##    #Memory Shared
##    statMemoryShared = BuildQuery(content, vchtime, (StatCheck(perf_dict, 'mem.shared.average')), "", vm, interval)
##    memoryShared = (float(sum(statMemoryShared[0].value[0].value) / 1024) / statInt)

##    #Memory Balloon
##    statMemoryBalloon = BuildQuery(content, vchtime, (StatCheck(perf_dict, 'mem.vmmemctl.average')), "", vm, interval)
##    memoryBalloon = (float(sum(statMemoryBalloon[0].value[0].value) / 1024) / statInt)

##    #Memory Swapped
##    statMemorySwapped = BuildQuery(content, vchtime, (StatCheck(perf_dict, 'mem.swapped.average')), "", vm, interval)
##    memorySwapped = (float(sum(statMemorySwapped[0].value[0].value) / 1024) / statInt)

##    #Datastore Average IO
##    statDatastoreIoRead = BuildQuery(content, vchtime, (StatCheck(perf_dict, 'datastore.numberReadAveraged.average')), "*", vm, interval)
##    DatastoreIoRead = (float(sum(statDatastoreIoRead[0].value[0].value)) / statInt)
##    statDatastoreIoWrite = BuildQuery(content, vchtime, (StatCheck(perf_dict, 'datastore.numberWriteAveraged.average')), "*", vm, interval)
##    DatastoreIoWrite = (float(sum(statDatastoreIoWrite[0].value[0].value)) / statInt)

##    #Datastore Average Latency
##    statDatastoreLatRead = BuildQuery(content, vchtime, (StatCheck(perf_dict, 'datastore.totalReadLatency.average')), "*", vm, interval)
##    DatastoreLatRead = (float(sum(statDatastoreLatRead[0].value[0].value)) / statInt)
##    statDatastoreLatWrite = BuildQuery(content, vchtime, (StatCheck(perf_dict, 'datastore.totalWriteLatency.average')), "*", vm, interval)
##    DatastoreLatWrite = (float(sum(statDatastoreLatWrite[0].value[0].value)) / statInt)

##    #Network usage (Tx/Rx)
##    statNetworkTx = BuildQuery(content, vchtime, (StatCheck(perf_dict, 'net.transmitted.average')), "", vm, interval)
##    networkTx = (float(sum(statNetworkTx[0].value[0].value) * 8 / 1024) / statInt)
##    statNetworkRx = BuildQuery(content, vchtime, (StatCheck(perf_dict, 'net.received.average')), "", vm, interval)
##    networkRx = (float(sum(statNetworkRx[0].value[0].value) * 8 / 1024) / statInt)

#    print('===============================================\/=============================================================')
#    print('[VM] CPU Ready: Average {:.1f} %, Maximum {:.1f} %'.format((cpuReady / 20000 * 100), ((float(max(statCpuReady[0].value[0].value)) / 20000 * 100))))
#    print('[VM] CPU (%)  : {:.0f} %'.format(cpuUsage))
#    print('===============================================\/=============================================================')

    cpuload='{:.0f}'.format(cpuUsage)
    aver='{:.0f}'.format(cpuReady / 20000 * 100)
    maxim='{:.0f}'.format(float(max(statCpuReady[0].value[0].value)) / 20000 * 100)
    usg=(cpuUsage)
    rdy=(cpuReady / 20000 * 100)

    #================= Cheack CPU Ready Average ================
    if rdy > maxAver:
        data = '{\"phone\": '+phone1+', \"text\": \"Warning: CPU Ready is: '+('{:.1f}'.format(cpuReady / 20000 * 100))+'%  | VM: '+VMN+'\"}'
        req = urllib2.Request(url, data, {'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        for x in f:
            print(x)
        f.close

        if phone2 != '':
            data = '{\"phone\": '+phone2+', \"text\": \"Warning: CPU Ready is: '+('{:.1f}'.format(cpuReady / 20000 * 100))+'%  | VM: '+VMN+'\"}'
            req = urllib2.Request(url, data, {'Content-Type': 'application/json'})
            f = urllib2.urlopen(req)
            for x in f:
                print(x)
            f.close
        #=======================================================================
##    else:
##        print('Average is Ok')

    #================= Check CPU Max Load =======================
##    print('CPU Usage (detail) :',usg,' Warning :',maxCPL,'%')

    if usg > maxCPL:
        data = '{\"phone\": '+phone1+', \"text\": \"Warning: CPU Usage is: '+('{:.1f}'.format(cpuUsage))+'% | VM: '+VMN+'\"}'
        req = urllib2.Request(url, data, {'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        for x in f:
            print(x)
        f.close()

        if phone2 != '':
            data = '{\"phone\": '+phone2+', \"text\": \"Warning: CPU Usage is: '+('{:.1f}'.format(cpuUsage))+'% | VM: '+VMN+'\"}'
            req = urllib2.Request(url, data, {'Content-Type': 'application/json'})
            f = urllib2.urlopen(req)
            for x in f:
                print(x)
            f.close()


##    else:
##        print('CPU Load is Ok')

    #================= Print Section ============================
##    print('==============================================================================================================')
##    print('CPU Load : ' + cpuload + '%')
##    print('CPU Aver : ' + aver + '%')
##    print('CPU Max : ' + maxim + '%')
##    print('CPU Ready (detail) : ',rdy,'Warning:',maxAver,'%')
##    print('==============================================================================================================')

#==========Stat Check
def StatCheck(perf_dict, counter_name):
    counter_key = perf_dict[counter_name]
    return counter_key

#===========Get Properties
def GetProperties(content, viewType, props, specType):
    # Build a view and get basic properties for all Virtual Machines
    objView = content.viewManager.CreateContainerView(content.rootFolder, viewType, True)
    tSpec = vim.PropertyCollector.TraversalSpec(name='tSpecName', path='view', skip=False, type=vim.view.ContainerView)
    pSpec = vim.PropertyCollector.PropertySpec(all=False, pathSet=props, type=specType)
    oSpec = vim.PropertyCollector.ObjectSpec(obj=objView, selectSet=[tSpec], skip=False)
    pfSpec = vim.PropertyCollector.FilterSpec(objectSet=[oSpec], propSet=[pSpec], reportMissingObjectsInResults=False)
    retOptions = vim.PropertyCollector.RetrieveOptions()
    totalProps = []
    retProps = content.propertyCollector.RetrievePropertiesEx(specSet=[pfSpec], options=retOptions)
    totalProps += retProps.objects
    while retProps.token:
        retProps = content.propertyCollector.ContinueRetrievePropertiesEx(token=retProps.token)
        totalProps += retProps.objects
    objView.Destroy()
    # Turn the output in retProps into a usable dictionary of values
    gpOutput = []
    for eachProp in totalProps:
        propDic = {}
        for prop in eachProp.propSet:
            propDic[prop.name] = prop.val
        propDic['moref'] = eachProp.obj
        gpOutput.append(propDic)
    return gpOutput


# From other file  == Endit
def endit():
    """
    times how long it took for this script to run.

    :return:
    """
    end = clock()
    total = end - START
    print("Completion time: {0} seconds.".format(total))




#=== Main Func
def main():
    while True:
        try:
            try:
                si = SmartConnect(host=hostVM,
                                  user=userVM,
                                  pwd=pwdVM,
                                  port=portVM,
                                  sslContext=context)

            except IOError as e:
                pass
            if not si:
                print('Could not connect to the specified host using specified username and password')
                return -1
            atexit.register(Disconnect, si)
            atexit.register(endit)

            content = si.RetrieveContent()
            vm_properties = ["name", "config.uuid", "config.hardware.numCPU",
                     "config.hardware.memoryMB", "guest.guestState",
                     "config.guestFullName", "config.guestId",
                     "config.version"]
            view = pchelper.get_container_view(si,
                                       obj_type=[vim.VirtualMachine])
            vm_data = pchelper.collect_properties(si, view_ref=view,
                                          obj_type=vim.VirtualMachine,
                                          path_set=vm_properties,
                                          include_mors=True)
            for vm in vm_data:
#                print('==========================================================================')
#                print("Name:                    {0}".format(vm["name"]))
#                print("PowerState:              {0}".format(vm["guest.guestState"]))
#                print('==========================================================================')

                vmnames="{0}".format(vm["name"])
                vchtime = si.CurrentTime()
                perf_dict = {}
                perfList = content.perfManager.perfCounter
                for counter in perfList:
                    counter_full = "{}.{}.{}".format(counter.groupInfo.key, counter.nameInfo.key, counter.rollupType)
                    perf_dict[counter_full] = counter.key
                retProps = GetProperties(content, [vim.VirtualMachine], ['name', 'runtime.powerState'], vim.VirtualMachine)

                #Find VM supplied as arg and use Managed Object Reference (moref) for the PrintVmInfo
                for vm in retProps:
                    if (vm['name'] in vmnames) and (vm['runtime.powerState'] == "poweredOn"):
                        PrintVmInfo(vm['moref'], content, vchtime, interval, perf_dict, vmnames, url, phone1, phone2, maxCPL, maxAver)
#                    elif vm['name'] in vmnames:
#                        print('ERROR: Problem connecting to Virtual Machine.  {} is likely powered off or suspended'.format(vm['name']))

        except vmodl.MethodFault as e:
            print('Caught vmodl fault : ' + e.msg)
            return -1
        except Exception as e:
            print('Caught exception : ' + str(e))
            return -1
        if ReRun != '':
            print("Wait "+'{0}'.format(ReRun)+" seconds")
            time.sleep(ReRun)
    return 0
# Start program
if __name__ == "__main__":
    main()
