import os

class EncarsiaConfig:
    def __init__(
        self,
        reference_sources: list[str],
        cascade_receptor_sources: list[str],
        difuzzrtl_receptor_sources: list[str],
        processorfuzz_receptor_sources: list[str],
        host_module: str,
        not_synthesizable: list[str],
        sensitization_cycles: int,
        propagation_cycles: int,
        timeout: int,
        observables: list[str],
        sets: list[str],
        instruction_signal: str,
        cascade_directory: str,
        cascade_executable: str,
        difuzzrtl_toplevel: str
    ):
        # paths
        self.reference_sources = reference_sources
        self.cascade_receptor_sources = cascade_receptor_sources
        self.difuzzrtl_receptor_sources = difuzzrtl_receptor_sources
        self.processorfuzz_receptor_sources = processorfuzz_receptor_sources

        # injection
        self.host_module = host_module
        self.not_synthesizable = not_synthesizable

        # verifier
        self.sensitization_cycles = sensitization_cycles
        self.propagation_cycles = propagation_cycles
        self.timeout = timeout
        self.observables = observables
        # TODO make the input names match those of the original design not those of the miter
        self.sets = sets

        # build
        self.instruction_signal = instruction_signal

        # cascade
        self.cascade_directory = cascade_directory
        self.cascade_executable = cascade_executable

        self.difuzzrtl_toplevel = difuzzrtl_toplevel

rocket_config = EncarsiaConfig(
    reference_sources = [
        os.path.abspath("/cascade-chipyard/cascade-rocket/src/dependencies/plusarg_reader.v"),
        os.path.abspath("/cascade-chipyard/sims/verilator/generated-src/chipyard.TestHarness.MyBigVMRocketConfig/chipyard.TestHarness.MyBigVMRocketConfig.top.v")
    ],
    cascade_receptor_sources = [
        os.path.abspath("/cascade-chipyard/cascade-common/src/defines.v"),
        os.path.abspath("/cascade-chipyard/cascade-rocket/src/dependencies/ClockDividerN.sv"),
        os.path.abspath("/cascade-chipyard/cascade-rocket/src/dependencies/EICG_wrapper.v"),
        os.path.abspath("/cascade-chipyard/cascade-rocket/src/dependencies/IOCell.v"),
        os.path.abspath("/cascade-chipyard/cascade-rocket/src/dependencies/plusarg_reader.v"),
        os.path.abspath("/cascade-chipyard/cascade-rocket/src/dependencies/sram_behav_models.v"),
        os.path.abspath("/cascade-chipyard/sims/verilator/generated-src/chipyard.TestHarness.MyBigVMRocketConfig/chipyard.TestHarness.MyBigVMRocketConfig.top.mems.v"),
        os.path.abspath("/cascade-chipyard/sims/verilator/generated-src/chipyard.TestHarness.MyBigVMRocketConfig/chipyard.TestHarness.MyBigVMRocketConfig.top.v"),
        os.path.abspath("/cascade-chipyard/cascade-rocket/generated/rocket_axi_to_mem.v"),
        os.path.abspath("/cascade-chipyard/cascade-rocket/generated/rocket_mem_top.v")
    ],
    difuzzrtl_receptor_sources = [
        os.path.abspath("/encarsia-difuzz-rtl/Benchmarks/Verilog/RocketTile_encarsia.v")
    ],
    processorfuzz_receptor_sources = [
        os.path.abspath("/encarsia-processorfuzz/Benchmarks/Verilog/RocketTile_encarsia.v")
    ],
    host_module = "Rocket",
    not_synthesizable= [],
    sensitization_cycles = 18,
    propagation_cycles = 32,
    timeout = 600,
    observables = ["rf\[10\]"],
    sets = [
        "in_io_dmem_resp_bits_data_word_bypass 0",
        "in_io_dmem_resp_bits_data 0",
        "in_io_fpu_store_data 0",
        "in_io_fpu_toint_data 0"
    ],
    instruction_signal = "io_imem_resp_bits_data",
    cascade_directory = os.path.abspath("/cascade-chipyard/cascade-rocket"),
    cascade_executable = "Vtop_tiny_soc",
    difuzzrtl_toplevel = "RocketTile"
)

boom_config = EncarsiaConfig(
    reference_sources = [
        os.path.abspath("/cascade-chipyard/cascade-boom/src/dependencies/plusarg_reader.v"),
        os.path.abspath("/cascade-chipyard/sims/verilator/generated-src/chipyard.TestHarness.MyMediumBoomConfigTracing/chipyard.TestHarness.MyMediumBoomConfigTracing.top.v"),
        os.path.abspath("/cascade-chipyard/sims/verilator/generated-src/chipyard.TestHarness.MyMediumBoomConfigTracing/chipyard.TestHarness.MyMediumBoomConfigTracing.top.mems.v")
    ],
    cascade_receptor_sources = [
        os.path.abspath("/cascade-chipyard/cascade-common/src/defines.v"),
        os.path.abspath("/cascade-chipyard/cascade-boom/src/dependencies/ClockDividerN.sv"),
        os.path.abspath("/cascade-chipyard/cascade-boom/src/dependencies/EICG_wrapper.v"),
        os.path.abspath("/cascade-chipyard/cascade-boom/src/dependencies/IOCell.v"),
        os.path.abspath("/cascade-chipyard/cascade-boom/src/dependencies/plusarg_reader.v"),
        os.path.abspath("/cascade-chipyard/cascade-boom/src/dependencies/sram_behav_models.v"),
        os.path.abspath("/cascade-chipyard/sims/verilator/generated-src/chipyard.TestHarness.MyMediumBoomConfigTracing/chipyard.TestHarness.MyMediumBoomConfigTracing.top.mems.v"),
        os.path.abspath("/cascade-chipyard/sims/verilator/generated-src/chipyard.TestHarness.MyMediumBoomConfigTracing/chipyard.TestHarness.MyMediumBoomConfigTracing.top.v"),
        os.path.abspath("/cascade-chipyard/cascade-boom/generated/boom_axi_to_mem.v"),
        os.path.abspath("/cascade-chipyard/cascade-boom/generated/boom_mem_top.v")
    ],
    difuzzrtl_receptor_sources = [
        os.path.abspath("/encarsia-difuzz-rtl/Benchmarks/Verilog/SmallBoomTile_encarsia.v")
    ],
    processorfuzz_receptor_sources = [
        os.path.abspath("/encarsia-processorfuzz/Benchmarks/Verilog/SmallBoomTile_encarsia.v")
    ],
    host_module = "BoomCore",
    not_synthesizable= [],
    sensitization_cycles = 12,
    propagation_cycles = 20,
    timeout = 600,
    observables = ["iregfile.io_read_ports_0_data"],
    sets = [],
    instruction_signal = "io_ifu_fetchpacket_bits_uops_0_bits_inst",
    cascade_directory = os.path.abspath("/cascade-chipyard/cascade-boom"),
    cascade_executable = "Vtop_tiny_soc",
    difuzzrtl_toplevel = "BoomTile"
)

cva6_config = EncarsiaConfig(
    reference_sources = [
        os.path.abspath("/encarsia-cva6/cascade/generated/sv2v_out.v")
    ],
    cascade_receptor_sources = [
        os.path.abspath("/encarsia-cva6/cascade/generated/sv2v_out.v")
    ],
    difuzzrtl_receptor_sources = [],
    processorfuzz_receptor_sources = [],
    host_module = "cva6",
    not_synthesizable= [],
    sensitization_cycles = 32,
    propagation_cycles = 32,
    timeout = 10000000,
    observables = ["issue_stage_i.i_issue_read_operands.gen_asic_regfile.i_ariane_regfile.mem"],
    sets = [],
    instruction_signal = "frontend.fetch_entry_o",
    cascade_directory = os.path.abspath("/encarsia-cva6/cascade"),
    cascade_executable = "Variane_tiny_soc",
    difuzzrtl_toplevel = ""
)

ibex_config = EncarsiaConfig(
    reference_sources = [
        os.path.abspath("/encarsia-ibex/cellift/generated/out/vanilla.sv")
    ],
    cascade_receptor_sources = [
        os.path.abspath("/encarsia-ibex/cellift/generated/out/vanilla.sv")
    ],
    difuzzrtl_receptor_sources = [],
    processorfuzz_receptor_sources = [],
    host_module = "cellift_ibex_top",
    not_synthesizable= [],
    sensitization_cycles = 32,
    propagation_cycles = 32,
    timeout = 10000000,
    observables = ["gen_regfile_ff.register_file_i.rf_reg"],
    sets = [],
    instruction_signal = "u_ibex_core.instr_rdata_i",
    cascade_directory = os.path.abspath("/encarsia-ibex/cellift"),
    cascade_executable = "Vibex_tiny_soc",
    difuzzrtl_toplevel = ""
)

def get_host_config(name: str):
    if name == "rocket":
        return rocket_config
    elif name == "boom":
        return boom_config
    elif name == "cva6":
        return cva6_config
    elif name == "ibex":
        return ibex_config
    else:
        raise Exception(f"No configuration found for host '{name}'")