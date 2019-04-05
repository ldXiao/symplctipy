import numpy as np
import numpy.fft as fft
import scipy as scp
import matplotlib.pyplot as plt

def fDFT(fsample:list):
    n = len(fsample)
    fsample_shift = fft.ifftshift(fsample)
    # shift to sample space of [0,L]
    fhat_shift = fft.fft(fsample_shift)
    # got a frequence spec in [0,n]
    fhat = fft.fftshift(fhat_shift)/n
    #shift back to [-n/2, -n/2)
    # the python fft use different convention
    return fhat

def ifDFT(fhat):
    """
    :param fhat: Fourier coefficients in [-n/2, n/2) format
    :return: fsample in [-L/2, L/2) format
    """
    n = len(fhat)
    # shift to [0,n) format
    fhat_shift = fft.ifftshift(fhat)
    fsample_shift = fft.ifft(fhat_shift) * n
    fsample = fft.fftshift(fsample_shift)
    return fsample

def extend_sample(fhat, M):
    """
    extend the fourier coefficients to a finer grid.
    :param fhat_shift: dft coefficients generated by fDFT, in [-n/2, n/2 ) format.
    :param M: A large integer, even
    :return an extended sample in x space with [-L/2, L) for mat
    """
    n = len(fhat)
    if n % 2 ==0:
        zeros_left = np.zeros((M-n)//2)
        zeros_right = np.zeros((M-n)//2)
    else:
#         print("called")
        zeros_left = np.zeros((M-n+1)//2)
        zeros_right = np.zeros((M-n-1)//2)
    fhat = np.concatenate( (np.concatenate((zeros_left,fhat), axis=0), zeros_right), axis=0)
    fhat_shift = fft.ifftshift(fhat)
    phisample_shift = fft.ifft(fhat_shift) * M
    # we multiply by M because python used a different convension.
    phisample = fft.fftshift(phisample_shift)
    return phisample

def pdDiff(fhat, p:int, L:float):
    """
    the pseudo_spectral differential operator of D_p(f)
    :param fhat: the Fourier mode of a funciton f in [low, high) format
    :param low: lower bound for the grid
    :param high: higher bound fot the grid
    :param p: oder of derivative
    """
    n = len(fhat)
    if p % 2 == 0:
        if n % 2 == 0:
            ksample = np.arange(-n / 2, n / 2, 1)
        else:
            ksample = np.arange(-(n - 1) / 2, (n + 1) / 2, 1)
        multip = np.array([((2 * np.pi * 1j) / L * k) ** p for k in ksample])

    elif p % 2 == 1:
        if n % 2 == 0:
            ksample = np.arange(-n / 2, n / 2, 1)
            # ksample[0] = 0.0
        else:
            ksample = np.arange(-(n - 1) / 2, (n + 1) / 2, 1)
        multip = np.array([((2 * np.pi * 1j) / L * k) ** p for k in ksample])
    return np.multiply(multip, fhat)

class Operator():
    # the base class of differential operators
    def __init__(self, L:float):
        self.L = L
    def forward(self, phi:list):
        # the phi is values of function on a grid
        # between low high in [low, high) format
        return 0
    def __call__(self, phi):
        return self.forward(self, phi)


class Linear(Operator):
    # a derived class of liner differential operators
    # it will return a numpy array representing the diagonal of the matrix
    def __init__(self, kl:float, df_coeffs:list, L:float):
        """
        :param kl: float constant
        :param df_coeffs: list of the form [(int, list)] to represent
        D_x q(x) (D_x p(x) phi(x))
        :param L:
        """
        super(Linear, self).__init__(L)
        self.kl = kl
        self.df_coeffs = df_coeffs

    def forward(self, phihat:list):
        # the phi is values of function on a grid
        # between low high in [low, high) format
        # phisample = ifDFT(phihat)
        # mul = phisample
        # mulhat = phihat
        mulhat = np.ones_like(phihat, float)
        mul = ifDFT(mulhat)
        for df_degree, qx in self.df_coeffs[::-1]:
            if qx is not None:
                print("called")
                mulhat = pdDiff(
                    fDFT(np.multiply(qx, mul)),
                    df_degree,
                    self.L)
            else:
                mulhat = pdDiff(mulhat, df_degree, self.L)
            mul = ifDFT(mulhat)
        # for i in range(len(mulhat)):
        #     if mulhat[i] == 0.0:
        #         mulhat[i] = 0.001
        return self.kl * mulhat


    def __call__(self, phihat):
        return self.forward(phihat)


class NonLinear(Operator):
    # a derived class of nonliner differential operators
    # must be a monomial of variables phis and partial_derivatives
    def __init__(self, kn:float, degrees:list, L:float):
        super(NonLinear, self).__init__(L)
        self.kn = kn
        self.degrees = degrees

    def forward(self, phihat:list):
        phisample = ifDFT(phihat)
        # use mul to store the multiply repsults in space region
        mul = np.ones_like(phihat, float)
        mulhat = np.ones_like(phihat, float)
        for df_degree, pow_degree in self.degrees[::-1]:
            mulhat = pdDiff(
                fDFT(np.multiply(pow(phisample, pow_degree), mul)),
                df_degree,
                self.L)
            mul = ifDFT(mulhat)
        return self.kn * mulhat

    def __call__(self, phihat):
        return self.forward(phihat)


# print(x)