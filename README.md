# TAScheduling
 A simple scheduling software to be used as an aid to assign TAs to courses at the University of Iowa.


## Requirements
To run TAScheduling, you will need to have Python 3.10, Julia 1.7, and a Gurobi Academic License.


## Installation Instructions.

Download the necessary programming languages.

### Python

Get Python 3.10 here:

https://www.python.org/downloads/

We use Python Version 3.10 when we developed the code.

Make sure this version of Python is tied to your PATH in whichever terminal screen you are using.
You can test this by running "python" in the terminal screen to see if it launches Python.
	-Following this, you can quit by typing the command "quit()"

### Julia

Get Julia 1.7 here. Make sure ther version of Julia you are using is added to PATH:

https://julialang.org/downloads/

With platform specific instructions here (including adding Julia to PATH):

https://julialang.org/downloads/platform/

### Gurobi

NOTE: YOU WILL NEED TO BE CONNECTED TO A UIOWA CAMPUS NETWORK IN ORDER TO INSTALL GUROBI

Gurobi is a closed-source software used to solve optimization problems (which we formulate TAScheduling as).
We use it because it is very fast at determining assignments. Students, faculty, and staff at the
University of Iowa can get it for free. First, register for a license, here.

https://www.gurobi.com/downloads/end-user-license-agreement-academic/

Then download the latest version of Gurobi (with your account logged in), here:

https://www.gurobi.com/downloads/gurobi-software/

Finally, make sure the Gurobi license is installed on your computer. Otherwise, Gurobi will not run.
More information is found here:

https://www.gurobi.com/documentation/9.5/remoteservices/licensing.html

In particular, once you have navigated to your license key 
(something like ab01c234-567d-89ef-gh01-2345ij67890)
enter the following command in the terminal:

grbgetkey <license key>


## Installing needed Python Modules and Julia Packages

### Python

In the command line install the following modules using "pip install <module>"

modules: pandas, numpy, julia, bs4, requests

For "julia", you also need to do the following:

* Enter a python environment by typing "python"
* Enter the command "import julia"
* Enter the command "julia.install()"
	- Make sure Julia is is installed and the PATH variable is configured at this step.
	- This will install PyCall.jl, you may see an error screen in the middle, but it should still work.

### Julia

In the command line, start julia by typing in "julia"

Then in the REPL, hit "]" to start Julia's Package Manager.

Install the following packages using "add <package>"

packages: DataFrames, CSV, JuMP, Statistics, Gurobi.

For Gurobi, also run "]" -> "build Gurobi"


### TAScheduling

Download TAScheduling by either 
* downloading the zip file and unzipping where you want it on your personal computer
OR
* in your terminal, move to the directory where you want it and run:
"git clone https://github.com/mkratochvil/TAScheduling.git"


## Usage

Make sure you have downloaded the survey results from Qualtrics.
	- From the Qualtrics page, go to 
		Data & Analysis -> Export & Import -> Export Data...
		- Then download data as a CSV with "Download all fields" checked and
			"Use choice text" selected.

To start the TAScheduling package, run the command in your terminal:

python <path to TAScheduling>/TAScheduling/src/ta_assignment

The screen should now load.

When starting a New Project, select the directory where you want the results to be saved.
A new directory "ta_assignment_project" will be created there and all generated files should be saved there.
You must delete this directory manually and re-run the above command if you wish to start over.

When running "Load and clean TA survey results" this is the EXACT csv file created, using the instructions
above.

When running "alphabetize TAs", make sure the TA list is in the same format as in "list-of-TAs-fall2022.csv"
 (and it is in fact saved as a CSV file). For the scope of the example output, every TA's first name is "TA"
 and their last name is whatever number they were assigned.

After this screen, there is a screen that lists the TAs and provides a warning for potential issues.
TAs can be REMOVED from the list at this step. THIS STEP CANNOT BE UNDONE.
There is not a way to add TAs at this step. We suggest that this TA fills out the Qualtrics survey and
the process is started over at this time. Also, if a TA is removed in error, we suggest simply starting
the process over.

If a TA is not on the list, a warning will appear. Check these in a case-by-case basis, and plan accordingly.
In this case, they will appear at the BOTTOM of the list of TAs to be marked for removal.
There are several possibilities for why a TA does not appear:
	- A graduate student filled out the survey but is not a TA this semester.
	- A TA has a typo in their last name.
	- There could be a bug in the software (TAs are sorted based on whether the listed last name appears).

If a TA is marked as taking a survey multiple times, there could be several reasons for this:
	- The TA took the survey multiple times...their responses are stored in the order they took the survey
		with the first result not marked, while later results marked with the number of the reply.
	- There could be a bug in the software (TAs are sorted based on whether the listed last name appears).

If a TA is marked as not having taken the survey, there could be several reasons for this:
	- This TA did not take the survey.
	- A TA has a typo in their last name.
	- There could be a bug in the software (TAs are sorted based on whether the listed last name appears).

When entering the URLs, do the following:
	- Go to myui.uiowa.edu -> COURSES / REGISTRATION
	- Put in the correct Session (e.g. Fall 2022) under "Session"
	- Under Course Subject, enter "MATH"
	- Click the green "Search" button.

The URLs to be entered are the results for each of the pages.
Make sure ALL math courses are entered, as we use 5000+ level math courses to help determine TAs' availability.
Make sure these are entered in order, as well.

The suggested courses (courses that are checked in the next screen) are based on:
	- Course numbers that have historically been taught by TAs
	- Whether or not an instructor has been assigned to this course.
	- Whether this course is listed in the MyUI results INDEPENDENT of status.

Handling whether or not a course should be added or removed is on a case-by-case basis.
We suggest following along with the MyUI listing when making these determinations. 
Further, note that any 4000 level course that is taught by a TA is cross-listed with either a 3000 or 5000
level course. Therefore, all 4000 level courses should remain unchecked.

WE STRONGLY RECOMMEND HAVING ALL COURSES 3000+ DECIDED BEFORE RUNNING THE AUTOMATION STEP.
If you do not do this, you will have bizarre outcomes such as TAs not being qualified to teach these
courses assigned to them.

To determine preference/availability, Click "Search TA availability by Course"
This will give the list of students who prefer the course/are available, are only available, and only
 prefer the course, in that order.

Once you know which TAs you want for certain courses, Use the "Assign this TA to this course" section.
WARNING: at this time, once an assignment has been made, the TA can be placed elsewhere, but cannot be
 removed from the manual process. Therefore, you should be careful when selecting these TAs.
 Fixing this is a top priority.

If you wish to assign a TA to NO course, select "Intentionally Left Blank"

When running the optimization, the results are saved under "TA_output.csv" and "course_output.csv"
We recommend running in order of level constraint, from Light to Last Resort. The optimization solver
will display on the terminal screen whether a solution is feasible. If it is infeasible, then the model
can be ran again. The manual placement will be saved.

Note that being "nicer" to first year TAs is hard-coded into the solver. This means they are restricted to
at most two sections of large lecture discussions and will not be given 3 sections or stand alone courses,
regardless of their preferences/ level of constraint. 

If you have any questions/issues, contact Michael Kratochvil at mkratochvil91@gmail.com or post a comment in this repo.

