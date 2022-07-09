from tkinter import *
from tkinter import filedialog
import tkinter as tk
from tkinter import ttk
import os
import pandas as pd
import sys
import numpy as np
import julia
from julia import Main


original_stdout = sys.stdout # Save a reference to the original standard output
from bs4 import BeautifulSoup
import requests# Request to website and download HTML contents

def assignTAToCourse(savedir, taData, courseData, taClicked, courseClicked):
    
    if taClicked.get() == "":
        Label(second_frame, text="Please select a TA                                                                         ").grid(row=6,column=0,sticky='w')
    elif courseClicked.get() == "":
        Label(second_frame, text="Please select a course                                                                     ").grid(row=6,column=0,sticky='w')
    else:
        #assign TA to course
        assignmentMade = 0
        for i in taData.index:
            # probably inefficient
            if taData.loc[i,"name"] == taClicked.get():
                if str(taData.loc[i,"assignment"]) == "nan":
                    taData.loc[i,"assignment"] = [courseClicked.get()]
                else:
                    if type(taData.loc[i,"assignment"]) == str:
                        courses = taData.loc[i,"assignment"]
                        courses = courses.lstrip('[')
                        courses = courses.rstrip(']')
                        courses = courses.split(',')
                        for j in range(len(courses)):
                            course = courses[j]
                            course = course.strip(" ")
                            course = course.strip("'")
                            courses[j] = course
                        if courseClicked.get() in courses:#taData.loc[i,"assignment"]:
                            Label(second_frame, text="TA already selected for this course.").grid(row=6,column=0,sticky='w')
                        else:
                            courses.append(courseClicked.get())
                            Label(second_frame, text="                                                                          ").grid(row=6,column=0,sticky='w')
                            taData.loc[i,"assignment"] = str(courses)
                    else:
                        if courseClicked.get() in taData.loc[i,"assignment"]:
                            Label(second_frame, text="TA already selected for this course.").grid(row=6,column=0,sticky='w')
                        else:
                            taData.loc[i,"assignment"].append(courseClicked.get())
                            Label(second_frame, text="                                                                          ").grid(row=6,column=0,sticky='w')
                assignmentMade += 1
        taData.to_csv(savedir + "ta_dataset.csv",index=False)
        
        for i in courseData.index:
            # probably inefficient
            courseString2 = courseData.loc[i,"course_number"] + " - " + courseData.loc[i,"course_name"]
            if courseString2 == courseClicked.get():
                if not str(courseData.loc[i,"ta_assigned"]) == "nan":
                    if not courseData.loc[i,"ta_assigned"] == taClicked.get():
                        oldTA = courseData.loc[i,"ta_assigned"]
                        Label(second_frame, text="Warning: Overwriting TA " + oldTA + " teaching this course.                            ").grid(row=6,column=0,sticky='w')
                        # remove old ta from list of assignments
                        for j in taData.index:
                            if taData.loc[j,"name"] == oldTA:
                                if type(taData.loc[j,"assignment"]) == str:
                                    courses = taData.loc[j,"assignment"]
                                    courses = courses.lstrip('[')
                                    courses = courses.rstrip(']')
                                    courses = courses.split(',')
                                    for k in range(len(courses)):
                                        course = courses[k]
                                        course = course.strip(" ")
                                        course = course.strip("'")
                                        courses[k] = course
                                    for course in courses:
                                        if course in courseClicked.get() or courseClicked.get() in course:
                                            courses.remove(course)
                                    if len(courses) == 0:
                                        taData.loc[j,"assignment"] = np.nan
                                    else:
                                        taData.loc[j,"assignment"] = str(courses)
                                    taData.to_csv(savedir + "ta_dataset.csv",index=False)
                                else:
                                    taData.loc[j,"assignment"].remove(courseClicked.get())
                                    if len(taData.loc[j,"assignment"]) == 0:
                                        taData.loc[j,"assignment"] = np.nan
                                    taData.to_csv(savedir + "ta_dataset.csv",index=False)
                else:
                    Label(second_frame, text="                                                                             ").grid(row=6,column=0,sticky='w')
                courseData.loc[i,"ta_assigned"] = taClicked.get()
                assignmentMade += 1
        courseData.to_csv(savedir + "course_dataset.csv",index=False)
        if assignmentMade == 2:
            assmade=Label(second_frame,text="TA " + taClicked.get() + " assigned to course " + courseClicked.get() + "                                    ")
            assmade.grid(row=7,column=0,sticky='w')
        else:
            Label(second_frame,text="                                                                                      ").grid(row=6,column=0,sticky='w')

            
            
def saveParameters(savedir,value):
    optpath = sys.argv[0].rstrip("ta_assignment.py")
    with open(optpath+'optimization_parameters.csv', 'w') as f:
        sys.stdout = f # Change the standard output to the file we created.
        print("parameter,value")
        print("directory," + savedir)
        print("workload_id," + str(value))
        
        sys.stdout = original_stdout
        
def optimize(savedir,value):

    saveParameters(savedir,value)
    
    #Label(second_frame,text="Optimizing...This may take a few minutes (check command line)").grid(row=16,column=0,sticky='w')
    j = julia.Julia(compiled_modules=False)
    
    optpath = sys.argv[0].rstrip("ta_assignment.py")
    curdir = os.path.abspath(os.getcwd())
    os.chdir(optpath)
    Main.include("TAassignment.jl")
    os.chdir(curdir)
    Label(second_frame,text="Done!                                     ").grid(row=16,column=0,sticky='w')

    
def listTAs(savedir, courseClicked2):
    courseTAPref = pd.read_csv(savedir+"courses_requested.csv")
    
    ### change way this is displayed / add scroll bar
    newWindow2 = Toplevel(root)
    newWindow2.geometry("650x450")
    main_frame = Frame(newWindow2)
    main_frame.pack(fill=BOTH, expand=1)
    
    my_canvas = Canvas(main_frame)
    my_canvas.pack(side=LEFT, fill=BOTH, expand=1)
    my_scrollbar = ttk.Scrollbar(main_frame, orient=VERTICAL, command=my_canvas.yview)
    my_scrollbar.pack(side=RIGHT,fill=Y)
    
    my_canvas.configure(yscrollcommand=my_scrollbar.set)
    my_canvas.bind('<Configure>', lambda e: my_canvas.configure(scrollregion = my_canvas.bbox("all")))
    
    second_frame = Frame(my_canvas)
    
    my_canvas.create_window((0,0), window=second_frame, anchor="nw")
    
    Label(second_frame, text="TAs who requested " + courseClicked2.get() + " (lower preference = more preferred).").grid(row=0,column=0,sticky='w')
    Label(second_frame, text="Teaching assistant | year # | pref # | available?").grid(row=1,column=0,sticky='w')
    Label(second_frame, text="").grid(row=2,column=0,sticky='w')
    Label(second_frame, text="TA WITH PREFERANCE INDICATED AND IS AVAILABLE").grid(row=3,column=0,sticky='w')
    Label(second_frame, text="").grid(row=4,column=0,sticky='w')
    count = 0
    for i in courseTAPref.index:
        if courseTAPref.loc[i, "course_number"] in courseClicked2.get() and courseTAPref.loc[i,"TA_available"] > 0 and courseTAPref.loc[i,"TA_preference"] > 0:
            if courseTAPref.loc[i,"TA_available"] > 0:
                avail = "yes"
            else:
                avail = "no"
            Label(second_frame, text=courseTAPref.loc[i,"TA_name"]+ " | y" + str(courseTAPref.loc[i,"TA_year"]) + " | p" + str(courseTAPref.loc[i,"TA_preference"]) + " | " + avail).grid(row=count+5,column=0,sticky='w')
            count += 1
    Label(second_frame, text="").grid(row=count+5,column=0,sticky='w')
    Label(second_frame, text="TA WITH PREFERANCE NOT INDICATED AND IS AVAILABLE").grid(row=count+6,column=0,sticky='w')
    Label(second_frame, text="").grid(row=count+7,column=0,sticky='w')
    for i in courseTAPref.index:
        if courseTAPref.loc[i, "course_number"] in courseClicked2.get() and courseTAPref.loc[i,"TA_available"] > 0 and courseTAPref.loc[i,"TA_preference"] == 0:
            if courseTAPref.loc[i,"TA_available"] > 0:
                avail = "yes"
            else:
                avail = "no"
            Label(second_frame, text=courseTAPref.loc[i,"TA_name"]+ " | y" + str(courseTAPref.loc[i,"TA_year"]) + " | p" + str(courseTAPref.loc[i,"TA_preference"]) + " | " + avail).grid(row=count+8,column=0,sticky='w')
            count += 1
    Label(second_frame, text="").grid(row=count+9,column=0,sticky='w')
    Label(second_frame, text="TA WITH PREFERANCE INDICATED AND IS NOT AVAILABLE").grid(row=count+10,column=0,sticky='w')
    Label(second_frame, text="").grid(row=count+11,column=0,sticky='w')
    for i in courseTAPref.index:
        if courseTAPref.loc[i, "course_number"] in courseClicked2.get() and courseTAPref.loc[i,"TA_available"] == 0 and courseTAPref.loc[i,"TA_preference"] > 0:
            if courseTAPref.loc[i,"TA_available"] > 0:
                avail = "yes"
            else:
                avail = "no"
            Label(second_frame, text=courseTAPref.loc[i,"TA_name"]+ " | y" + str(courseTAPref.loc[i,"TA_year"]) + " | p" + str(courseTAPref.loc[i,"TA_preference"]) + " | " + avail).grid(row=count+12,column=0,sticky='w')
            count += 1
            
def courseTASearch(savedir, courseData):
    j = julia.Julia(compiled_modules=False)
    
    if not os.path.exists(savedir + "courses_requested.csv"):
        optpath = sys.argv[0].rstrip("ta_assignment.py")
        curdir = os.path.abspath(os.getcwd())
        os.chdir(optpath)
        Main.include("courses_requested.jl")
        os.chdir(curdir)
    
    newWindow = Toplevel(root)
    newWindow.title("Select Course for available TA")
    
    Label(newWindow, text="Select Course for available TA").grid(row=0,column=0,sticky='w')
    courseData2 = pd.read_csv(savedir+"course_dataset.csv")
    courseList2 =[]
    courseClicked2 = StringVar()
    courseClicked2.set("")
    for i in courseData2.index:
        if courseData2.loc[i,"ta_needed"] == 1:
            courseString2 = courseData2.loc[i,"course_number"] + " - " + courseData2.loc[i,"course_name"]
            courseList2.append(courseString2)

    courseDrop2 = OptionMenu(newWindow, courseClicked2, *courseList2)
    courseDrop2.grid(row=1,column=0,sticky='w')
    
    resultsButton=Button(newWindow,text="See Students who have this course as a preference and are available.",command=lambda: listTAs(savedir, courseClicked2))
    Label(newWindow,text=" ").grid(row=2,column=0)
    resultsButton.grid(row=3,column=0,sticky='w')

def viewTAAssignment(taData, taClicked):

    # possibly add preference info
    newWindow = Toplevel(root)
    taname = taClicked.get()
    
    Label(newWindow,text=taname).grid(row=0,column=0)
    for i in taData.index:
        if taname == taData.loc[i,"name"]:
            count = 0
            if str(taData.loc[i,"assignment"]) == "nan":
                Label(newWindow,text="No assignment has been made.").grid(row=1,column=0,sticky='w')
            elif type(taData.loc[i,"assignment"]) == str:
                courses = taData.loc[i,"assignment"]
                courses = courses.lstrip('[')
                courses = courses.rstrip(']')
                courses = courses.split(',')
                for course in courses:
                    course = course.strip(" ")
                    course = course.strip("'")
                    count+=1
                    Label(newWindow,text=course).grid(row=count,column=0,sticky='w')
            else:
                for course in taData.loc[i,"assignment"]:
                    count+=1
                    Label(newWindow,text=course).grid(row=count,column=0,sticky='w')
                    
                    
def viewCourseAssignment(courseData, courseClicked):

    # possibly add preference info
    newWindow = Toplevel(root)
    coursename = courseClicked.get()
    
    Label(newWindow,text=coursename).grid(row=0,column=0)
    for i in courseData.index:
        if courseData.loc[i,"course_number"] in coursename:
            count = 0
            if str(courseData.loc[i,"ta_assigned"]) == "nan":
                Label(newWindow,text="No assignment has been made.").grid(row=1,column=0,sticky='w')
            else:
                count+=1
                Label(newWindow,text=courseData.loc[i,"ta_assigned"]).grid(row=count,column=0,sticky='w')

            
def checkToAssign(savedir):
    for widgets in second_frame.winfo_children():
        widgets.destroy()
    assign(savedir)

def checkAssignments(savedir):

    taData = pd.read_csv(savedir+"ta_dataset.csv")
    courseData = pd.read_csv(savedir+"course_dataset.csv")
    
    # be careful if TA/Course is already assigned
    taList = taData["name"].tolist()
    taList.sort()
    
    courseList = ["Intentionally left unassigned"]
    for i in courseData.index:
        if courseData.loc[i,"ta_needed"] == 1:
            courseString = courseData.loc[i,"course_number"] + " - " + courseData.loc[i,"course_name"]
            courseList.append(courseString)
    
    taClicked = StringVar()
    taClicked.set("")
    courseClicked = StringVar()
    courseClicked.set("")
    Label(second_frame, text="Check assignment for this TA:").grid(row=0,column=0,sticky='w')
    taDrop = OptionMenu(second_frame, taClicked, *taList)
    taDrop.grid(row=1,column=0,sticky='w')
    taButton = Button(second_frame, text="View TA Assignment.",command=lambda: viewTAAssignment(taData, taClicked))
    taButton.grid(row=2,column=0,sticky='w')
    Label(second_frame, text="Check assignment for this course:").grid(row=3,column=0,sticky='w')
    courseDrop = OptionMenu(second_frame, courseClicked, *courseList)
    courseDrop.grid(row=4,column=0,sticky='w')
    courseButton = Button(second_frame, text="View Course Assignment.",command=lambda: viewCourseAssignment(courseData, courseClicked))
    courseButton.grid(row=5,column=0,sticky='w')
    Label(second_frame, text="").grid(row=6,column=0)
    backButton = Button(second_frame, text = "Change assignments (back to previous page)", command=lambda: checkToAssign(savedir))
    backButton.grid(row=7,column=0,sticky='w')

def assignToCheck(savedir):
    for widgets in second_frame.winfo_children():
        widgets.destroy()
    checkAssignments(savedir)
    
def assignToCourse(savedir):
    for widgets in second_frame.winfo_children():
        widgets.destroy()
    viewCourseFunction(savedir)       
    
def assign(savedir):

    taData = pd.read_csv(savedir+"ta_dataset.csv")
    courseData = pd.read_csv(savedir+"course_dataset.csv")
    
    # be careful if TA/Course is already assigned
    taList = taData["name"].tolist()
    taList.sort()
    
    courseList = ["Intentionally left unassigned"]
    for i in courseData.index:
        if courseData.loc[i,"ta_needed"] == 1:
            courseString = courseData.loc[i,"course_number"] + " - " + courseData.loc[i,"course_name"]
            courseList.append(courseString)
    
    taClicked = StringVar()
    taClicked.set("")
    courseClicked = StringVar()
    courseClicked.set("")
    Label(second_frame, text="Assign this TA:").grid(row=0,column=0,sticky='w')
    taDrop = OptionMenu(second_frame, taClicked, *taList)
    taDrop.grid(row=1,column=0,sticky='w')
    Label(second_frame, text="to this course:").grid(row=2,column=0,sticky='w')
    Label(second_frame, text="NOTE: If you wish to exclude the TA from the optimization (e.g. for grading), select 'Intentionally left unassigned'").grid(row=3,column=0,sticky='w')
    courseDrop = OptionMenu(second_frame, courseClicked, *courseList)
    courseDrop.grid(row=4,column=0,sticky='w')
    
    myButton = Button(second_frame, text="Assign TA to Course", command=lambda: assignTAToCourse(savedir, taData, courseData, taClicked, courseClicked))
    myButton.grid(row=5,column=0,sticky='w')
    Label(second_frame, text= " ").grid(row=6,column=0,sticky='w')
    Label(second_frame, text= " ").grid(row=7,column=0,sticky='w')
    
    # Adding button here
    Label(second_frame, text = " ").grid(row=8,column=0,sticky='w')
    courseButton =Button(second_frame,text="Search TA availability by Course (may take a while to load when clicked)", command=lambda: courseTASearch(savedir, courseData))
    courseButton.grid(row=9,column=0,sticky='w')
    Label(second_frame, text=" ").grid(row=10,column=0,sticky='w')
    STRUCTURE = [
    ("Light (courses 0100-1120 and 3000+ full load, 1340-1860 1/2 load)",1),
    ("Moderate (1120 now 1/2 load, 1340-1550 1/3 load compared to 'Light')",2),
    ("Heavy (3000-4000 now 1/2 compared to 'Moderate')",3),
    ("Last Resort (1560-1860 now 1/3 load and 5000+ now 1/2 load compared to 'Heavy')",4)]


    workload_id = IntVar()

    count=0
    for text, val in STRUCTURE:
        count+=1
        Radiobutton(second_frame, text=text, variable=workload_id, value=val).grid(row=10+count,column=0,sticky='w')#, command=lambda: clicked(r.get())).pack()
        
    optimizeButton = Button(second_frame, text="Run optimization...This may take a few minutes (check command line)", command=lambda: optimize(savedir, workload_id.get()))
    optimizeButton.grid(row=15,column=0,sticky='w')
    Label(second_frame, text="").grid(row=16,column=0,sticky='w')
    Label(second_frame, text="").grid(row=17,column=0,sticky='w')
    summaryButton = Button(second_frame, text="View Assignments by Individual Course/Student",command=lambda: assignToCheck(savedir))
    summaryButton.grid(row=18,column=0,sticky='w')
    Label(second_frame, text="").grid(row=19,column=0,sticky='w')
    backButton = Button(second_frame, text="Back to Course Assignment Selection", command=lambda: assignToCourse(savedir))
    backButton.grid(row=20,column=0,sticky='w')


def viewCoursetoAssign(savedir):
    for widgets in second_frame.winfo_children():
      widgets.destroy()
    assign(savedir)
    

def viewCourseFunction_2(my_scrollbar_3,my_canvas_3, second_frame_3,savedir, courseUpdateText, submit):

    courseData = pd.read_csv(savedir+"course_dataset.csv")
    checkBoxDict = {}
    for i in courseData.index:
        checkBoxDict[i] = tk.IntVar(value=courseData.loc[i,"ta_needed"])
        courseNumber = courseData.loc[i,"course_number"]
        courseName = courseData.loc[i,"course_name"] 
        checkButtonText = courseNumber + " - " + courseName
        tk.Checkbutton(second_frame_3, text=checkButtonText, variable=checkBoxDict[i]).pack(anchor='w')
    
    submit.config(command=lambda: updateTaughtCourses(my_scrollbar_3,my_canvas_3, second_frame_3, courseData, savedir, checkBoxDict, submit))
    count = 1
    for update in courseUpdateText:
        Label(second_frame, text=update).grid(row=3+count,column=0,sticky='w')
        count += 1

def updateTaughtCourses(my_scrollbar_3,my_canvas_3, second_frame_3, courseData, savedir, checkBoxDict, submit):
    courseUpdateText = []
    for i in courseData.index:
        if courseData.loc[i, "ta_needed"] == 1 and checkBoxDict[i].get() == 0:
            courseData.loc[i, "ta_needed"] = 0
            courseNumber = courseData.loc[i,"course_number"]
            courseName = courseData.loc[i,"course_name"] 
            checkButtonText = courseNumber + " - " + courseName
            courseUpdateText.append(checkButtonText + " will no longer be taught by a TA.")
            #Label(viewCourse, text = checkButtonText + " will no longer be taught by a TA.                             ").pack()
        elif courseData.loc[i, "ta_needed"] == 0 and checkBoxDict[i].get() == 1:
            courseData.loc[i, "ta_needed"] = 1
            courseNumber = courseData.loc[i,"course_number"]
            courseName = courseData.loc[i,"course_name"] 
            checkButtonText = courseNumber + " - " + courseName
            courseUpdateText.append(checkButtonText + " will now be taught by a TA.")
            #Label(viewCourse, text = checkButtonText + " will now be taught by a TA.                                   ").pack()
    
    courseData.to_csv(savedir + "course_dataset.csv",index=False)
    
    for widgets in second_frame_3.winfo_children():
      widgets.destroy()
    
    viewCourseFunction_2(my_scrollbar_3,my_canvas_3, second_frame_3,savedir, courseUpdateText, submit)
    #viewCourse.destroy()
    


def viewCourseFunction(savedir):
    
    ### start scrollbar here
    #main_frame_2 = Frame(second_frame).grid(row=0,column=0,ipadx=640,sticky='nw')
    #create a canvas
    my_canvas_3 = Canvas(second_frame)
    my_canvas_3.grid(row=0,column=0,sticky='w')
    #main_frame_2.pack(fill=BOTH, expand=1)
    #my_canvas_2.pack(side=LEFT, fill=BOTH, expand=1)
    #my_canvas_2.config(bg='green')
    
    # add a scrollbar to the canvas
    my_scrollbar_3 = ttk.Scrollbar(second_frame, orient=VERTICAL, command=my_canvas_3.yview)
    # this needs to change...
    my_scrollbar_3.grid(row=0,column=1, ipady=135)
    
    #my_scrollbar_2.pack(side=RIGHT, fill=Y)
    
    # configure the canvas
    my_canvas_3.configure(yscrollcommand=my_scrollbar_3.set)
    my_canvas_3.bind('<Configure>', lambda e: my_canvas_3.configure(scrollregion=my_canvas_3.bbox("all")))
    
    # create another frame inside the canvas
    second_frame_3 = Frame(my_canvas_3)#.grid(row=0,column=0,ipadx=640,sticky='nw')
    
    #add that new frame to a window in the canvas
    my_canvas_3.create_window((0,0), window=second_frame_3, anchor="nw")
    ### end scroll bar here. make sure to add items to "second_frame"
    
    courseData = pd.read_csv(savedir+"course_dataset.csv")
    checkBoxDict = {}
    for i in courseData.index:
        checkBoxDict[i] = tk.IntVar(value=courseData.loc[i,"ta_needed"])
        courseNumber = courseData.loc[i,"course_number"]
        courseName = courseData.loc[i,"course_name"] 
        checkButtonText = courseNumber + " - " + courseName
        tk.Checkbutton(second_frame_3, text=checkButtonText, variable=checkBoxDict[i]).pack(anchor='w')
        
    submit = Button(second_frame, text="Make checked courses those to be taught by TAs", command=lambda: updateTaughtCourses(my_scrollbar_3,my_canvas_3, second_frame_3, courseData, savedir, checkBoxDict, submit))
    submit.grid(row=1,column=0,sticky='w')
    nextWindow = Button(second_frame, text="Move on to next step", command=lambda: viewCoursetoAssign(savedir)).grid(row=2,column=0,sticky='w')
    Label(second_frame, text=" ").grid(row=3,column=0,ipadx=310)#.pack(anchor='sw')


def cleanCourseData(savedir):
    data = pd.read_csv(savedir+"courses_scraped.csv")

    data["days1"] = np.NaN
    data["times1"] = np.NaN
    data["days2"] = np.NaN
    data["times2"] = np.NaN

    # if a course has two day-times (e.g. MATH:1005 in sp22), the day-times need to be split

    for ind in data.index:
        if '+' in str(data.loc[ind,"days"]):
            twodays = data.loc[ind,"days"].split('+')
            data.loc[ind, "days1"] = twodays[0]
            data.loc[ind, "days2"] = twodays[1]
        else:
            data.loc[ind, "days1"] = data.loc[ind, "days"]
        if '+' in str(data.loc[ind,"times"]):
            twotimes = data.loc[ind,"times"].split('+')
            data.loc[ind, "times1"] = twotimes[0]
            data.loc[ind, "times2"] = twotimes[1]
        else:
            data.loc[ind, "times1"] = data.loc[ind, "times"]
            
    data = data.drop(["times", "days"], axis=1)

    data["ta_assigned"] = ""
    data["ta_needed"] = 0
    
    data["workload_1"] = 1.0
    data["workload_2"] = 1.0
    data["workload_3"] = 1.0
    data["workload_4"] = 1.0
    
    #hard coding "cross-listed" discussions for Fall
    #index_drop = [];
    for i in data.index:
        course_number = int(data.loc[i,"course_number"][5:9])
        section_number = str(data.loc[i,"course_number"][10:14])
        if course_number == 3770 and section_number == "0C03":
            data.loc[i,"course_number"] = "MATH:3770:0C03/MATH:4010:0A01"
            data.loc[i,"course_name"] = "Fundamental Properties Spaces/Funct  I/Basic Analysis"
        #if course_number == 4010 and section_number == "0A01":
            #index_drop.append(i)
        #if course_number == 4090 and section_number == "0A01":
        #    data.loc[i,"course_number"] = "MATH:4090:0A01/MATH:5000:0A01"
        #    data.loc[i,"course_name"] = "A Rigorous Intro to Abstract Algebra/Abstract Algebra I"
        if course_number == 5000 and section_number == "0A01":
            data.loc[i,"course_number"] = "MATH:5000:0A01/MATH:4090:0A01"
            data.loc[i,"course_name"] = "Abstract Algebra I/A Rigorous Intro to Abstract Algebra"
            #index_drop.append(i)
    #data = data.drop(index_drop)
    
    # ta_needed is to be used to suggest the courses to assign TAs, which can be turned off/on by DGS
    # suggestions are based on the course number being <2000 or between 3600,6000 strictly,
    # as well as if "Primary Instructor" is NOT listed and if the section number ends in a number
    for i in data.index:
        course_number = int(data.loc[i,"course_number"][5:9])
        if course_number < 2000 or (course_number > 3600 and course_number < 4000) or (course_number >= 5000 and course_number < 6000):
            if (not "Primary Instructor" in str(data.loc[i, "instructors"])) and data.loc[i,"course_number"][-1].isnumeric():
                data.loc[i,"ta_needed"] = 1
        if course_number < 1120:
            data.loc[i,"workload_1"] = 1
            data.loc[i,"workload_2"] = 1
            data.loc[i,"workload_3"] = 1
            data.loc[i,"workload_4"] = 1
        elif course_number == 1120:
            data.loc[i,"workload_1"] = 1
            data.loc[i,"workload_2"] = 0.5
            data.loc[i,"workload_3"] = 0.5
            data.loc[i,"workload_4"] = 0.5
        elif course_number < 1560:
            data.loc[i,"workload_1"] = 0.5
            data.loc[i,"workload_2"] = 0.3333
            data.loc[i,"workload_3"] = 0.3333
            data.loc[i,"workload_4"] = 0.3333
        elif course_number < 1861:
            data.loc[i,"workload_1"] = 0.5
            data.loc[i,"workload_2"] = 0.5
            data.loc[i,"workload_3"] = 0.5
            data.loc[i,"workload_4"] = 0.3333
        elif course_number < 5000:
            data.loc[i,"workload_1"] = 1
            data.loc[i,"workload_2"] = 1
            data.loc[i,"workload_3"] = 0.5
            data.loc[i,"workload_4"] = 0.5
        elif course_number < 6000:
            data.loc[i,"workload_1"] = 1
            data.loc[i,"workload_2"] = 1
            data.loc[i,"workload_3"] = 1
            data.loc[i,"workload_4"] = 0.5
                
    data = data.rename(columns = {"instructors":"course_supervisor(s)"})

    data.to_csv(savedir+"course_dataset.csv",index=False)

def scrapeCourseData(savedir, url):
    with open(savedir+'courses_scraped.csv', 'w') as f:
        sys.stdout = f # Change the standard output to the file we created.
        print("course_number,course_name,times,days,instructors")
        
        for i in range(len(url)):
            req=requests.get(url[i])
            content=req.content

            soup=BeautifulSoup(content, "html.parser")
            results = soup.find(id = "search-result")
            courses = results.find_all("tr", class_=["odd", "even"])
            for course in courses:
                course_id = course.find("a", class_="text-underline")
                name = course.find("strong")
                time = course.find_all("span", class_="text-info")
                days = course.find_all("span", class_="text-danger")
                instructors = course.find("div", class_="instructors")
                if len(time) > 1:
                    if len(str(time[1].text)) < 25:
                        timeall = str(time[0].text+"+"+time[1].text)
                    else:
                        timeall = str(time[0].text)
                elif len(time) == 1:
                    timeall = str(time[0].text)
                else:
                    timeall = 'NA'
                if len(days) > 1:
                    if len(str(days[1].text)) < 8:
                        daysall = str(days[0].text+"+"+days[1].text)
                    else:
                        daysall = str(days[0].text)
                elif len(days) == 1:
                    daysall = str(days[0].text)
                else:
                    daysall = 'NA'
                if not(str(type(instructors)) == '<class \'NoneType\'>'):
                    instructors_short = instructors.text.replace("\r","")
                    instructors_short = instructors_short.replace("\n","")
                    instructors_short = instructors_short.replace("  ","")
                else:
                    instructors_short = 'NA'

                print(course_id.text+","+name.text+","+timeall+","+daysall+","+'"'+instructors_short + '"')

        sys.stdout = original_stdout # Reset the standard output to its original value

def createCourseData(savedir, entry1, entry2, entry3, entry4, entry5):
    url = []
    if not entry1.get() == "":
        url.append(entry1.get())
    if not entry2.get() == "":
        url.append(entry2.get())
    if not entry3.get() == "":
        url.append(entry3.get())
    if not entry4.get() == "":
        url.append(entry4.get())
    if not entry5.get() == "":
        url.append(entry5.get())
    
    Label(second_frame, text = "Scraping...").grid(row=13,column=0,sticky='w')
    scrapeCourseData(savedir, url)
    Label(second_frame, text = "...Cleaning...").grid(row=14,column=0,sticky='w')
    cleanCourseData(savedir)
    Label(second_frame, text = "Done!").grid(row=15,column=0,sticky='w')

def loadCourseToViewCourse(savedir):
    for widgets in second_frame.winfo_children():
      widgets.destroy()
    viewCourseFunction(savedir)

def loadCourseFunction(savedir):
    
    Label(second_frame, text="Enter in URLs from MyUI for search results of ALL math courses below.").grid(row=0,column=0,sticky='w')
    Label(second_frame, text="URL 1: ").grid(row=1,column=0,sticky='w')
    entry1 = Entry(second_frame, width=100, borderwidth=5)
    entry1.grid(row=2,column=0,sticky='w')
    
    Label(second_frame, text="URL 2: ").grid(row=3,column=0,sticky='w')
    entry2 = Entry(second_frame, width=100, borderwidth=5)
    entry2.grid(row=4,column=0,sticky='w')
    
    Label(second_frame, text="URL 3: ").grid(row=5,column=0,sticky='w')
    entry3 = Entry(second_frame, width=100, borderwidth=5)
    entry3.grid(row=6,column=0,sticky='w')
    
    Label(second_frame, text="URL 4: ").grid(row=7,column=0,sticky='w')
    entry4 = Entry(second_frame, width=100, borderwidth=5)
    entry4.grid(row=8,column=0,sticky='w')
    
    Label(second_frame, text="URL 5: ").grid(row=9,column=0,sticky='w')
    entry5 = Entry(second_frame, width=100, borderwidth=5)
    entry5.grid(row=10,column=0,sticky='w')
    
    addURL = Button(second_frame, text="Add URLs and create course dataset", command=lambda: createCourseData(savedir, entry1, entry2, entry3, entry4, entry5))
    addURL.grid(row=11,column=0,sticky='w')
    nextButton = Button(second_frame, text="Next", command=lambda: loadCourseToViewCourse(savedir))
    nextButton.grid(row=12,column=0,sticky='w')

def DeleteTAToLoadCourse(savedir):
    for widgets in second_frame.winfo_children():
      widgets.destroy()
    loadCourseFunction(savedir)
    
    
def viewTASelection_2(my_scrollbar_2,my_canvas_2, second_frame_2, savedir, submit):

    TAData = pd.read_csv(savedir+"ta_dataset.csv")
    TAData["delete_row"] = 0
    checkBoxDict = {}
    checkBoxButton = {}
    count=0
    for i in TAData.index:
        checkBoxDict[i] = tk.IntVar()
        TAName = TAData.loc[i,"name"]
        tk.Checkbutton(second_frame_2, text=TAName, variable=checkBoxDict[i]).pack(anchor='w')#.grid(row=count,column=0,sticky='nw')
        count+=1
        
    submit.configure(command =lambda: deleteTAs(my_scrollbar_2, my_canvas_2, second_frame_2, TAData, savedir, checkBoxDict, submit))#.grid(row=3,column=0,sticky='sw')#.pack(anchor='sw')

        
    
    
def TAToViewDeleteTA_2(my_scrollbar_2,my_canvas_2, second_frame_2, savedir, submit):
    for widgets in second_frame_2.winfo_children():
        widgets.destroy()
    #second_frame_2.destroy()
    #my_scrollbar_2.destroy()
    #my_canvas_2.destroy()
    #for widgets in second_frame.winfo_children():
    #  widgets.destroy()
    
    viewTASelection_2(my_scrollbar_2,my_canvas_2, second_frame_2, savedir, submit)
    
def deleteTAs(my_scrollbar_2, my_canvas_2, second_frame_2, TAData, savedir, checkBoxDict, submit):
    for i in TAData.index:
        TAData.loc[i,"delete_row"] = checkBoxDict[i].get()
    
    deleteIndex = (TAData["delete_row"] == 0)
    #Label(second_frame, text=str(deleteIndex)).pack()
    TAData = TAData[deleteIndex]
    TAData.to_csv(savedir + "ta_dataset.csv",index=False)
    
    TAToViewDeleteTA_2(my_scrollbar_2, my_canvas_2, second_frame_2, savedir, submit)
    


def viewTASelection(savedir):


    ### start scrollbar here
    #main_frame_2 = Frame(second_frame).grid(row=0,column=0,ipadx=640,sticky='nw')
    #create a canvas
    my_canvas_2 = Canvas(second_frame)
    my_canvas_2.grid(row=0,column=0,sticky='w')
    #main_frame_2.pack(fill=BOTH, expand=1)
    #my_canvas_2.pack(side=LEFT, fill=BOTH, expand=1)
    #my_canvas_2.config(bg='green')
    
    # add a scrollbar to the canvas
    my_scrollbar_2 = ttk.Scrollbar(second_frame, orient=VERTICAL, command=my_canvas_2.yview)
    # this needs to change...
    my_scrollbar_2.grid(row=0,column=1, ipady=135)
    
    #my_scrollbar_2.pack(side=RIGHT, fill=Y)
    
    # configure the canvas
    my_canvas_2.configure(yscrollcommand=my_scrollbar_2.set)
    my_canvas_2.bind('<Configure>', lambda e: my_canvas_2.configure(scrollregion=my_canvas_2.bbox("all")))
    
    # create another frame inside the canvas
    second_frame_2 = Frame(my_canvas_2)#.grid(row=0,column=0,ipadx=640,sticky='nw')
    
    #add that new frame to a window in the canvas
    my_canvas_2.create_window((0,0), window=second_frame_2, anchor="nw")
    ### end scroll bar here. make sure to add items to "second_frame"
    
    Label(second_frame, text = "Review the TAs. If any look incorrect, or if there are duplicates, check the listing and click 'Delete checked TAs'").grid(row=1,column=0,sticky='sw')#.pack(anchor='sw')
    Label(second_frame, text = "to remove them. Click 'Move on to next step' to move on. ").grid(row=2,column=0,sticky='sw')#.pack(anchor='sw')
    submit = Button(second_frame, text="Delete checked TAs", command=lambda: deleteTAs(my_scrollbar_2, my_canvas_2, second_frame_2, TAData, savedir, checkBoxDict, submit))
    submit.grid(row=3,column=0,sticky='sw')#.pack(anchor='sw')
    nextWindow = Button(second_frame, text="Move on to next step (do not delete listed TAs)", command=lambda: DeleteTAToLoadCourse(savedir))
    nextWindow.grid(row=4,column=0,sticky='sw')#.pack(anchor='sw')
    Label(second_frame, text=" ").grid(row=5,column=0,ipadx=310)#.pack(anchor='sw')
    

    TAData = pd.read_csv(savedir+"ta_dataset.csv")
    TAData["delete_row"] = 0
    checkBoxDict = {}
    checkBoxButton = {}
    count=0
    for i in TAData.index:
        checkBoxDict[i] = tk.IntVar()
        TAName = TAData.loc[i,"name"]
        tk.Checkbutton(second_frame_2, text=TAName, variable=checkBoxDict[i]).pack(anchor='w')#.grid(row=count,column=0,sticky='nw')
        count+=1
        
def alphabetizeData(filename, savedir): 
    ta_list = pd.read_csv(filename)
    data = pd.read_csv(savedir + "ta_dataset.csv")
    
    ta_list = ta_list.dropna(subset=["Name"])
    ta_list = ta_list.sort_values("Name").reset_index(drop=True)
    for i in range(len(ta_list)):
        ta_list.loc[i,"Name"] = ta_list.loc[i,"Name"].lstrip()
    ta_list = ta_list.sort_values("Name")

    ta_list = ta_list.dropna(subset=["Name"])
    ta_list = ta_list.sort_values("Name").reset_index(drop=True)
    for i in range(len(ta_list)):
        ta_list.loc[i,"Name"] = ta_list.loc[i,"Name"].lstrip()
    ta_list = ta_list.sort_values("Name")
    
    data["new_name"] = np.nan
    ta_list["found"] = 0
    
    ta_list["Last Name"] = "temp"
    for i in ta_list.index:
        ta_list.loc[i,"Last Name"] = ta_list.loc[i,"Name"].split(",")[0]
        
    for i in ta_list.index:
        ta_last = ta_list.loc[i,"Last Name"].lower()
        ta_last_words = ta_last.split(" ")
        for j in data.index:
            ta_given = data.loc[j,"name"].lower()
            ta_given_words = ta_given.split(" ")
            found = 0
            for ta_last_word in ta_last_words:
                if found == 1:
                    break
                for ta_given_word in ta_given_words:
                    if ta_last_word == ta_given_word:
                        #print(ta_last + " ... " + ta_given)
                        found = 1
                        ta_list.loc[i,"found"] += 1
                        # add all adjustments here
                        if ta_list.loc[i,"found"] == 1:
                            data.loc[j,"new_name"] = ta_list.loc[i,"Name"]
                        elif ta_list.loc[i,"found"] > 1:
                            data.loc[j,"new_name"] = str(ta_list.loc[i,"Name"] + " (" + str(ta_list.loc[i,"found"]) + ")")
                        break
                        
    data = data.rename(columns = {"name":"old_name"})
    col_to_move = data.pop("new_name")
    data.insert(0, "new_name", col_to_move)
    data = data.rename(columns = {"new_name":"name"})
    data = data.sort_values("name")
    
    newWindow = Toplevel(root)
    newWindow.title("TA warnings!")
    Label(newWindow, text="Warnings regarding listed TAs and those filling out the survey appear below.").pack(anchor='w')
    Label(newWindow, text="If no warnings appear, that means there are no issues, and you can close the window.").pack(anchor='w')
    Label(newWindow, text="Please make note of any warnings before closing this window.").pack(anchor='w')
    Label(newWindow, text=" ").pack(anchor='w')
    for i in ta_list.index:
        if ta_list.loc[i,"found"] == 0:
            Label(newWindow, text="Warning: " + ta_list.loc[i,"Name"] + " not found in survey data creating entry with no preferences/assuming unavailable many days.").pack(anchor='w')
            #data = data.append({"name":ta_list.loc[i,"Name"], "year_in_program":ta_list.loc[i,"Year"]}, ignore_index=True)
            data = pd.concat([data, pd.DataFrame.from_records([{"name":ta_list.loc[i,"Name"], "year_in_program":ta_list.loc[i,"Year"]}])], ignore_index=True)
            #data = data.concat({"name":ta_list.loc[i,"Name"], "year_in_program":ta_list.loc[i,"Year"]}, ignore_index=True)
        elif ta_list.loc[i,"found"] > 1:
            Label(newWindow, text="Warning: " + ta_list.loc[i,"Name"] + " found in survey data " + str(ta_list.loc[i,"found"]) + " times.").pack(anchor='w')
        
        data = data.sort_values("name")
    for j in data.index:
        if str(data.loc[j,"name"]) == "nan":
            data.loc[j,"name"] = data.loc[j,"old_name"]
            Label(newWindow,text="Warning: " + data.loc[j,"old_name"] + " appears in survey respondants but not TA List. Kept in data set and stored at end.").pack(anchor='w')
            
            
    data.to_csv(savedir + "ta_dataset.csv", index = False)
    

def alphabetizeTAtoDeleteTA(savedir):
    for widgets in second_frame.winfo_children():
      widgets.destroy()

    viewTASelection(savedir)

def loadAndAlphabetizeFunction(savedir):
    filename = filedialog.askopenfilename(title="Select a File", filetypes=[("csv files","*.csv")])
    alphabetizeData(filename, savedir)
    Label(second_frame, text="Done!").grid(row=6,column=0,sticky='w')
    
def alphabetizeTA(savedir):
    Label(second_frame, text="Now load in the TA list of old and new TAs.").grid(row=0,column=0,sticky='w')
    Label(second_frame, text="Make sure you are loading in a CSV file (convert excel to csv before uploading.").grid(row=1,column=0,sticky='w')
    Label(second_frame, text="Click the button below to add the file.").grid(row=2,column=0,sticky='w')
    
    backButton = Button(second_frame, text="Go back", command=newProject).grid(row=4,column=0,sticky='w')
    nextButton = Button(second_frame, text="Next", command=lambda: alphabetizeTAtoDeleteTA(savedir)).grid(row=5,column=0,sticky='w')
    
    loadTAButton = Button(second_frame, text="alphabetize TAs",command=lambda: loadAndAlphabetizeFunction(savedir)).grid(row=3,column=0,sticky='w')
    
def TAToAlphabetizeTA(savedir):
    for widgets in second_frame.winfo_children():
      widgets.destroy()

    alphabetizeTA(savedir)

def TAToViewDeleteTA(savedir):
    for widgets in second_frame.winfo_children():
      widgets.destroy()

    viewTASelection(savedir)

def cleanTAData(rawFile, saveDir):
    # the name will be selected by the user in the GUI
    data = pd.read_csv(rawFile)

    # drop first two rows
    data = data.drop(data.index[0])
    data = data.drop(data.index[0])

    for col in data.columns:
        if col[0] != 'Q':
            data = data.drop(col, axis=1)

    colchange= {
        "Q1" : "name",
        "Q2" : "email",
        "Q3" : "year_in_program",
        "Q4" : "hard_courses_taught",
        "Q5_1" : "07:30_09:30_pref",
        "Q5_2" : "09:30_11:30_pref",
        "Q5_3" : "12:00_14:00_pref",
        "Q5_4" : "14:00_16:00_pref",
        "Q5_5" : "16:00_23:59_pref",
        "Q6_1" : "1_course_pref",
        "Q6_2" : "2_course_pref",
        "Q6_3" : "3_course_pref",
        "Q6_4" : "4_course_pref",
        "Q6_5" : "5_course_pref",
        "Q7" : "time_course_pref",
        "Q8_1" : "07:30_08:20_unavail_days",
        "Q8_2" : "08:30_09:20_unavail_days",
        "Q8_3" : "09:30_10:20_unavail_days",
        "Q8_4" : "10:30_11:20_unavail_days",
        "Q8_5" : "11:00_11:50_unavail_days",
        "Q8_6" : "11:30_12:20_unavail_days",
        "Q8_7" : "12:30_13:20_unavail_days",
        "Q8_8" : "13:30_14:20_unavail_days",
        "Q8_9" : "14:00_14:50_unavail_days",
        "Q8_10" : "14:30_15:20_unavail_days",
        "Q8_11" : "15:30_16:20_unavail_days",
        "Q8_12" : "16:30_23:59_unavail_days",
        "Q9_1" : "gradmath_courses",
        "Q10" : "other_courses",
        "Q11" : "overload",
        "Q12" : "mathlab_or_grading",
        "Q13" : "comment"
    }

    data = data.rename(columns = colchange)

    data.insert(2, "assignment", "")

    for idx in data["year_in_program"].index:
        if data.loc[idx, "year_in_program"] == "7+":
            data.loc[idx, "year_in_program"] = 7
        else:
            data.loc[idx, "year_in_program"] = int(data.loc[idx, "year_in_program"])
        
    # this will likely be customizable, as well.
    data.to_csv(saveDir + "ta_dataset.csv",index=False)


def loadTAFunction(savedir):
    filename = filedialog.askopenfilename(title="Select a File", filetypes=[("csv files","*.csv")])
    cleanTAData(filename, savedir)
    Label(second_frame, text="Done!").grid(row=6,column=0,sticky='w')

def newTAFileFunction(savedir):
    Label(second_frame, text="First load in the TA survey results from qualtrics.").grid(row=0,column=0,sticky='w')
    Label(second_frame, text="Make sure you are loading in the full CSV file.").grid(row=1,column=0,sticky='w')
    Label(second_frame, text="Click the button below to add the file.").grid(row=2,column=0,sticky='w')
    
    loadTAButton = Button(second_frame, text="Load and clean TA survey results",command=lambda: loadTAFunction(savedir)).grid(row=3,column=0,sticky='w')
    backButton = Button(second_frame, text="Go back", command=newProject).grid(row=4,column=0,sticky='w')
    #find a way to disable until loadTAButton is loaded
    #nextButton = Button(second_frame, text="Next", command=lambda: TAToViewDeleteTA(savedir)).grid(row=5,column=0,sticky='w')
    nextButton = Button(second_frame, text="Next", command=lambda: TAToAlphabetizeTA(savedir)).grid(row=5,column=0,sticky='w')


def backToMain():
    for widgets in second_frame.winfo_children():
      widgets.destroy()
    newProjectButton = Button(second_frame, text="New Project", command=newProject).pack()

def saveDirectory(savedir,optpath):
    with open(optpath+'optimization_parameters.csv', 'w') as f:
        sys.stdout = f # Change the standard output to the file we created.
        print("parameter,value")
        print("directory," + savedir)
        #print("workload_id," + str(value))
        
        sys.stdout = original_stdout


def existingProjectFunction():
    global savedir
    savedir = filedialog.askdirectory(title='Select folder that contains data')+'/'
    for widgets in second_frame.winfo_children():
        widgets.destroy()
        
    assign(savedir)

def process_files():
    path = filedialog.askdirectory(title='Select folder to save results')
    global savedir
    savedir = path+"/ta_assignment_project/"
    # add if statement if this is already made
    os.makedirs(savedir)
    optpath = sys.argv[0].rstrip("ta_assignment.py")
    saveDirectory(savedir,optpath)
    Label(second_frame, text="Project directory created!").grid(row=4,column=0,sticky='w')
    Label(second_frame, text=savedir).grid(row=5,column=0,sticky='w')
    
def projectToTA(savedir):
    for widgets in second_frame.winfo_children():
      widgets.destroy()
    newTAFileFunction(savedir)
   
def newProject():
    for widgets in second_frame.winfo_children():
      widgets.destroy()
      
    #second_frame.columnconfigure(0, weight=1)
    #second_frame.columnconfigure(1, weight=1)
    instructions = Label(second_frame, text="Click the 'Choose Directory' button to choose a directory in which the files will be saved.")
    instructions.grid(row=0,column=0,sticky='w')
    
    newProjectDirectoryButton = Button(second_frame, text="Choose Directory",command=lambda: process_files()).grid(row=1,column=0,sticky='w')
    backButton = Button(second_frame, text="Go back", command=backToMain).grid(row=2,column=0,sticky='w')
    nextButton = Button(second_frame, text="Next", command=lambda: projectToTA(savedir)).grid(row=3,column=0,sticky='w')
    


# main window

root = Tk()
root.title("TA Assignment")
root.geometry("650x500")


### start scrollbar here
main_frame = Frame(root)
#create a canvas
my_canvas = Canvas(main_frame)
main_frame.pack(fill=BOTH, expand=1)
my_canvas.pack(side=LEFT, fill=BOTH, expand=1)

# add a scrollbar to the canvas
#my_scrollbar = ttk.Scrollbar(main_frame, orient=VERTICAL, command=my_canvas.yview)
#my_scrollbar.pack(side=RIGHT, fill=Y)

# configure the canvas
#my_canvas.configure(yscrollcommand=my_scrollbar.set)
#my_canvas.bind('<Configure>', lambda e: my_canvas.configure(scrollregion=my_canvas.bbox("all")))

# create another frame inside the canvas
second_frame = Frame(my_canvas)

#add that new frame to a window in the canvas
my_canvas.create_window((0,0), window=second_frame, anchor="nw")
### end scroll bar here. make sure to add items to "second_frame"


# buttons
#newProjectButton = Button(root, text="New Project", command=newTAFileFunction)
newProjectButton = Button(second_frame, text="New Project", command=newProject)#, command=newProjectDirectoryFunction)
existingProjectButton = Button(second_frame, text="Existing Project (select 'ta_assignment_project' directory)", command=existingProjectFunction)



# layout
Label(second_frame, text="If starting a new project click the 'New Project' Button below.").grid(row=0,column=0,sticky='w')
Label(second_frame, text="Otherwise, if you have started a project, clicke 'Existing Project'.").grid(row=1,column=0,sticky='w')
Label(second_frame, text="Note, existing projects should have the following: ").grid(row=2,column=0,sticky='w')
Label(second_frame, text=" - the directory 'ta_assignment_project'").grid(row=3,column=0,sticky='w')
Label(second_frame, text=" - inside the above directory: 'ta_dataset'").grid(row=4,column=0,sticky='w')
Label(second_frame, text=" - inside the above directory: 'course_dataset'").grid(row=5,column=0,sticky='w')
Label(second_frame, text=" ").grid(row=6,column=0,sticky='w')
newProjectButton.grid(row=7,column=0,sticky='w')
existingProjectButton.grid(row=8,column=0,sticky='w')
#existingProjectButton.pack()

root.mainloop()