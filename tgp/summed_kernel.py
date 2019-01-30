import numpy as np
from tgp.kernel import Kernel


class SummedKernel(Kernel):

    def __init__(self, kernels):

        self.kernels = kernels

    def calculate(self, X1, X2):

        result = np.zeros((X1.shape[0], X2.shape[0]))

        for cur_kernel in self.kernels:

            result += cur_kernel.calculate(X1, X2)

        return result
