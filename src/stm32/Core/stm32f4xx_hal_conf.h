
#pragma once

/* ========================================================================== */
/* 1. Module Selection (Uncomment what you need)                             */
/* ========================================================================== */
#define HAL_MODULE_ENABLED
#define HAL_CORTEX_MODULE_ENABLED
#define HAL_GPIO_MODULE_ENABLED
#define HAL_RCC_MODULE_ENABLED
#define HAL_UART_MODULE_ENABLED
#define HAL_DMA_MODULE_ENABLED      /* Fixed: Properly matched with include below */
#define HAL_FLASH_MODULE_ENABLED
#define HAL_PWR_MODULE_ENABLED 


/* ========================================================================== */
/* 2. Hardware / Oscillator Values                                            */
/* ========================================================================== */
#define HSE_VALUE               8000000U
#define HSI_VALUE               16000000U
#define HSE_STARTUP_TIMEOUT     100U
#define LSE_STARTUP_TIMEOUT     5000U
#define LSE_VALUE               32768U
#define TICK_INT_PRIORITY       0U
#define USE_RTOS                0U
#define VDD_VALUE               3300U
#define USE_HAL_UART_REGISTER_CALLBACKS 0U

/* ========================================================================== */
/* 3. Mandatory HAL Configuration Macros                                     */
/* ========================================================================== */
#define  USE_HAL_LEGACY         0U
#define  MAC_ADDR0              2U
#define  MAC_ADDR1              0U
#define  MAC_ADDR2              0U
#define  MAC_ADDR3              0U
#define  MAC_ADDR4              0U
#define  MAC_ADDR5              0U

/* Exported macro ------------------------------------------------------------*/
#ifdef  USE_FULL_ASSERT
  #define assert_param(expr) ((expr) ? (void)0U : assert_failed((uint8_t *)__FILE__, __LINE__))
  void assert_failed(uint8_t* file, uint32_t line);
#else
  #define assert_param(expr) ((void)0U)
#endif

/* ========================================================================== */
/* 4. Peripheral Header Inclusions (ST Standard Structure)                    */
/* ========================================================================== */
#ifdef HAL_RCC_MODULE_ENABLED
  #include "stm32f4xx_hal_rcc.h"
#endif

#ifdef HAL_GPIO_MODULE_ENABLED
  #include "stm32f4xx_hal_gpio.h"
#endif

#ifdef HAL_DMA_MODULE_ENABLED
  #include "stm32f4xx_hal_dma.h"    /* Fixed: Essential for UART DMA functionality */
#endif

#ifdef HAL_CORTEX_MODULE_ENABLED
  #include "stm32f4xx_hal_cortex.h"
#endif

#ifdef HAL_UART_MODULE_ENABLED
  #include "stm32f4xx_hal_uart.h"
#endif

#ifdef HAL_FLASH_MODULE_ENABLED
  #include "stm32f4xx_hal_flash.h"
#endif

#ifdef HAL_PWR_MODULE_ENABLED
  #include "stm32f4xx_hal_pwr.h"
  #include "stm32f4xx_hal_pwr_ex.h"
#endif
