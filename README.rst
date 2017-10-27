A Jupyter kernel for Rax

This requires IPython 3.

To install::

    pip install . --upgrade
    python -m rax_kernel.install

To use it, run one of:

.. code:: shell

    jupyter notebook
    # In the notebook interface, select Rax from the 'New' menu
    jupyter qtconsole --kernel rax
    jupyter console --kernel rax

This code was based on the `Bash kernel
<https://github.com/takluyver/bash_kernel>`_.
For details of how this works, see the Jupyter docs on `wrapper kernels
<http://jupyter-client.readthedocs.org/en/latest/wrapperkernels.html>`_, and
Pexpect's docs on the `replwrap module
<http://pexpect.readthedocs.org/en/latest/api/replwrap.html>`_
