#pragma once
#include <stdint.h>

#define FC3_BIAS_SCALE 0.003358f
#define FC3_BIAS_SIZE 3

static const int8_t FC3_BIAS[3] = {
    127, -107, 107
};
