#include "inference.h"
#include "../weights/fc1_weight.h"
#include "../weights/fc1_bias.h"
#include "../weights/fc2_weight.h"
#include "../weights/fc2_bias.h"
#include "../weights/fc3_weight.h"
#include "../weights/fc3_bias.h"


static float buf1[32]; 
static float buf2[16]; 
static float buf3[3];

int8_t predict(const float* input){
  
  float sum = 0; 

  for(int i = 0; i < 32; i++){
       sum = 0; 
       for(int j = 0; j < 8; j++)
           sum += FC1_WEIGHT[i][j] * input[j] + FC1_BIAS[i];

       buf1[i] = sum > 0 ? sum : 0;
   } 

   for(int i = 0; i < 16; i++){
       sum = 0; 
       for(int j = 0; j < 32; j++)
           sum += FC2_WEIGHT[i][j] * buf1[j] + FC2_BIAS[i];

       buf2[i] = sum > 0 ? sum : 0;
   }
   
   for(int i = 0; i < 3; i++){
       sum = 0; 
       for(int j = 0; j < 16; j++)
           sum += FC3_WEIGHT[i][j] * buf2[j] + FC3_BIAS[i];

       buf3[i] = sum; 
   }

   int8_t argmax = 0;
   float arg = 0; 
   for(int i = 0; i < 3; i++)
     if(arg < buf3[i]){
         arg = buf3[i]; 
         argmax = i; 
     } 
    
   return argmax+1; 
}

