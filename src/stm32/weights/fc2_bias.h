#pragma once
#include <stdint.h>

#define FC2_BIAS_SCALE 0.004415f
#define FC2_BIAS_SIZE 16

static const int8_t FC2_BIAS[16] = {
    -35, 39, 127, 14, 15, -52, -32, -21, 105, 89, 77, 99, 51, -38, -29, 48
};
