from tgp.kernel import Kernel
from ml_tools.kernels import matern_kernel_32


class MaternKernel32(Kernel):

    def __init__(self, lscales, sd):

        self.lscales = lscales
        self.sd = sd

    def calculate(self, X1, X2):

        return matern_kernel_32(X1, X2, self.sd, self.lscales)
