.data
msg: .asciiz "Humedad: "
x:   .float 42.5
.text
main:
    li   $v0, 4
    la   $a0, msg
    syscall
    lwc1 $f12, x
    li   $v0, 2
    syscall
    li   $v0, 11
    li   $a0, 10
    syscall
    li   $v0, 40
    li   $a0, 0
    li   $a1, 1234
    syscall
    li   $v0, 43
    li   $a0, 0
    syscall
    mov.s $f12, $f0
    li   $v0, 2
    syscall
    li   $v0, 10
    syscall
