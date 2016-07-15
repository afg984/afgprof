.global __gnu_mcount_nc
.type __gnu_mcount_nc,function

__gnu_mcount_nc:
    push    {r0-r3,lr}
    mov     r1,lr
    ldr     r0,[sp, #20]
    bl      __mcount_internal
    pop     {r0-r3,ip,lr}
    bx      ip
