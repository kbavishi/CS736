#! /usr/bin/python

import re

def parse_file(filename, exp_count=5):
    lines = open(filename, "r").readlines()

    # Used as a parsing flag. Indicates that I have seen a "snap run" in
    # previous lines, and therefore I'm waiting for the corresponding task-clock
    # times and total times.
    found_test = False
    results = {}

    metric_re = None

    if "sysbench" in filename:
        # For SysbenchDisk, it will be 1.2Mb/sec.
        # For SysbenchMem, it will be 1.2 MB/sec
        metric_re = "(\d+\.\d+)\s?M[bB]/sec"
    else:
        metric_re = "(\d+\.\d+) seconds time elapsed"

    for line in lines:
        if not line: continue

        if "snap run" in line:
            # We should have found the task clock and completion time for the
            # previous test by now
            assert found_test == False
            # We now officially expect to find the timestamps
            found_test = True

            test_name = re.search("snap run minebench.(\S+)", line).groups()[0]
            if test_name not in results:
                results[test_name] = {"count": 1, "no_interference": [],
                                      "interference_A": [], "interference_B": []}
            else:
                results[test_name]["count"] += 1

        elif re.search(metric_re, line):
            assert found_test == True
            # We can now resume our search for a new test
            found_test = False

            count = results[test_name]["count"]
            if count <= exp_count:
                test_type = "no_interference"
            else:
                if count % 2 == 0:
                    test_type = "interference_A"
                else:
                    test_type = "interference_B"

            metric = re.search(metric_re, line).groups()[0]
            results[test_name][test_type] += [float(metric)]

    # Finally process our results
    #print results

    scores = {}
    for test_name, result in results.items():
        time_no_int = sum(result["no_interference"]) / exp_count
        time_int_A = sum(result["interference_A"]) / exp_count
        time_int_B = sum(result["interference_B"]) / exp_count

        #score = abs(time_int_A - time_int_B) / time_no_int
        score = time_int_A / time_no_int
        # Fairness metric
        score = ((time_int_A + time_int_B)**2) / (2 * (time_int_A**2 +
                                                       time_int_B**2))
        # Cohab metric
        #score = (time_int_A + time_int_B) / (2 * time_no_int)
        if score < 0.9:
            print test_name, "<<<<"
        scores[test_name] = round(score, 3)

    return scores

def compile_results():
    results = []
    #for test_type in ("small", "medium", "large"):
    for test_type in ("medium",):
        # Compile results for serial tests
        #for num_cpu in [1, 4, 8]:
        for num_cpu in [1, 4]:
            outfile = "output/serial_%s_P%d.log" % (test_type, num_cpu)
            scores = parse_file(outfile)
            results += [("S_C%d" % num_cpu, scores)]

        # Compile results for parallel tests
        #for num_cpu in [1, 4, 8]:
        for num_cpu in [1, 4]:
            for num_threads in [1, 8]:
                outfile = "output/parallel_%s_P%d_T%d.log" % (test_type,
                                                              num_cpu,
                                                              num_threads)
                scores = parse_file(outfile)
                results += [("P_C%d_T%d" % (num_cpu, num_threads), scores)]

    # Compile results for sysbench tests
    for num_cpu in [1, 8]:
        outfile = "output/sysbench_P%d.log" % num_cpu
        scores = parse_file(outfile)
        results += [("B_C%d_T%d" % (num_cpu, num_cpu), scores)]

    results = sorted(results)
    for result in results:
        print result

if __name__ == "__main__":
    compile_results()


