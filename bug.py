# Copyright 2024 Matej Bölcskei, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import os
import subprocess
import datetime
import shutil

from host import Host
import defines

class Bug:
    def __init__(self, host: Host, name: str, driver: bool):
        self.host = host
        self.name = name
        self.driver = driver
        self.directory = os.path.join(host.driver_directory if driver else host.mux_directory, name)

    def prepare(self):
        if not os.path.exists(os.path.join(self.directory, "host.rtlil")):
            subprocess.run(
                [defines.YOSYS_PATH, '-c', self.host.prepare_driver if self.driver else self.host.prepare_multiplexer],
                check=True,
                cwd=self.directory,
                stdout=subprocess.DEVNULL
            )
        return self
    
    def create_miter(self):
        self.miter_log = os.path.join(self.directory, "miter.log")
        self.miter = os.path.join(self.directory, "miter.v")
        if not os.path.exists(self.miter):
            subprocess.run(
                [defines.YOSYS_PATH, '-c', self.host.miter_script],
                check=True,
                cwd=self.directory,
                stdout=open(self.miter_log, 'w'),
            )
        return self

    # cds_jasper jg run.tcl --- ~/encarsia/test_jasper/driver/30/miter.v v_miter.sva sequence.rst proof.vcd proof_optimized.vcd
    def verify(self):
        self.verify_log = os.path.join(self.directory, "verify.log")
        self.proof_path = os.path.join(self.directory, "proof.vcd")
        if not os.path.exists(self.verify_log):
            subprocess.run(
                [defines.JASPER, "jg", "-no_gui", os.path.join(defines.JASPER_SRCS, self.host.name, "run.tcl"), "---", self.miter, os.path.join(defines.JASPER_SRCS, self.host.name, "v_miter.sva"), os.path.join(defines.JASPER_SRCS, self.host.name, "sequence.rst"), self.proof_path, os.path.join(self.directory, "proof_optimized.vcd")],
                check=True,
                cwd=self.directory,
                stdout=open(self.verify_log, 'w'),
            )

        return self
    
    def yosys_verify(self):
        self.yosys_verify_log = os.path.join(self.directory, "yosys_verify.log")
        self.yosys_proof_path = os.path.join(self.directory, "yosys_proof.S")

        if not os.path.exists(self.yosys_proof_path):
            with open(self.yosys_verify_log, 'w') as f:
                f.write(datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S-%f"))
                f.flush()

                subprocess.run(
                    [defines.YOSYS_PATH, '-c', self.host.yosys_verify_script],
                    check=True,
                    cwd=self.directory,
                    stdout=f
                )

                f.flush()
                f.write(datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S-%f"))
                f.flush()

            with open(self.yosys_verify_log, 'r') as yosys_verify_file:
                for line in yosys_verify_file:
                    if 'Propagated the bug.' in line:
                        dasm_input = []
                        for line in yosys_verify_file:
                            if self.host.config.instruction_signal in line:
                                dasm_input.append('DASM(' + line.split()[3] + ')\n')
                        with open(self.yosys_proof_path, 'w') as yosys_proof_file:
                            subprocess.run([defines.SPIKE_DASM_PATH], input=''.join(dasm_input[::2]), text=True, stdout=yosys_proof_file, check=True)
                        break

        return self