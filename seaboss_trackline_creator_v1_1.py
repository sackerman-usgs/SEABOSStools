import win32com.client, sys, fileinput, os, string
import arcgisscripting
import time
##this version looks for the start of the line, not just the end
##this version is using a year, jdtime fields to calculate epoch to look
##for start and end
##this version uses Brian Andrew's template
##this version is supposed to work even if the exact
##times don't appear in the nav file and the drift log.
##should take the closest value from the nav file.
##feb. 2005 - modified to work with the output from Ed Sweeney's script
##Dec 2009 - rename script from...
##    "Script1_startend_9_2008proj.py" to "seaboss_trackline_creator_v1_1.py"
##
#Create the geoprocessor object
#GP=win32com.client.Dispatch("esriGeoprocessing.GpDispatch.1")
GP = arcgisscripting.create()
#startend is the first argument, but because we're using linein, don't need to specify it
##infile = sys.argv[1]
#Get the name of the output feature class
fcname = sys.argv[2]
#Get the name of the template feature class.
template = sys.argv[3]
#get the name of the navigation file to sort through
navfile = sys.argv[4]
inputfile = open(navfile,"r")

desc = GP.Describe(template).SpatialReference
print desc.name
##inputfile = open("c:/temp/bookdata_startend.txt")
##f1 = open(infile,"r")
##print template
def isNumber(s):
    try:
        float(s)
        return 1 #no exception, must be a number
    except:
        print "header line"
        return 0 #threw exception, it's not a number
try:
    #Create the feature class
    print os.path.dirname(fcname)
    print os.path.basename(fcname)
    GP.ClusterTolerance = "0.0000001"
    #GP.CreateFeatureClass(os.path.dirname(fcname),os.path.basename(fcname),"Polyline", template)
    GP.CreateFeatureClass(os.path.dirname(fcname),os.path.basename(fcname),"Polyline", template,"","",desc)
    #GP.XYTolerance = "0.0000001"
    
    #Open an insert cursor for the new feature class.
    cur=GP.InsertCursor(fcname)
    #Create the array and point objects needed to create a feature
    lineArray = GP.CreateObject("Array")
    pnt = GP.CreateObject("Point")
    ID = -1 #Initialize a variable for keeping track of a feature's ID.
    count = 0

    #assume all IDs are positive.
##    for line in fileinput.input(infile): #open the input file
    for startinfo in fileinput.input():
        if startinfo in ("__DATA__", "__END__"):
            fileinput.close()
            break
        starts = string.split(startinfo,",")
        lineid = starts[0]
##        print "reading startend file"
        print "lineid " + lineid
        yearid = eval(starts[5])
        startjd = string.atoi(starts[1])
        startjdtime = starts[2]
        startstuff = string.split(startjdtime,":")
        starthr = string.atoi(startstuff[0])
        startmin = string.atoi(startstuff[1])
        startsec = string.atoi(startstuff[2])
        startepoch = (time.mktime((yearid,1,startjd,starthr,startmin,startsec,0,0,0)))
        endjdtime = starts[4]
        endjd = string.atoi(starts[3])
        endstuff = string.split(endjdtime,":")
##        endjd = string.atoi(endstuff[0])
        endhr = string.atoi(endstuff[0])
        endmin = string.atoi(endstuff[1])
        endsec = string.atoi(endstuff[2])
        endepoch = (time.mktime((yearid,1,endjd,endhr,endmin,endsec,0,0,0)))
        collect = 0
        firstpass = 0
        while 1:
            
            line = inputfile.readline()
            values = string.split(line,",")
            lat = values[0]
##            print lat
            if isNumber(lat):
                navyear = eval(values[6])
                navjd = string.atoi(values[5])
    ##            navjdtime = values[2]
    ##            navtimestuff = string.split(navjdtime,":")
                navhr = string.atoi(values[2])
                navmin = string.atoi(values[3])
                navsec = string.atoi(values[4])
                navepoch = (time.mktime((navyear,1,navjd,navhr,navmin,navsec,0,0,0)))
                test1 = navepoch
                test2 = startepoch
                test3 = endepoch
                diffstart = abs(test1 - test2)
                diffend = abs(test1 - test3)
    ##            print "made it here"

                if test1 == test2:
    ##                print "it matches start"
                    collect = 1
                    pnt.id = count
                    pnt.x = float(values[1])
                    pnt.y = float(values[0])
                    lineArray.add(pnt)             

                if (firstpass == 1 and holddiffstart <= diffstart and collect == 0):
                    collect = 1
                    pnt.id = count
                    pnt.x = holdx
                    pnt.y = holdy
                    lineArray.add(pnt)
                    pnt.x = float(values[1])
                    pnt.y = float(values[0])
                    lineArray.add(pnt)
                    
                if (collect == 1 and diffend < holddiffend):
                    pnt.id = count
                    pnt.x = float(values[1])
                    pnt.y = float(values[0])
                    lineArray.add(pnt)
                
                if ID == -1:
                    ID = count
                    holdid = lineid
                #add the point to the feature's array of points.
                #If the ID has changed create a new feature

                if test1 == test3:
    ##                print "it matches end"
    ##                print lineid
                    lineArray.add(pnt)
                    #Create a new row, or feature, in the feature class.
                    feat = cur.NewRow()
                    #Set the geometry of the new feature to the array of points
                    feat.shape = lineArray
                    feat.ID = pnt.id
                    feat.JDAY = startjd
                    feat.LINENAME_1 = lineid
                    feat.LINESTART = startjdtime
                    feat.LINEEND = endjdtime
                    
                    #Insert the feature
                    cur.InsertRow(feat)              
                    lineArray.RemoveAll()
                    count = count + 1
                    holdid = lineid               
                    collect = 0
                    break
                
                if (firstpass == 1 and diffend >= holddiffend and collect == 1):

                    #Create a new row, or feature, in the feature class.
                    feat = cur.NewRow()
                    #Set the geometry of the new feature to the array of points
                    feat.shape = lineArray
                    feat.ID = pnt.id
                    feat.JDAY = startjd
                    feat.LINENAME_1 = lineid
                    feat.LINESTART = startjdtime
                    feat.LINEEND = endjdtime

                    #Insert the feature
                    cur.InsertRow(feat)
                    lineArray.RemoveAll()
                    count = count + 1
                    holdid = lineid               
                    collect = 0
                    break
                
                
                holddiffstart = diffstart
                holddiffend = diffend
                holdx = values[1]
                holdy = values[0]
                firstpass = 1
                ID = count

       

except:
##    if ID != -1:
##    if endid == matchid:
##        print "attempting dump"
##        feat = cur.NewRow()
##        feat.shape = lineArray
##        feat.ID = pnt.id
##        feat.DRIFTID = holdid
##        cur.InsertRow(feat)
##        lineArray.RemoveAll()
        
##        GP.CalculateField(fcname,"DRIFTID",holdid)
##        lineArray.add(pnt)
##    print "couldn't do it"
    print GP.GetMessages(2)

inputfile.close()
