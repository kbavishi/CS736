#! /usr/bin/python

import snap_testlib

if __name__ == '__main__':
    for testspec in (snap_testlib.SERIAL_S_TEST_ARGS,
                     snap_testlib.SERIAL_M_TEST_ARGS,
                     snap_testlib.SERIAL_L_TEST_ARGS,
                     snap_testlib.PARALLEL_S_TEST_ARGS,
                     snap_testlib.PARALLEL_M_TEST_ARGS,
                     snap_testlib.PARALLEL_L_TEST_ARGS):
        hit = snap_testlib.build_test_args(testspec)
        for key, val in hit.items():
            print val
        print "-" * 30
