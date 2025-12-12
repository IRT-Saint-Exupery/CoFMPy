import warnings

warnings.warn(
    "The 'cofmpy' project has been renamed 'cofmupy'."
    "Please update your imports and dependencies.",
    DeprecationWarning,
    stacklevel=2,
)

from cofmupy import *
