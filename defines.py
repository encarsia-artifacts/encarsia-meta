import os

YOSYS_PATH = "yosys"
SPIKE_DASM_PATH = "spike-dasm"
FUSESOC_PATH = "fusesoc"
DIFUZZRTL_FUZZER = "/encarsia-difuzz-rtl/Fuzzer"
DIFUZZRTL_VERILOG = "/encarsia-difuzz-rtl/Benchmarks/Verilog"
PROCESSORFUZZ_FUZZER = "/encarsia-processorfuzz/Fuzzer"
PROCESSORFUZZ_VERILOG = "/encarsia-processorfuzz/Benchmarks/Verilog"
CASCADE_PATH = "/encarsia-cascade/fuzzer/do_fuzzdesign.py"
PREFILTER_PATH = "/encarsia-cascade/fuzzer/do_testsingle.py"
JASPER = os.path.abspath("cds_jasper")
JASPER_SRCS = os.path.abspath("./jasper")