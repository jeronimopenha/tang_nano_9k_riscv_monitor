import os
import sys

if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

import argparse
import traceback
from veriloggen import *
from math import ceil


def write_file(name: str, string: str):
    with open(name, 'w') as fp:
        fp.write(string)
        fp.close()


def create_args():
    parser = argparse.ArgumentParser('create_project -h')
    parser.add_argument(
        '-i', '--i_o_number', help='Number of interface I/Os', type=int, default=1)
    parser.add_argument(
        '-f', '--io_fifo_depth', help='Depth bits for each I/O FIFOs', type=int, default=2)
    parser.add_argument(
        '-w', '--data_width', help='Acc word width in bis. Max = 64b', type=int, default=8)
    parser.add_argument(
        '-o', '--output', help='Project output folter location', type=str, default='.')

    return parser.parse_args()


# TODO
def create_project(interface_root: str, output_path: str, data_width: int, i_o_number: int, fifo_depth:int):
    pass

    '''sa_graph = _u.SaGraph(dot_file)
    # sa_graph.n_cells = 144
    # sa_graph.n_cells_sqrt = 12
    sa_acc = _sa.SaAccelerator(sa_graph, copies)
    acc_axi = AccAXIInterface(sa_acc)

    template_path = sa_root + '/resources/template.prj'
    cmd = 'cp -r %s  %s/%s' % (template_path, output_path, name)
    _u.commands_getoutput(cmd)

    hw_path = '%s/%s/xilinx_aws_f1/hw/' % (output_path, name)
    sw_path = '%s/%s/xilinx_aws_f1/sw/' % (output_path, name)

    m = acc_axi.create_kernel_top(name)
    m.to_verilog(hw_path + 'src/%s.v' % name)

    acc_config = '#define NUM_CHANNELS (%d)\n' % sa_acc.copies
    #acc_config += '#define NUM_THREADS (%d)\n' % sa_acc.threads
    #acc_config += '#define NUM_NOS (%d)\n' % sa_acc.nodes_qty
    #acc_config += '#define STATE_SIZE_WORDS (%d)\n' % ceil(sa_acc.nodes_qty / 8)
    #acc_config += '#define BUS_WIDTH_BYTES (%d)\n' % (sa_acc.bus_width // 8)
    #acc_config += '#define OUTPUT_DATA_BYTES (%d)\n' % (ceil(bits_width / bus_width) * bus_width // 8)
    #acc_config += '#define ACC_DATA_BYTES (%d)\n' % (sa_acc.axi_bus_data_width // 8)

    num_axis_str = 'NUM_M_AXIS=%d' % sa_acc.get_num_in()
    conn_str = acc_axi.get_connectivity_config(name)

    write_file(hw_path + 'simulate/num_m_axis.mk', num_axis_str)
    write_file(hw_path + 'synthesis/num_m_axis.mk', num_axis_str)
    write_file(sw_path + 'host/prj_name', name)
    write_file(sw_path + 'host/include/acc_config.h', acc_config)
    write_file(hw_path + 'simulate/prj_name', name)
    write_file(hw_path + 'synthesis/prj_name', name)
    write_file(hw_path + 'simulate/vitis_config.txt', conn_str)
    write_file(hw_path + 'synthesis/vitis_config.txt', conn_str)'''


def main():
    args = create_args()
    running_path = os.getcwd()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    interface_root = os.getcwd()

    if args.output == '.':
        args.output = running_path
    if args.data_width > 64:
        raise TypeError("The Acc data width cannot be greater than 64b.")
    if args.io_fifo_depth < 0:
        raise TypeError("The I/O FIFOs depth cannot be less than 1.")

    create_project(interface_root, args.output,
                   args.data_width, args.i_o_number, args.io_fifo_depth)
    print('Project successfully created in %s/' % (args.output))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(e)
        traceback.print_exc()
