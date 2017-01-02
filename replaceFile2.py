import os
import time
import datetime
import glob
import re
from lxml import etree as lt

# This python script is used to replace the xml file with PWO, CWO and the Action Date automatically
# PWO & CWO is set over here.
# Action_Date is caculated based on system clock.

# Set the input PWO and CWO
#PWO = 'WOR100000183284'
#CWO = 'WOR100000183297'

#  Prompt the end-user that this tool is going to be run:
print '-------------------- Welcome to use replaceFile2 ------------------------'
print 'Author:      Oliver Xu'
print 'Version:     5.0'
print 'Last Update: 2016.11.07\n'
print 'This tool would replace PWO and CWO for the *.xml file.'
print 'It updates the Action_Date to current timestamp as well.'
print 'It could also update the Spec, Activity, Category and Version.'
print 'In version 4.0, this tool accepts the <version> like 0.28.4 and 3.0.4 both.'
print 'In version 5.0, this tool accepts one line input.'
print ''
print 'e.g.'
print 'PWO:WOR100000396565 CWO:WOR100000396583 FTTB_Activation_Work_Order_Specification: Activity_FTTB_Activation: 2.1.0'
print ''
# print 'Press \"ENTER\" to skip the VALUE Change in the xml files'
closeInput = raw_input("Press ENTER to Start")


#  Obtain the input from keyboard for PWO, CWO
print '-------------------------------------------------------------------------'

"""
Sample Spec and Activity for the work order:

FTTB_Activation_Work_Order_Specification
FTTN_Activation_Work_Order_Specification
FTTB_Activation_No_Appointment_Work_Order_Specification
CSLL_Service_Assurance_Work_Order_Specification
CSLL_Service_Assurance_No_Appointment_Work_Order_Specification
General_Work_Order_Specification
General_Network_Assurance_Work_Order_Specification

Activity_Common_Remediation
Activity_FTTB_Activation
Activity_CSLL_Service_Assurance 
Activity_CSLL_Service_Assurance_No_Appointment
Activity_General
Activity_General_Network_Assurance

"""

# PWO = raw_input("Parent Work Order: (e.g. WOR100000183111) ")
# CWO = raw_input("Child Work Order:  (e.g. WOR100000183223) ")

# Version = raw_input("Version: (e.g. 3.0.4) ")
# Spec = raw_input("Work Order Spec: (e.g. FTTN_Activation_Work_Order_Specification) ")
# Activity = raw_input("Work Order Activity: (e.g. Activity_FTTN_Activation) ")

user_input = raw_input('Please input the PWO, CWO, Spec, Activity, and Version: ')

print ''
print ''

# get PWO & CWO, 1st WO is PWO, 2nd is CWO
if re.search('WOR\d{12}',user_input):
    result = re.findall('WOR\d{12}',user_input)
    PWO = result[0]
    print 'Use the PWO from user input: ' + PWO
    if len(result) > 1:
        CWO = result[1]
        print 'Use the CWO from user input: ' + CWO
    else: 
        CWO = '' 
else:
    PWO = ''
    CWO = ''

# get the Specification and Category
# e.g.  Spec     = FTTB_Activation_Work_Order_Specification
#       Category = FTTB

if re.search('[\w\_]+Work\_Order\_Specification', user_input):
    Spec = re.search('[\w\_]+Work\_Order\_Specification', user_input).group(0)
    print 'Use the Spec from user input: ' + Spec
    Category = Spec.split('_')[0].upper()
    print 'Use the Category from user input: ' + Category
else:
    Spec = ''
    Category = ''

# get Activity
# e.g.  Activity_FTTB_Activation

if re.search('Activity_[a-zA-Z\_]+', user_input):
    Activity = re.search('Activity_[a-zA-Z_]+', user_input).group(0)
    print 'Use the Activity from user input: ' + Activity
else:
    Activity = ''

# get version
# e.g. 3.0.2
if re.search(r'\d{1,2}\.\d{1,2}\.\d{1,2}', user_input):
    Version = re.search(r'\d{1,2}\.\d{1,2}\.\d{1,2}', user_input).group(0)
    print "use the Version from user input: " + Version
else:
    Version = ''


# NTD Serial Number                     ALCLF*  ALCLF-FFF99C6
# PSU Serial Number Standard            K*      K-LCLFFFF99C6
# PSU Serial Number w Battery Backup    DAEIW*  DAEIW-FFF99C6

# defeine the pattern to match the NTD Serial Number  ALCLF*  ALCLFFFF99C6
if re.search(r'ALCLF[A-Fa-f0-9]{7}', user_input):
    NTD_Serial = re.search(r'ALCLF[A-Fa-f0-9]{7}', user_input).group(0)
    print "use the NTD Serial Number from user input: " + NTD_Serial
else:
    NTD_Serial = ''

print ''

closeInput = raw_input("Press ENTER to Start")



# Using system time to set the Action_Date & currentActivityStateDateTime
# <currentActivityStateDateTime>2016-03-16T09:00:00Z
# <value>2016-03-17T09:30:00+11:00</value>

current_Time = datetime.datetime.now()
year = current_Time.year
mon  = current_Time.month
day  = current_Time.day
hour = current_Time.hour
min  = current_Time.minute

def Local2UTC(LocalTime):
    EpochSecond = time.mktime(LocalTime.timetuple())
    utcTime = datetime.datetime.utcfromtimestamp(EpochSecond)
    return utcTime

LocalTime = current_Time
UTCTime= Local2UTC(LocalTime)
#print LocalTime.hour
#print UTCTime.hour

TZ = LocalTime.hour - UTCTime.hour
if TZ < 0:
    TZ = TZ + 24
TZ = str(TZ)

if mon < 10:
    mon = '0' + str(mon)
    
if day < 10:
    day = '0' + str(day)

if hour <10:
    hour = '0' + str(hour)

if min <10:
    min = '0' + str(min)

# set the Action_Date to the format: "2016-03-22T09:15:00+11:00"
Action_Date = str(year) + '-' + str(mon) + '-' + str(day) + 'T' + str(hour) + ':' + str(min) + ':00+' + TZ + ':00'

# set currentActivityStateDateTime to the format: "2016-03-21T09:15:00Z"
currentActivityStateDateTime = str(year) + '-' + str(mon) + '-' + str(day) + 'T' + str(hour) + ':' + str(min) + ':00Z'




# define a function set the ELement's text for the matached item by using lxml.elementtree

def setText_xml(ltree, path, text):
    # PWO_ID is the node for PWO 
    # path = ltree.find('FieldWork/ID')
    
    if text != '':
        if ltree.find(path) != None:
            elem = ltree.find(path)    
            elem.text = text

def set_DescribedBy(ltree, DescribedBy_path, DescribedBy_ID, DescribedBy_Value): 
    if DescribedBy_Value != '':   
        # ltree = lt.parse(xml_file) or lt.fromstring(input_string) 
        # DescribedBy_path = the path for the target DescrbiedBy element 
        # DescribedBy_ID : e.g. NTD Serial Number, NTD PSU Serial Number 
        # DescribedBy_Value: the value to be set for the ID

        # ID_lst is a list which stores all the nodes of Described_ID 
        path = DescribedBy_path + '/Characteristic/ID'
        ID_lst = ltree.findall(path)
    
        if DescribedBy_ID != 'NTD Serial Number':
            for elem in ID_lst:
                # e.g. DescribedBy_ID = Action Date
                if elem.text == DescribedBy_ID:
                    DescribedBy_ID = elem
                    #print DescribedBy_ID.text, '=',
            
                    # getparent() to get the parent node
                    Characteristic = elem.getparent()
                    DescribedBy = Characteristic.getparent()
            
                    # get the node for NTD value
                    value_node = DescribedBy.find('value')
                    #print value_node.text
            
                    # set the value for it
                    value_node.text = DescribedBy_Value
    
        else:      
        # DescribedBy_ID = 'NTD Serial Number'
            for elem in ID_lst:
                # DescribedBy_ID = NTD Serial Number
                # Update both NTD/PSU Serial Number
                # e.g. input NTD Serial Number = ALCLFFFF99C6
                # update the right most 7 letters for PSU Serial as well.
                # update following:
                # NTD Serial Number                     ALCLF*  ALCLF-FFF99C6
                # PSU Serial Number Standard            K*      K-LCLFFFF99C6
                # PSU Serial Number w Battery Backup    DAEIW*  DAEIW-FFF99C6
            
                if elem.text == 'NTD Serial Number':
                    DescribedBy_ID = elem
                    #print DescribedBy_ID.text, '=',
            
                    # getparent() to get the parent node
                    Characteristic = elem.getparent()
                    DescribedBy = Characteristic.getparent()
            
                    # get the node for NTD value
                    value_node = DescribedBy.find('value')
                    #print value_node.text
            
                    # set the value for NTD Serial
                    value_node.text = DescribedBy_Value
                    #print 'NTD Serial Number', value_node.text 
                elif elem.text == 'NTD PSU Serial Number':
                    DescribedBy_ID = elem
                    #print DescribedBy_ID.text, '=',
            
                    # getparent() to get the parent node
                    Characteristic = elem.getparent()
                    DescribedBy = Characteristic.getparent()
            
                    # get the node for NTD PSU value
                    value_node = DescribedBy.find('value')
                    
            
                    # set the value for PSU based on NTD Serial Number's last 7 letters
                    # keep its first 5 letters unchanged.
                    # NTD Serial Number                     ALCLF*  ALCLF-FFF99C6
                    # PSU Serial Number Standard            K*      K-LCLFFFF99C6
                    # PSU Serial Number w Battery Backup    DAEIW*  DAEIW-FFF99C6
                    
                    value_node.text = value_node.text[:5] + DescribedBy_Value[-7:]
                    #print 'NTD PSU Serial Number', value_node.text


print '---------------------------  Processing ---------------------------------'

print ''

# get the list xml file with the name starting with 2. e.g. 2a.xml
xml_file_list = glob.glob("./*.xml")

for xml_file in xml_file_list:
    # print xml_file, 
    # e.g.  ".\2a.xml", to remove the leading ".\"
    # so that the file name is changed to "2a.xml"
    file = xml_file.replace(".\\" , "")
    print file
    
    # file_handle = open(file, 'r')
    # file_string = file_handle.read()
    # file_handle.close()
         
    # using lxml.etree to parse xml file
    ltree = lt.parse(xml_file) 
    root = ltree.getroot()

    # set the PWO, it is the 1st matched WOR123456789012 in the xml 
    setText_xml(ltree, 'FieldWork/ID', PWO)
         
    # set the CWO, it is the 2nd and 3rd matched WOR123456789012 in the xml
    setText_xml(ltree, 'FieldWork/HasStatusSnapshot/SnapshotOfCurrentStatus/ActivityStatusInfo/ID', CWO)
    setText_xml(ltree, 'FieldWork/FieldWorkHasChanges/ActivityChangeEntry/OccursWithinActivity/ID', CWO)

    # set the currentActivityStateDateTime   
    setText_xml(ltree, 'FieldWork/HasStatusSnapshot/SnapshotOfCurrentStatus/ActivityStatusInfo/currentActivityStateDateTime', currentActivityStateDateTime)
    
    # set Version
    setText_xml(ltree, 'FieldWork/FieldWorkSpecifiedBy/version', Version)
    
    # set Spec
    setText_xml(ltree, 'FieldWork/FieldWorkSpecifiedBy/ID', Spec)
    
    # set Activity
    setText_xml(ltree, 'FieldWork/HasStatusSnapshot/SnapshotOfCurrentStatus/ActivityStatusInfo/ActivityInstantiatedBy/ID', Activity)
    setText_xml(ltree, 'FieldWork/FieldWorkHasChanges/ActivityChangeEntry/OccursWithinActivity/ActivityInstantiatedBy/ID', Activity)

    # set Category
    setText_xml(ltree, 'FieldWork/FieldWorkSpecifiedBy/category', Category)
    #setText_xml(ltree, 'FieldWork/FieldWorkHasChanges/ActivityChangeEntry/OccursWithinActivity/ID', Category)
    
    # set Action Date
    set_DescribedBy(ltree, 'FieldWork/FieldWorkHasChanges/ActivityChangeEntry/InputData/DescribedBy', 'Action Date', Action_Date)
    
    # set Additional Info
    #set_DescribedBy(ltree, 'FieldWork/FieldWorkHasChanges/ActivityChangeEntry/InputData/DescribedBy', 'Additional Info', 'SIT Testing')
    
    # set the NTD Serial Number: NTD_Serial
    # set_DescribedBy(ltree, 'FieldWork/FieldWorkHasChanges/ActivityChangeEntry/InputData/DescribedBy', 'NTD Serial Number', NTD_Serial)
    
    # increase NTD/PSU Serial Number if NTD_Serial == ''
    if NTD_Serial == '':
        pass
    else:
        # set the NTD Serial Number: NTD_Serial
        set_DescribedBy(ltree, 'FieldWork/FieldWorkHasChanges/ActivityChangeEntry/InputData/DescribedBy', 'NTD Serial Number', NTD_Serial)
                              
    # use lxml to write back the xml file
    # write the updated value back to the xml        
    lt.ElementTree(root).write(xml_file, pretty_print=True)
   
    
#  debugging... Terminal is not closed till hit ENTER

print ''
print 'Updated Parent Work Order to: ' + PWO
print 'Updated Child  Work Order to: ' + CWO
print 'Updated Spec to: ' + Spec
print 'Updated Category to: ' + Category
print 'Updated Activity to: ' + Activity
print 'Updated Version to: ' + Version
print 'Updated NTD Serial Number to: ' + NTD_Serial
print 'Updated Action_Date to: ' + Action_Date
print 'Updated currentActivityStateDateTime to: ' + currentActivityStateDateTime
print '-------------------------------------------------------------------------'
closeInput = raw_input("Press ENTER to exit")
print "Closing..."     
