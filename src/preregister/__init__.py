"""preregister — pre-registration, multiple-comparison budgets and null
ladders, as code.

Every idea in this package was first written down as a rule in a trading
bot's gate log and then enforced by hand for 58 sections. The bot ran 66
pre-registered trials and adopted none of them, which is the result the
method is supposed to produce when there is nothing to find. This package
makes the parts of that discipline that were prose into arithmetic.

Importing it opens no file, reads no environment variable and touches no
network; `tests/test_package_purity.py` pins that.
"""
__version__ = "0.1.0"
