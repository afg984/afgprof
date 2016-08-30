.global __gnu_mcount_nc
.type __gnu_mcount_nc, function
.align  2

__gnu_mcount_nc:
    push    {r0-r3,lr}
    mov     r1,lr
    ldr     r0,[sp, #20]
    str     r0,[sp, #16]
    str     r1,[sp, #20]
    bl      __mcount_internal
    pop     {r0-r3,lr}
    pop     {pc}


.global mcount
.type mcount, function
.align  2

mcount:
    push    {r0-r3,lr}
    mov     r1,lr
    ldr     r0,[fp, #4]
    bl      __mcount_internal
    pop     {r0-r3}
    ldr     lr,[fp, #4]
    pop     {pc}
