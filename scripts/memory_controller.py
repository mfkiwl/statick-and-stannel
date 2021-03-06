#!/usr/bin/env python3
import argparse, re
from math import ceil, log
from os import path

parser = argparse.ArgumentParser(description="Generate memory controller components")
parser.add_argument("-c", "--cells", default=4, help="The number of cells to generate (can infer)")
parser.add_argument("-u", "--users", default=2, help="The number of users to generate (can infer)")
parser.add_argument("-o", "--output", default=None, help="Output file (can infer)")
args = parser.parse_args()

if args.output is None:
    args.output = "MemoryController{}x{}.v".format(args.cells, args.users)
else:
    p = re.compile("MemoryController([\\d]+)x([\\d]+).v")
    m = p.search(path.basename(args.output))
    if m is not None:
        args.cells = int(m.group(1))
        args.users = int(m.group(2))

module = args.output.replace(".v", "")

with open(args.output, "w") as f:
    # Opening comment
    f.write("// Do not edit. Generated by {}\n".format(__file__))
    def pl(k):
        return "s" if k != 1 else ""
    f.write("// Supports {} component{} accessing {} cell{}\n".format(args.users, pl(args.users), args.cells, pl(args.cells)))
    f.write('`include "defaults.vh"\n')

    # Module header
    f.write("module {} #(parameter addrBits = `ADDRESS_BITS, parameter dataBits = `DATA_BITS) (\n".format(module))
    for i in range(args.users):
        f.write("  input  wire [addrBits-1:0] address{},\n".format(i))
    for i in range(args.users):
        f.write("  input  wire                readWriteMode{},\n".format(i))
    for i in range(args.users):
        f.write("  input  wire [dataBits-1:0] dataIn{},\n".format(i))
    for i in range(args.users):
        f.write("  output wire [dataBits-1:0] dataOut{},\n".format(i))
    # TODO: Get this number correct, and then handle other cases in the muxes below.
    bits_for_users = max(1, int(ceil(log(args.users, 2))))
    for i in range(args.cells):
        f.write("  input  wire [{}:0]          cell{}ToUser,\n".format(bits_for_users-1, i))
    # Deliberately last to avoid trailing comma issues
    f.write("  input  wire                clk\n")
    f.write(");\n\n")

    for i in range(args.cells):
        # Declare all the inputs and outputs of individual cells

        f.write("  reg [addrBits-1:0] cellAddress{};\n".format(i))
        f.write("  reg                cellReadWriteMode{};\n".format(i))
        f.write("  reg [dataBits-1:0] cellDataIn{};\n".format(i))
        f.write("  reg [dataBits-1:0] cellDataOut{};\n".format(i))

        # Declare the cell
        f.write("  IceRam #(.addrBits(addrBits), .dataBits(dataBits)) cell{} (\n".format(i))
        f.write("    .clk(clk),\n")
        f.write("    .address(cellAddress{}),\n".format(i))
        f.write("    .readWriteMode(cellReadWriteMode{}),\n".format(i))
        f.write("    .dataIn(cellDataIn{}),\n".format(i))
        f.write("    .dataOut(cellDataOut{})\n".format(i))
        f.write("  );\n\n")

    # Registers for output
    for i in range(args.users):
        f.write("  reg [dataBits-1:0] rDataOut{};\n".format(i))
        f.write("  assign dataOut{} = rDataOut{};\n\n".format(i, i))

    f.write("  always @(*)\n")
    f.write("  begin\n")


    # Route inputs

    for i in range(args.cells):
        f.write("    case (cell{}ToUser)\n".format(i))
        for j in range(args.users):
            f.write("      {}:\n".format(j))
            f.write("      begin\n")
            f.write("        cellAddress{}       = address{};\n".format(i, j))
            f.write("        cellReadWriteMode{} = readWriteMode{};\n".format(i, j))
            f.write("        cellDataIn{}        = dataIn{};\n".format(i, j))
            f.write("      end\n")
        # In the default case, as a safety measure, we always set to read but use an arbitrary address
        f.write("      default:\n")
        f.write("      begin\n")
        f.write("        cellAddress{}".format(i) + " =       {addrBits{1'bx}};\n")
        f.write("        cellReadWriteMode{}".format(i) + " = `RAM_READ;\n")
        f.write("        cellDataIn{}".format(i) + " =        {dataBits{1'bx}};\n")
        f.write("      end\n")
        f.write("    endcase\n\n")

    for i in range(args.users):
        f.write("    rDataOut{} =\n".format(i))
        for j in range(args.cells):
            f.write("      cell{}ToUser == {} ? cellDataOut{} :\n".format(j, i, j))
        f.write("      {dataBits{1'bx}};\n")
        f.write("\n")

    f.write("  end\n")
    f.write("endmodule\n")
