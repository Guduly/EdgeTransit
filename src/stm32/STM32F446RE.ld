_estack = ORIGIN(SRAM) + LENGTH(SRAM);

MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 512K
    SRAM  (rwx) : ORIGIN = 0x20000000, LENGTH = 128K
}

ENTRY(Reset_Handler)

SECTIONS
{
    /* The vector table and application code go into FLASH */
    .text :
    {
        . = ALIGN(4);
        KEEP(*(.isr_vector)) /* Vector table */
        *(.text)             /* Program code */
        *(.text*)            /* Program code sub-sections */
        *(.glue_7)           /* Glue arm to thumb code */
        *(.glue_7t)          /* Glue thumb to arm code */
        *(.eh_frame)

        KEEP (*(.init))
        KEEP (*(.fini))

        . = ALIGN(4);
        _etext = .;          /* Define global symbol for end of code */
    } > FLASH

    /* Constant data goes into FLASH */
    .rodata :
    {
        . = ALIGN(4);
        *(.rodata)
        *(.rodata*)
        . = ALIGN(4);
    } > FLASH

    /* C++ runtime initialization arrays required by __libc_init_array */
    .preinit_array :
    {
        . = ALIGN(4);
        PROVIDE_HIDDEN (__preinit_array_start = .);
        KEEP (*(.preinit_array*))
        PROVIDE_HIDDEN (__preinit_array_end = .);
    } > FLASH
  
    .init_array :
    {
        . = ALIGN(4);
        PROVIDE_HIDDEN (__init_array_start = .);
        KEEP (*(SORT(.init_array.*)))
        KEEP (*(.init_array*))
        PROVIDE_HIDDEN (__init_array_end = .);
    } > FLASH
  
    .fini_array :
    {
        . = ALIGN(4);
        PROVIDE_HIDDEN (__fini_array_start = .);
        KEEP (*(SORT(.fini_array.*)))
        KEEP (*(.fini_array*))
        PROVIDE_HIDDEN (__fini_array_end = .);
    } > FLASH

    /* Used by the startup to initialize data from FLASH to RAM */
    _sidata = LOADADDR(.data);

    /* Initialized data sections into RAM, loaded via FLASH */
    .data :
    {
        . = ALIGN(4);
        _sdata = .;        /* RAM start address marker */
        *(.data)
        *(.data*)
        . = ALIGN(4);
        _edata = .;        /* RAM end address marker */
    } > SRAM AT > FLASH

    /* Uninitialized data section into RAM */
    .bss :
    {
        . = ALIGN(4);
        _sbss = .;         /* BSS start marker */
        __bss_start__ = _sbss;
        *(.bss)
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;         /* BSS end marker */
        __bss_end__ = _ebss;
    } > SRAM
}
