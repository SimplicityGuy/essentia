.. How to use TensorFlow models and Gaia SVM classifiers 

Using machine learning models
=======================

Essentia includes algorithms for running inference with data-driven machine learning models that can be used for high-level annotation of music audio.
Specifically, Essentia provides a wrapper for TensorFlow that allows using virtually any TensorFlow model within our audio analysis framework.

We provide pre-trained models for various music analysis and classification tasks.
Current :ref:`Essentia Models` are based on TensorFlow.

*Note*: We also provide legacy `Gaia SVM models <gaia_svm_models.html>`_ based on handcrafted music audio features.
These models have been superseded by our current models.


Installation
------------

Essentia with TensorFlow support is available for Linux and macOS as a separate Python package, `essentia-tensoflow <https://pypi.org/project/essentia-tensorflow/>`_:

.. highlight:: none

.. code-block::

    pip install essentia-tensorflow

Building Essentia with TensorFlow support 
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Alternatively, we provide instructions to build Essentia from source and link it against the shared TensorFlow libraries.
To avoid collisions when importing both Essentia and TensorFlow in Python, we link against the shared libraries inside the TensorFlow Python package itself rather than against a separate copy of `libtensorflow <https://www.tensorflow.org/install/lang_c>`_.

Follow these steps to build and install Essentia with TensorFlow support:

At least pip version ≥19.3 is required:

.. code-block::

    pip3 install --upgrade pip

Install TensorFlow. Version 2.13 is the minimum, because from that release the C API is exported by ``libtensorflow_cc``; earlier wheels exported it from the Python wrapper extension, which cannot be linked against:

.. code-block::

    pip3 install "tensorflow>=2.13"

Clone Essentia:

.. code-block::

    git clone https://github.com/MTG/essentia.git

Generate a ``tensorflow.pc`` describing the libraries and headers inside that wheel. The script only writes symlinks and the ``tensorflow.pc`` itself, so pick a prefix you own; the default of ``/usr/local`` needs ``sudo`` on most systems:

.. code-block::

    cd essentia
    python3 src/3rdparty/tensorflow/setup_tensorflow.py --prefix ~/.local
    export PKG_CONFIG_PATH=~/.local/lib/pkgconfig:$PKG_CONFIG_PATH

Install the `dependencies <https://essentia.upf.edu/installing.html#installing-dependencies-on-linux>`_ for Essentia with Python 3 (may require `sudo`):

.. code-block::

    apt-get install build-essential libyaml-dev libfftw3-dev libavcodec-dev libavformat-dev libavutil-dev libavresample-dev python-dev libsamplerate0-dev libtag1-dev libchromaprint-dev python-six python3-dev python3-numpy-dev python3-numpy python3-yaml libeigen3-dev

Configure Essentia with TensorFlow and Python 3:


.. code-block::

    python3 waf configure --build-static --with-python --with-tensorflow

Configuration fails here, rather than at import time, if the ``tensorflow.pc`` on ``PKG_CONFIG_PATH`` names a library that does not export the C API. The error reports the ``.pc`` it used, the flags it took from it, and the libraries it tried to link.


Build everything:

.. code-block::

    python3 waf

Install:

.. code-block::

    python3 waf install


Inference with GPU
-----------------
It is possible to run inference with Essentia Models using GPU when the correct version of the CUDA and CuDNN libraries are installed on your system.
We recommend using a package manager such as `Conda <https://docs.conda.io/en/latest/>`_ to install the required components.

These are the recommended steps to follow:

Install `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_ (or Anaconda).
Create and activate a Conda environment: 

.. code-block::

    conda create -n ess python=3.10
    conda activate ess

Install CUDA, CuDNN, and essentia-tensorflow:

.. code-block::

    conda install -c conda-forge -y cudatoolkit=11.2 cudnn=8.1
    pip install essentia-tensorflow


It is possible to use CUDA environment variables to control GPU usage.
For example, the following line of code launches a script using GPU 1:

.. code-block::

  CUDA_VISIBLE_DEVICES=1 python my_script.py 

.. highlight:: default
