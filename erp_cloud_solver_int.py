# General utilities
import csv, datetime 
# Time-out logic from: https://stackoverflow.com/questions/366682/how-to-limit-execution-time-of-a-function-call-in-python 
import signal
# Line Graphs
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
# import plotly.plotly as py
# import plotly.graph_objs as go
# Solver Imports
from pysmt.shortcuts import *
# Canvas Graphics Imoprts: 
from graphics import *
#To install graphics:
# https://www.pas.rochester.edu/~rsarkis/csc161/python/pip-graphics.html
# $>pip3 install --user http://bit.ly/csc161graphics

INPUT_FILE_NAME = "erp_reqs.csv"
TIME_OUT_MAX    = 10

# To run: exec(open("erp_cloud_solver.py").read())

def signal_handler(signum, frame):
    raise Exception("Timed out!")

def set_bounds(t,b):
    global THE_SOLVER
    THE_SOLVER.add_assertion(Equals(MAX_TIME, Int(t)))
    THE_SOLVER.add_assertion(Equals(MAX_BAND, Int(b)))
    THE_SOLVER.add_assertion(Equals(MIN_TIME, Int(0)))
    THE_SOLVER.add_assertion(Equals(MIN_BAND, Int(0)))

def get_max_time():
    global reqInput
    return int(reqInput[0][1])

def get_max_bandwidth():
    global reqInput
    return int(reqInput[0][2])

def get_color():
    global CURR_COLOR
    if CURR_COLOR == 1:
        color = "green"
    elif CURR_COLOR == 2:
        color = "red"
    elif CURR_COLOR == 3:
        color = "salmon"
    elif CURR_COLOR == 4:
        color = "yellow"
    elif CURR_COLOR == 5:
        color = "blue"
    elif CURR_COLOR == 6:
        color = "pink"
    elif CURR_COLOR == 7:
        color = "light blue"
    elif CURR_COLOR == 8:
        color = "dark orange"
    elif CURR_COLOR == 9:
        color = "brown"
    elif CURR_COLOR == 10:
        color = "light green"
    else:
        color = "magenta"
        CURR_COLOR = 0
    CURR_COLOR = CURR_COLOR + 1
    return color

def readCsvFile(fileName):
    fileContent = []
    with open(fileName,'r') as file:
        csvReader = csv.reader(file)
        for row in csvReader:
            fileContent.append(row)
    return fileContent

def add_req(reqName, reqTime, reqBandwidth, currSolver):
    global req_list
    global TIMED_OUT

    # Save Current List of Assertions
    currentAssertions = currSolver.assertions[:]
    # Define two points:
    #   - Lower Left Point (xo,yo)
    #   - Upper Right Point (xe, ye)
    xo = Symbol(reqName+'_Xo', INT)
    yo = Symbol(reqName+'_Yo', INT)
    xe = Symbol(reqName+'_Xe', INT)
    ye = Symbol(reqName+'_Ye', INT)
    # Request dimensions
    currSolver.add_assertion(Equals(Minus(xe,xo),Int(reqTime)))
    currSolver.add_assertion(Equals(Minus(ye,yo),Int(reqBandwidth)))
    # Request must NOT exceed boundaries
    # - Right boundary (x-axis)
    currSolver.add_assertion(LE(xo, MAX_TIME))
    currSolver.add_assertion(LE(xe, MAX_TIME))
    # - Left boundary (0 point)
    currSolver.add_assertion(LE(MIN_TIME, xo))
    currSolver.add_assertion(LE(MIN_TIME, xe))
    # - Upper boundary (y-axis)
    currSolver.add_assertion(LE(yo, MAX_BAND))
    currSolver.add_assertion(LE(ye, MAX_BAND))
    # - Lower boundary (0 point)
    currSolver.add_assertion(LE(MIN_BAND, yo))
    currSolver.add_assertion(LE(MIN_BAND, ye))
    # At least one of the dimensions of the new request must NOT overlap with
    # any existing dimension
    for req in req_list:
        no_overlap_list = []
        # The end point of one request can't be larger than the start
        # point of the other on at least one dimension
        no_overlap_list.append(LE(xe, req[3][0])) # x-axis new to old
        no_overlap_list.append(LE(req[4][0], xo)) # x-axis old to new
        no_overlap_list.append(LE(ye, req[3][1])) # y-axis new to old
        no_overlap_list.append(LE(req[4][1], yo)) # y-axis old to new
        # Add the above conditions as ONE composite condition of ORs
        currSolver.add_assertion(Or(no_overlap_list))

    start_time = datetime.datetime.now()

    # Set the timeout alarm
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(TIME_OUT_MAX)

    try:
        solvable = currSolver.solve()
    except Exception as e:
        solvable = False
        TIMED_OUT = True
    # Disable the timeout alarm
    signal.alarm(0)

    end_time = datetime.datetime.now()
    time_ms  = int((end_time - start_time).microseconds)
    time_sol = int((end_time - start_time).seconds)

    atomCond = 0
    if not TIMED_OUT:
        line_graph_x.append(len(req_list) + 1)
        line_graph_y.append(time_ms)
        loc_formula = And(currSolver.assertions)
        atomCond    = len(loc_formula.get_atoms())
        line_graph_z.append(atomCond)

    time_unt = "s"
    if time_sol == 0:
        time_sol = time_ms
        time_unt = "ms"

    if solvable:
        print("Request %s is servicible\tSolver Time: %i %s\tAtomic Conditions: %i" % (reqName, time_sol, time_unt, atomCond))
        retSolver = currSolver
        servicible = True
    else:
        print("Request %s is NOT servicible\tSolver Time: %i %s" % (reqName, time_sol, time_unt))
        newSolver = Solver()
        for a in currentAssertions:
            newSolver.add_assertion(a)
        retSolver = newSolver
        servicible = False

    # Request Tuple: Name, Time/Width, Bandwidth/Height, Lower Left Point, Upper Left Point
    req_list.append((reqName, reqTime, reqBandwidth, (xo, yo), (xe, ye), servicible, start_time, end_time))

    if TIMED_OUT:
        print("\t***Request timed out; no more requests can be evaluated")

    return retSolver

THE_SOLVER      = Solver()
TIMED_OUT       = False
CURR_COLOR      = 0
MAX_X           = 0
MAX_Y           = 0
reqInput        = []
req_list        = []
line_graph_x    = []
line_graph_y    = []
line_graph_z    = []

SCALE = 10 #Graph Scaling Factor

if len(sys.argv) > 1:
    input_file_name = str(sys.argv[1])
else:
    input_file_name = INPUT_FILE_NAME

reqInput = readCsvFile(input_file_name)

if len(reqInput) <= 1:
    print("Unable to read input from file %s" % input_file_name)
else:
    MAX_TIME = Symbol("MAX_TIME", INT) #Width
    MAX_BAND = Symbol("MAX_BAND", INT) #Height
    MIN_TIME = Symbol("MIN_TIME", INT)
    MIN_BAND = Symbol("MIN_BAND", INT)

    set_bounds(get_max_time(),get_max_bandwidth())

    for reqIn in reqInput[1:]:
        THE_SOLVER = add_req(reqIn[0],int(reqIn[1]),int(reqIn[2]),THE_SOLVER)
        if TIMED_OUT:
            break

    # Construct formula of ANDs
    formula = And(THE_SOLVER.assertions)
    # Run the solver
    check_model = get_model(formula)
    # If model is valid
    if check_model:
        # Get model in a dictionary format
        model = dict(check_model)

        req_window = GraphWin("Requests",SCALE * get_max_time() + 50,SCALE * get_max_bandwidth() + 50)
        main_canvas = Rectangle(Point(0,0),Point(SCALE * get_max_time(),SCALE * get_max_bandwidth()))
        main_canvas.setWidth(5)
        for req in req_list:
            if req[5]: #If servicible
                locXo = locYo = locXe = locYe = 0
                locXo = model.get(req[3][0]).constant_value()
                locYo = model.get(req[3][1]).constant_value()
                locXe = model.get(req[4][0]).constant_value()
                locYe = model.get(req[4][1]).constant_value()
                lblX  = SCALE * (locXo + (locXe-locXo)/2)
                lblY  = SCALE * (locYo + (locYe-locYo)/2)
                reqRectangle = Rectangle(Point(SCALE * locXo, SCALE * locYo), Point(SCALE * locXe, SCALE * locYe))
                reqRectangle.setFill(get_color())
                reqRectangle.draw(req_window)
                reqLabel = Text(Point(lblX,lblY),req[0])
                reqLabel.draw(req_window)
        main_canvas.draw(req_window)

        # plt.plot(line_graph_x,line_graph_y,line_graph_z)
        # plt.xlabel("Number of Requests")
        # plt.ylabel("Solver Time (ms)")
        # plt.show()
        plt.figure(1)
        plt.subplot(211)
        plt.plot(line_graph_x, line_graph_y)
        plt.title("Analysis of Solver Processing Time")
        plt.ylabel("Solver Time (ms)")

        plt.subplot(212)
        plt.plot(line_graph_x, line_graph_z)
        plt.ylabel("Atomic Conditions")
        plt.xlabel("Number of Requests")
        plt.show()
    else:
        print("Model is unsatisfiable")

