# Copyright 2024 Matej Bölcskei, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import datetime
import os
import tabulate

def read_duration(log_path):
    with open(log_path, 'r') as log:
        lines = log.readlines()
        start = datetime.datetime.strptime(lines[0].strip(), "%d-%m-%Y-%H-%M-%S-%f")
        end = datetime.datetime.strptime(lines[-1].strip(), "%d-%m-%Y-%H-%M-%S-%f")
        return end-start
    
def num_injections(filename, driver):
    count = 0
    with open(filename, 'r') as file:
        for line in file:
            count += line.count("host_driver.rtlil" if driver else "host_amt.rtlil")
    return count

injection_data = []
def save_injection_results(host):
    num_driver_bugs = num_injections(host.inject_driver_log, True)
    num_mux_bugs = num_injections(host.inject_multiplexer_log, False)

    injection_data.append([host.name, num_driver_bugs, read_duration(host.inject_driver_log)/num_driver_bugs, num_mux_bugs, read_duration(host.inject_multiplexer_log)/num_mux_bugs])

def plot_injection():
  injection_headers = ["Design", "#Transf. (Mix-ups)", "Avg. T. (Mix-ups)", "#Transf. (Conditionals)", "Avg. T. (Conditionals)"]
  print("\nInjection results:")
  print(tabulate.tabulate(injection_data, headers=injection_headers, stralign="center", numalign="right", tablefmt="grid"))

verification_data = []
def save_verification_results(host, bugs):
    driver_trials = [bug for bug in bugs if os.path.exists(bug.yosys_verify_log) and bug.driver]
    mux_trials = [bug for bug in bugs if os.path.exists(bug.yosys_verify_log) and not bug.driver]

    driver_successful = [bug for bug in bugs if os.path.exists(bug.yosys_proof_path) and bug.driver]
    mux_successful = [bug for bug in bugs if os.path.exists(bug.yosys_proof_path) and not bug.driver]

    driver_times = [read_duration(bug.yosys_verify_log).total_seconds() for bug in driver_successful]
    mux_times = [read_duration(bug.yosys_verify_log).total_seconds() for bug in mux_successful]

    avg_t_driver = sum(driver_times)/len(driver_times) if len(driver_times) > 0 else "-"
    avg_t_mux = sum(mux_times)/len(mux_times) if len(mux_times) > 0 else "-"

    verification_data.append([host.name, len(driver_trials), len(driver_successful)/len(driver_trials)*100, avg_t_driver, len(mux_trials), len(mux_successful)/len(mux_trials)*100, avg_t_mux])

def plot_verification():
    verification_headers = ["Design", "#Transf. (Mix-ups)", "Succ. % (Mix-ups)", "Avg. T. (Mix-ups)", "#Transf. (Conditionals)", "Succ. % (Conditionals)", "Avg. T. (Conditionals)"]
    print("\nVerification results:")
    print(tabulate.tabulate(verification_data, headers=verification_headers, stralign="center", numalign="right", tablefmt="grid"))

fuzzing_data = []
totals = []
max_bugs = 0
def save_fuzzing_results(host, fuzzer, duts):
    global max_bugs
    success_driver = []
    success_multiplexer = []
    duts.sort(key=lambda x: int(x.bug.name))
    for dut in duts:
        with open(dut.check_summary, 'r') as check_summary_file:
            detected = "✘" if "NOT DETECTED" in check_summary_file.read() else "✔"
            if dut.bug.driver:
                success_driver.append(detected)
            else:
                success_multiplexer.append(detected)

    driver_data = [host.name, "Mix-up", fuzzer]
    driver_data.extend(success_driver)
    totals.append(sum([1 if success == "✔" else 0 for success in success_driver]))
    multiplexer_data = [host.name, "Conditional", fuzzer]
    multiplexer_data.extend(success_multiplexer)
    totals.append(sum([1 if success == "✔" else 0 for success in success_multiplexer]))
    fuzzing_data.append(driver_data)
    fuzzing_data.append(multiplexer_data)
    if len(success_driver) > max_bugs:
        max_bugs = len(success_driver)
    if len(success_multiplexer) > max_bugs:
        max_bugs = len(success_multiplexer)

def plot_fuzzing():
    fuzzing_headers = ["Design", "Bug Category", "Fuzzer"]
    fuzzing_headers.extend(range(1, max_bugs+1))
    fuzzing_headers.append("Total")
    for row in fuzzing_data:
        row.extend(["-" for _ in range(len(fuzzing_headers) - len(row) - 1)])
        row.append(totals.pop(0))
        
    print("\nFuzzing results:")
    print(tabulate.tabulate(fuzzing_data, headers=fuzzing_headers, stralign="center", numalign="right", tablefmt="grid"))