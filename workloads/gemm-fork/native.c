// gemm-fork's target: gemm-tile8's C, unchanged. tensor-fork splits C into blocks of rows (or columns) and every block
// runs tensor-array's own Tile8 cells, so its bits are gemm-tile8's at every depth; on one thread, where run.sh times the
// C targets, the sequential product is its twin, and the ratio measures what the fork path costs over plain C.
#include "../gemm-tile8/native.c"
