#!/usr/bin/python

import sys                  # command line arguments
import time                 # time handling
import subprocess           # call gnulpot
from time import strftime   # convert time to string
import os                   # wait on gnuplot

# Check for correct arguments
if (len(sys.argv) != 4):
    print "\nUsage: python acc-plotter.py [data.csv] [num-channels] \
    [graph-freq]\n"
    print "[data.csv] is the data CSV file which should be plotted\n"
    print "[num-channels] is the number of data channels which should \
    be plotted"
    print "The data channels will be plotted in the consecutive order found\
     in the file starting with the second column, where the first column \
     is the x axis.\n"
    print "[graph-freq] is the sample frequency in Hz of the plotted data."
    print "A value of 0 will use the full frequency of the given file."
    print "Any non-zero value must be lower than the frequency of data in \
    the given file.\n"
    sys.exit()

#[start-time] is the start time of the data to be plotted.  
# Give in format HH:MM
# A value of 0 will plot the entire time range of the given data file

#[end-time] is the end time range of the plot.  
# TODO: Include the option to manually set the yrange

filename = sys.argv[1]
numchannels = int(sys.argv[2])
freq = int(sys.argv[3])

# Get metadata from the file
with open(filename) as f:
    head=[f.next() for x in xrange(8)]
# Get the channel frequency
freq_file = int(head[6].lstrip("Collection Rate (Hz),"))
# TODO: Get the total number of rows
# TODO: Get the number of channels

every = freq_file/freq

# Get number_of_channels of log file
# Check that the given parameter is within bounds
# if ([num-channels] > number_of_channels) return 0;

# Get data_frequency of log file
# Check that given parameter is within bounds
# if ([data-freq] > ) return 0;
# Calculate how often to skip a data point to meet [data-freq]
# else {
#     every = data_frequency/[data-freq];
# }
# Calculate the number of points to skip to achieve the desired
#    graph sample rate

# Get absolute start_time of file
starttime = time.strptime(filename, "LOG_%d%b%Y_%Hh%Mm%Ss.csv")
# Convert to Unix Epoch time
epoch = time.mktime(starttime)
# Convert start time to string
ststr = strftime("%d%b%Y_%Hh%Mm%Ss", starttime)
# TODO: Calculate end time of file

# Check if given parameters are within bounds
# if ([start-time] < start_time) return 0;
# if ([end-time] > end_time) return 0;

# Send gnuplot commands
# Open the subprocess
plot = subprocess.Popen(['gnuplot', 'p'], stdin=subprocess.PIPE, shell=True)
plot.stdin.write("set datafile separator \",\"\n")
# Is this necessary?
# cd 'C:\Users\bjorr.CTLPC30\Desktop\AccTests\'
plot.stdin.write("set terminal png font \"arial,55\" size 5000,5000\n")
# set yrange [32730:32780]
plot.stdin.write("set autoscale\n")
plot.stdin.write("set xlabel \"Time (HH:MM)\"\n")
plot.stdin.write("set ylabel \"Accelerometer Output (Qualitative Unit)\"\n")
plot.stdin.write("set key autotitle columnhead\n")  # Get line names from the first row of data
plot.stdin.write("set xdata time\n")
plot.stdin.write("set timefmt \"%s\"\n")
plot.stdin.write("set format x \"%H:%M\"\n")
plot.stdin.write("set title \"Vibration Data Starting at %s\"\n" % strftime("%d%b%Y at %H:%M:%S", starttime))
# TODO: Add the duration time of the plot
plot.stdin.write("set output '%s_%dchan.png'\n" % (ststr,numchannels))

# Number of lines occupied by metadata which should be skipped
md = 8

# Handle the plot commands
if numchannels == 1:
    # There is only one line to plot
    plot.stdin.write("plot '%s' every %d::%d using ($1+%d-(5*3600)):2 with \
        linespoints\n" % (filename, every, md, epoch))
    plot.stdin.write("quit\n")
    os.waitpid(plot.pid, 0)
else:
    # First line
    plot.stdin.write("plot '%s' every %d::%d using ($1+%d-(5*3600)):2 with \
    linespoints," % (filename, every, md, epoch))
    # Loop through the middle portion of the requested channels
    for i in range(3, numchannels + 1):
        plot.stdin.write("'%s' every %d::%d using ($1+%d-(5*3600)):%d with \
        linespoints," % (filename, every, md, epoch, i))
    # Final line
    plot.stdin.write("'%s' every %d::%d using ($1+%d-(5*3600)):%d with \
    linespoints\n" % (filename, every, md, epoch, numchannels + 1))
    plot.stdin.write("quit\n")
    os.waitpid(plot.pid, 0) # Wait for the 
    