# Copyright 2024 Matej Bölcskei, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import argparse
import os
import datetime
import multiprocessing

from host import Host
from bug import Bug
from fuzzers.cascade_dut import CascadeDUT
from fuzzers.difuzzrtl_dut import DifuzzRTLDUT
from fuzzers.no_cov_difuzzrtl_dut import NoCovDifuzzRTLDUT
from fuzzers.processorfuzz_dut import ProcessorfuzzDUT
from fuzzers.no_cov_processorfuzz_dut import NoCovProcessorfuzzDUT
from fuzzers.prefilter_dut import PrefilterDUT

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--directory", type=str, default=os.path.join(os.getcwd(), "out", datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S")), help="Working directory.\nA new directory will be created if none is specified.")
parser.add_argument("-H", "--hosts", type=str, nargs='+', help="List of host devices")
parser.add_argument("-p", "--processes", type=int, default=32, help="Number of processes running in parallel")
parser.add_argument("-M", "--multiplexer-bugs", type=str, nargs='+', help="Multiplexer bugs to be verified and evaluated")
parser.add_argument("-D", "--driver-bugs", type=str, nargs='+', help="Driver bugs to be verified and evaluated")
parser.add_argument("-P", "--prefilter", action="store_true", help="Enable bug prefiltering")
parser.add_argument("-V", "--verify", action="store_true", help="Enable bug verification")
parser.add_argument("-Y", "--yosys-verify", action="store_true", help="Enable bug verification with Yosys")
parser.add_argument("-F", "--fuzzers", type=str, nargs='+', help="Fuzzers to be verified and evaluated")
args = parser.parse_args()
working_directory = os.path.abspath(args.directory)

if __name__ == "__main__":
    # TODO parallelize injection
    for host in [Host(working_directory, name) for name in args.hosts]:
        host.inject()
        mux_directories = [name for name in os.listdir(host.mux_directory) if os.path.isdir(os.path.join(host.mux_directory, name))]
        driver_directories = [name for name in os.listdir(host.driver_directory) if os.path.isdir(os.path.join(host.driver_directory, name))]
        if args.driver_bugs:
            for driver_bug in args.driver_bugs:
                if driver_bug not in driver_directories:
                    print(driver_directories)
                    raise Exception(f"Bug '{driver_bug}' not found in the working directory {working_directory}!")
            driver_directories = args.driver_bugs
        if args.multiplexer_bugs:
            for mux_bug in args.multiplexer_bugs:
                if mux_bug not in mux_directories:
                    print(mux_directories)
                    raise Exception(f"Bug '{mux_bug}' not found in the working directory {working_directory}!")
            mux_directories = args.multiplexer_bugs

        driver_bugs = [Bug(host, name, True) for name in driver_directories]
        mux_bugs = [Bug(host, name, False) for name in mux_directories]
        bugs = driver_bugs+mux_bugs
        with multiprocessing.Pool(processes=args.processes) as verifier_pool:
            bugs = verifier_pool.map(Bug.prepare, bugs)
            
            if args.prefilter:
                prefilter_duts = [PrefilterDUT(host, bug) for bug in bugs]
                prefilter_duts = verifier_pool.map(PrefilterDUT.create_dut, prefilter_duts)
                prefilter_duts = verifier_pool.map(PrefilterDUT.compile_dut, prefilter_duts)
                prefilter_duts = verifier_pool.map(PrefilterDUT.fuzz, prefilter_duts)

                prefiltered_bugs = []
                for bug in bugs:
                    prefilter_log_path = os.path.join(bug.directory, "prefilter", "fuzz.log")
                    if os.path.exists(prefilter_log_path):
                        with open(prefilter_log_path, 'r') as prefilter_log:
                            if "Success\n" in prefilter_log.read():
                                prefiltered_bugs.append(bug)

                bugs = prefiltered_bugs

            if args.verify:
                bugs = verifier_pool.map(Bug.create_miter, bugs)
                bugs = verifier_pool.map(Bug.verify, bugs)
                bugs = [bug for bug in bugs if os.path.exists(bug.proof_path)]

            if args.yosys_verify:
                bugs = verifier_pool.map(Bug.create_miter, bugs)
                bugs = verifier_pool.map(Bug.yosys_verify, bugs)
                bugs = [bug for bug in bugs if os.path.exists(bug.yosys_proof_path)]

            if args.fuzzers:
                for fuzzer in args.fuzzers:
                    if fuzzer == "cascade":
                        duts = [CascadeDUT(host, bug) for bug in bugs]
                        duts = verifier_pool.map(CascadeDUT.create_dut, duts)
                        duts = verifier_pool.map(CascadeDUT.compile_dut, duts)
                        duts = verifier_pool.map(CascadeDUT.fuzz, duts)
                    elif fuzzer == "difuzzrtl":
                        duts = [DifuzzRTLDUT(host, bug) for bug in bugs]
                        duts = verifier_pool.map(DifuzzRTLDUT.create_dut, duts)
                        duts = verifier_pool.map(DifuzzRTLDUT.compile_dut, duts)
                        duts = verifier_pool.map(DifuzzRTLDUT.create_reference, duts)
                        duts = verifier_pool.map(DifuzzRTLDUT.compile_reference, duts)
                        duts = verifier_pool.map(DifuzzRTLDUT.check_mismatch, duts)
                    elif fuzzer == "no_cov_difuzzrtl":
                        duts = [NoCovDifuzzRTLDUT(host, bug) for bug in bugs]
                        duts = verifier_pool.map(NoCovDifuzzRTLDUT.create_dut, duts)
                        duts = verifier_pool.map(NoCovDifuzzRTLDUT.compile_dut, duts)
                        duts = verifier_pool.map(NoCovDifuzzRTLDUT.create_reference, duts)
                        duts = verifier_pool.map(NoCovDifuzzRTLDUT.compile_reference, duts)
                        duts = verifier_pool.map(NoCovDifuzzRTLDUT.check_mismatch, duts)
                    elif fuzzer == "processorfuzz":
                        duts = [ProcessorfuzzDUT(host, bug) for bug in bugs]
                        duts = verifier_pool.map(ProcessorfuzzDUT.create_dut, duts)
                        duts = verifier_pool.map(ProcessorfuzzDUT.compile_dut, duts)
                        duts = verifier_pool.map(ProcessorfuzzDUT.create_reference, duts)
                        duts = verifier_pool.map(ProcessorfuzzDUT.compile_reference, duts)
                        duts = verifier_pool.map(ProcessorfuzzDUT.check_mismatch, duts)
                    elif fuzzer == "no_cov_processorfuzz":
                        duts = [NoCovProcessorfuzzDUT(host, bug) for bug in bugs]
                        duts = verifier_pool.map(NoCovProcessorfuzzDUT.create_dut, duts)
                        duts = verifier_pool.map(NoCovProcessorfuzzDUT.compile_dut, duts)
                        duts = verifier_pool.map(NoCovProcessorfuzzDUT.create_reference, duts)
                        duts = verifier_pool.map(NoCovProcessorfuzzDUT.compile_reference, duts)
                        duts = verifier_pool.map(NoCovProcessorfuzzDUT.check_mismatch, duts)
                    else:
                        raise Exception(f"Fuzzer '{fuzzer}' not found!")