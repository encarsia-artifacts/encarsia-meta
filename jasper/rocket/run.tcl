clear -all

analyze -sv [lindex $argv 3]
analyze -sv [lindex $argv 4]

elaborate -top miter -disable_auto_bbox

clock in_clock
reset -sequence [lindex $argv 5] -non_resettable_regs 0

abstract -init_value \\reference.csr.reg_mstatus_fs 
assume -bound 1 "\\reference.csr.reg_mstatus_fs ==2'b01"

abstract -init_value \\host.csr.reg_mstatus_fs 
assume -bound 1 "\\host.csr.reg_mstatus_fs ==2'b01"

abstract -init_value \\reference.csr.reg_mstatus_mpp
assume -bound 1 "\\reference.csr.reg_mstatus_mpp ==2'b11"

abstract -init_value \\host.csr.reg_mstatus_mpp
assume -bound 1 "\\host.csr.reg_mstatus_mpp ==2'b11"

abstract -init_value \\reference.csr.reg_mstatus_spp
assume -bound 1 "\\reference.csr.reg_mstatus_spp ==1'b1"

abstract -init_value \\host.csr.reg_mstatus_spp
assume -bound 1 "\\host.csr.reg_mstatus_spp ==1'b1"

set_prove_time_limit 10m

if {[prove -all] == "covered"} {
    visualize -property <embedded>::miter.i_miter.c_propagated -new_window
    visualize -save -force -vcd [lindex $argv 6] -window visualize:0
    visualize -quiet true -window visualize:0
    visualize -replot -bg -window visualize:0 -prompt
    visualize -save -force -vcd [lindex $argv 7] -window visualize:0
}

exit 0 -force