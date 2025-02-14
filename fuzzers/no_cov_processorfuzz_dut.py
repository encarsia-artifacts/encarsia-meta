# Copyright 2024 Matej Bölcskei, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import os
import subprocess
import random
import string
import time

import defines
from host import Host
from bug import Bug

class NoCovProcessorfuzzDUT():
    def __init__(self, host: Host, bug: Bug):
        self.directory = os.path.join(bug.directory, "no_cov_processorfuzz")
        os.makedirs(self.directory, exist_ok=True)
        self.host = host
        self.bug = bug
        self.name = self.bug.name+(''.join(random.choices(string.ascii_letters + string.digits, k=16)))
        self.env = os.environ.copy()
        self.env["SPIKE"] = "/encarsia-processorfuzz/processorfuzz_spike"
        self.env["PYTHONPATH"] = f"{self.env['PATH']}:/encarsia-processorfuzz/Fuzzer"
        self.env["PYTHONPATH"] = f"{self.env['PATH']}:/encarsia-processorfuzz/Fuzzer/src"
        self.env["PYTHONPATH"] = f"{self.env['PATH']}:/encarsia-processorfuzz/Fuzzer/RTLSim/src"
        self.env["COCOTB_RESULTS_FILE"] = self.name

    def create_dut(self):
        self.module = os.path.join(self.directory, "host.v")
        if not os.path.exists(self.module):
            subprocess.run(
                [defines.YOSYS_PATH, '-c', self.host.instrument_script],
                check=True,
                cwd=self.directory,
                stdout=subprocess.DEVNULL
            )

        self.dut_path = os.path.join(self.directory, "dut.v")
        if not os.path.exists(self.dut_path):
            with open(self.dut_path, 'w') as dut_file:
                with open(self.host.processorfuzz_receptor, 'r') as receptor_file:
                    dut_file.write(receptor_file.read())

                with open(self.module, 'r') as module_file:
                    dut_file.write(module_file.read())

        return self
    
    def create_reference(self):
        self.reference = os.path.join(self.directory, "reference.v")
        if not os.path.exists(self.reference):
            subprocess.run(
                [defines.YOSYS_PATH, '-c', self.host.export_difuzzrtl_reference],
                check=True,
                cwd=self.directory,
                stdout=subprocess.DEVNULL
            )

        self.reference_dut = os.path.join(self.directory, "reference_dut.v")
        if not os.path.exists(self.reference_dut):
            with open(self.reference_dut, 'w') as reference_dut_file:
                with open(self.host.processorfuzz_receptor, 'r') as receptor_file:
                    reference_dut_file.write(receptor_file.read())

                with open(self.reference, 'r') as reference_file:
                    reference_dut_file.write(reference_file.read())

        return self
    
    def compile_dut(self):
        self.build_directory = os.path.join(self.directory, "build")
        self.out_directory = os.path.join(self.directory, "out")

        if not os.path.exists(self.out_directory):
            subprocess.run(
                [
                    "make",
                    f"SIM_BUILD={os.path.relpath(self.build_directory, defines.PROCESSORFUZZ_FUZZER)}",
                    f"VFILE={os.path.relpath(self.dut_path[:-2], defines.PROCESSORFUZZ_VERILOG)}",
                    f"TOPLEVEL={self.host.config.difuzzrtl_toplevel}",
                    f"NUM_ITER=1",
                    f"OUT={os.path.relpath(self.out_directory, defines.PROCESSORFUZZ_FUZZER)}",
                    f"ALL_CSR=0",
                    f"FP_CSR=0",
                    f"NO_GUIDE=1",
                    f"NO_ISA_GUIDE=1"
                ],
                check=True,
                cwd=defines.PROCESSORFUZZ_FUZZER,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=self.env
            )

        return self
    
    def fuzz(self):
        self.fuzz_log = os.path.join(self.directory, "fuzz.log")
        if not os.path.exists(self.fuzz_log):
            with open(self.fuzz_log, 'w') as fuzz_log:
                process = subprocess.Popen(
                    [
                        "make",
                        f"SIM_BUILD={os.path.relpath(self.build_directory, defines.PROCESSORFUZZ_FUZZER)}",
                        f"VFILE={os.path.relpath(self.dut_path[:-2], defines.PROCESSORFUZZ_VERILOG)}",
                        f"TOPLEVEL={self.host.config.difuzzrtl_toplevel}",
                        f"NUM_ITER=10000000",
                        f"OUT={os.path.relpath(self.out_directory, defines.PROCESSORFUZZ_FUZZER)}",
                        f"ALL_CSR=0",
                        f"FP_CSR=0",
                        f"NO_GUIDE=1",
                        f"NO_ISA_GUIDE=1"
                    ],
                    cwd=defines.PROCESSORFUZZ_FUZZER,
                    stdout=fuzz_log,
                    stderr=subprocess.DEVNULL,
                    env=self.env
                )
                time.sleep(defines.FUZZING_TIMEOUT)
                process.terminate()

        return self
    
    def compile_reference(self):
        self.build_reference_directory = os.path.join(self.directory, "build_reference")
        self.out_reference_directory = os.path.join(self.directory, "out_reference")
        self.out_replay_directory = os.path.join(self.directory, "out_replay")

        if not os.path.exists(self.out_reference_directory):
            subprocess.run(
                [
                    "make",
                    f"SIM_BUILD={os.path.relpath(self.build_reference_directory, defines.PROCESSORFUZZ_FUZZER)}",
                    f"VFILE={os.path.relpath(self.reference_dut[:-2], defines.PROCESSORFUZZ_VERILOG)}",
                    f"TOPLEVEL={self.host.config.difuzzrtl_toplevel}",
                    f"NUM_ITER=1",
                    f"OUT={os.path.relpath(self.out_reference_directory, defines.PROCESSORFUZZ_FUZZER)}",
                    f"ALL_CSR=0",
                    f"FP_CSR=0",
                    f"NO_GUIDE=1",
                    f"NO_ISA_GUIDE=1"
                ],
                check=True,
                cwd=defines.PROCESSORFUZZ_FUZZER,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=self.env
            )

        if not os.path.exists(self.out_replay_directory):
            subprocess.run(
                [
                    "make",
                    f"SIM_BUILD={os.path.relpath(self.build_directory, defines.PROCESSORFUZZ_FUZZER)}",
                    f"VFILE={os.path.relpath(self.dut_path[:-2], defines.PROCESSORFUZZ_VERILOG)}",
                    f"TOPLEVEL={self.host.config.difuzzrtl_toplevel}",
                    f"NUM_ITER=1",
                    f"OUT={os.path.relpath(self.out_replay_directory, defines.PROCESSORFUZZ_FUZZER)}",
                    f"ALL_CSR=0",
                    f"FP_CSR=0",
                    f"NO_GUIDE=1",
                    f"NO_ISA_GUIDE=1"
                ],
                check=True,
                cwd=defines.PROCESSORFUZZ_FUZZER,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=self.env
            )

        return self
    
    def check_mismatch(self):
        mismatch_inputs = os.listdir(os.path.join(self.out_directory, "mismatch", "sim_input"))
        self.check_summary = os.path.join(self.directory, "check_summary.log")

        if not os.path.isdir(os.path.join(self.out_reference_directory, "mismatch", "check")):
            os.makedirs(os.path.join(self.out_reference_directory, "mismatch", "check"))

        if not os.path.isdir(os.path.join(self.out_replay_directory, "mismatch", "check")):
            os.makedirs(os.path.join(self.out_replay_directory, "mismatch", "check"))

        for input in mismatch_inputs:
            log_replay = os.path.join(self.out_replay_directory, "mismatch", "check", input[:-3]+"_replay.log")
            if not os.path.exists(log_replay):
                subprocess.run(
                    [
                        "make",
                        f"SIM_BUILD={os.path.relpath(self.build_directory, defines.PROCESSORFUZZ_FUZZER)}",
                        f"VFILE={os.path.relpath(self.dut_path[:-2], defines.PROCESSORFUZZ_VERILOG)}",
                        f"TOPLEVEL={self.host.config.difuzzrtl_toplevel}",
                        f"NUM_ITER=1",
                        f"OUT={os.path.relpath(self.out_replay_directory, defines.PROCESSORFUZZ_FUZZER)}",
                        f"IN_FILE={os.path.relpath(os.path.join(self.out_directory, 'mismatch', 'sim_input', input), defines.PROCESSORFUZZ_FUZZER)}",
                        f"ALL_CSR=0",
                        f"FP_CSR=0",
                        f"NO_GUIDE=1",
                        f"NO_ISA_GUIDE=1"
                    ],
                    check=True,
                    cwd=defines.PROCESSORFUZZ_FUZZER,
                    stdout=open(log_replay, 'w'),
                    stderr=subprocess.DEVNULL,
                    env=self.env
                )
            with open(log_replay, 'r') as log_file:
                contents = log_file.read()
                if "MISMATCH:" not in contents and "Bug --" not in contents:
                    continue

            log = os.path.join(self.out_reference_directory, "mismatch", "check", input[:-3]+".log")
            if not os.path.exists(log):
                subprocess.run(
                    [
                        "make",
                        f"SIM_BUILD={os.path.relpath(self.build_reference_directory, defines.PROCESSORFUZZ_FUZZER)}",
                        f"VFILE={os.path.relpath(self.reference_dut[:-2], defines.PROCESSORFUZZ_VERILOG)}",
                        f"TOPLEVEL={self.host.config.difuzzrtl_toplevel}",
                        f"NUM_ITER=1",
                        f"OUT={os.path.relpath(self.out_reference_directory, defines.PROCESSORFUZZ_FUZZER)}",
                        f"IN_FILE={os.path.relpath(os.path.join(self.out_directory, 'mismatch', 'sim_input', input), defines.PROCESSORFUZZ_FUZZER)}",
                        f"ALL_CSR=0",
                        f"FP_CSR=0",
                        f"NO_GUIDE=1",
                        f"NO_ISA_GUIDE=1"
                    ],
                    check=True,
                    cwd=defines.PROCESSORFUZZ_FUZZER,
                    stdout=open(log, 'w'),
                    stderr=subprocess.DEVNULL,
                    env=self.env
                )

            with open(log, 'r') as log_file:
                contents = log_file.read()
                if "MISMATCH:" not in contents and "Bug --" not in contents:
                    with open(self.check_summary, 'w') as check_summary_file:
                        check_summary_file.write("DETECTED: "+input)
                    return self
                
        with open(self.check_summary, 'w') as check_summary_file:
            check_summary_file.write("NOT DETECTED")

        return self