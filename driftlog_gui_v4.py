#This is the gui version of photo_locations.py
#The purpose of this script is to combine the navigation parsed
#from HYPACK files with the information stripped from the EXIF headers
#of SEABOSS JPEG images.
#Time is the common factor - and the result is a shapefile
#of photo locations.
#added timeoffset as an attribute so I can keep track of what the user enters.
#modified Jan. 30, 2014
#   fixed the projection information to match what ArcGIS does in 9.3.1
#   can't remember where I got the old proj strings from, the new
#   ones come from spatialreference.org
#modified August 5, 2015
#   Seth discovered bizareness, and I think the problem is that I was not
#   emptying the array when the end drift time actually equaled something in the
#   nav file. The bizarness manifested itself as stringing several driftlines
#   together, instead of them being individual lines.
#   I had to add the line list[] to empty the buffer. The problem only
#   surfaced when the end time actually had a value in the GPS file.
#   Making other adjustments to the output, write file for axiom
#modified August 6-10, 2016
#   making sure the correct epoch time is written out - not based on local time.
#   need to make sure I have the right start and end gps time, when it doesn't equal drift time
#   I want to get the closest time to the drift time, whether it's before or after.
#   While doing this, I also discovered that in the polyline file, I was repeating values at start
#   if they equaled the drift time. Not a big deal, unless you want to do something with the
#   verticies. I don't think
#   However, I was having a similar problem with the Axiom output, and had to futz to figure out
#   what was causing the repeats. When the next nav time was further away then the previous nav
#   time, but not equal, I was repeating the nav time. Basically I didn't need to write
#   out the nav to axiom, as it was already taken care of elsewhere. The reason the shapefile
#   vertice didn't repeat is because I didn't have an append to the list, I simply wrote to the shapefile.
#   However, the problem I had with the shapefile is that it was writing out the wrong GPS time in the attribute
#   table because I wasn't writing out the previously held value - which is where the nav point was from.
#   Added the following attributes: Survey, Year, GPSStart, GPSEnd
#   I also added the output to axiom to include the following elements:
#       survey, station, longitude, latitude, epochtime, year, jdtime (jd:hh:mm:ss)
#   some notes on things I ran into. To get the appropritae epochtime, I had to use calendar.timegm
#   for my own purposes, I had used time.mktime - but that gave epochtime assuming the time was local.
#   Seth suggested adding survey to the attribute table (GREAT idea), and I also decided I should add year
#   in case the survey ID did not have that value in it. the GPSStart and GPSEnd I added more for myself to
#   make it obvious that the start and end of the actual lines didn't necessarily equal the values of the start
#   and end of the drift.
#   Tested and works with Idle 2.7.3
 
import sys, os, string
import time
import calendar
from Tkinter import *
import tkFileDialog
import tkMessageBox

#this next two are special and does not ship with Python
#from dbfpy import dbf
import shapefile

class DriftLog(Frame):
  
    def __init__(self, parent):
        Frame.__init__(self, parent)   
         
        self.parent = parent
        
        self.initUI()
        
    def initUI(self):
        
      
        self.parent.title("SeaBOSS Drift Navigation")

        self.pack(fill=BOTH, expand=1)

        #my attempts
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=1)
        self.rowconfigure(5, weight=1)
        self.rowconfigure(6, weight=1)
        self.rowconfigure(7, weight=1)
        self.rowconfigure(8, weight=1)
        self.rowconfigure(9, weight=1)
        self.rowconfigure(10, weight=1)
        self.rowconfigure(11, weight=1)
        self.rowconfigure(12, weight=1)
        self.rowconfigure(13, weight=1)
        self.rowconfigure(14, weight=1)
        self.rowconfigure(15, weight=1)
        self.rowconfigure(16, weight=1)
        self.rowconfigure(17, weight=1)
        self.rowconfigure(18, weight=1)
        self.rowconfigure(19, weight=1)
        self.rowconfigure(20, weight=1)

        self.columnconfigure(0, weight=1, pad=1)
        self.columnconfigure(1, weight=1, pad=1)
        self.columnconfigure(2, weight=1, pad=1)


        junk = "junk test"
        junk2 = "Junk test 2"
        self.projType = IntVar()
        
        lbl = Label(self, text="Input")
        lbl.grid(sticky=W, pady=4, padx=5)

        #input drift file
        #expect format of file is:
        #sta, startjd, starttimehh:mm:ss, endjd, endtimehh:mm:ss
        entryLabel = Label(self, text="Start and End drift text file: ", fg="red")
        entryLabel.grid(row=1, sticky=W, column=0, padx=5)

        #as entry line
        self.entryLabel2 = Entry(self, relief="sunken")
        self.entryLabel2.insert(0, junk)
        self.entryLabel2.grid(row=2, padx=5,columnspan=3, sticky=W+E)
        
        abtn = Button(self, text="OPEN Drift file", command=self.getDRIFTfile)
        abtn.grid(row=3, column=0, padx=5, sticky=W)

        #input navigation file
        #format
        #Latitude, Longitude, Hours, Minutes, Seconds, JulianDay, Year, CruiseID
        entryNavLbl = Label(self, text="Parsed navigation file: ", )
        entryNavLbl.grid(row=4, sticky=W, column=0, padx=5)

        self.entryNav = Entry(self, relief="sunken")
        self.entryNav.insert(0, junk)
        self.entryNav.grid(row=5, padx=5, columnspan=3, sticky=W+E)

        navbtn = Button(self, text="OPEN NAV file", command=self.getNAVfile)
        navbtn.grid(row=6, column=0, padx=5, sticky=W)

        #output shapefile
        outLabel = Label(self, text="Output file: ")
        outLabel.grid(row=7,padx=5, sticky=W)

        #output filename as entry line
        self.outLabel2 = Entry(self, relief="sunken")
        self.outLabel2.insert(0, junk2)
        self.outLabel2.grid(row=8, padx=5, columnspan=3,sticky=W+E)

        filebtn = Button(self, text="Output shapefile", command=self.saveSHPtext)
        filebtn.grid(row=9,column=0, padx=5, sticky=W)

        #get field activity added Aug 6, 2015
        faLabel = Label(self, text="Field Activity: such as 2015-003-FA")
        faLabel.grid(row=10, column=0, sticky=W)
        self.entryFA = Entry(self, width=40)
        self.entryFA.grid(row=11, column=0, padx=10, sticky='w')

        #projection radio buttons - everything shifted down to make room for Field Activity
        prjLabel = Label(self, text="Shapefile projection: ", font='bold')
        prjLabel.grid(row=13, padx=5, sticky=W)
        #projOpt = Radiobutton(text="Geographic, WGS 84", variable=projType, value=1).grid(row=10, column=1, sticky = W)
        self.projOpt = Radiobutton(self, text="Geographic, WGS 84", variable=self.projType, value=1)
        self.projOpt.grid(row=14, column=0, sticky=W)
        self.projOpt = Radiobutton(self, text="Geographic NAD 83", variable=self.projType, value=2)
        self.projOpt.grid(row=15, column=0, sticky=W)
        self.projOpt = Radiobutton(self, text="Other", variable=self.projType, value=3)
        self.projOpt.grid(row=16, column=0, sticky=W)
        #self.projOpt.grid(row=11)
        #prjResult =




        #submit and close buttons
        hbtn = Button(self, text="Submit", command=self.MergeDriftNav)
        #hbtn = Button(self, text="Submit")
        hbtn.grid(row=20, column=0, padx=5)
        
        cbtn = Button(self, text="Close", command=self.cbtnClick)
        cbtn.grid(row=20, column=2)


    def cbtnClick(self):
        print "close button event handler"
        self.parent.destroy()

    def getHYPACKFolder(self):
        #HYPfolder = tkFileDialog.askdirectory(initialdir="F:/", title='PickHYPACK')
        HYPfolder = tkFileDialog.askdirectory(initialdir="C:/", title='PickHYPACK')
        #need to clear anything that's there
        self.entryLabel2.delete(0,END)
        if len(HYPfolder) > 0:
            print "now read HYPACK folder %s" % HYPfolder
            #self.entryLabel2.config(text=HYPfolder)
            #this took forever to get to work. I had to add the self. to the entryLabel2
            #and then the self here. without it in both places - no go.
            #for entry widget
            self.entryLabel2.insert(0,HYPfolder)

    def getDRIFTfile(self):
        #IMGfile = tkFileDialog.askopenfile(mode='r', initialdir = "C:/", title='Image EXIF info')
        IMGfile = tkFileDialog.askopenfilename(initialdir="D:/edrive/python/TKinter/test/grid/junk/", title='Image EXIF info')
        print IMGfile
        self.entryLabel2.delete(0,END)
        self.entryLabel2.insert(0, IMGfile)        

    def getNAVfile(self):
        #IMGfile = tkFileDialog.askopenfile(mode='r', initialdir = "C:/", title='Image EXIF info')
        NAVfile = tkFileDialog.askopenfilename(initialdir="D:/edrive/python/TKinter/test/grid/junk/", title='Parsed HYPACK Nav file')
        print NAVfile
        self.entryNav.delete(0,END)
        self.entryNav.insert(0, NAVfile)
        

    def saveSHPtext(self):
        SHPtext = tkFileDialog.asksaveasfilename(filetypes=[('Shapefile','.shp')], title='Save Shapefile')
        print SHPtext
        #need to clear anything that's there
        self.outLabel2.delete(0,END)
        self.outLabel2.insert(0,SHPtext)


    def MergeDriftNav(self):
        try:
            #gather variables.
            #print "gather variables"
            navfile = self.entryNav.get()
            #print "got nav file"
            inputfile = open(navfile,"r")
            #print "open nav file for reading"
            driftfile = self.entryLabel2.get()
            #print "got exiffile"
            #print exiffile
            outshp = self.outLabel2.get()
            #mod to output the points
            outpoints = outshp + "axiom"
            outaxiom = open(outpoints,"w")
            newline = "\n"
            outaxiom.write("survey, station, longitude, latitude, epochtime, year, jdtime%s" %(newline))
            #outaxiom.write("%s" %(newline))
            #mod to get survey
            surveyentry = self.entryFA.get()
            survey = surveyentry.strip()
            print survey
            
            #print "got output shape"
            
            #create feature class
            print "create feature class"
            wshp = shapefile.Writer(shapefile.POLYLINE)
            wshp.field('ID', 'N', 10)
            wshp.field('Survey', 'C', 15)
            wshp.field('Station', 'C', 15)
            wshp.field('Year', 'N', 4)
            wshp.field('JD','N', 3, 0)
            wshp.field('LineStart', 'C', 10)
            wshp.field('LineEnd', 'C', 10)
            wshp.field('GPSStart', 'C', 10)
            wshp.field('GPSEnd', 'C', 10)

            print "finished creating feature class"
            #writing projection
            #getProj = self.projOpt.get()
            #getProj = self.projType.get()
            #print getProj
            projPrefix = os.path.splitext(outshp)[0]
            if self.projType.get() == 1:
                print "projection wgs84"
                #based on: http://spatialreference.org/ref/epsg/4326/
                epsg = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",0.017453292519943295]]'
                prjpoint = open("%s.prj" % projPrefix, "w")
                prjpoint.write(epsg)
                prjpoint.close()
                print "finished writing projection file %s" % prjpoint
            elif self.projType.get() == 2:
                print "projection nad83"
                #based on: http://spatialreference.org/ref/sr-org/7169/
                epsg = 'GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.017453292519943295]]'
                prjpoint = open("%s.prj" % projPrefix, "w")
                prjpoint.write(epsg)
                prjpoint.close()
            else:
                print "projection other"
            
            ID = -1 #Initialize a variable for keeping track of a feature's ID
            count = 0
            navrecord = 0
            list = []
            #for startinfo in fileinput.input(exiffile):
            for startinfo in open(driftfile):
                #print "starting to read driftfile"
                if startinfo in ("__DATA__", "__END__"):
                    fileinput.close(driftfile)
                    print "close driftfile"
                    break
                starts = string.split(startinfo,",")
                lineid = starts[0]
                #print lineid
                yearid = eval(starts[5])
                startjd = string.atoi(starts[1])
                startjdtime = starts[2]
                startstuff = string.split(startjdtime, ":")
                starthr = string.atoi(startstuff[0])
                startmin = string.atoi(startstuff[1])
                startsec = string.atoi(startstuff[2])
                #startepoch = (time.mktime((yearid,1,startjd,starthr,startmin,startsec,0,0,0)))
                startepoch = (calendar.timegm((yearid,1,startjd,starthr,startmin,startsec,0,0,0)))
                #print startepoch
                
                endjdtime = starts[4]
                endjd = string.atoi(starts[3])
                endstuff = string.split(endjdtime,":")
                endhr = string.atoi(endstuff[0])
                endmin = string.atoi(endstuff[1])
                endsec = string.atoi(endstuff[2])
                #endepoch = (time.mktime((yearid,1,endjd,endhr,endmin,endsec,0,0,0)))
                endepoch = (calendar.timegm((yearid,1,endjd,endhr,endmin,endsec,0,0,0)))
                #print endepoch
                collect = 0
                firstpass = 0
                startsame = 0
                #endsame = 0
                #print startjdtime
                #print endjdtime

                #firstpass = 0
                #collect = 0
                while 1:
                    #print "in the while loop"
                    #now I should be opening the nav file
                    line = inputfile.readline()
                    if line == "":
                        print "end of nav file - check to see if you covered all the drift times"
                        system.exit("end of file")
                    #print "got first row of nav file"
                    values = string.split(line,",")
                    lat = values[0]
                    longi = values[1]
                    #print lat
                    #print longi
                    #I don't think isNumber is working I'm not calling it properly
                    if self.isNumber(lat):
                        #print "seeing if it's a number"
                        navrecord = navrecord + 1
                        navyear = eval(values[6])
                        navjd = string.atoi(values[5])
                        navhr = string.atoi(values[2])
                        navmin = string.atoi(values[3])
                        navsec = string.atoi(values[4])
                        #added this aug 6, 2015 for shapefile
                        #navtime = values[2] + ":" + values[3] + ":" + values[4]
                        navtime = ("%02d:%02d:%02d" % (navhr, navmin, navsec))
                        #print navtime
                        #navepoch = (time.mktime((navyear,1,navjd,navhr,navmin,navsec,0,0,0)))
                        navepoch = (calendar.timegm((navyear,1,navjd,navhr,navmin,navsec,0,0,0)))
                        test1 = navepoch
                        #print test1
                        test2 = startepoch
                        test3 = endepoch
                        #print test1
                        #print test2
                        diffstart = abs(test1 - test2)
                        diffend = abs(test1 - test3)
                        #print "finished doing number stuff"
                        if (navrecord == 1 and test1 > test2):
                            print "must have a nav point for the beginning of the drift - the drift starts before the navigation"
                            system.exit("run away")

                        if test1 == test2:
                            collect = 1
                            startsame = 1
                            #print "made it test equal"
                            navstart = navtime
                            #do shapefile stuff                            
                            list.append([float(longi), float(lat)])
                            outaxiom.write("%s, %s, %f, %f, %s, %i, %03d:%02d:%02d:%02d%s" %(survey, lineid, float(longi), float(lat), navepoch, navyear, navjd, navhr, navmin, navsec, newline))
                            navstart = navtime
                            #print "finished test equal"

                        if (firstpass == 1 and holddiffstart <= diffstart and collect == 0):
                        #if (firstpass == 1 and holddiffstart < diffstart and collect == 0):
                            collect = 1
                        #print "here 1"
                            list.append([float(holdx), float(holdy)])
                            navstart = holdnavtime
                            #outaxiom.write("%f, %f, %s, %03d:%02d:%02d:%02d, %i%s" %(float(holdx), float(holdy), navyear, holdjd, holdhr, holdmin, holdsec, holdnavepoch, newline))
                            outaxiom.write("%s, %s, %f, %f, %s, %i, %03d:%02d:%02d:%02d%s" %(survey, lineid, float(holdx), float(holdy), holdnavepoch, navyear, holdjd, holdhr, holdmin, holdsec, newline))

                        if (collect == 1 and diffend < holddiffend and startsame == 0 and test1 != test3):
                            #print "here 2"
                            list.append([float(longi), float(lat)])
                            navend = navtime
                            #outaxiom.write("%f, %f, %s, %03d:%02d:%02d:%02d, %i%s" %(float(longi), float(lat), navyear, navjd, navhr, navmin, navsec, navepoch, newline))
                            outaxiom.write("%s, %s, %f, %f, %s, %i, %03d:%02d:%02d:%02d%s" %(survey, lineid, float(longi), float(lat), navepoch, navyear, navjd, navhr, navmin, navsec, newline))
                            #print "here 2"

                        if ID == -1:
                            ID = count
                            holdid = lineid
                            #print "here 3"

                        if test1 == test3:
                            print "begin here 4"
                            #shouldn't need this next line because I supposedly break out of the loop, but
                            #for some reason, the polyline is repeating the last point.
                            #endsame = 1
                            list.append([float(longi), float(lat)])
                            navend = navtime
                            wshp.line(parts=[list])
                            wshp.record(count, survey, lineid, navyear, startjd, startjdtime, endjdtime, navstart, navend)
                            #I need to empy the array
                            list = []
                            count = count + 1
                            holdid = lineid
                            collect = 0
                            #print "here 4"
                            #print "exit 2"
                            #outaxiom.write("%f, %f, %s, %03d:%02d:%02d:%02d, %i%s" %(float(longi), float(lat), navyear, navjd, navhr, navmin, navsec, navepoch, newline))
                            outaxiom.write("%s, %s, %f, %f, %s, %i, %03d:%02d:%02d:%02d%s" %(survey, lineid, float(longi), float(lat), navepoch, navyear, navjd, navhr, navmin, navsec, newline))
                            break

                        if (firstpass ==1 and diffend >= holddiffend and collect == 1):
                        #if (firstpass ==1 and diffend >= holddiffend and collect == 1 and endsame == 0):
                        #if (firstpass ==1 and diffend > holddiffend and collect == 1):
                            #print "begin here 5"
                            wshp.line(parts=[list])
                            navend = holdnavtime
                            #print "here 5a"
                            wshp.record(count, survey, lineid, navyear, startjd, startjdtime, endjdtime, navstart, navend)
                            #wshp.record("field1", "fld2", "fld3", "fld4", "fld5")
                            #print "here 5b"
                            #empty the array
                            list = []
                            count = count +1
                            holdid = lineid
                            collect = 0
                            #outaxiom.write("%f, %f, %s, %03d:%02d:%02d:%02d, %i%s" %(float(holdx), float(holdy), navyear, holdjd, holdhr, holdmin, holdsec, holdnavepoch, newline))
                            #outaxiom.write("%s, %s, %f, %f, %s, %i, %03d:%02d:%02d:%02d%s" %(survey, lineid, float(holdx), float(holdy), holdnavepoch, navyear, holdjd, holdhr, holdmin, holdsec, newline))
                            #print "exit 3"
                            break
                            
                            
                        holddiffstart = diffstart
                        holddiffend = diffend
                        holdx = values[1]
                        holdy = values[0]
                        holdjd = navjd
                        holdhr = navhr
                        holdmin = navmin
                        holdsec = navsec
                        holdnavepoch = navepoch
                        holdnavtime = navtime
                        #holdgpstime = gpstime
                        firstpass = 1
                        ID = count
                        startsame = 0
                        #endsame = 0
                    else:
                        print "not a number"
        except:
            print "booboo"

        inputfile.close()
        outaxiom.close()
        wshp.save(outshp)
                                           
        #prjpoint.write(epsg)
        #prjpoint.close()
        print "done"
                    
        

    def isNumber(self, s):
        #print "in isNumber"
        try:
            float(s)
            return 1 #no exception, must be a number
        except:
            print "header line"
            
def main():
  
    root = Tk()
    root.geometry("550x400+300+300")
    app = DriftLog(root)
    root.mainloop()
    


if __name__ == '__main__':
    main()
