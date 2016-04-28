#!/usr/bin/env python
# encoding: utf-8

## ==============================================
## GOAL : Benchmark devices with fio
## ==============================================

import os
import shlex
import csv
import argparse
import logging
import matplotlib
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import LinearLocator
import pprint
import subprocess
import matplotlib.pyplot as plot
import re
import pylab

## ==============================================
## 			LOGGING CONFIGURATION
## ==============================================

LOG = logging.getLogger(__name__)
LOG_handler = logging.StreamHandler()
LOG_formatter = logging.Formatter(
	fmt='%(asctime)s [%(funcName)s:%(lineno)03d] %(levelname)-5s: %(message)s',
	datefmt='%m-%d-%Y %H:%M:%S'
)
LOG_handler.setFormatter(LOG_formatter)
LOG.addHandler(LOG_handler)
LOG.setLevel(logging.INFO)

## ==============================================
## CONFIGURATION
## ==============================================

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

OPT_FONT_NAME = 'Helvetica'
OPT_GRAPH_HEIGHT = 300
OPT_GRAPH_WIDTH = 400

# Make a list by cycling through the colors you care about
# to match the length of your data.

NUM_COLORS = 5
COLOR_MAP = ( '#F58A87', '#80CA86', '#9EC9E9', '#FED113', '#D89761' )

OPT_COLORS = COLOR_MAP

OPT_GRID_COLOR = 'gray'
OPT_LEGEND_SHADOW = False
OPT_MARKERS = (['o', 's', 'v', "^", "h", "v", ">", "x", "d", "<", "|", "", "|", "_"])
OPT_PATTERNS = ([ "////", "////", "o", "o", "\\\\" , "\\\\" , "//////", "//////", ".", "." , "\\\\\\" , "\\\\\\" ])

OPT_LABEL_WEIGHT = 'bold'
OPT_LINE_COLORS = COLOR_MAP
OPT_LINE_WIDTH = 6.0
OPT_MARKER_SIZE = 8.0

AXIS_LINEWIDTH = 1.3
BAR_LINEWIDTH = 1.2

# SET FONT

LABEL_FONT_SIZE = 14
TICK_FONT_SIZE = 12
TINY_FONT_SIZE = 8
LEGEND_FONT_SIZE = 16

SMALL_LABEL_FONT_SIZE = 10
SMALL_LEGEND_FONT_SIZE = 10

AXIS_LINEWIDTH = 1.3
BAR_LINEWIDTH = 1.2

# SET TYPE1 FONTS
matplotlib.rcParams['ps.useafm'] = True
matplotlib.rcParams['font.family'] = OPT_FONT_NAME
matplotlib.rcParams['pdf.use14corefonts'] = True
#matplotlib.rcParams['text.usetex'] = True
#matplotlib.rcParams['text.latex.preamble']=[r'\usepackage{euler}']

LABEL_FP = FontProperties(style='normal', size=LABEL_FONT_SIZE, weight='bold')
TICK_FP = FontProperties(style='normal', size=TICK_FONT_SIZE)
TINY_FP = FontProperties(style='normal', size=TINY_FONT_SIZE)
LEGEND_FP = FontProperties(style='normal', size=LEGEND_FONT_SIZE, weight='bold')

SMALL_LABEL_FP = FontProperties(style='normal', size=SMALL_LABEL_FONT_SIZE, weight='bold')
SMALL_LEGEND_FP = FontProperties(style='normal', size=SMALL_LEGEND_FONT_SIZE, weight='bold')

YAXIS_TICKS = 3
YAXIS_ROUND = 1000.0

###################################################################################
# FIO CONFIGURATION
###################################################################################

FIO = "fio"

HDD_DIR = "/data/"
SSD_DIR = "/data1/"
NVM_DIR = "/mnt/pmfs/"

DEVICE_DIRS = [NVM_DIR, SSD_DIR, HDD_DIR]

IOENGINE = "sync" # "libaio"
FIO_TEST_NAME = "test" # test name
IODEPTH = 1
DIRECT = 1
FIO_IO_SIZE = "64G"
FIO_FILE_NAME = "fio" # generated file name
RANDREPEAT = 1
SYNC = 1
NUM_THREADS = 1

FIO_RUNTIME = 10 # seconds

READ_WRITE_MODES = ["randwrite", "write"]
BLOCK_SIZES = ["1024", "4096", "16384", "65536"]

OUTPUT_FILE = "fio.txt"

FIO_DIR = BASE_DIR + "/results/fio/"
BANDWIDTH_DIR = "bw"
IOPS_DIR = "iops"

###################################################################################
# UTILS
###################################################################################

def chunks(l, n):
	""" Yield successive n-sized chunks from l.
	"""
	for i in xrange(0, len(l), n):
		yield l[i:i + n]

def loadDataFile(n_rows, n_cols, path):
	data_file = open(path, "r")
	reader = csv.reader(data_file)

	data = [[0 for x in xrange(n_cols)] for y in xrange(n_rows)]

	row_num = 0
	for row in reader:
		column_num = 0
		for col in row:
			data[row_num][column_num] = float(col)
			column_num += 1
		row_num += 1

	return data

# # MAKE GRID
def makeGrid(ax):
	axes = ax.get_axes()
	axes.yaxis.grid(True, color=OPT_GRID_COLOR)
	for axis in ['top','bottom','left','right']:
			ax.spines[axis].set_linewidth(AXIS_LINEWIDTH)
	ax.set_axisbelow(True)

# # SAVE GRAPH
def saveGraph(fig, output, width, height):
	size = fig.get_size_inches()
	dpi = fig.get_dpi()
	LOG.debug("Current Size Inches: %s, DPI: %d" % (str(size), dpi))

	new_size = (width / float(dpi), height / float(dpi))
	fig.set_size_inches(new_size)
	new_size = fig.get_size_inches()
	new_dpi = fig.get_dpi()
	LOG.debug("New Size Inches: %s, DPI: %d" % (str(new_size), new_dpi))

	pp = PdfPages(output)
	fig.savefig(pp, format='pdf', bbox_inches='tight')
	pp.close()
	LOG.info("OUTPUT: %s", output)

###################################################################################
# PLOT HELPERS
###################################################################################

def create_legend():
	fig = pylab.figure()
	ax1 = fig.add_subplot(111)

	figlegend = pylab.figure(figsize=(9, 0.5))
	idx = 0
	lines = [None] * (len(DEVICE_DIRS) + 1)
	data = [1]
	x_values = [1]

	TITLE = "Devices : "
	LABELS = [TITLE, "NVM", "SSD", "HDD"]

	lines[idx], = ax1.plot(x_values, data, linewidth = 0)
	idx = 0

	for group in xrange(len(DEVICE_DIRS)):
		lines[idx + 1], = ax1.plot(x_values, data,
							   color=OPT_LINE_COLORS[idx], linewidth=OPT_LINE_WIDTH,
							   marker=OPT_MARKERS[idx], markersize=OPT_MARKER_SIZE, label=str(group))

		idx = idx + 1

	# LEGEND
	figlegend.legend(lines, LABELS, prop=LEGEND_FP,
					 loc=1, ncol=4, mode="expand", shadow=OPT_LEGEND_SHADOW,
					 frameon=False, borderaxespad=0.0, handlelength=4)

	figlegend.savefig('legend.pdf')

def create_fio_line_chart(datasets):
	fig = plot.figure()
	ax1 = fig.add_subplot(111)

	# X-AXIS
	x_values = BLOCK_SIZES

	idx = 0

	# GROUP
	for group_index, group in enumerate(DEVICE_DIRS):
		group_data = []

		# LINE
		for line_index, line in enumerate(x_values):
			group_data.append(datasets[group_index][line_index][1])

		device = get_device(group)
		LOG.info("%s group_data = %s ", device, str(group_data))

		ax1.plot(x_values, group_data, color=OPT_LINE_COLORS[idx], linewidth=OPT_LINE_WIDTH,
				 marker=OPT_MARKERS[idx], markersize=OPT_MARKER_SIZE, label=str(group))

		idx = idx + 1

	# GRID
	makeGrid(ax1)

	# Y-AXIS
	ax1.yaxis.set_major_locator(LinearLocator(YAXIS_TICKS))
	ax1.minorticks_off()
	ax1.set_ylabel("IOPS", fontproperties=LABEL_FP)
	ax1.set_yscale('log', basey=10)
	Y_MIN = pow(10, 1)
	Y_MAX = pow(10, 6)	
	ax1.set_ylim(Y_MIN, Y_MAX)

	# X-AXIS
	ax1.set_xlabel("Block size", fontproperties=LABEL_FP)
	ax1.set_xscale('log', basex=2)

	for label in ax1.get_yticklabels() :
		label.set_fontproperties(TICK_FP)
	for label in ax1.get_xticklabels() :
		label.set_fontproperties(TICK_FP)

	return (fig)

# FIO -- PLOT
def fio_plot():

	for READ_WRITE_MODE in READ_WRITE_MODES:

		datasets = []
	
		for DEVICE_DIR in DEVICE_DIRS:
	
			# Figure out device dir
			device = get_device(DEVICE_DIR)	
			data_file = FIO_DIR + "/" + READ_WRITE_MODE + "/" + device + "/" +  IOPS_DIR + "/" + "fio.csv"
			
			dataset = loadDataFile(len(BLOCK_SIZES), 2, data_file)
			datasets.append(dataset)
	
		fig = create_fio_line_chart(datasets)
	
		fileName = READ_WRITE_MODE + ".pdf"
	
		saveGraph(fig, fileName, width= OPT_GRAPH_WIDTH, height=OPT_GRAPH_HEIGHT/2.0)


## ==============================================
## UTILS
## ==============================================

def get_device(device_dir):
	# Figure out device
	device = "INVALID"
	if device_dir == DEVICE_DIRS[0]:
		device = "NVM"
	elif device_dir == DEVICE_DIRS[1]:
		device = "SSD"
	elif device_dir == DEVICE_DIRS[2]:
		device = "HDD"
		
	return device

# CLEAN UP RESULT DIR
def clean_up_dir(result_directory):

	subprocess.call(['rm', '-rf', result_directory])
	if not os.path.exists(result_directory):
			os.makedirs(result_directory)


def exec_cmd(cmd):
	"""
	Execute the external command and get its exitcode, stdout and stderr.
	"""
	args = shlex.split(cmd)
	verbose = True

	try:
		if verbose == True:
			subprocess.check_call(args)
		else:
			subprocess.check_call(args, 
								  stdout=subprocess.STDOUT, 
								  stderr=subprocess.STDOUT)
	# Exception
	except subprocess.CalledProcessError as e:
		print "Command	 :: ", e.cmd
		print "Return Code :: ", e.returncode
		print "Output	  :: ", e.output

# COLLECT STATS
def collect_stats(result_dir, result_file_name, 
				  read_write_mode, device_dir, block_size):

	fp = open(OUTPUT_FILE)
	lines = fp.readlines()
	fp.close()

	# Stats
	bw = 0
	iops = 0
		
	# Collect stats
	for line in lines:
		if "iops" in line: 
			data = line.split(',')		
			LOG.info(line.rstrip('\n'))

			bw_scale = 1
			bw_raw = data[1].split('=')[1].rstrip(',')
			if bw_raw.endswith("KB/s"):
				bw_scale = 1024
			elif bw_raw.endswith("MB/s"):
				bw_scale = 1024 * 1024				
			elif bw_raw.endswith("GB/s"):
				bw_scale = 1024 * 1024 * 1024				
			bw = float(re.sub('[^0-9]','', bw_raw)) * bw_scale

			iops_scale = 1
			iops_raw = data[2].split('=')[1].rstrip(',')			
			if iops_raw.endswith("K"):
				iops_scale = 1024
			elif iops_raw.endswith("M"):
				iops_scale = 1024 * 1024				
			elif iops_raw.endswith("G"):
				iops_scale = 1024 * 1024 * 1024

			iops = float(re.sub('[^0-9]','', iops_raw)) * iops_scale
			LOG.info("BW : --" + str(bw) + "--")
			LOG.info("IOPS : --" + str(iops) + "--")
	
	# Figure out device dir
	device = get_device(device_dir)	

	# Make result dir and file
	bw_result_directory = result_dir + "/" + read_write_mode + "/" + device + "/" + BANDWIDTH_DIR
	iops_result_directory = result_dir + "/" + read_write_mode + "/" + device + "/" + IOPS_DIR

	if not os.path.exists(bw_result_directory):
		os.makedirs(bw_result_directory)
	if not os.path.exists(iops_result_directory):
		os.makedirs(iops_result_directory)

	bw_file_name = bw_result_directory + "/" + result_file_name
	bw_result_file = open(bw_file_name, "a")
	iops_file_name = iops_result_directory + "/" + result_file_name
	iops_result_file = open(iops_file_name, "a")

	# Write out stats
	bw_result_file.write(str(block_size) + " , " + str(bw) + "\n")
	bw_result_file.close()
	iops_result_file.write(str(block_size) + " , " + str(iops) + "\n")
	iops_result_file.close()

def fio_eval():

		# Cleanup
		clean_up_dir(FIO_DIR)
		
		# Go over all the readwrite modes
		for READ_WRITE_MODE in READ_WRITE_MODES:

			# Go over all the devices
			for DEVICE_DIR in DEVICE_DIRS:		

				# Go over all the block sizes
				for BLOCK_SIZE in BLOCK_SIZES:
					
					fio_test_file_name = DEVICE_DIR + FIO_FILE_NAME
							
					# fio --randrepeat=1 --ioengine=sync --name=test --iodepth=64 --direct=1 --bs=4k 
					# --filename=/data/fio --size=64M --readwrite=randread
					fio_command = FIO \
					+ " --readwrite=" + str(READ_WRITE_MODE) \
					+ " --filename=" + fio_test_file_name \
					+ " --blocksize=" + str(BLOCK_SIZE) \
					+ " --ioengine=" + IOENGINE \
					+ " --randrepeat=" + str(RANDREPEAT) \
					+ " --name=" + FIO_TEST_NAME \
					+ " --iodepth=" + str(IODEPTH) \
					+ " --sync=" + str(SYNC) \
					+ " --direct=" + str(DIRECT) \
					+ " --size=" + str(FIO_IO_SIZE) \
					+ " --runtime=" + str(FIO_RUNTIME) \
					+ " --output=" + str(OUTPUT_FILE) \
					+ " --max-jobs=" + str(NUM_THREADS)
					
					LOG.info(fio_command)
		
					# Run command
					exec_cmd(fio_command)
					
					# Collect stats
					collect_stats(FIO_DIR, "fio.csv", READ_WRITE_MODE, DEVICE_DIR, BLOCK_SIZE)
				
## ==============================================
## 				Main Function
## ==============================================

if __name__ == '__main__':

	parser = argparse.ArgumentParser(description='Benchmark devices with fio')

	parser.add_argument("-f", "--fio", help='run fio on devices', action='store_true')

	parser.add_argument("-a", "--fio_plot", help='plot fio results', action='store_true')

	args = parser.parse_args()
	
	if args.fio:
		fio_eval()

	if args.fio_plot:
		fio_plot()

	#create_legend()
