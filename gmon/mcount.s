.global __gnu_mcount_nc
.type __gnu_mcount_nc,function
.align  2

__gnu_mcount_nc:
    push    {r0-r3,lr}
    mov     r1,lr
    ldr     r0,[sp, #20]
    str     r0,[sp, #16]
    str     r1,[sp, #20]
    bl      __mcount_internal
    pop     {r0-r3,lr,pc}
