# -*- coding: utf-8 -*-
import matplotlib
# matplotlib.use('Agg')
import os, getopt, sys, shutil, glob, logging, yaml, re, pickle
import datetime as DT
import numpy as np
from frontback import frontBackNEW
from getdatatestbed.getDataFRF import getObs
from testbedutils import fileHandling
from prepdata import writeRunRead as wrrClass

def Master_workFlow(inputDict):
    """This function will run CMS with any version prefix given start, end, and timestep.

    Args:
      inputDict: a dictionary that is read from the input yaml

    Returns:
      None

    """
    ## unpack input Dictionary
    version_prefix = inputDict['modelSettings']['version_prefix']
    testName = inputDict['testName']
    endTime = inputDict['endTime']
    startTime = inputDict['startTime']
    simulationDuration = inputDict['simulationDuration']
    workingDir = inputDict['workingDirectory']
    generateFlag = inputDict['generateFlag']
    runFlag = inputDict['runFlag']
    pbsFlag = inputDict['pbsFlag']
    analyzeFlag = inputDict['analyzeFlag']
    plotFlag = inputDict['plotFlag']
    modelName = inputDict['modelSettings'].get('modelName', None)
    log = inputDict.get('logging', True)
    updateBathy = inputDict['updateBathy']

    # __________________pre-processing checks________________________________
    fileHandling.checkVersionPrefix(modelName, inputDict)
    # __________________input directories________________________________
    cmtbRootDir = os.getcwd()  # location of working directory
    if workingDir[0] == '.':
        #make absolute path for easier bookkeeping- remove the ./ on relative path
        workingDirectory = os.path.join(cmtbRootDir,workingDir[2:],modelName.lower(), version_prefix)
    else:
        workingDirectory = os.path.join(workingDir, modelName.lower(), version_prefix)
    inputDict['netCDFdir'] = os.path.join(inputDict['netCDFdir'], 'waveModels')
    inputDict['path_prefix'] = workingDirectory
    # ______________________ Logging/FileHandling ____________________________
    # auto generated Log file using start_end time?
    LOG_FILENAME = fileHandling.logFileLogic(workingDirectory, version_prefix, startTime, endTime, log=log)
    dateStartList, dateStringList, projectStart, projectEnd = fileHandling.createTimeInfo(startTime, endTime,
                                                                                  simulationDuration=simulationDuration)
    fileHandling.displayStartInfo(projectStart, projectEnd, version_prefix, LOG_FILENAME, modelName)
    
    # ______________________________gather all data _____________________________
    if generateFlag == True:
        go = getObs(projectStart-DT.timedelta(hours=3), projectEnd+DT.timedelta(hours=3)) # initialize get observation
        if modelName in ['ww3']:
            gauge = 'waverider-26m'
        elif modelName.lower() in ['swash', 'funwave']:
            gauge = '8m-array'
        elif modelName.lower() in ['cshore']:
            gauge = 'awac-6m'
            
        rawspec = go.getWaveData(gaugenumber=gauge, spec=True)
        rawWL = go.getWL()
        rawwind = go.getWind(gaugenumber=0)

    # ________________________________________________ RUN LOOP ________________________________________________
    # run the process through each of the above dates
    errors, errorDates = [], []
    for time in dateStringList:
        print('Beginning to setup simulation {}'.format(DT.datetime.now()))
        try:
            dateString = ''.join(''.join(time.split(':')).split('-'))
            if not testName:
                testName = dateString
            # datadir = os.path.join(workingDirectory, dateString)  # moving to the new simulation's
            # pickleSaveName = os.path.join(datadir, timeStamp + '_ww3io.pickle')
            # # if generateFlag == True:
            #     ww3io = frontBackWW3.ww3simSetup(time, inputDict=inputDict, allWind=rawwind, allWL=rawWL,
            #                                      allWave=rawspec)
            #
            ####### THE NEW WAY!
            # load the instance of wrr # TBD later on what will control this
            # are there other things we need to load?

            print("TODO: Ty here you are creating a function that initalizes wrr and preps irregardless of model")
            if modelName in ['ww3']:
                wrr = wrrClass.ww3io(workingDirectory=workingDirectory,testName=testName, versionPrefix=version_prefix,
                                     startTime=DT.datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ'),
                                     endTime=DT.datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ') + DT.timedelta(
                                     hours=inputDict['simulationDuration']), runFlag=runFlag,
                                     generateFlag=generateFlag, readFlag=analyzeFlag, pbsFlag=pbsFlag)
                
                if generateFlag is True:
                    wavePacket, windPacket, wlPacket, bathyPacket, gridFname, wrr = frontBackNEW.ww3simSetup(time,
                                                                                                     inputDict=inputDict,
                                                                                                     allWind=rawwind,
                                                                                                     allWL=rawWL,
                                                                                                     allWave=rawspec,
                                                                                                     wrr=wrr)
                    ctdPacket = None
                
            elif modelName in ['swash']:
                wrr = wrrClass.swashIO(fNameBase=dateString, versionPrefix=version_prefix,
                                       startTime=DT.datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ'),
                                       simulatedRunTime=inputDict['simulationDuration'],
                                       endTime=DT.datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ') + DT.timedelta(
                                           hours=inputDict['simulationDuration']), runFlag=runFlag,
                                       generateFlag=generateFlag, readFlag=analyzeFlag)
                if generateFlag is True:

                    wavePacket, windPacket, wlPacket, bathyPacket, gridFname, wrr = frontBackNEW.swashSimSetup(time,
                                                                                                     inputDict=inputDict,
                                                                                                     allWind=rawwind,
                                                                                                     allWL=rawWL,
                                                                                                     allWave=rawspec,
                                                                                                     wrr=wrr)
            elif modelName in ['cshore']:
                wrr = wrrClass.cshoreio(workingDirectory=workingDirectory,testName=testName, versionPrefix=version_prefix,
                                       startTime=DT.datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ'),
                                       simulatedRunTime=inputDict['simulationDuration'],
                                       endTime=DT.datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ') + DT.timedelta(
                                           hours=inputDict['simulationDuration']), runFlag=runFlag,
                                       generateFlag=generateFlag, readFlag=analyzeFlag, pbsFlag=pbsFlag)
                if generateFlag is True:
                    rawbathy = go.getBathyTransectFromNC(profilenumbers=960)
                    rawctd = go.getCTD()
                    wavePacket, windPacket, wlPacket, bathyPacket, ctdPacket, wrr = frontBackNEW.cshoreSimSetup(time,
                                                                                                     inputDict=inputDict,
                                                                                                     allWind=rawwind,
                                                                                                     allWL=rawWL,
                                                                                                     allWave=rawspec,
                                                                                                     allBathy=rawbathy,
                                                                                                     allCTD=rawctd,
                                                                                                     wrr=wrr)
                    gridFname = None
                    
            if generateFlag is True:
                print(" TODO: TY you're handing me back the same prepdata packets from all frontBacks")
                print('TODO: document Packets coming from sim-setup')
                try:
                    print('    PrepData Dicts below')
                    print("wavePacket has keys: {}".format(wavePacket.keys()))
                    print("wlPacket has keys: {}".format(wlPacket.keys()))
                    print("bathyPacket has keys: {}".format(bathyPacket.keys()))
                    print("windPacket has keys: {}".format(windPacket.keys()))
                except AttributeError:
                    pass
                
                if pbsFlag is True:
                    wrr.hpcCores = inputDict['hpcSettings']['hpcCores']
                    wrr.hpcNodes = inputDict['hpcSettings']['hpcNodes']
                # write simulation files (if assigned)
                wrr.writeAllFiles(bathyPacket, wavePacket=wavePacket, wlPacket=wlPacket, windPacket=windPacket,
                                  ctdPacket=ctdPacket,gridfname=gridFname,updateBathy=updateBathy)
                
            # run simulation (as appropriate)
            if runFlag is True:
                wrr.runSimulation(modelExecutable=inputDict['modelExecutable'])
            
            # post process (as appropriate)
            #spatialData, savePointData = wrr.readAllFiles()

            if analyzeFlag == True:
                results = wrr.readAllFiles()
                #if generateFlag is False and runFlag is False:
                #    try:  # to load the pickle
                #        with open(wrr.pickleSaveName, 'rb') as fid:
                #            ww3io = pickle.load(fid)
                #    except(FileNotFoundError):
                #        print("couldn't load sim metadata pickle for post-processing: moving to next time")
                #        continue
                #frontBackNEW.genericPostProcess(time, inputDict=inputDict, ww3io=ww3io)

            # if it's a live run, move the plots to the output directory
            if plotFlag is True and DT.date.today() == projectEnd:
                # move files
                moveFnames = glob.glob(cmtbRootDir + 'cmtb*.png')
                moveFnames.extend(glob.glob(cmtbRootDir + 'cmtb*.gif'))
                liveFileMoveToDirectory = '/mnt/gaia/cmtb'
                for file in moveFnames:
                    shutil.move(file,  liveFileMoveToDirectory)
                    print('moved {} to {} '.format(file, liveFileMoveToDirectory))
            print('------------------SUCCESS-----------------------------------------')

        except Exception as e:
            print('<< ERROR >> HAPPENED IN THIS TIME STEP ')
            print(e)
            logging.exception('\nERROR FOUND @ {}\n'.format(time, exc_info=True))
            os.chdir(cmtbRootDir)


if __name__ == "__main__":
    opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    print('___________________________________\n___________________________________\n___________________'
          '________________\n')
    print('USACE FRF Coastal Model Test Bed :')

    try:
        # assume the user gave the path
        yamlLoc = args[0]
        if os.path.exists('.cmtbSettings'):
            with open('.cmtbSettings', 'r') as fid:
                inputDict = yaml.safe_load(fid)
        with open(os.path.join(yamlLoc), 'r') as f:
            a = yaml.safe_load(f)
        inputDict.update(a)
        
    except:
        raise IOError('Input YAML file required. See yaml_files/TestBedExampleInputs/[model]_Input_example for example '
                      'yaml file.')

    Master_workFlow(inputDict=inputDict)
