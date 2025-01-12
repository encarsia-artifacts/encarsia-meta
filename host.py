import os
import re
import subprocess
import datetime

import defines
import config

class Host:
    def __init__(self, out_directory: str, name: str):
        self.name = name
        self.config = config.get_host_config(name)

        self.directory = os.path.join(out_directory, name)
        self.mux_directory = os.path.join(self.directory, "multiplexer")
        if not os.path.isdir(self.mux_directory):
            os.makedirs(self.mux_directory)
        self.driver_directory = os.path.join(self.directory, "driver")
        if not os.path.isdir(self.driver_directory):
            os.makedirs(self.driver_directory)

        self.create_reference()

        self.create_inject_script()
        self.create_prepare_scripts()
        self.create_miter_script()
        self.create_yosys_verify_script()

        self.create_export_script()
        self.create_instrument_script()

        self.create_cascade_receptor()
        self.create_difuzzrtl_receptor()
        self.create_processorfuzz_receptor()

    def create_reference(self):
        self.reference_path = os.path.join(self.directory, "reference.v")
        if not os.path.exists(self.reference_path):
            reference = "\n".join(open(source, 'r').read() for source in self.config.reference_sources)
            for module in self.config.not_synthesizable:
                reference = re.sub(
                    pattern=r'\bmodule\s+' + module + r'\b.*?\bendmodule\b',
                    repl="",
                    string=reference,
                    flags=re.MULTILINE | re.DOTALL
                )
            with open(self.reference_path, 'w') as reference_file:
                reference_file.write(reference)

    def create_inject_script(self):
        self.inject_driver = os.path.join(self.directory, "inject_driver.tcl")
        if not os.path.exists(self.inject_driver):
            inject_driver = (
                f'yosys "read_verilog{" -defer" if self.name == "cva6" else ""} -sv {self.reference_path}"\n'
                f'yosys "hierarchy -check -top {self.config.host_module}"\n'
                f'yosys "setattr -unset always_comb p:*"\n'
                f'yosys "proc -norom"\n' +
                (f'yosys "opt_clean"\n' if self.name == "cva6" else "") +
                f'yosys "inject_driver -output-dir {self.driver_directory}"\n'
            )
            with open(self.inject_driver, 'w') as inject_driver_file:
                inject_driver_file.write(inject_driver)

        self.inject_multiplexer = os.path.join(self.directory, "inject_multiplexer.tcl")
        if not os.path.exists(self.inject_multiplexer):
            inject_multiplexer = (
                f'yosys "read_verilog{" -defer" if self.name == "cva6" else ""} -sv {self.reference_path}"\n'
                f'yosys "hierarchy -check -top {self.config.host_module}"\n'
                f'yosys "setattr -unset always_comb p:*"\n'
                f'yosys "proc -norom"\n' +
                # f'yosys "muxpack"\n' +
                (f'yosys "opt_clean"\n' if self.name == "cva6" else "") +
                f'yosys "inject -output-dir {self.mux_directory}"\n'
            )
            with open(self.inject_multiplexer, 'w') as inject_multiplexer_file:
                inject_multiplexer_file.write(inject_multiplexer)

    def create_prepare_scripts(self):
        self.prepare_driver = os.path.join(self.directory, "prepare_driver.tcl")
        if not os.path.exists(self.prepare_driver):
            prepare_driver = (
                f'yosys "read_rtlil host_driver.rtlil"\n'
                f'yosys "flatten"\n'
                f'yosys "write_rtlil host.rtlil"\n'
                f'yosys "delete"\n'
                f'yosys "read_rtlil reference_driver.rtlil"\n'
                f'yosys "flatten"\n'
                f'yosys "write_rtlil reference.rtlil"\n'
            )
            with open(self.prepare_driver, 'w') as prepare_driver_file:
                prepare_driver_file.write(prepare_driver)

        self.prepare_multiplexer = os.path.join(self.directory, "prepare_multiplexer.tcl")
        if not os.path.exists(self.prepare_multiplexer):
            prepare_multiplexer = (
                f'yosys "read_rtlil host_amt.rtlil"\n'
                f'yosys "inject_map"\n'
                f'yosys "flatten"\n'
                f'yosys "write_rtlil host.rtlil"\n'
                f'yosys "delete"\n'
                f'yosys "read_rtlil ../reference.rtlil"\n'
                f'yosys "inject_map"\n'
                f'yosys "flatten"\n'
                f'yosys "write_rtlil reference.rtlil"\n'
            )
            with open(self.prepare_multiplexer, 'w') as prepare_multiplexer_file:
                prepare_multiplexer_file.write(prepare_multiplexer)

    def create_miter_script(self):
        self.miter_script = os.path.join(self.directory, "miter.tcl")
        if not os.path.exists(self.miter_script):
            observables = " \\\n".join(f"-observable {observable}" for observable in self.config.observables)
            miter_script = (
                f'yosys "read_rtlil host.rtlil"\n'
                f'yosys "rename {self.config.host_module} host"\n'
                f'yosys "read_rtlil reference.rtlil"\n'
                f'yosys "rename {self.config.host_module} reference"\n' +
                ('yosys "memory m:*rf*"\n' if self.name == "rocket" else "") +
                f'yosys "create_miter \\\n'
                f'{observables}"'
            )
            with open(self.miter_script, 'w') as miter_script_file:
                miter_script_file.write(miter_script)

    def create_yosys_verify_script(self):
        self.yosys_verify_script = os.path.join(self.directory, "yosys_verify_script.tcl")
        if not os.path.exists(self.yosys_verify_script):
            sets = " \\\n".join(f"-set {set}" for set in self.config.sets)
            yosys_verify_script = (
                f'yosys "read_rtlil miter.rtlil"\n'
                f'yosys "verify_miter \\\n'
                f'-max-sensitization {self.config.sensitization_cycles} \\\n'
                f'-max-propagation {self.config.propagation_cycles} \\\n'
                f'-timeout {self.config.timeout} \\\n'
                f'-set-init-zero \\\n'
                f'{sets} \\\n'
                f'-show-inputs \\\n'
                f'-show-outputs"'
            )
            with open(self.yosys_verify_script, 'w') as verify_file:
                verify_file.write(yosys_verify_script)

    def create_export_script(self):
        self.export_script = os.path.join(self.directory, "export.tcl")
        if not os.path.exists(self.export_script):
            export_script = (
                f'yosys "read_rtlil ../host.rtlil"\n'
                f'yosys "write_verilog host.v"\n'
            )
            with open(self.export_script, 'w') as export_script_file:
                export_script_file.write(export_script)

    def create_instrument_script(self):
        self.instrument_script = os.path.join(self.directory, "instrument.tcl")
        if not os.path.exists(self.instrument_script):
            instrument_script = (
                f'yosys "read_rtlil ../host.rtlil"\n'
                f'yosys "difuzzrtl_instrument"\n'
                f'yosys "write_verilog host.v"\n'
            )
            with open(self.instrument_script, 'w') as instrument_script_file:
                instrument_script_file.write(instrument_script)

        self.export_difuzzrtl_reference = os.path.join(self.directory, "export_difuzzrtl_reference.tcl")
        if not os.path.exists(self.export_difuzzrtl_reference):
            export_difuzzrtl_reference_script = (
                f'yosys "read_rtlil ../reference.rtlil"\n'
                f'yosys "difuzzrtl_instrument"\n'
                f'yosys "write_verilog reference.v"\n'
            )
            with open(self.export_difuzzrtl_reference, 'w') as export_difuzzrtl_reference_file:
                export_difuzzrtl_reference_file.write(export_difuzzrtl_reference_script)

    def create_cascade_receptor(self):
        self.cascade_receptor = os.path.join(self.directory, "cascade_receptor.v")
        if not os.path.exists(self.cascade_receptor):
            cascade_receptor = "\n".join(open(source, 'r').read() for source in self.config.cascade_receptor_sources)
            for module in self.config.not_synthesizable + [self.config.host_module]:
                cascade_receptor = re.sub(
                    pattern=r'\bmodule\s+' + module + r'\b.*?\bendmodule\b',
                    repl="",
                    string=cascade_receptor,
                    flags=re.MULTILINE | re.DOTALL
                )
            with open(self.cascade_receptor, 'w') as cascade_receptor_file:
                cascade_receptor_file.write(cascade_receptor)

    def create_difuzzrtl_receptor(self):
        self.difuzzrtl_receptor = os.path.join(self.directory, "difuzzrtl_receptor.v")
        if not os.path.exists(self.difuzzrtl_receptor):
            difuzzrtl_receptor = re.sub(
                pattern=r'\bmodule\s+' + self.config.host_module + r'\b.*?\bendmodule\b',
                repl="",
                string="\n".join(open(source, 'r').read() for source in self.config.difuzzrtl_receptor_sources),
                flags=re.MULTILINE | re.DOTALL
            )
            with open(self.difuzzrtl_receptor, 'w') as difuzzrtl_receptor_file:
                difuzzrtl_receptor_file.write(difuzzrtl_receptor)

    def create_processorfuzz_receptor(self):
        self.processorfuzz_receptor = os.path.join(self.directory, "processorfuzz_receptor.v")
        if not os.path.exists(self.processorfuzz_receptor):
            processorfuzz_receptor = re.sub(
                pattern=r'\bmodule\s+' + self.config.host_module + r'\b.*?\bendmodule\b',
                repl="",
                string="\n".join(open(source, 'r').read() for source in self.config.processorfuzz_receptor_sources),
                flags=re.MULTILINE | re.DOTALL
            )
            with open(self.processorfuzz_receptor, 'w') as processorfuzz_receptor_file:
                processorfuzz_receptor_file.write(processorfuzz_receptor)

    def inject(self):
        self.inject_multiplexer_log = os.path.join(self.directory, "inject_multiplexer.log")
        if not os.path.exists(self.inject_multiplexer_log):
            with open(self.inject_multiplexer_log, 'w') as f:
                f.write(datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S-%f"))
                f.flush()
                subprocess.run(
                    [defines.YOSYS_PATH, '-c', self.inject_multiplexer],
                    check=True,
                    stdout=f
                )
                f.flush()
                f.write(datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S-%f"))
                f.flush()

        self.inject_driver_log = os.path.join(self.directory, "inject_driver.log")
        if not os.path.exists(self.inject_driver_log):
            with open(self.inject_driver_log, 'w') as f:
                f.write(datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S-%f"))
                f.flush()
                subprocess.run(
                    [defines.YOSYS_PATH, '-c', self.inject_driver],
                    check=True,
                    stdout=f
                )

                f.flush()
                f.write(datetime.datetime.now().strftime("%d-%m-%Y-%H-%M-%S-%f"))
                f.flush()