clear -all

analyze -sv [lindex $argv 3]
analyze -sv [lindex $argv 4]

elaborate -top miter -disable_auto_bbox

clock in_clk_i
reset -sequence [lindex $argv 5] -non_resettable_regs 0

abstract -init_value \\reference.u_ibex_core.cs_registers_i.u_mstatus_csr.rdata_q
assume -bound 1 "\\reference.u_ibex_core.cs_registers_i.u_mstatus_csr.rdata_q ==6'b001100"

abstract -init_value \\host.u_ibex_core.cs_registers_i.u_mstatus_csr.rdata_q
assume -bound 1 "\\host.u_ibex_core.cs_registers_i.u_mstatus_csr.rdata_q ==6'b001100"

set_prove_time_limit 10m

if {[prove -all] == "covered"} {
    visualize -property <embedded>::miter.i_miter.c_propagated -new_window
    visualize -save -force -vcd [lindex $argv 6] -window visualize:0
    visualize -quiet true -window visualize:0
    visualize -replot -bg -window visualize:0 -prompt
    visualize -save -force -vcd [lindex $argv 7] -window visualize:0
}

exit 0 -force