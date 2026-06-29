"""
config/suppress_warnings.py
=============================================
Suppresses noisy but harmless warnings from
third-party libraries.

Key issue:
  wrappers.py in a third-party package
  imports the old 'gym' library which
  triggers a deprecation warning.
  We cannot edit wrappers.py directly
  because it is in site-packages/.
  We suppress the warning here instead.

Author: ENSITE Project, UNH
Date: June 2026
"""

import os
import warnings

# ============================================
# MUST BE SET BEFORE ANY OTHER IMPORTS
# These environment variables must be set
# before tensorflow or gym are imported
# ============================================

# Suppress TensorFlow oneDNN warning
# "You may see slightly different numerical
#  results due to floating-point round-off"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Suppress TensorFlow info/warning messages
# 0=all, 1=filter INFO, 2=filter WARNING, 3=errors only
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Suppress absl logging warning
# "All log messages before absl::InitializeLog()
#  is called are written to STDERR"
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "3"


# ============================================
# GYM DEPRECATION WARNING
# ============================================
# Root cause:
#   wrappers.py inside a third-party package
#   (likely langgraph or deepagents) imports
#   the old 'gym' library.
#
# Why we cannot fix it directly:
#   wrappers.py is in site-packages/
#   Editing it would break on next pip install
#   The package maintainer needs to update it
#
# What we do instead:
#   Suppress the specific warning message
#   so it does not clutter our terminal output
# ============================================

warnings.filterwarnings(
    "ignore",
    message=".*Gym has been unmaintained.*"
)
warnings.filterwarnings(
    "ignore",
    message=".*upgrade to Gymnasium.*"
)
warnings.filterwarnings(
    "ignore",
    message=".*maintained drop-in replacement.*"
)
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module="gym"
)
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="gym"
)

# ============================================
# NUMPY COMPATIBILITY WARNINGS
# ============================================
# Some older packages not yet updated for
# NumPy 2.0 emit compatibility warnings.
# These do not affect ENSITE functionality.

warnings.filterwarnings(
    "ignore",
    message=".*numpy.*",
    category=DeprecationWarning
)
warnings.filterwarnings(
    "ignore",
    message=".*np\\..*",
    category=DeprecationWarning
)

# ============================================
# GENERAL DEPRECATION WARNINGS
# FROM THIRD-PARTY PACKAGES
# ============================================

warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module="pkg_resources"
)
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module="distutils"
)