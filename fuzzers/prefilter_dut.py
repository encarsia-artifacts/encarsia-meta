import os
import subprocess
import shutil
import random
import string

import defines
from host import Host
from bug import Bug

class PrefilterDUT():
    def __init__(self, host: Host, bug: Bug):
        self.directory = os.path.join(bug.directory, "prefilter")
        os.makedirs(self.directory, exist_ok=True)
        self.host = host
        self.bug = bug
        self.name = self.bug.name+(''.join(random.choices(string.ascii_letters + string.digits, k=16)))
        self.env = os.environ.copy()
        if self.host.name == "ibex":
            self.env["CELLIFT_META_ROOT"] = "/encarsia-cellift"
            self.env["CELLIFT_DESIGN_PROCESSING_ROOT"] = "/encarsia-cellift/design-processing"
            self.env["CELLIFT_JOBS"] = "250"
            self.env["CELLIFT_DATADIR"] = f'{os.path.join(self.directory, "experimental-data-cellift")}'
            self.env["CELLIFT_PYTHON_COMMON"] = "/encarsia-cellift/design-processing/common/python_scripts"
            self.env["CELLIFT_ENV_SOURCED"] = "yes"
            self.env["CELLIFT_ENV_VERSION"] = "1"
            self.env["CELLIFT_YS"] = "/encarsia-cellift/design-processing/common/yosys"
            self.env["CELLIFT_GCC"] = "riscv32-unknown-elf-gcc"
            self.env["CELLIFT_OBJDUMP"] = "riscv32-unknown-elf-objdump"
            self.env["OPENTITAN_ROOT"] = "/encarsia-cellift/external-dependencies/cellift-opentitan"
            self.env["LD_LIBRARY_PATH"] = "/prefix-cellift/lib64:"
        else:
            self.env["OPENTITAN_ROOT"] = "/encarsia-cascade/external-dependencies/cascade-opentitan"
            self.env["LD_LIBRARY_PATH"] = "/prefix-cascade/lib64:"

            
        self.env["CASCADE_META_ROOT"] = "/encarsia-cascade"
        self.env["CASCADE_DESIGN_PROCESSING_ROOT"] = "/encarsia-cascade/design-processing"
        self.env["CASCADE_JOBS"] = "250"
        self.env["CASCADE_DATADIR"] = f'{os.path.join(self.directory, "experimental-data")}'
        self.env["CASCADE_PYTHON_COMMON"] = "/encarsia-cascade/design-processing/common/python_scripts"
        self.env["CASCADE_RISCV_BITWIDTH"] = "64"
        self.env["CASCADE_ENV_SOURCED"] = "yes"
        self.env["CASCADE_ENV_VERSION"] = "1"
        self.env["CASCADE_YS"] = "/encarsia-cascade/design-processing/common/yosys"
        self.env["CASCADE_GCC"] = "riscv32-unknown-elf-gcc"
        self.env["CASCADE_OBJDUMP"] = "riscv32-unknown-elf-objdump"
        self.env["CASCADE_PATH_TO_FIGURES"] = "/encarsia-cascade/figures"

    def create_dut(self):
        self.module = os.path.join(self.directory, "host.v")
        if not os.path.exists(self.module):
            subprocess.run(
                [defines.YOSYS_PATH, '-c', self.host.export_script],
                check=True,
                cwd=self.directory,
                stdout=subprocess.DEVNULL
            )

        self.dut_path = os.path.join(self.directory, "dut.v")
        if not os.path.exists(self.dut_path):
            with open(self.dut_path, 'w') as dut_file:
                with open(self.host.cascade_receptor, 'r') as receptor_file:
                    dut_file.write(receptor_file.read())

                with open(self.module, 'r') as module_file:
                    dut_file.write(module_file.read())

        return self

    def compile_dut(self):
        self.verilator_executable = os.path.join(self.directory, self.host.config.cascade_executable)
        if not os.path.exists(self.verilator_executable):
            with open(os.path.join(self.host.config.cascade_directory, "run_vanilla_notrace.core"), 'r') as core_source:
                core = core_source.read()
                core = core.replace("run_vanilla_notrace", self.name)
                core = core.replace("generated/out/vanilla.sv", self.dut_path)
                with open(os.path.join(self.host.config.cascade_directory, self.name+".core"), 'w') as core_destination:
                    core_destination.write(core)

            if self.host.name == "ibex":
                subprocess.run(
                    [defines.FUSESOC_PATH, '--cores-root=/encarsia-cellift/external-dependencies/cellift-opentitan', 'run', '--build', self.name],
                    check=True,
                    cwd=self.host.config.cascade_directory,
                    env=self.env,
                    stdout=open(os.path.join(self.directory, "build.log"), 'w'),
                )
            else:
                subprocess.run(
                    [defines.FUSESOC_PATH, 'run', '--build', self.name],
                    check=True,
                    cwd=self.host.config.cascade_directory,
                    env=self.env,
                    stdout=open(os.path.join(self.directory, "build.log"), 'w'),
                )
            shutil.copy(os.path.join(self.host.config.cascade_directory, "build", self.name+"_0.1", "default-verilator", self.host.config.cascade_executable), self.verilator_executable)
            shutil.rmtree(os.path.join(self.host.config.cascade_directory, "build", self.name+"_0.1"))
            os.remove(os.path.join(self.host.config.cascade_directory, self.name+".core"))

        return self

    def fuzz(self):
        self.fuzz_log = os.path.join(self.directory, "fuzz.log")
        if not os.path.exists(self.fuzz_log):
            subprocess.run(
                ["python", defines.PREFILTER_PATH, self.host.name, self.verilator_executable],
                check=True,
                cwd=self.host.config.cascade_directory,
                stdout=open(self.fuzz_log, 'w'),
                env=self.env
            )
        
        return self