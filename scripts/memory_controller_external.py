#!/usr/bin/env python3
import argparse, re
from math import ceil, log
from os import path

parser = argparse.ArgumentParser(description="Generate MemoryControllerExternal components")
parser.add_argument("-u", "--users", type=int, default=4, help="The number of users to generate (can infer)")
parser.add_argument("-o", "--output", default=None, help="Output file (can infer)")
args = parser.parse_args()

if args.output is None:
    args.output = "MemoryControllerExternal{}.v".format(args.cells)
else:
    p = re.compile("MemoryControllerExternal([\\d]+).v")
    m = p.search(path.basename(args.output))
    if m is not None:
        args.users = int(m.group(1))

module = args.output.replace(".v", "")

with open(args.output, "w") as f:
    # Opening comment
    f.write("// Do not edit. Generated by {}\n".format(__file__))
    def pl(k):
        return "s" if k != 1 else ""
    f.write("// Supports {} component{} accessing 1 cell\n".format(args.users, pl(args.users)))
    f.write('`include "defaults.vh"\n')

    # Module header
    f.write("module {} #(parameter addrBits = `ADDRESS_BITS, parameter dataBits = `DATA_BITS) (\n".format(module))
    for i in range(args.users):
        f.write("  input  wire [addrBits-1:0] address{},\n".format(i))
        f.write("  input  wire                readWriteMode{},\n".format(i))
        f.write("  input  wire [dataBits-1:0] dataIn{},\n".format(i))
    bits_for_users = max(1, int(ceil(log(args.users, 2))))
    f.write("  input  wire [{}:0]          cellToUser,\n".format(bits_for_users-1))
    f.write("  output wire [addrBits-1:0] address,\n")
    f.write("  output wire [dataBits-1:0] dataIn,\n")
    f.write("  output wire                readWriteMode\n")
    f.write(");\n\n")

    f.write("  reg [addrBits-1:0] wAddress;\n")
    f.write("  reg [dataBits-1:0] wDataIn;\n")
    f.write("  reg                wReadWriteMode;\n\n")

    f.write("  assign address       = wAddress;\n")
    f.write("  assign dataIn        = wDataIn;\n")
    f.write("  assign readWriteMode = wReadWriteMode;\n\n")

    f.write("  always @(*)\n")
    f.write("    case (cellToUser)\n")
    for j in range(args.users):
        f.write("      {}:\n".format(j))
        f.write("      begin\n")
        f.write("        wAddress       = address{};\n".format(j))
        f.write("        wReadWriteMode = readWriteMode{};\n".format(j))
        f.write("        wDataIn        = dataIn{};\n".format(j))
        f.write("      end\n")
    # In the default case, as a safety measure, we always set to read but use an arbitrary address
    f.write("      default:\n")
    f.write("      begin\n")
    f.write("        wAddress       = {addrBits{1'bx}};\n")
    f.write("        wReadWriteMode = `RAM_READ;\n")
    f.write("        wDataIn        = {dataBits{1'bx}};\n")
    f.write("      end\n")
    f.write("    endcase\n\n")
    f.write("endmodule\n")
