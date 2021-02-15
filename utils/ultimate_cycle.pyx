cimport numpy as np

cpdef np.ndarray[double] ultimate_cycle(np.ndarray policy, np.ndarray buys, np.ndarray sells, np.ndarray index):
    token = 1
    for idx in index:
        if token and buys[idx]:
            policy[idx] = 1
            token = 0
        elif not token and sells[idx]:
            policy[idx] = 1
            token = 1
    return policy