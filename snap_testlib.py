#! /usr/bin/python

import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
import netaddr
import spur
import waiting
from termcolor import cprint

USERNAME = "kbavishi"
PCAP_FILE = "output.pcap"

snap_app_cmd = {
    '__KMEANS__small': 'minebench.KMeansSmall',
    '__KMEANS__medium': 'minebench.KMeansMedium',
    '__FUZZY_KMEANS__small': 'minebench.FuzzyKMeansSmall',
    '__FUZZY_KMEANS__medium': 'minebench.FuzzyKMeansMedium',
    '__HOP__small': 'minebench.HOPSmall',
    '__HOP__medium': 'minebench.HOPMedium',
    '__HOP__large': 'minebench.HOPLarge',
    '__PLSA__': 'minebench.PLSA',
    '__ScalParC__small': 'minebench.ScalParCSmall',
    '__ScalParC__medium': 'minebench.ScalParCMedium',
    '__ScalParC__large': 'minebench.ScalParCLarge',
    '__SEMPHY__': 'minebench.SEMPHY',
    '__SVM_RFE__': 'minebench.SVMRFE',
    '__ParETI__': 'minebench.ParETI',
    '__RSEARCH__': 'minebench.RSEARCH',
    '__BIRCH__small': 'minebench.BIRCHSmall',
    '__BIRCH__medium': 'minebench.BIRCHMedium',
    '__BIRCH__large': 'minebench.BIRCHLarge',
    '__APRIORI__small': 'minebench.AprioriSmall',
    '__APRIORI__medium': 'minebench.AprioriMedium',
    '__APRIORI__large': 'minebench.AprioriLarge',
    '__ECLAT__small': 'minebench.ECLATSmall',
    '__ECLAT__medium': 'minebench.ECLATMedium',
    '__ECLAT__large': 'minebench.ECLATLarge',
    '__BAYESIAN__': 'minebench.Bayesian',
    '__SYSBENCH_MEM__': 'minebench.SysbenchMem',
    '__SYSBENCH_DISK__': 'minebench.SysbenchDisk',
    '__SYSBENCH_DISK_PREP__': 'minebench.SysbenchDiskPrep',
    '__SYSBENCH_DISK_CLEANUP__': 'minebench.SysbenchDiskCleanup',
}

INTERFERENCE_TEST_SPEC = [
    ("PLSA", {"seq1": "30k_1.txt", "seq2": "30k_2.txt",
              "matrix": "pam120.bla", "num_threads": 1}),
]

SYSBENCH_UTIL_TEST_SPEC = [
    ("SysbenchDiskPrep", {"file_total_size": "3G"}),
    ("SysbenchDiskCleanup", {"file_total_size": "3G"}),
]

SYSBENCH_TEST_SPEC = [
    ("SysbenchMem", {"num_threads": 1, "mem_block_size": "50G",
                     "total_mem_size": "1000G"}),
    ("SysbenchDisk", {"num_threads": 1, "file_total_size": "3G",
                      "file_test_mode": "rndrw", "max_requests": 0,
                      "max_time": 120}),
]

PARALLEL_S_TEST_SPEC = [
    ("HOP", {"dataset": "particles_0_64", "num_threads": 1}),
    ("KMeans", {"dataset": "edge100", "num_threads": 1, "binary": False}),
    ("FuzzyKMeans", {"dataset": "edge100", "num_threads": 1, "binary": False}),
    ("ScalParC", {"dataset": "para_F26-A32-D125K\/F26-A32-D125K.tab",
                  "num_records": 125000, "num_attributes": 32,
                  "num_threads": 1}),
    ("Apriori", {"dataset":
                 "data.ntrans_400.tlen_10.nitems_1.npats_2000.patlen_6",
                 "offset_file": "offset_file_400_10_1",
                 "num_threads": 1}),
]

PARALLEL_M_TEST_SPEC = [
    ("HOP", {"dataset": "particles_0_128", "num_threads": 1}),
    ("KMeans", {"dataset": "edge", "num_threads": 1}),
    ("FuzzyKMeans", {"dataset": "edge", "num_threads": 1}),
    ("ScalParC", {"dataset": "para_F26-A32-D250K\/F26-A32-D250K.tab",
                  "num_records": 250000, "num_attributes": 32,
                  "num_threads": 1}),
    ("Apriori", {"dataset":
                 "data.ntrans_1000.tlen_10.nitems_1.npats_2000.patlen_6",
                 "offset_file": "offset_file_1000_10_1",
                 "num_threads": 1}),
]

PARALLEL_L_TEST_SPEC = [
    ("HOP", {"dataset": "particles_0_256", "num_threads": 1}),
    ("ScalParC", {"dataset": "para_F26-A64-D250K\/F26-A64-D250K.tab",
                  "num_records": 250000, "num_attributes": 64,
                  "num_threads": 1}),
    ("Apriori", {"dataset":
                 "data.ntrans_2000.tlen_20.nitems_1.npats_2000.patlen_6",
                 "offset_file": "offset_file_2000_20_1",
                 "num_threads": 1}),
    #("Apriori", {"dataset":
    #             "data.ntrans_4000.tlen_20.nitems_1.npats_2000.patlen_6",
    #             "offset_file": "offset_file_2000_20_1",
    #             "num_threads": 1}),
]

SERIAL_S_TEST_SPEC = [
    ("BIRCH", {"para_file": "AMR_64.para", "schema_file": "AMR_64.scheme",
               "proj_file": "AMR_64.proj", "dataset": "particles_0_64_ascii"}),
    ("ECLAT", {"dataset": "ntrans_400.tlen_10.nitems_1.npats_2000.patlen_6",
               "partitions": 4}),
]

SERIAL_M_TEST_SPEC = [
    ("BIRCH", {"para_file": "AMR_128.para", "schema_file": "AMR_128.scheme",
               "proj_file": "AMR_128.proj", "dataset": "particles_0_128_ascii"}),
    ("ECLAT", {"dataset": "ntrans_1000.tlen_10.nitems_1.npats_2000.patlen_6",
               "partitions": 4}),
]

SERIAL_L_TEST_SPEC = [
    ("BIRCH", {"para_file": "AMR_256.para", "schema_file": "AMR_256.scheme",
               "proj_file": "AMR_256.proj", "dataset": "particles_0_256_ascii"}),
    ("ECLAT", {"dataset": "ntrans_2000.tlen_20.nitems_1.npats_2000.patlen_6",
               "partitions": 4}),
    #("ECLAT", {"dataset": "ntrans_4000.tlen_20.nitems_1.npats_2000.patlen_6",
    #           "partitions": 4}),
]

class TestShell(spur.SshShell):
    """
    Wrapper class around the spur.SshShell class. Provides the following
    benefits:

    1. Easier to run commands since it allows strings instead of just lists.
    Eg. It allows "ls -al", compared to spur.SshShell which only allows
    ["ls", "-al" ]

    2. Also handles the pipe (|) and redirect operators (>>) in a cleaner way
    than spur.SshShell

    3. Prints commands in colour. Easier to distinguish between the command
    being run and its output

    4. Also keeps track of spawned processes and cleans them on object deletion.
    [This doesn't quite work correctly yet]
    """
    def __init__(self, *args, **kwargs):
        self.processes = []
        super(TestShell, self).__init__(*args, **kwargs)

    def run(self, cmd, *args, **kwargs):
        """Can run any bash command. Note:

        1. To run complex bash commands with pipes and redirectors, set
        "use_bash"=True in the kwargs just to be safe.
        Eg. shell.run("ps aux | grep DataNode", use_bash=True)

        2. Any commands defined in run.sh won't work. Use the function
        `run_hadoop_cmd` instead for those commands.
        """
        if isinstance(cmd, str):
            if ">>" in cmd or "|" in cmd or 'use_bash' in kwargs:
                # It is not possible to run commands which have pipes or the
                # redirect operators without this hack
                cmd = ["bash", "-c", cmd]
                kwargs.pop('use_bash', None)
            else:
                cmd = shlex.split(cmd)
        return super(TestShell, self).run(cmd, *args, **kwargs)

    def spawn(self, cmd, *args, **kwargs):
        if isinstance(cmd, str):
            # Convert the `str` type command to type `list`
            cmd = shlex.split(cmd)

        if 'stdout' not in kwargs:
            # Dump the output of the command to stdout. Without this, it is hard
            # to know if a command is stuck
            kwargs['stdout'] = sys.stdout

        # Print the command in yellow. This makes it easier to distinguish
        # from its output. Useful if a lot of output is dumped
        cprint(" ".join(cmd), 'yellow', attrs=['bold'])

        proc = super(TestShell, self).spawn(cmd, *args, **kwargs)
        self.processes += [proc]
        return proc

    def is_public_addr(self, ip_addr):
        """Hacky utility function which guesses if given IP addr is a public IP addr
        or a private one"""
        return not ip_addr.startswith("10.") and not ip_addr.startswith("172.")

    def get_public_ip_addr(self):
        """Gives you the public IP address of the node"""
        result = self.run("hostname -I")
        ip_addrs = result.output.split(' ')
        for ip_addr in ip_addrs:
            if self.is_public_addr(ip_addr):
                return ip_addr
        assert False, "Could not find public IP address"

    def get_private_intf(self):
        """Gives you the interface name which has a private IP address of the
        form 10.X.X.X"""
        output = self.run("ifconfig | grep 10.10 -B 1").output
        return output.split()[0]

    def get_private_intf_mac(self):
        """Gives you the MAC address of the interface which has a private IP
        address of the form 10.X.X.X"""
        output = self.run("ifconfig | grep 10.10 -B 1").output
        return output.split()[4]

    def get_private_ip_addr(self, allow_public_ip=False):
        """Gives you the private IP address which will be used for HDFS
        communication. It assumes that they will be of the form 10.X.X.X"""

        result = self.run("hostname -I")
        ip_addrs = result.output.split(' ')
        private_ip_addrs = []
        # We know that CloudLab picks IP addrs of the form 10.x.x.x
        # Hack to take advantage of that
        for ip_addr in ip_addrs:
            if ip_addr.startswith('10.10'):
                private_ip_addrs += [ip_addr]

        if not private_ip_addrs:
            if allow_public_ip:
                # For GDA settings, we may be forced to use the public IP
                # address instead
                return self.get_public_ip_addr()
            else:
                assert False, "Could not find public IP address"
        else:
            # There can be multiple IP addresses belonging to different subnets
            # of the form 10.X.X.X. Pick the lexicographically first one
            return sorted(private_ip_addrs)[0]

    def copyFile(self, localPath, remotePath):
        with self.open(remotePath, "wcb") as remote_file:
            with open(localPath, "rb") as local_file:
                shutil.copyfileobj(local_file, remote_file)

    def __del__(self):
        """Tries to cleanup any processes that may be running"""
        for process in self.processes:
            try:
                process.send_signal(signal.SIGINT)
            except:
                # Process probably already dead
                continue

def setup_passwordless(main_shell, host_shells):
    """Sets up passwordless access for easy installation using Ansible."""
    try:
        # Check if the RSA public key already exists
        main_shell.run("ls .ssh/id_rsa.pub")
    except:
        # Need to create an RSA key since nothing exists
        main_shell.run("ssh-keygen -f /users/kbavishi/.ssh/id_rsa -t rsa -N '' ",
                     use_bash=True)

    # Add the public RSA key to the authorized_keys list on each slave
    publickey = main_shell.run("cat .ssh/id_rsa.pub").output.strip("\n").strip()

    for shell, ip_addr in host_shells:
        try:
            # Check if it has already been added
            shell.run("grep '%s' .ssh/authorized_keys" % publickey, use_bash=True)
        except:
            # Hasn't been added. Update the authorized_keys list
            shell.run("echo -e '%s' >> .ssh/authorized_keys" % publickey)
            # Add the host's IP address to the known_hosts list on the master.
            # Creates issues otherwise
            shell.run("ssh-keyscan -H %s >> .ssh/known_hosts" % ip_addr)

def get_cpuset(shell, process_name):
    pid = shell.run("pidof %s" % process_name).output.strip()
    return shell.run("sudo taskset -cp %s" % pid).output.split()[-1].strip()

def set_cpuset(shell, process_name, cpuset):
    pid = shell.run("pidof %s" % process_name).output.strip()
    shell.run("sudo taskset -cp %s %s" % (cpuset, pid))

def generate_test_args(test_name, **kwargs):
    if test_name == "KMeans":
        assert "dataset" in kwargs
        assert "num_threads" in kwargs
        exec_name = "$SNAP\/KMeans\/example"
        dataset = "$SNAP\/datasets\/kmeans\/%s" % kwargs["dataset"]
        threads = kwargs["num_threads"]
        binary = kwargs.get("binary", False)
        snap_script_args = "%s -i %s -o -p %s" % (exec_name, dataset, threads)
        if binary:
            snap_script_args += " -b"
        key = "__KMEANS__"

    elif test_name == "FuzzyKMeans":
        assert "dataset" in kwargs
        assert "num_threads" in kwargs
        exec_name = "$SNAP\/KMeans\/example"
        dataset = "$SNAP\/datasets\/kmeans\/%s" % kwargs["dataset"]
        threads = kwargs["num_threads"]
        binary = kwargs.get("binary", False)
        snap_script_args = "%s -i %s -o -f -p %s" % (exec_name, dataset, threads)
        if binary:
            snap_script_args += " -b"
        key = "__FUZZY_KMEANS__"

    elif test_name == "HOP":
        exec_name = "$SNAP\/HOP\/para_hop"
        particles = kwargs.get("num_particles", 61440)
        dataset = "$SNAP\/datasets\/HOP\/%s" % kwargs["dataset"]
        nsmooth = kwargs.get("nsmooth", 64)
        bucket_size = kwargs.get("bucket_size", 16)
        nhop = kwargs.get("nhop", -1)
        threads = kwargs["num_threads"]
        snap_script_args = "%s %s %s %s %s %s %s" % (exec_name, particles,
                                                     dataset, nsmooth,
                                                     bucket_size, nhop, threads)
        key = "__HOP__"

    elif test_name == "PLSA":
        exec_name = "$SNAP\/PLSA\/parasw"
        seq1 = "$SNAP\/datasets\/PLSA\/%s" % kwargs["seq1"]
        seq2 = "$SNAP\/datasets\/PLSA\/%s" % kwargs["seq2"]
        matrix = "$SNAP\/datasets\/PLSA\/%s" % kwargs["matrix"]
        block_height = kwargs.get("block_height", 600)
        block_length = kwargs.get("block_length", 400)
        grid_h_count = kwargs.get("grid_h_count", 3)
        grid_w_count = kwargs.get("grid_w_count", 3)
        k_path = kwargs.get("k_path", 1)
        threads = kwargs["num_threads"]
        snap_script_args = "%s %s %s %s %s %s %s "\
                           "%s %s %s" % (exec_name, seq1, seq2, matrix,
                                         block_height, block_length,
                                         grid_h_count, grid_w_count,
                                         k_path, threads)
        key = "__PLSA__"

    elif test_name == "ScalParC":
        exec_name = "$SNAP\/ScalParC\/scalparc"
        dataset = "$SNAP\/datasets\/ScalParC\/%s" % kwargs["dataset"]
        records = kwargs.get("num_records", 250000)
        attributes = kwargs.get("num_attributes", 32)
        classes = kwargs.get("num_classes", 2)
        threads = kwargs["num_threads"]
        snap_script_args = "%s %s %s %s %s %s" % (exec_name, dataset,
                                                  records, attributes,
                                                  classes, threads)
        key = "__ScalParC__"

    elif test_name == "SEMPHY":
        exec_name = "$SNAP\/SEMPHY\/programs\/semphy\/semphy"
        dataset = "$SNAP\/datasets\/semphy\/%s" % kwargs["dataset"]
        alpha = kwargs.get("alpha", 0.3)
        threads = kwargs["num_threads"]
        snap_script_args = "env OMP_NUM_THREADS=%s %s "\
                           "-s %s -A %s" % (threads, exec_name, dataset, alpha)
        key = "__SEMPHY__"

    elif test_name == "SVM_RFE":
        exec_name = "$SNAP\/SVM-RFE\/svm_mkl"
        dataset = "$SNAP\/datasets\/SVM-RFE\/%s" % kwargs["dataset"]
        cases = kwargs.get("num_cases", 253)
        genes = kwargs.get("num_genes", 15154)
        iterations = kwargs.get("num_iter", 30)
        threads = kwargs["num_threads"]
        snap_script_args = "env OMP_NUM_THREADS=%s %s %s"\
                           "%s %s %s" % (threads, exec_name, dataset,
                                         cases, genes, iterations)
        key = "__SVM_RFE__"

    elif test_name == "ParETI":
        ld_lib_path = "$SNAP\/usr\/lib:$SNAP\/usr\/lib\/x86_64-linux-gnu:\/usr\/lib"
        exec_name = "env LD_LIBRARY_PATH=%s "\
                    "$SNAP\/usr\/bin\/mpirun.openmpi --allow-run-as-root -np %s "\
                    "$SNAP\/ParETI\/pareti" % (ld_lib_path, kwargs["num_cpu"])
        dataset = "$SNAP\/datasets\/ETI\/%s" % kwargs["dataset"]
        support = kwargs.get("support", 3000)
        epsilon = kwargs.get("epsilon", 0.5)
        snap_script_args = "%s %s %s %s" % (exec_name, dataset, support, epsilon)
        key = "__ParETI__"

    elif test_name == "RSEARCH":
        exec_name = "$SNAP\/RSEARCH\/rsearch"
        matrix = "$SNAP\/datasets\/rsearch\/matrices\/%s" % kwargs["matrix_file"]
        sequence = "$SNAP\/datasets\/rsearch\/Queries\/%s" % kwargs["seq_file"]
        db_file = "$SNAP\/datasets\/rsearch\/Databasefile\/%s" % kwargs["db_file"]
        e_val_cutoff = kwargs.get("e_value_cutoff", 10)
        evd_samples = kwargs.get("evd_samples", 1000)
        threads = kwargs["num_threads"]
        snap_script_args = "env OMP_NUM_THREADS=%s %s -c -n %s -E %s "\
                           "-m %s %s %s" % (threads, exec_name, evd_samples,
                                            e_val_cutoff, matrix,
                                            sequence, db_file)
        key = "__RSEARCH__"

    elif test_name == "BIRCH":
        exec_name = "$SNAP\/BIRCH\/birch"
        para_file = "$SNAP\/datasets\/birch\/%s" % kwargs["para_file"]
        schema_file = "$SNAP\/datasets\/birch\/%s" % kwargs["schema_file"]
        proj_file = "$SNAP\/datasets\/birch\/%s" % kwargs["proj_file"]
        dataset = "$SNAP\/datasets\/birch\/%s" % kwargs["dataset"]
        snap_script_args = "%s %s %s %s %s" % (exec_name, para_file,
                                               schema_file, proj_file, dataset)
        key = "__BIRCH__"

    elif test_name == "Apriori":
        exec_name = "$SNAP\/Apriori\/omp_apriori"
        dataset = "$SNAP\/datasets\/APR\/%s" % kwargs["dataset"]
        offset_file = "$SNAP\/datasets\/APR\/%s_P%s.txt" % (kwargs["offset_file"],
                                                            kwargs["num_threads"])
        num_threads = kwargs["num_threads"]
        min_support_perc = kwargs.get("min_support_perc", 0.0075)
        snap_script_args = "%s -i %s -f %s "\
                           "-n %s -s %s" % (exec_name, dataset, offset_file,
                                            num_threads, min_support_perc)
        key = "__APRIORI__"

    elif test_name == "ECLAT":
        # NOTE: ECLAT requires special .conf files and other files. Assume that
        # utility scripts have run before this is done
        exec_name = "$SNAP\/ECLAT\/eclat"
        dataset = "$SNAP\/datasets\/APR\/%s" % kwargs["dataset"]
        partitions = kwargs.get("partitions", 4)
        min_support_perc = kwargs.get("min_support_perc", 0.0075)
        snap_script_args = "%s -i %s -s %s -e %s" % (exec_name, dataset,
                                                     min_support_perc,
                                                     partitions)
        key = "__ECLAT__"

    elif test_name == "Bayesian":
        exec_name = "$SNAP\/Bayesian\/bayes\/src\/bci"
        header_file = "$SNAP\/datasets\/Bayesian\/%s" % kwargs["header_file"]
        table_file = "$SNAP\/datasets\/Bayesian\/%s" % kwargs["table_file"]
        bc_file = "$SNAP\/datasets\/Bayesian\/%s" % kwargs["bc_file"]
        snap_script_args = "%s -d %s %s %s" % (exec_name, header_file,
                                               table_file, bc_file)
        key = "__BAYESIAN__"

    elif test_name == "SysbenchMem":
        ld_lib_path = "$SNAP\/usr\/lib:$SNAP\/usr\/lib\/x86_64-linux-gnu:\/usr\/lib"
        exec_name = "env LD_LIBRARY_PATH=%s "\
                    "$SNAP\/usr\/bin\/sysbench" % ld_lib_path
        num_threads = kwargs.get("num_threads", 1)
        mem_block_size = kwargs.get("mem_block_size", "50G")
        total_mem_size = kwargs.get("total_mem_size", "1000G")
        snap_script_args = "%s --test=memory --num-threads=%s "\
                           "--memory-block-size=%s "\
                           "--memory-total-size=%s run" % (exec_name, num_threads,
                                                           mem_block_size,
                                                           total_mem_size)
        key = "__SYSBENCH_MEM__"

    elif test_name == "SysbenchDisk":
        ld_lib_path = "$SNAP\/usr\/lib:$SNAP\/usr\/lib\/x86_64-linux-gnu:\/usr\/lib"
        exec_name = "env LD_LIBRARY_PATH=%s "\
                    "$SNAP\/usr\/bin\/sysbench" % ld_lib_path
        num_threads = kwargs.get("num_threads", 1)
        file_total_size = kwargs.get("file_total_size", "3G")
        file_test_mode = kwargs.get("file_test_mode", "rndrw")
        max_requests = kwargs.get("max_requests", 0)
        max_time = kwargs.get("max_time", 300)
        snap_script_args = "%s --test=fileio --num-threads=%s "\
               "--file-total-size=%s --file-test-mode=%s --max-requests=%s "\
               "--max-time=%s run" % (exec_name, num_threads, file_total_size,
                                      file_test_mode, max_requests, max_time)
        key = "__SYSBENCH_DISK__"

    elif test_name == "SysbenchDiskPrep":
        ld_lib_path = "$SNAP\/usr\/lib:$SNAP\/usr\/lib\/x86_64-linux-gnu:\/usr\/lib"
        exec_name = "env LD_LIBRARY_PATH=%s "\
                    "$SNAP\/usr\/bin\/sysbench" % ld_lib_path
        file_total_size = kwargs.get("file_total_size", "3G")
        snap_script_args = "%s --test=fileio "\
                           "--file-total-size=%s prepare" % (exec_name,
                                                             file_total_size)
        key = "__SYSBENCH_DISK_PREP__"

    elif test_name == "SysbenchDiskCleanup":
        ld_lib_path = "$SNAP\/usr\/lib:$SNAP\/usr\/lib\/x86_64-linux-gnu:\/usr\/lib"
        exec_name = "env LD_LIBRARY_PATH=%s "\
                    "$SNAP\/usr\/bin\/sysbench" % ld_lib_path
        file_total_size = kwargs.get("file_total_size", "3G")
        snap_script_args = "%s --test=fileio "\
                           "--file-total-size=%s cleanup" % (exec_name,
                                                             file_total_size)
        key = "__SYSBENCH_DISK_CLEANUP__"


    else:
        assert False, "Unsupported testcase"

    return key, snap_script_args

def build_test_dict(test_spec, test_type=""):
    """Expected input format of test_spec is like this:

    [(test_name1, {"arg1":val1, "arg2":val2}),
     (test_name2, ...) ]

    """
    tests = {}
    for test_name, test_kwargs in test_spec:
        key, val = generate_test_args(test_name, **test_kwargs)
        key += test_type
        tests[key] = val
    return tests

def run_snap(shell, test_name, cpu=0, interference=False):
    if type(cpu) == int:
        cpu = [str(cpu)]
    elif type(cpu) == list:
        cpu = map(str, cpu)
    output = "-" * 30 + "\n"

    # Drop VM caches before every run to not see false gains
    #shell.run("sync")
    #shell.run("echo 3 | sudo tee /proc/sys/vm/drop_caches")

    if test_name == "__SYSBENCH_DISK__":
        # Need to run prepare and cleanup scripts before running snap
        shell.run("sudo snap run minebench.SysbenchDiskPrep")

    sysbench_test = "SYSBENCH" in test_name
    if sysbench_test:
        # Don't run perf stat for sysbench tests as they may hamper performance
        cmd = "sudo taskset -c %s snap run %s" % (",".join(cpu),
                                                  snap_app_cmd[test_name])
        output += "%s\n" % cmd
    else:
        cmd = "sudo perf stat -d taskset -c %s "\
              "snap run %s" % (",".join(cpu), snap_app_cmd[test_name])

    if interference:
        # Spawn a snap process which runs just before us
        proc1 = shell.spawn(cmd, store_pid=True)

    # Run the actual snap command and measure its running time
    result = shell.run(cmd)
    # Since we don't run perf stat for sysbench tests, we need to save the
    # output for parsing later
    output += result.output if sysbench_test else result.stderr_output

    if interference:
        # Measure the running time of the first process
        result = proc1.wait_for_result()
        # Since we don't run perf stat for sysbench tests, we need to save the
        # output for parsing later
        output += "%s\n" % cmd if sysbench_test else ""
        output += result.output if sysbench_test else result.stderr_output

    if test_name == "__SYSBENCH_DISK__":
        # Need to run prepare and cleanup scripts before running snap
        shell.run("sudo snap run minebench.SysbenchDiskCleanup")
        
    return output

def parse_host(host_str):
    """Parses strings of the format <hostname:port> and returns the necessary
    fqdn and port"""
    values = host_str.split(':')
    if len(values) == 1:
        # If port hasn't been provided, assume the default SSH port 22
        host, port = values[0], 22
    elif len(values) == 2:
        host, port = values
    else:
        assert False, "Unparseable string: %s" % host_str

    # If domain name is not provided, assume it is a node on Wisc CloudLab
    if "cloudlab" not in host:
        domain_name = ".wisc.cloudlab.us"
        host += domain_name

    return host, port

def create_ssh_shell(hostname, username=USERNAME, password=None, port=22):
    """Utility function which creates a TestShell class"""
    # Accept even if host key is missing. Without this, it just fails and quits.
    return TestShell(hostname=hostname, username=username,
                     password=password, port=port,
                     missing_host_key=spur.ssh.MissingHostKey.accept)

def install_pkg(shell, pkg_name):
    # Check if the package already exists. If not, install it
    try:
        # Redirect the output blob since only care about return code
        shell.run("dpkg -s %s > /dev/null" % pkg_name, use_bash=True)
    except:
        # Package doesn't exist. Install it
        try:
            shell.run("sudo apt-get install -y %s" % pkg_name)
        except:
            # Sometimes we may fail to install because we haven't run update in
            # a while.
            shell.run("sudo apt-get update")
            shell.run("sudo apt-get install -y %s" % pkg_name)

def get_test_spec(workload_type, test_type, num_threads=1):
    if workload_type == "parallel":
        if test_type == "small":
            test_spec = list(PARALLEL_S_TEST_SPEC)
        elif test_type == "medium":
            test_spec = list(PARALLEL_M_TEST_SPEC)
        elif test_type == "large":
            test_spec = list(PARALLEL_L_TEST_SPEC)
        else:
            assert False, "Unsupported test type %s" % test_type

        for test_name, test_args in test_spec:
            test_args["num_threads"] = num_threads

    elif workload_type == "serial":
        if test_type == "small":
            test_spec = list(SERIAL_S_TEST_SPEC)
        elif test_type == "medium":
            test_spec = list(SERIAL_M_TEST_SPEC)
        elif test_type == "large":
            test_spec = list(SERIAL_L_TEST_SPEC)
        else:
            assert False, "Unsupported test type %s" % test_type
    else:
        assert False, "Unsupported workload type: %s" % workload_type

    return test_spec

def build_minebench_snap(shell, num_threads):
    """
    Creates the appropriate testspec for creating the YAML file and then builds
    the minebench snap.
    """
    final_test_spec = []
    final_test_dict = {}

    for workload_type in ("serial", "parallel"):
        for test_type in ("small", "medium", "large"):
            # Get the necessary test spec and dictionaries
            test_spec = get_test_spec(workload_type, test_type, num_threads)
            test_dict = build_test_dict(test_spec, test_type=test_type)

            # Update our global test spec and dictionaries
            final_test_spec.extend(test_spec)
            final_test_dict.update(test_dict)

    # Add the Sysbench related tests
    final_test_spec.extend(SYSBENCH_TEST_SPEC)
    test_dict = build_test_dict(SYSBENCH_TEST_SPEC)
    final_test_dict.update(test_dict)

    # Add the Sysbench util related scripts
    final_test_spec.extend(SYSBENCH_UTIL_TEST_SPEC)
    test_dict = build_test_dict(SYSBENCH_UTIL_TEST_SPEC)
    final_test_dict.update(test_dict)

    # Now build our snap
    _build_minebench_yaml_and_snap(shell, final_test_dict, final_test_spec)

def generate_apriori_files(shell, data_file, offset_file, partitions):
    # Make sure our offset program exists
    shell.run("cd snap/prime/Apriori; make offsets", use_bash=True)

    offsets_cmd = "snap/prime/Apriori/offsets"
    data_prefix = "snap/prime/datasets/APR"

    # First generate the data binary
    shell.run("%s %s/%s %s | tee %s/%s_P%s.txt" % (offsets_cmd, data_prefix,
                                                   data_file, partitions,
                                                   data_prefix, offset_file,
                                                   partitions))

def check_apriori_data(shell, test_spec):
    data_prefix = "snap/prime/datasets/APR"
    changed = False
    for test_name, args in test_spec:
        if test_name != "Apriori":
            continue
        # Check if conf file exists
        try:
            shell.run("ls %s/%s_P%s.txt" % (data_prefix, args["offset_file"],
                                            args["num_threads"]))
        except spur.RunProcessError:
            generate_apriori_files(shell, args["dataset"], args["offset_file"],
                                   args["num_threads"])
            changed = True

    return changed

def generate_eclat_files(shell, data_file, partitions):
    bin_cmd = "snap/prime/ECLAT/util/makebin"
    conf_cmd = "snap/prime/ECLAT/util/getconf"
    tpose_cmd = "snap/prime/ECLAT/util/exttpose"
    data_prefix = "snap/prime/datasets/APR"

    # First generate the data binary
    shell.run("%s %s/data.%s %s/%s.data" % (bin_cmd, data_prefix,
                                            data_file, data_prefix,
                                            data_file))
    # Generate the conf files
    shell.run("%s -i %s/%s -o %s/%s" % (conf_cmd, data_prefix, data_file,
                                        data_prefix, data_file))

    # Generate the tpose files
    shell.run("env LD_PRELOAD=/usr/lib/libtcmalloc_minimal.so.4 "
              "%s -i %s/%s -o %s/%s "\
              "-p %s" % (tpose_cmd, data_prefix, data_file, data_prefix,
                         data_file, partitions))

def check_eclat_data(shell, test_spec):
    data_prefix = "snap/prime/datasets/APR"
    changed = False
    for test_name, args in test_spec:
        if test_name != "ECLAT":
            continue
        # Check if conf file exists
        try:
            shell.run("ls %s/%s.conf" % (data_prefix, args["dataset"]))
        except spur.RunProcessError:
            generate_eclat_files(shell, args["dataset"], args["partitions"])
            changed = True

    return changed

def disable_hyperthreading(shell):
    # Assume that this is c220g1 for now
    assert "c220g1" in shell.run("hostname -A").output

    cores = 32
    for cpu_core in xrange(cores/2, cores):
        shell.run("echo 0 | sudo tee /sys/devices/system/cpu/cpu%d/online" %
                  cpu_core)

def setup_perf(shell):
    version = shell.run("uname -r").output.strip()
    pkgs = ["linux-tools-common", "linux-tools-%s" % version,
            "linux-cloud-tools-%s" % version]
    for pkg in pkgs:
        install_pkg(shell, pkg)

def setup_minebench_snap_deps(shell):
    try:
        shell.run("ls snap/snapcraft.yaml")
    except spur.RunProcessError:
        install_pkg(shell, "snapd")
        install_pkg(shell, "snapcraft")
        install_pkg(shell, "libopenmpi-dev")
        install_pkg(shell, "libtcmalloc-minimal4")
        shell.run("snapcraft init")

    shell.run("sudo snap remove minebench", allow_error=True)

def _build_minebench_yaml_and_snap(shell, test_dict, test_spec):
    shell.copyFile("snapcraft.yaml", "snap/snapcraft.yaml")
    shell.copyFile("wrapper", "snap/wrapper")
    shell.run("chmod +x snap/wrapper")

    # Modify snapcraft YAML
    for key, value in test_dict.items():
        shell.run("sed -i -e 's/%s/%s/g' snap/snapcraft.yaml" % (key, value))

    # Remove the previous version for sanity
    shell.run("sudo snap remove minebench", allow_error=True)

    # Finally build our snap
    try:
        shell.run("cd snap; snapcraft", use_bash=True)
    except spur.RunProcessError:
        # Sometimes we hit an error because of cleanup issues. Cleanup and try
        # again.
        shell.run("cd snap; snapcraft clean", use_bash=True)
        shell.run("cd snap; snapcraft", use_bash=True)

    changed = False

    # Check if the eclectic data file requirements of ECLAT are satisfied
    changed |= check_eclat_data(shell, test_spec)

    # Check if requirements of Apriori are satisfied
    changed |= check_apriori_data(shell, test_spec)

    if changed:
        # Need to rebuild snap
        shell.run("cd snap; snapcraft", use_bash=True)

    # Install it now
    shell.run("sudo snap install --devmode snap/minebench_0.1_amd64.snap")

    # Remove the snap because it occupies a lot of space
    shell.run("rm snap/minebench_0.1_amd64.snap")

def setup_shell(host_str):
    hostname, port = parse_host(host_str)
    shell = create_ssh_shell(hostname, port=int(port))
    setup_minebench_snap_deps(shell)
    setup_perf(shell)
    disable_hyperthreading(shell)
    return shell

