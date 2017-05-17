#! /usr/bin/python

import pylint
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

def run_tests(shell, test_dict, cpu_list, outfile_name, iterations=5):
    # Persist our results in a known location
    outfile = open(outfile_name, "w")

    # Time to run the tests now
    for test_name, test_args in test_dict.items():
        # First perform non-interference tests
        for _ in xrange(iterations):
            output = snap_testlib.run_snap(shell, test_name,
                                           cpu=cpu_list, interference=False)
            outfile.write("%s" % output)
            outfile.flush()

        # Then perform interference tests
        for _ in xrange(iterations):
            output = snap_testlib.run_snap(shell, test_name,
                                           cpu=cpu_list, interference=True)
            outfile.write("%s" % output)
            outfile.flush()

    outfile.close()

def run_parallel_tests(shell, test_type, num_threads, num_cpu):
    cpu_list = range(0, num_cpu)

    # Generate the test arguments
    test_spec = snap_testlib.get_test_spec("parallel", test_type,
                                           num_threads=num_threads)
    tests = snap_testlib.build_test_dict(test_spec, test_type=test_type)
    
    outfile_name = "output/parallel_%s_P%d_T%d.log" % (test_type, num_cpu,
                                                       num_threads)
    run_tests(shell, tests, cpu_list, outfile_name)

def run_serial_tests(shell, test_type, num_cpu):
    cpu_list = range(0, num_cpu)

    # Generate the test arguments
    test_spec = snap_testlib.get_test_spec("serial", test_type)
    tests = snap_testlib.build_test_dict(test_spec, test_type=test_type)
    
    outfile_name = "output/serial_%s_P%d.log" % (test_type, num_cpu)

    # Time to run the tests now
    run_tests(shell, tests, cpu_list, outfile_name)

def run_sysbench_tests(shell, num_cpu):
    cpu_list = range(0, num_cpu)

    # Generate the test arguments
    test_spec = snap_testlib.SYSBENCH_TEST_SPEC
    for (test_name, args) in test_spec:
        args["num_threads"] = num_cpu
    tests = snap_testlib.build_test_dict(test_spec)

    outfile_name = "output/sysbench_P%d.log" % (num_cpu)

    # Time to run the tests now
    run_tests(shell, tests, cpu_list, outfile_name)

def minebench_snap_test(host_str):
    shell = snap_testlib.setup_shell(host_str)

    # First, run them as single-threaded applications.
    # Then, run them as actual multithreaded applications
    #num_threads_list = [1, 8]
    num_threads_list = [8]
    for num_threads in num_threads_list:
        # Build our snap with the necessary tests
        snap_testlib.build_minebench_snap(shell, num_threads)
        import pdb; pdb.set_trace()

        #for num_cpu in [1, 4, 8]:
        for num_cpu in [4]:
            # Run the serial tests.
            if num_threads == 1:
                # But only run them once
                run_serial_tests(shell, test_type="small", num_cpu=num_cpu)
                run_serial_tests(shell, test_type="medium", num_cpu=num_cpu)
                run_serial_tests(shell, test_type="large", num_cpu=num_cpu)

            # Run the parallel tests.
            #run_parallel_tests(shell, test_type="small", num_cpu=num_cpu,
            #                   num_threads=num_threads)
            run_parallel_tests(shell, test_type="medium", num_cpu=num_cpu,
                               num_threads=num_threads)
            #run_parallel_tests(shell, test_type="large", num_cpu=num_cpu,
            #                   num_threads=num_threads)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Incorrect number of arguments"
        sys.exit(1)

    minebench_snap_test(sys.argv[1])
