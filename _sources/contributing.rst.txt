Contributing
============

Testing
-------

HumanMark has good test coverage via pytest. Install the extras with:

.. code::

    pip install -e ".[test]"
    pip install -e ".[cli]"

... and run the tests with:

.. code::

    pytest


Building Documentation
----------------------

To rebuild the documentation, install sphinx and a few extensions:

.. code::

    pip install -e ".[release]"

... then build the documentation:

.. code::

    cd docs && make html
