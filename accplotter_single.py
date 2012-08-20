#!/usr/bin/python
# Built for Python 2.6
# Written by Alex Dunn of APS, Argonne National Lab

import sys                  # command line arguments
import time                 # time handling
import subprocess           # call gnulpot
from time import strftime   # convert time to string
import os                   # wait on gnuplot

def main():
    # Check for correct arguments
    if (len(sys.argv) != 9):
        print "\nUsage: python acc-plotter.py [data.csv] [channels] " + \
        "[graph-freq] [title] [start] [end] [y-min] [y-max]\n"
        print "[data.csv] is the data CSV file which should be plotted\n"
        print "[channels] is a list of channels to plot.  Channel numbering" + \
        " starts at 1.  Example: '1,3,4'.  If set to '0', will plot all channels."
        print "The data channels will be plotted in the consecutive order found" + \
         "in the file starting with the second column, where the first column" + \
         "is the x axis.\n"
        print "[graph-freq] is the sample frequency in Hz of the plotted data."
        print "A value of 0 will use the full frequency of the given file."
        print "Any non-zero value must be lower than the frequency of data in" + \
        "the given file.\n"
        print "[title] is an alternative title for the plot which will be " + \
        "printed as '[title] Starting at DATE'.  A value of zero will use the " + \
        "default plot title, 'Vibration Data Starting at DATE'\n"
        print "[start] is the start time in HH:MM.  If '0', then starts of file's start.\n"
        print "[end] is the graph end time in HH:MM.  If '0', then ends at file's end."
        print "[y-min] is the minimum range for the y-axis. " + \
        "A value of 0 lets gnuplot decide.\n"
        print "[y-max] is the maximum rnage for the y-axis. " + \
        "A value of 0 lets gnuplot decide."
        sys.exit()
    
    # TODO: Include the option to manually set the output resolution
    
    fname_arg = sys.argv[1]
    chann_arg = sys.argv[2]
    freq_arg = int(sys.argv[3])
    title_arg = sys.argv[4]
    start_arg = sys.argv[5]
    end_arg = sys.argv[6]
    min_arg = float(sys.argv[7])
    max_arg = float(sys.argv[8])
    
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
    
    # Configure y-range variables
    if min_arg == 0:
        ymin = ""
    else:
        ymin = str(min_arg)
    if max_arg == 0:
        ymax = ""
    else:
        ymax = str(max_arg)
    
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
    # Calculate end time of file
    epoch_end = epoch_start + ((1/float(freq_file))*(float(rows_file)-1))/numchan_file
    
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
    plot = subprocess.Popen(['gnuplot', 'p'], stdin=subprocess.PIPE, shell=True)
    
    # Set the title
    if title_arg != "0":
        # Custom graph title
        plot.stdin.write("set title \"%s Starting at %s, %dHz\"\n" % 
                    (title_arg, strftime("%d %b %Y at %H:%M:%S", start_stct), freq_arg))
    else:
        # Default graph title
        plot.stdin.write("set title \"Accelerometer Data Starting at %s, %dHz\"\n" % 
                         strftime("%d %b %Y at %H:%M:%S", start_stct), freq_arg)
    
    plot.stdin.write("set datafile separator \",\"\n")
    # Is this necessary?
    # cd 'C:\Users\bjorr.CTLPC30\Desktop\AccTests\'
    plot.stdin.write("set terminal png font \"arial,55\" size 5000,5000\n")
    # set yrange [32730:32780]
    plot.stdin.write("set autoscale\n")
    plot.stdin.write("set yrange [%s:%s]\n" % (ymin, ymax))
    # x-axis label
    plot.stdin.write("set xlabel \"Time (HH:MM:SS)\"\n")
    # y-axis label
    plot.stdin.write("set ylabel \"Accelerometer Output with Gain (Volts)\"\n")
    # Get line names from the first row of data
    plot.stdin.write("set key autotitle columnhead\n")  
    # Interpret the x-axis data as a time unit
    plot.stdin.write("set xdata time\n")
    # Interpret it as seconds since Unix epoch
    plot.stdin.write("set timefmt \"%s\"\n")
    # x-axis tics should be in the format Hours:Minutes
    plot.stdin.write("set format x \"%H:%M:%S\"\n")
    
    # Handle channels
    # Get a list of channel numbers to plot
    if chann_arg == '0':
        numchan = numchan_file
        chan_dict = range(2,numchan+2)
    else:
        chan_dict = [int(x)+1 for x in chann_arg.split(',')]
        numchan = len(chan_dict)
    
    # Check that the given parameter is within bounds
    if len(chan_dict) > numchan_file:
        print "Error: You are asking for more channels than are present in the file.\n"
        sys.exit()
    
    plot.stdin.write("set output '%s_%dchan_%sto%s.png'\n" % 
                     (strftime("%d%b%Y", starttime),
                      numchan, 
                      strftime("%H:%M", start_stct),
                      strftime("%H:%M", end_stct)))
    # Set the range to be plotted
    plot.stdin.write("set xrange [%f-(5*3600):%f-(5*3600)]\n" % 
                     (plot_start, plot_end))
    
    colargs = [plot, numchan, every, epoch_start, chan_dict]
    
    print "Plotting..."
    
    plot.stdin.write("plot ")
    iterate_columns(fname_arg, colargs)
    plot.stdin.write("\n")
    plot.stdin.write("quit\n")
    os.waitpid(plot.pid, 0) # Wait for the process to quit

def iterate_columns(fname, colargs):
    
    plot = colargs[0]
    numchan = colargs[1]
    every = colargs[2]
    epoch_start = colargs[3]
    chan_dict = colargs[4]
    
    # Number of lines occupied by metadata which should be skipped
    md = 8
    
    # Names of thechannels that will be referenced
    chan_names = ["x-axis", "y-axis", "z-axis", "IN", "OUT", "TOP", "BOT"]
    
    # Handle the plot commands
    if numchan == 1:
        # There is only one line to plot
        plot.stdin.write("'%s' every %d::%d using \
                        ($1+%d-(5*3600)):((($%d-32768)/32768)*10) with \
                        linespoints title '%s'" 
                        % (fname, 
                           every, md, 
                           epoch_start, 
                           chan_dict[0], 
                           chan_names[chan_dict[0]-2]))
    else:
        
        # Create a dictionary without the first and last columns for middles
        chan_dict_l = list(chan_dict)
        del chan_dict_l[0]
        del chan_dict_l[-1]
        
        # First line
        plot.stdin.write("'%s' every %d::%d using \
                        ($1+%d-(5*3600)-32768):((($%d-32768)/32768)*10) \
                        with linespoints title '%s'," 
                         % (fname, 
                            every, md, 
                            epoch_start, 
                            chan_dict[0], 
                            chan_names[chan_dict[0]-2]))
        # Loop through the middle portion of the requested channels
        for i in chan_dict_l:
            print chan_dict_l
            plot.stdin.write("'%s' every %d::%d using \
                            ($1+%d-(5*3600)):((($%d-32768)/32768)*10) with \
                            linespoints title '%s'," 
                            % (fname, 
                               every, md, 
                               epoch_start, 
                               i, chan_names[i-2]))
        # Final line
        plot.stdin.write("'%s' every %d::%d using \
                        ($1+%d-(5*3600)):((($%d-32768)/32768)*10) with \
                        linespoints title '%s'" 
                        % (fname, 
                           every, md, 
                           epoch_start, 
                           chan_dict[numchan-1], 
                           chan_names[chan_dict[numchan-1]-2]))


# Run main()
if __name__ == "__main__":
    main()
