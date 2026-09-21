#include "stm32f4xx_hal.h"

UART_HandleTypeDef huart2; 

extern "C" {
    void SystemClock_Config(void); 
    void HAL_UART_MspInit(UART_HandleTypeDef* huart);

    void SysTick_Handler(void){
        HAL_IncTick();
    }
}

int main(){
    return 0; 
}


