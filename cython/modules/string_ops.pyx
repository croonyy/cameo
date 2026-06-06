# cython/modules/string_ops.pyx
def reverse_string(str s):
    cdef int i, n = len(s)
    cdef str result = ""
    for i in range(n-1, -1, -1):
        result += s[i]
    return result