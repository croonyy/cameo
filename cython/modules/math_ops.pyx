# app/core/cython_modules/math_ops.pyx
def cy_sum(int n):
    cdef long long i
    cdef long long total = 0
    for i in range(n):
        total += i
    return total