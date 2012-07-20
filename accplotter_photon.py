#!/usr/bin/python
# Built for Python 2.6
# Written by Alex Dunn of APS, Argonne National Lab

import sys                  # command line arguments
import time                 # time handling
import subprocess           # call gnulpot
from time import strftime   # convert time to string
import os                   # wait on gnuplot

# Check for correct arguments
if (len(sys.argv) != 6):
    print "\nUsage: python acc-plotter.py [data.csv] " + \
    "[graph-freq] [title] [start] [end]\n"
    print "[data.csv] is the data CSV file which should be plotted\n"
    print "[graph-freq] is the sample frequency in Hz of the plotted data."
    print "A value of 0 will use the full frequency of the given file."
    print "Any non-zero value must be lower than the frequency of data in" + \
    "the given file.\n"
    print "[title] is an alternative title for the plot which will be" + \
    "printed as '[title] Starting at DATE'.  A value of zero will use the" + \
    "default plot title, 'Vibration Data Starting at DATE'\n"
    print "[start] is the start time in HH:MM.  If '0', then starts of file's start.\n"
    print "[end] is the graph end time in HH:MM.  If '0', then ends at file's end."
    sys.exit()

# Note: This assumes that the DAQ is set to +/- 10V scanning range

# TODO: Include the option to manually set the yrange
# TODO: Include the option to manually set the output resolution

fname_arg = sys.argv[1]
freq_arg = int(sys.argv[2])
title_arg = sys.argv[3]
start_arg = sys.argv[4]
end_arg = sys.argv[5]

# Get metadata from the file
with open(fname_arg) as f:
    head=[f.next() for x in xrange(8)]
# Get the channel frequency
freq_file = int(head[6].lstrip("Collection Rate (Hz),"))
# Get the total number of rows
rows_file = int(head[4].lstrip("No. of Samples,"))
# Get the number of channels
chan_low = int(head[1].lstrip("Low Channel,"))
chan_high = int(head[2].lstrip("High Channel,"))
numchan_file = chan_high - chan_low + 1

# Check that given frequency is within bounds
if freq_file < freq_arg:
    print "Your requested frequency is higher than the file's data sample rate"
    sys.exit()

# Calculate the number of points to skip from the data file
#    frequency and the desired graph sampling rate
if freq_arg == 0:
    # Plot all data points
    every = 1
else:
    every = freq_file/freq_arg

# Get absolute start_time of file
starttime = time.strptime(fname_arg, "LOG_%d%b%Y_%Hh%Mm%Ss.csv")
file_startsecs = starttime.tm_hour*3600 + starttime.tm_min*60
# Convert to Unix Epoch time
epoch_start = time.mktime(starttime)
# Convert start time to string
ststr = strftime("%d%b%Y_%Hh%Mm%Ss", starttime)
# Calculate end time of file
epoch_end = epoch_start + \
    ((1/float(freq_file))*(float(rows_file)-1))/numchan_file
# Convert to time structure
endtime = time.gmtime(epoch_end)

# Calculate start position
if start_arg != '0':
    start_split = start_arg.partition(':')
    start_hr = int(start_split[0])
    start_mn = int(start_split[2])
    my_startsecs = start_hr*3600 + start_mn*60
    plot_start = my_startsecs - file_startsecs + epoch_start
else:
    plot_start = epoch_start

# Calculate end position
if end_arg != '0':
    file_endsecs = endtime.tm_hour*3600 + endtime.tm_min*60
    end_split = end_arg.partition(':')
    end_hr = int(end_split[0])
    end_mn = int(end_split[2])
    my_endsecs = end_hr*3600 + end_mn*60
    plot_end = my_endsecs - file_startsecs + epoch_start
else:
    plot_end = epoch_end

start_stct = time.gmtime(plot_start - 5*3600)
end_stct = time.gmtime(plot_end - 5*3600)

# Send gnuplot commands
# Open the subprocess
plot = subprocess.Popen(['gnuplot', 'p'], 
                        stdin=subprocess.PIPE, 
                        shell=True)

# Set the title
if title_arg != "0":
    # Custom graph title
    plot.stdin.write("set title \"%s Starting at %s, %dHz\"\n" % 
                (title_arg, 
                 strftime("%d %b %Y at %H:%M:%S", start_stct), 
                 freq_arg))
else:
    # Default graph title
    plot.stdin.write("set title \"Photon Data Starting at %s, %dHz\"\n" % 
                     strftime("%d %b %Y at %H:%M:%S", start_stct),
                     freq_arg)

plot.stdin.write("set datafile separator \",\"\n")
# Is this necessary?
# cd 'C:\Users\bjorr.CTLPC30\Desktop\AccTests\'
plot.stdin.write("set terminal png font \"arial,55\" size 5000,5000\n")
# set yrange [32730:32780]
plot.stdin.write("set autoscale\n")
# x-axis label
plot.stdin.write("set xlabel \"Time (HH:MM)\"\n")
# y-axis label
plot.stdin.write("set ylabel \"Photon Data\"\n")
# Get line names from the first row of data
plot.stdin.write("set key autotitle columnhead\n")  
# Interpret the x-axis data as a time unit
plot.stdin.write("set xdata time\n")
# Interpret it as seconds since Unix epoch
plot.stdin.write("set timefmt \"%s\"\n")
# x-axis tics should be in the format Hours:Minutes
plot.stdin.write("set format x \"%H:%M\"\n")

plot.stdin.write("set output '%s_inout_%sto%s.png'\n" % 
                 (strftime("%d%b%Y", starttime),
                  strftime("%H:%M", start_stct),
                  strftime("%H:%M", end_stct)))
# Set the range to be plotted
plot.stdin.write("set xrange [%f-(5*3600):%f-(5*3600)]\n" % 
                 (plot_start, plot_end))

chan_names = ["x-axis", "y-axis", "z-axis", "IN", "OUT", "TOP", "BOT"]

# Number of lines occupied by metadata which should be skipped
md = 8

print "Plotting data starting at " + str(plot_start)
print "Graph will end at " + str(plot_end)

plot.stdin.write("plot '%s' every %d::%d using ($1+%d-(5*3600)):(((($5-$6/($5+$6))-32768)/32768)*10) with \
    linespoints title '(IN-OUT)/(IN+OUT)'\n" % (fname_arg, 
                                     every, md, 
                                     epoch_start))

plot.stdin.write("set output '%s_topbot_%sto%s.png'\n" % 
                 (strftime("%d%b%Y", starttime),
                  strftime("%H:%M", start_stct),
                  strftime("%H:%M", end_stct)))

plot.stdin.write("plot '%s' every %d::%d using ($1+%d-(5*3600)):(((($7-$8/($7+$8))-32768)/32768)*10) with \
    linespoints title '(TOP-BOT)/(TOP+BOT)'\n" % (fname_arg, 
                                     every, md, 
                                     epoch_start))

plot.stdin.write("quit\n")
os.waitpid(plot.pid, 0)