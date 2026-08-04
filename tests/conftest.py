"""
Must run before numpy is imported anywhere in the process: on machines
with many cores, OpenBLAS's default thread pool makes the p-y solver's
repeated small (~360x360) linear solves ~280x slower due to thread
synchronization overhead, turning a 3s test run into a multi-minute hang.
Setting the env var after numpy import has no effect -- OpenBLAS reads it
at load time -- so this has to be the first thing pytest does, before it
collects any test module that imports helical_pile_design (and therefore
numpy).
"""
import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
