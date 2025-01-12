
clear -all

analyze -sv miter.v
analyze -sv v_miter.sva

elaborate -top miter -disable_auto_bbox

clock in_clk_i
reset -sequence sequence.rst -non_resettable_regs 0

# abstract -init_value \\reference.u_ibex_core.cs_registers_i.mstatus_q
# assume -bound 1 "\\reference.u_ibex_core.cs_registers_i.mstatus_q ==6'b001100"

# abstract -init_value \\host.u_ibex_core.cs_registers_i.mstatus_q
# assume -bound 1 "\\host.u_ibex_core.cs_registers_i.mstatus_q ==6'b001100"

prove -all -time_limit 600m