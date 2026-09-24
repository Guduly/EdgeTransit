cmake_minimum_required(VERSION 3.20)

# Cross-compilation toolchain
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR arm)
set(CMAKE_C_COMPILER arm-none-eabi-gcc)
set(CMAKE_CXX_COMPILER arm-none-eabi-g++)
set(CMAKE_ASM_COMPILER arm-none-eabi-gcc)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)

project(edgetransit CXX C ASM)

# Cortex-M4 flags
set(CPU_FLAGS "-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard")
set(CMAKE_CXX_FLAGS "${CPU_FLAGS} -O2 -fno-exceptions -fno-rtti")
set(CMAKE_C_FLAGS   "${CPU_FLAGS} -O2")
set(CMAKE_ASM_FLAGS "${CPU_FLAGS}")

# Include paths
include_directories(
    Core
    weights
    cmsis-device-f4/Include
    CMSIS_6/CMSIS/Core/Include
    stm32f4xx-hal-driver/Inc
)

# HAL source files
file(GLOB HAL_SOURCES
    stm32f4xx-hal-driver/Src/stm32f4xx_hal.c
    stm32f4xx-hal-driver/Src/stm32f4xx_hal_rcc.c
    stm32f4xx-hal-driver/Src/stm32f4xx_hal_gpio.c
    stm32f4xx-hal-driver/Src/stm32f4xx_hal_uart.c
    stm32f4xx-hal-driver/Src/stm32f4xx_hal_cortex.c
    stm32f4xx-hal-driver/Src/stm32f4xx_hal_dma.c
    stm32f4xx-hal-driver/Src/stm32f4xx_hal_pwr.c
    stm32f4xx-hal-driver/Src/stm32f4xx_hal_pwr_ex.c
)

# Your sources (FIXED: system_stm32f4xx.c explicitly added back)
set(SOURCES
    Core/main.cpp
    Core/inference.cpp
    cmsis-device-f4/Source/Templates/gcc/startup_stm32f446xx.s
    cmsis-device-f4/Source/Templates/system_stm32f4xx.c
    ${HAL_SOURCES}
)

# Chip define — tells HAL which STM32F4 variant you have
add_definitions(-DSTM32F446xx -DUSE_HAL_DRIVER)

# Linker
set(LINKER_SCRIPT ${CMAKE_SOURCE_DIR}/STM32F446RE.ld)

set(CMAKE_EXE_LINKER_FLAGS
    "${CPU_FLAGS} -T${LINKER_SCRIPT} --specs=nosys.specs --specs=nano.specs -Wl,--gc-sections")

add_executable(edgetransit.elf ${SOURCES})

# Generate .bin file for flashing
add_custom_command(TARGET edgetransit.elf POST_BUILD
    COMMAND arm-none-eabi-objcopy -O binary edgetransit.elf edgetransit.bin
    COMMENT "Generating edgetransit.bin"
)
