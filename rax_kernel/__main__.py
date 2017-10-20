from ipykernel.kernelapp import IPKernelApp
from .kernel import RaxKernel
IPKernelApp.launch_instance(kernel_class=RaxKernel)
