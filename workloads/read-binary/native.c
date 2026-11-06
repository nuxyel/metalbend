// read-binary's target: read-native's C, unchanged. Both workloads read the same 16 MB of data/dense.bin into an array
// of F32 and print its hash, so one fread is the C version of either read.
#include "../read-native/native.c"
