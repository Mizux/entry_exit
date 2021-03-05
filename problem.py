#!/usr/bin/env python3

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import math
import numpy as np


def create_data_model():
    data = {}
    fuel_capacity = 30_000  # fuel_capacity in -ft
    _locations = [
        (2.5, 2.5),  # start 0
        ((2.875, 3.35), (3.25, 4.2)), # refill 1
        ((3.79, 4.335), (4.33, 4.47)),
        ((4.19, 3.61), (4.05, 2.75)),
        ((4.475, 2.225), (4.9, 1.7)),
        ((4.235, 1.25), (3.57, 0.8)),
        ((2.785, 0.4), (2.0, 0.0)),
        ((1.265, 0.15), (0.53, 0.3)),
        ((0.715, 0.785), (0.9, 1.27)),
        ((1.125, 1.96), (1.35, 2.65)),
        ((1.0625, 3.3), (1.0625, 3.3)), # refill 10
        (0.775, 3.95),  # end 11
        (1.3, 1.1),  # first location 12
        (0.6, 4.2),
        (4.6, 4.0),
        (1.3, 4.2),
        (4.3, 0.5),
        (4.8, 1.3),
        (0.6, 0.2),
        (5, 2.1),
        (3.1, 1.3),
        (2.0, 2.5),
        (3.2, 3.9),
        (4.1, 4.7),
        (3.3, 0.6),
        (3.3, 4.5),
        (0.7, 2.8),
        (4.1, 2.6),
        (1.2, 1.0),
        (0.7, 3.2),
        (0.3, 0.3),
        (4.3, 4.7),
        (2, 0),
        (0.2, 1.7),
        (0.5, 4.2),
        (0.7, 0.4),
        (4, 2.9), # last location 36
    ]

    # only count visit locations
    data["counter"] = [
        0, # start 0
        0, # refill 1
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0, # refill 10
        0,  # end 11
        1,  # first location 12
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1,
        1, # last location 36
        ]
    assert (sum(data["counter"]) == 25)
    #data["coordinates"] = _locations
    data["num_locations"] = len(_locations)

    #data["locations"] = [(l[0] * 5280, l[1] * 5280) for l in _locations
    #                     ]  # 26.4k x 26.4k sq. ft. (5 x 5 miles sq.)
    #print(data["locations"])
    data["time_windows"] = [
        (0, 60), # start 0
        ((500, 1100), (1000, 2200)), # refill 1
        ((1500, 3300), (2000, 4400)),
        ((2500, 5500), (3000, 6600)),
        ((3500, 7700), (4000, 8800)),
        ((4500, 9900), (5000, 11000)),
        ((5500, 12100), (6000, 13200)),
        ((6500, 14300), (7000, 15400)),
        ((7500, 16500), (8000, 17600)),
        ((8500, 18700), (9000, 19800)),
        ((9500, 20900), (9500, 20900)), # refill 10
        (0, 100_000), # end 11
        (0, 100_000), # first location 12
        (7, 100_000),
        (10, 100_000),
        (14, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000),
        (0, 100_000), # last location 36
    ]
    data["stations"] = list(range(1,11))
    data["num_vehicles"] = 2
    data["fuel_capacity"] = fuel_capacity
    data["vehicle_speed"] = 33  # ft/s
    data["starts"] = [0, 0]
    data["ends"] = [11, 11]

    distance_matrix = np.zeros((data["num_locations"], data["num_locations"]), dtype=int)
    for i in range(data["num_locations"]):
        for j in range(data["num_locations"]):
            if i == j:
                distance_matrix[i][j] = 0
            else:
                if i in data["stations"]:
                    from_location = _locations[i][1] # use the exit point
                else:
                    from_location = _locations[i]
                from_location = [5280 * i for i in from_location]

                if j in data["stations"]:
                    to_location = _locations[j][0] # use the entry point
                else:
                    to_location = _locations[j]
                to_location = [5280 * i for i in to_location]

                distance_matrix[i][j] = euclidean_distance(from_location, to_location)

                # if from is a station exit point need to add the distance(entry,exit)
                if i in data["stations"]:
                    entry =  _locations[i][0]
                    entry = [5280 * i for i in entry]
                    distance_matrix[i][j] += euclidean_distance(entry, from_location)


    data["distance_matrix"] = distance_matrix.tolist()
    #print(distance_matrix)
    assert len(data['distance_matrix']) == len(data['time_windows'])
    assert len(data['starts']) == len(data['ends'])
    assert data['num_vehicles'] == len(data['starts'])
    return data


def euclidean_distance(position_1, position_2):
    return round(
        math.hypot((position_1[0] - position_2[0]),
                   (position_1[1] - position_2[1])))


def print_solution(manager, routing, solution):
    print("Objective: {}".format(solution.ObjectiveValue()))
    # total_distance = 0
    total_load = 0
    total_time = 0
    time_dimension = routing.GetDimensionOrDie("Time")
    fuel_dimension = routing.GetDimensionOrDie("Fuel")
    dropped_nodes = "Dropped nodes:"
    for node in range(routing.Size()):
        if routing.IsStart(node) or routing.IsEnd(node):
            continue
        if solution.Value(routing.NextVar(node)) == node:
            dropped_nodes += " {}".format(manager.IndexToNode(node))
    print(dropped_nodes)

    for vehicle_id in range(manager.GetNumberOfVehicles()):
        index = routing.Start(vehicle_id)
        print(f"Route for vehicle {vehicle_id}:")
        plan_output = ""
        # time = 0
        while not routing.IsEnd(index):
            fuel_var = fuel_dimension.CumulVar(index)
            time_var = time_dimension.CumulVar(index)
            slack_var = time_dimension.SlackVar(index)
            plan_output += "{0} Fuel({1}) Time({2},{3}) Slack({4},{5}) -> ".format(
                manager.IndexToNode(index), solution.Value(fuel_var),
                solution.Min(time_var), solution.Max(time_var),
                solution.Min(slack_var), solution.Max(slack_var))
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            # print(f"plop {routing.GetArcCostForVehicle(previous_index, index, vehicle_id)}\n")
            # time += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
        fuel_var = fuel_dimension.CumulVar(index)
        time_var = time_dimension.CumulVar(index)
        plan_output += "{0} Fuel({1}) Time({2},{3})\n".format(
            manager.IndexToNode(index), solution.Value(fuel_var),
            solution.Min(time_var), solution.Max(time_var))
        # plan_output += "Distance of the route: {} ft\n".format(time)
        plan_output += "Remaining Fuel of the route: {}\n".format(
            solution.Value(fuel_var))
        plan_output += "Total Time of the route: {} seconds\n".format(
            solution.Min(time_var))
        print(plan_output)
        # total_time += time
        total_load += solution.Value(fuel_var)
        total_time += solution.Min(time_var)
    # print('Total Distance of all routes: {} ft'.format(total_time))
    print('Total Fuel remaining of all routes: {}'.format(total_load))
    print('Total Time of all routes: {} seconds'.format(total_time))


def main():
    # Instantiate the data problem.
    data = create_data_model()

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
            len(data["distance_matrix"]),
            data["num_vehicles"],
            data["starts"],
            data["ends"])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Enable drop
    visit_penalty = 1_000_000
    station_penalty = 0
    for node in range(len(data["distance_matrix"])):
        if node == 0 or node == 11: # start/end node
            continue
        if node > 11: # location
            index = manager.NodeToIndex(node)
            routing.AddDisjunction([index], visit_penalty)
        else: # station
            index = manager.NodeToIndex(node)
            routing.AddDisjunction([index], station_penalty)

    # Time
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        result = 0
        if from_node in data["stations"]:
            result += 60 * 2 # refuel time 2 minutes ?
        return result + int(data["distance_matrix"][from_node][to_node] / data["vehicle_speed"])

    time_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(time_callback_index)

    routing.AddDimension(
            time_callback_index,
            60 * 5, # slack: 5 min
            60 * 60, # duration: 1 hours
            False, # cumul var to zero
            'Time')
    time_dimension = routing.GetDimensionOrDie('Time')
    #time_dimension.SetGlobalSpanCostCoefficient(10_000)

    enable_tw = True
    if enable_tw:
        for location_idx, time_window in enumerate(data["time_windows"]):
            if location_idx == 0 or location_idx == 11: # start/end nodes
                continue
            index = manager.NodeToIndex(location_idx)
            if location_idx in data["stations"]:
                time_dimension.CumulVar(index).SetRange(
                        0 * time_window[0][0],
                        500_000 + time_window[1][1])
            else:
                time_dimension.CumulVar(index).SetRange(
                        0 * time_window[0],
                        500_000 + time_window[1])
            routing.AddToAssignment(time_dimension.SlackVar(index))
        # Add time window constraints for each vehicle start node
        # and "copy" the slack var in the solution object (aka Assignment) to print it
        for vehicle_id in range(data["num_vehicles"]):
            index = routing.Start(vehicle_id)
            time_dimension.CumulVar(index).SetRange(0 * data["time_windows"][0][0],
                                                    500_000 + data["time_windows"][0][1])
            routing.AddToAssignment(time_dimension.SlackVar(index))

    for i in range(manager.GetNumberOfVehicles()):
        start = routing.Start(i)
        end = routing.End(i)
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(start))
        routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(end))

    enable_mean = True
    if enable_mean:
        routing.AddVectorDimension(
            data["counter"],
            manager.GetNumberOfNodes(),
            True,  # start cumul to zero
            "Counter")
        counter_dimension = routing.GetDimensionOrDie("Counter")
        nb_visit = sum(data["counter"]) // manager.GetNumberOfVehicles()
        print(f'visit_mean: {nb_visit}')

        for vehicle_id in range(data["num_vehicles"]):
            index = routing.End(vehicle_id)
            counter_dimension.SetCumulVarSoftLowerBound(index, nb_visit, 1000)
            counter_dimension.SetCumulVarSoftUpperBound(index, nb_visit + 1, 1000)


    # Fuel constraints
    def fuel_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        # temp = 0
        # if to_node in stations:
        #     from_node = to_node
        #     to_node = to_node + 1
        #     return from_node*0 + to_node*0
        # else:
        return -data["distance_matrix"][from_node][to_node]

    fuel_callback_index = routing.RegisterTransitCallback(fuel_callback)
    routing.AddDimension(
            fuel_callback_index,
            data["fuel_capacity"],
            data["fuel_capacity"],
            False, # cumul var to zero
            'Fuel')

    fuel_dimension = routing.GetDimensionOrDie('Fuel')
    for vehicle_id in range(data["num_vehicles"]):
        fuel_dimension.SlackVar(routing.Start(vehicle_id)).SetValue(0)
    for node in range(len(data["distance_matrix"])):
        if node == 0 or node == 11: # start/end node
            continue
        if node > 11:
            index = manager.NodeToIndex(node)
            fuel_dimension.SlackVar(index).SetValue(0)
        routing.AddVariableMinimizedByFinalizer(fuel_dimension.CumulVar(index))

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.log_search = True
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(10)

    search_parameters.log_search = True
    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        print_solution(manager, routing, solution)
    else:
        print("No solution found!")

    print("Solver status:", routing.status())


if __name__ == '__main__':
    main()
