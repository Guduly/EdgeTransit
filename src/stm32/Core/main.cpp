#include "stm32f4xx_hal.h"
#include "inference.h"

UART_HandleTypeDef huart2;

// ----------------------------------------------------------------------------
// System Clock Configuration
// Sets up 180MHz using HSI (internal 16MHz oscillator)
// HSI(16MHz) → PLL → SYSCLK(180MHz)
// ----------------------------------------------------------------------------
void SystemClock_Config(void) {
    RCC_OscInitTypeDef RCC_OscInitStruct = {0};
    RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

    // Enable power controller clock and set voltage scaling
    __HAL_RCC_PWR_CLK_ENABLE();
    __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

    // Configure HSI as PLL source
    RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
    RCC_OscInitStruct.HSIState       = RCC_HSI_ON;
    RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
    RCC_OscInitStruct.PLL.PLLState   = RCC_PLL_ON;
    RCC_OscInitStruct.PLL.PLLSource  = RCC_PLLSOURCE_HSI;
    // HSI(16) / PLLM(8) = 2MHz VCO input
    // 2MHz * PLLN(180) = 360MHz VCO output
    // 360MHz / PLLP(2) = 180MHz SYSCLK
    RCC_OscInitStruct.PLL.PLLM      = 8;
    RCC_OscInitStruct.PLL.PLLN      = 180;
    RCC_OscInitStruct.PLL.PLLP      = RCC_PLLP_DIV2;
    RCC_OscInitStruct.PLL.PLLQ      = 4;
    HAL_RCC_OscConfig(&RCC_OscInitStruct);

    // Enable Over-Drive mode to reach 180MHz
    HAL_PWREx_ActivateOverDrive();

    // Configure bus clocks
    // SYSCLK=180MHz, AHB=180MHz, APB1=45MHz, APB2=90MHz
    RCC_ClkInitStruct.ClockType      = RCC_CLOCKTYPE_HCLK  |
                                       RCC_CLOCKTYPE_SYSCLK |
                                       RCC_CLOCKTYPE_PCLK1  |
                                       RCC_CLOCKTYPE_PCLK2;
    RCC_ClkInitStruct.SYSCLKSource   = RCC_SYSCLKSOURCE_PLLCLK;
    RCC_ClkInitStruct.AHBCLKDivider  = RCC_SYSCLK_DIV1;
    RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV4;
    RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV2;
    HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_5);
}

// ----------------------------------------------------------------------------
// UART2 Initialization
// PA2 = TX, PA3 = RX (connected to ST-Link USB on Nucleo)
// 115200 baud, 8N1
// ----------------------------------------------------------------------------
void UART2_Init(void) {
    // Enable clocks for GPIOA and USART2
    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_USART2_CLK_ENABLE();

    // Configure PA2 and PA3 as alternate function (UART)
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    GPIO_InitStruct.Pin       = GPIO_PIN_2 | GPIO_PIN_3;
    GPIO_InitStruct.Mode      = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Pull      = GPIO_NOPULL;
    GPIO_InitStruct.Speed     = GPIO_SPEED_FREQ_VERY_HIGH;
    GPIO_InitStruct.Alternate = GPIO_AF7_USART2;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    // Configure UART peripheral
    huart2.Instance          = USART2;
    huart2.Init.BaudRate     = 115200;
    huart2.Init.WordLength   = UART_WORDLENGTH_8B;
    huart2.Init.StopBits     = UART_STOPBITS_1;
    huart2.Init.Parity       = UART_PARITY_NONE;
    huart2.Init.Mode         = UART_MODE_TX_RX;
    huart2.Init.HwFlowCtl    = UART_HWCONTROL_NONE;
    huart2.Init.OverSampling = UART_OVERSAMPLING_16;
    HAL_UART_Init(&huart2);
}

// ----------------------------------------------------------------------------
// SysTick Handler
// Called every 1ms by HAL to update the tick counter
// Must be extern "C" so the C startup file can find it by name
// ----------------------------------------------------------------------------
extern "C" void SysTick_Handler(void) {
    HAL_IncTick();
}

// ----------------------------------------------------------------------------
// Main
// ----------------------------------------------------------------------------
int main(void) {
    // Initialize HAL (sets up SysTick at 1ms, resets peripherals)
    HAL_Init();

    // Configure system clock to 180MHz
    SystemClock_Config();

    // Initialize UART2 at 115200 baud
    UART2_Init();

    // Receive buffer: 8 floats × 4 bytes = 32 bytes
    uint8_t rx_buf[32];
    uint8_t result;

    while(1) {
        // Block until 32 bytes arrive from PC
        // HAL_MAX_DELAY means wait forever — no timeout
        HAL_UART_Receive(&huart2, rx_buf, 32, HAL_MAX_DELAY);

        // Reinterpret raw bytes as float array
        // No copy — same memory, different type interpretation
        float* features = reinterpret_cast<float*>(rx_buf);

        // Run MLP forward pass
        result = (uint8_t)predict(features);

        // Send predicted class back (0=On-Time, 1=Late, 2=Severely Late)
        HAL_UART_Transmit(&huart2, &result, 1, HAL_MAX_DELAY);
    }
}
