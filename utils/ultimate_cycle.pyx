import numpy as pnp
cimport numpy as np

cpdef np.ndarray[double] ultimate_cycle(np.ndarray policy, np.ndarray buys, np.ndarray sells, np.ndarray index):
    cdef int token = 1
    for idx in index:
        if token and buys[idx]:
            policy[idx] = 1
            token = 0
        elif not token and sells[idx]:
            policy[idx] = 1
            token = 1
    return policy

cpdef np.ndarray[double] cycle_checkgain(np.ndarray policy, np.ndarray buys, np.ndarray sells, np.ndarray index, np.ndarray price, double mingain):
    cdef int token = 1
    cdef double buy_price = 0
    for idx in index:
        if token and buys[idx]:
            policy[idx] = 1
            buy_price = price[idx]
            token = 0
        elif not token and sells[idx] and (price[idx]/buy_price >= 1 + mingain):
            policy[idx] = 1
            token = 1
    return policy

cpdef int selection_stoploss_mingain(np.int32_t idx, np.ndarray[np.float32_t, ndim=1] price, double buy_price, double mingain, double stoploss):
    cdef np.ndarray[np.npy_bool, ndim=1, cast=True, mode='c'] x1 = price[idx:]/buy_price >= 1 + mingain
    cdef np.ndarray[np.npy_bool, ndim=1, cast=True, mode='c'] x2 = price[idx:]/buy_price <= 1 - stoploss
    for i in range(len(x1)):
        if x1[i] or x2[i]:
            return i
    return -1

cpdef int selection_mingain(np.int32_t idx, np.ndarray[np.float32_t, ndim=1] price, double buy_price, double mingain, double stoploss):
    cdef np.ndarray[np.npy_bool, ndim=1, cast=True, mode='c'] x1 = price[idx:]/buy_price >= 1 + mingain
    cdef int i
    for i in range(len(x1)):
        if x1[i]:
            return i
    return -1

cpdef int selection_stoploss(np.int32_t idx, np.ndarray[np.float32_t, ndim=1] price, double buy_price, double mingain, double stoploss):
    cdef np.ndarray[np.npy_bool, ndim=1, cast=True, mode='c'] x1 = price[idx:]/buy_price <= 1 - stoploss
    cdef int i
    for i in range(len(x1)):
        if x1[i]:
            return i
    return -1

cpdef np.ndarray[double] cycle_absolutegain(np.ndarray[np.npy_bool, ndim=1, cast=True] policy, np.ndarray[np.npy_bool, ndim=1, cast=True] buys, np.ndarray[np.int32_t, ndim=1] index, np.ndarray[np.float32_t, ndim=1] price, double mingain, double stoploss):
    # I need just buy indexes here
    cdef double buy_price
    cdef int i = 0
    cdef int idx
    cdef int idx_index
    cdef int selection_idx
    cdef object callback
    print("This simulation may take a while.")
    if stoploss != 0 and mingain != 0:
        callback = selection_stoploss_mingain
    elif stoploss == 0 and mingain != 0:
        callback = selection_mingain
    elif stoploss != 0 and mingain == 0:
        callback = selection_stoploss
    while i < len(index):
        idx = index[i]
        policy[idx] = 1
        buy_price = price[idx]
        idx += 1
        selection_idx = callback(idx, price, buy_price, mingain, stoploss)
        if selection_idx == -1:
            i = len(index)
            break
        idx = idx + selection_idx
        policy[idx] = 1
        for idx_index in range(len(index[i+1:])):
            if index[idx_index] > idx:
                i = idx_index
                break
        else:
            i = len(index)
    return policy