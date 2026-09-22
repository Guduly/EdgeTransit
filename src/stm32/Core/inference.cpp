#include "inference.h"
#include <float.h> // For FLT_MAX
#include "../weights/fc1_weight.h"
#include "../weights/fc1_bias.h"
#include "../weights/fc2_weight.h"
#include "../weights/fc2_bias.h"
#include "../weights/fc3_weight.h"
#include "../weights/fc3_bias.h"

// Static buffers keep allocations out of the heap and stack
static float buf1[32]; 
static float buf2[16]; 
static float buf3[3];

int8_t predict(const float* input){
    
    // --- LAYER 1: FC (8 -> 32) + ReLU ---
    for(int i = 0; i < 32; i++){
        // Initialize sum with the bias to fix the duplication bug
        float sum = FC1_BIAS[i]; 
        
        // Unroll small inner loops or let compiler know it's fixed
        for(int j = 0; j < 8; j++) {
            sum += FC1_WEIGHT[i][j] * input[j];
        }
        
        // Branchless ReLU optimization
        buf1[i] = (sum > 0.0f) ? sum : 0.0f;
    } 

    // --- LAYER 2: FC (32 -> 16) + ReLU ---
    for(int i = 0; i < 16; i++){
        float sum = FC2_BIAS[i]; 
        for(int j = 0; j < 32; j++) {
            sum += FC2_WEIGHT[i][j] * buf1[j];
        }
        buf2[i] = (sum > 0.0f) ? sum : 0.0f;
    }
   
    // --- LAYER 3: FC (16 -> 3) ---
    for(int i = 0; i < 3; i++){
        float sum = FC3_BIAS[i]; 
        for(int j = 0; j < 16; j++) {
            sum += FC3_WEIGHT[i][j] * buf2[j];
        }
        buf3[i] = sum; 
    }

    // --- ARGMAX ---
    int8_t argmax = 0;
    float max_val = -FLT_MAX; // Fixes bug if all outputs are negative
    
    for(int i = 0; i < 3; i++) {
        if(buf3[i] > max_val){
            max_val = buf3[i]; 
            argmax = i; 
        } 
    }
    
    return argmax; 
}
