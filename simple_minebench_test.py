#! /usr/bin/python

import sys
import snap_testlib

TEST_ARGS = [
    ("KMeans", {"dataset": "edge", "num_threads": 4}),
    ("HOP", {"dataset": "particles_0_64", "num_threads": 4}),
    # Takes too long
    #("PLSA", {"seq1": "30k_1.txt", "seq2": "30k_2.txt",
    #          "matrix": "pam120.bla", "num_threads": 4}),
    ("ScalParC", {"dataset": "para_F26-A32-D250K\/F26-A32-D250K.tab",
                  "num_threads": 4}),
    # SEMPHY needs an input tree. Don't know how to work.
    #("SEMPHY", {"dataset": "108.phy", "num_threads": 4}),
    ("SVM_RFE", {"dataset": "outData.txt", "num_threads": 4}),
    ("RSEARCH", {"matrix_file": "RIBOSUM85-60.mat", "seq_file": "mir-40.stk",
                 "db_file": "100Kdb.fa", "num_threads" : 4}),
    # mpirun doesn't seem to work.
    #("ParETI", {"dataset": "data1", "num_cpu": 4}),
]

def get_test_args(test_type, num_threads):
    if test_type == "small":
        tests = list(snap_testlib.PARALLEL_S_TEST_ARGS)
    elif test_type == "medium":
        tests = list(snap_testlib.PARALLEL_M_TEST_ARGS)
    elif test_type == "large":
        tests = list(snap_testlib.PARALLEL_L_TEST_ARGS)
    else:
        assert False, "Unsupported test type %s" % test_type

    for test_name, test_args in tests:
        test_args["num_threads"] = num_threads
    return tests

def run_parallel_tests(shell, test_type, num_threads, num_cpu, iterations=2):
    cpu_list = range(0, num_cpu)

    # Generate the test arguments
    snap_test_args = get_test_args(test_type, num_threads=num_threads)
    tests = snap_testlib.build_test_args(snap_test_args)
    
    # Rebuild minebench snap with updated test arguments
    snap_testlib.build_minebench_snap(shell, tests, snap_test_args)

    # Persist our results in a known location
    outfile = open("output/parallel_%s_P%d_T%d.log" % (test_type, num_cpu,
                                                       num_threads), "w")

    # Time to run the tests now
    for test_name, test_args in tests.items():
        # First perform non-interference tests
        for _ in xrange(iterations):
            output = snap_testlib.run_snap(shell, test_name, test_args,
                                           cpu=cpu_list, interference=False)
            outfile.write("%s" % output)
            outfile.flush()

        # Then perform interference tests
        for _ in xrange(iterations):
            output = snap_testlib.run_snap(shell, test_name, test_args,
                                           cpu=cpu_list, interference=True)
            outfile.write("%s" % output)
            outfile.flush()

    outfile.close()

def run_serial_tests(shell, test_type, num_cpu, iterations=2):
    cpu_list = range(0, num_cpu)

    # Generate the test arguments
    if test_type == "small":
        snap_test_args = list(snap_testlib.SERIAL_S_TEST_ARGS)
    elif test_type == "medium":
        snap_test_args = list(snap_testlib.SERIAL_M_TEST_ARGS)
    elif test_type == "large":
        snap_test_args = list(snap_testlib.SERIAL_L_TEST_ARGS)
    else:
        assert False, "Unsupported test type %s" % test_type

    tests = snap_testlib.build_test_args(snap_test_args)
    
    # Rebuild minebench snap with updated test arguments
    snap_testlib.build_minebench_snap(shell, tests, snap_test_args)

    # Persist our results in a known location
    outfile = open("output/serial_%s_P%d.log" % (test_type, num_cpu), "w")

    # Time to run the tests now
    for test_name, test_args in tests.items():
        # First perform non-interference tests
        for _ in xrange(iterations):
            output = snap_testlib.run_snap(shell, test_name, test_args,
                                           cpu=cpu_list, interference=False)
            outfile.write("%s" % output)
            outfile.flush()

        # Then perform interference tests
        for _ in xrange(iterations):
            output = snap_testlib.run_snap(shell, test_name, test_args,
                                           cpu=cpu_list, interference=True)
            outfile.write("%s" % output)
            outfile.flush()

    outfile.close()

def minebench_snap_test(host_str):
    shell = snap_testlib.setup_shell(host_str)

    # Run the serial tests
    for num_cpu in [1, 4, 8]:
        run_serial_tests(shell, test_type="small", num_cpu=num_cpu)
        run_serial_tests(shell, test_type="medium", num_cpu=num_cpu)
        run_serial_tests(shell, test_type="large", num_cpu=num_cpu)
        import pdb; pdb.set_trace()

    import pdb; pdb.set_trace()

    # Run the multithreaded tests
    # First, run them as single-threaded applications with multiple CPUs
    for num_cpu in [1, 4, 8]:
        run_parallel_tests(shell, test_type="small", num_cpu=num_cpu,
                           num_threads=1)
        run_parallel_tests(shell, test_type="medium", num_cpu=num_cpu,
                           num_threads=1)
        run_parallel_tests(shell, test_type="large", num_cpu=num_cpu,
                           num_threads=1)

    # Now, run them as actual multithreaded applications
    for num_cpu in [1, 4, 8]:
        run_parallel_tests(shell, test_type="small", num_cpu=num_cpu,
                           num_threads=num_cpu)
        run_parallel_tests(shell, test_type="medium", num_cpu=num_cpu,
                           num_threads=num_cpu)
        run_parallel_tests(shell, test_type="large", num_cpu=num_cpu,
                           num_threads=num_cpu)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Incorrect number of arguments"
        sys.exit(1)

    minebench_snap_test(sys.argv[1])
