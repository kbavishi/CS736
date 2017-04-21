# Performance Isolation Methodology

This document talks about the nitty gritties of the experimental setup and benchmarks used in our performance isolation studies.

## Machine Setup

We use CloudLab for our experiments. The exact settings of the DUT are given below. For ease of testing, please import the CloudLab [profile](profile/cloudlab_profile.py), which uses all of these settings to pick an appropriate machine in the Wisconsin CloudLab cluster.

## Machine Details

* OS: Ubuntu 16.04
* Kernel version: 4.4.0-45-generic
* Hyperthreading disabled (Disable cores 16-31. More info [here](#testing-tools-and-notes))
* Hardware details: See section for c220g1 [here](http://docs.cloudlab.us/hardware.html)

## Datasets to be downloaded

1. APR.tar.gz
2. birch.tar.gz
3. HOP.tar.gz
4. kmeans.tar.gz
5. ScalParC.tar.gz

The link to the download page is [here](http://cucis.ece.northwestern.edu/projects/DMS/MineBenchDownload.html)

## MineBench tests (CPU isolation)

We run 6 different kinds of workloads structured along 2 dimensions: type of test (ie. serial or parallel), and size of dataset (small, medium or large). 

The tests along with their arguments and dataset names are stated below for each workload.
* Serial Tests: ECLAT, BIRCH
* Parallel Tests: Fuzzy KMeans, KMeans, Apriori, ScalParC, HOP


### S1: Serial tests, small datasets

```
ECLAT/eclat -i datasets/APR/ntrans_400.tlen_10.nitems_1.npats_2000.patlen_6 -s 0.0075 -e 4
BIRCH/birch datasets/birch/AMR_64.para datasets/birch/AMR_64.scheme datasets/birch/AMR_64.proj datasets/birch/particles_0_64_ascii
```

NOTE - We need to preprocess the dataset for ECLAT before it can be used. Please see the [Issues section](#issues) for more details.

### S2: Serial tests, medium datasets

```
ECLAT/eclat -i datasets/APR/ntrans_1000.tlen_10.nitems_1.npats_2000.patlen_6 -s 0.0075 -e 4
BIRCH/birch datasets/birch/AMR_128.para datasets/birch/AMR_128.scheme datasets/birch/AMR_128.proj datasets/birch/particles_0_128_ascii
```

NOTE - We need to preprocess the dataset for ECLAT before it can be used. Please see the [Issues section](#issues) for more details.

### S3: Serial tests, large datasets

```
ECLAT/eclat -i datasets/APR/ntrans_2000.tlen_20.nitems_1.npats_2000.patlen_6 -s 0.0075 -e 4
BIRCH/birch datasets/birch/AMR_256.para datasets/birch/AMR_256.scheme datasets/birch/AMR_256.proj datasets/birch/particles_0_256_ascii
```

NOTE - We need to preprocess the dataset for ECLAT before it can be used. Please see the [Issues section](#issues) for more details.

### P1: Parallel tests, small datasets

```
KMeans/example -i datasets/kmeans/edge100 -o -f -p <num_threads>
KMeans/example -i datasets/kmeans/edge100 -o -p <num_threads>
Apriori/omp_apriori -i datasets/APR/data.ntrans_400.tlen_10.nitems_1.npats_2000.patlen_6 -f datasets/APR/offset_file_400_10_1_P1.txt -n <num_threads> -s 0.0075
ScalParC/scalparc datasets/ScalParC/para_F26-A32-D125K/F26-A32-D125K.tab 125000 32 2 <num_threads>
HOP/para_hop 61440 datasets/HOP/particles_0_64 64 16 -1 <num_threads>
```

NOTE - We need to preprocess the dataset for Apriori before it can be used. Please see the [Issues section](#issues) for more details.

### P2: Parallel tests, medium datasets

```
KMeans/example -i datasets/kmeans/edge -b -o -f -p <num_threads>
KMeans/example -i datasets/kmeans/edge -b -o -p <num_threads>
Apriori/omp_apriori -i datasets/APR/data.ntrans_1000.tlen_10.nitems_1.npats_2000.patlen_6 -f datasets/APR/offset_file_1000_10_1_P1.txt -n <num_threads> -s 0.0075
ScalParC/scalparc datasets/ScalParC/para_F26-A32-D250K/F26-A32-D250K.tab 250000 32 2 <num_threads>
HOP/para_hop 61440 datasets/HOP/particles_0_128 64 16 -1 <num_threads>
```

NOTE - We need to preprocess the dataset for Apriori before it can be used. Please see the [Issues section](#issues) for more details.

### P3: Parallel tests, large datasets

```
Apriori/omp_apriori -i datasets/APR/data.ntrans_2000.tlen_20.nitems_1.npats_2000.patlen_6 -f datasets/APR/offset_file_2000_20_1_P1.txt -n <num_threads> -s 0.0075
ScalParC/scalparc datasets/ScalParC/para_F26-A64-D250K/F26-A64-D250K.tab 250000 64 2 <num_threads>
HOP/para_hop 61440 datasets/HOP/particles_0_256 64 16 -1 <num_threads>
```

NOTE - We need to preprocess the dataset for Apriori before it can be used. Please see the [Issues section](#issues) for more details.

## Memory Isolation

TODO

## Disk Isolation

TODO

## Experiment methodology

### Measuring performance isolation

We measure the performance isolation using two metrics:
* Fairness metric - Indicates how fairly are resources distributed between competing instances.
* Cohabitation metric - Indicates whether instances happen to be mutually destructive.

The fairness metric is based on [Jain's fairness metric](https://en.wikipedia.org/wiki/Fairness_measure), and is calculated in the following manner:
1. Run a standalone instance of a test and record its completion time. Let's denote this by ```T-standalone```
2. Run two instances of the same test in parallel, and record the completion times of both processes. Let's denote them by ```T1-int``` and ```T2-int```.
3. Repeat steps 1 and 2 to get 5 runs.
4. Fairness metric F is calculated using the following formula: ```F = (avg(T1-int) + avg(T2-int))^2 / 2*(avg(T1-int)^2 + avg(T2-int)^2)```. The worst case value of F is 0.5, and the best case value is closer to 1.
5. Cohab metric C is calculated by: ```C = (avg(T1-int) + avg(T2-int)) / 2*avg(T-standalone)```. Ideally, we expect the 2 parallel instances testcase to take no more than twice the amount of time for the standalone testcase. Therefore, a value of C > 2.0 indicates mutually detrimental processes.

### Testing tools and notes
1. Perform 5 runs of each workload type and use the average completion time for the metric calculation.
2. We will use ```perf stat``` to measure the completion time of a test.
3. We will use ```taskset``` to pin the test process to particular cores.
5. Disable hyperthreading by disabling cores 16-31: ```echo 0 | sudo tee /sys/devices/system/cpu/cpu16/online```. Replace with the appropriate CPU num in the previous command.

### Variation #1: Number of cores

We repeat all the workload experiments with different number of cores:
* C1: One core
* C4: Four cores
* C8: Eight cores

### Variation #2: Number of threads (for parallel workloads)

In addition, we will vary the number of threads for our parallel workloads to get a better sense of isolation for multithreaded applications:
* T1: One thread
* T8: Eight threads

### Summary of workloads 

In summary, we should have run the following workloads:
1. S1_C1
2. S1_C4
3. S1_C8
4. S2_C1
5. S2_C4
6. S2_C8
7. S3_C1
8. S3_C4
9. S3_C8
10. P1_C1_T1
11. P1_C4_T1
12. P1_C8_T1
13. P1_C1_T8
14. P1_C4_T8
15. P1_C8_T8
16. P2_C1_T1
17. P2_C4_T1
18. P2_C8_T1
19. P2_C1_T8
20. P2_C4_T8
21. P2_C8_T8
22. P3_C1_T1
23. P3_C4_T1
24. P3_C8_T1
25. P3_C1_T8
26. P3_C4_T8
27. P3_C8_T8

## Issues

1. ECLAT preprocessing - The APR datasets are not ready to be used for ECLAT as is, and need to go through some preprocessing. Here are the steps to be followed:
```
sudo apt-get -y install libtcmalloc-minimal4
cd ECLAT/util
make
./makebin ../../datasets/APR/data.ntrans_400.tlen_10.nitems_1.npats_2000.patlen_6 ../datasets/APR/ntrans_400.tlen_10.nitems_1.npats_2000.patlen_6.data
./getconf -i ../../datasets/APR/ntrans_400.tlen_10.nitems_1.npats_2000.patlen_6 -o ../datasets/APR/ntrans_400.tlen_10.nitems_1.npats_2000.patlen_6
env LD_PRELOAD=/usr/lib/libtcmalloc_minimal.so.4 ./exttpose -i ../../datasets/APR/ntrans_400.tlen_10.nitems_1.npats_2000.patlen_6 -o ../datasets/APR/ntrans_400.tlen_10.nitems_1.npats_2000.patlen_6 -p 4
```

Replace the dataset file with the appropriate one in the steps above.

2. Apriori preprocessing - The offsets file needed by Apriori may not be present, and therefore needs to be generated for the test to run. Also note that these steps need to be performed everytime we pick a different value for ```num_threads```.
```
cd Apriori
make offsets
./offsets ../datasets/APR/data.ntrans_2000.tlen_20.nitems_1.npats_2000.patlen_6 <num_threads> | tee ../datasets/APR/offset_file_2000_20_1_P<num_threads>.txt
```

Replace the dataset file, offset file and number of threads with the appropriate values.

