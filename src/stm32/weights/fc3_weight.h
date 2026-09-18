#pragma once
#include <stdint.h>

#define FC3_WEIGHT_SCALE 0.050542f
#define FC3_WEIGHT_ROWS 3
#define FC3_WEIGHT_COLS 16

static const int8_t FC3_WEIGHT[3][16] = {
    {0, -62, 41, -5, 2, -48, -15, -2, 43, 37, 53, 34, -112, 9, -47, -51},
    {-1, -1, -27, -3, -4, 17, 21, -1, -23, -17, -50, -23, 127, 14, 55, -13},
    {3, 47, -13, 4, -4, 18, -9, 1, -39, -127, -47, -27, -41, -108, -16, 51},
};
