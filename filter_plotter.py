#!/usr/bin/env python
import os
import sys
import gc
from math import *
import time
import random


# Get position of read based on chr with sam or bam file
def get_read_pos_with_sam_bam_file(sam_bam_file, chr_len_db, bin_size, out_list):
	long_bin_size = bin_size.upper()
	long_bin_size = long_bin_size.replace('K', '000')
	long_bin_size = long_bin_size.replace('M', '000000')
	long_bin_size = long_bin_size.replace('G', '000000000')
	long_bin_size = int(long_bin_size)
	
	random.seed()
	read_on_chr = {}
	if sam_bam_file[-3:] == "bam":
		f_in = os.popen("samtools view "+sam_bam_file, 'r')
	else:
		f_in = open(sam_bam_file, 'r')
	
	with open(bin_size.upper()+"_"+out_list, 'w') as fout:
		for line in f_in:
			if line.strip() == '' or line[0] == '@':
				continue
			if 'WGS' in line:
				fout.write(line.strip().split()[0]+"\n")
				continue
			data = line.strip().split()
			read_id = data[0]
			if data[2] == '*' or data[6] == '*':
				continue
			chr1 = data[2].replace('_pilon', '')
			read_pos1 = int(data[3])
			if data[6] != '=':
				chr2 = data[6].replace('_pilon', '')
			else:
				chr2 = chr1
			read_pos2 = int(data[7])
			if chr1 == chr2 and chr1 in chr_len_db:
				bin_count_of_chr = int(round((chr_len_db[chr1]*1.0/long_bin_size+0.5)))
				pos1_index = int(read_pos1/long_bin_size)
				pos2_index = int(read_pos2/long_bin_size)
				if (pos1_index+pos2_index) in range(bin_count_of_chr-11, bin_count_of_chr+10):
					#border = 1.0/(sqrt(2*pi)*3)*exp(-(abs(bin_count_of_chr-(pos1_index+pos2_index)-1))**2/18.0)*8
					#print(border)
					border = abs(bin_count_of_chr-1-(pos1_index+pos2_index))
					if abs(pos1_index-pos2_index) < 4:
						border = 0
					elif abs(pos1_index-pos2_index) < 7:
						border = 1
					else:
						border = 4.0-int((border+1)/2)
					if random.random() > 1.0/(2**border):
						fout.write(read_id+'\n')
						if read_id in read_on_chr:
							read_on_chr.pop(read_id)
						continue
			read_on_chr[read_id] = [chr1, read_pos1, chr2, read_pos2]
	f_in.close()
	return read_on_chr


# Get chromosome length
def get_chr_len(chr_list):
	chr_len_db = {}
	chr_order = []
	with open(chr_list, 'r') as f_in:
		for line in f_in:
			if line.strip() == '':
				continue
			data = line.strip().split()
			chr_order.append(data[0])
			chr_len_db[data[0]] = int(data[1])
	return chr_len_db, chr_order


# Calc read counts on each bin
def calc_read_count_per_bin(chr_len_db, chr_order, read_on_chr, bin_size):
	long_bin_size = bin_size.upper()
	long_bin_size = long_bin_size.replace('K', '000')
	long_bin_size = long_bin_size.replace('M', '000000')
	long_bin_size = long_bin_size.replace('G', '000000000')
	long_bin_size = int(long_bin_size)
	
	read_count_per_chr = {}
	read_count_whole_genome = {}
	
	bin_offset = [0 for i in range(0, len(chr_order)+1)]
	bin_count = [0 for i in range(0, len(chr_order)+1)]
	total_bin_count = 0
	
	for chrn in chr_len_db:
		bin_count_of_chr = int(round((chr_len_db[chrn]*1.0/long_bin_size+0.5)))
		total_bin_count += bin_count_of_chr
		bin_count[chr_order.index(chrn)+1] = bin_count_of_chr
		read_count_per_chr[chrn] = [[0 for i in range(0, bin_count_of_chr)] for j in range(0, bin_count_of_chr)]
	
	for i in range(0, len(bin_count)):
		for j in range(0, i+1):
			bin_offset[i] += bin_count[j]
	
	read_count_whole_genome = [[0 for i in range(0, total_bin_count)] for j in range(0, total_bin_count)]
	
	for read in read_on_chr:
		chr1, pos1, chr2, pos2 = read_on_chr[read]
		if chr1 not in chr_len_db or chr2 not in chr_len_db:
			continue
		pos1_index = int(pos1/long_bin_size)
		pos2_index = int(pos2/long_bin_size)
		if chr1 == chr2 and chr1 in read_count_per_chr:
			read_count_per_chr[chr1][pos1_index][pos2_index] += 1
			read_count_per_chr[chr1][pos2_index][pos1_index] += 1

		chr1_index = chr_order.index(chr1)
		chr2_index = chr_order.index(chr2)

		whole_pos1 = bin_offset[chr1_index] + pos1_index
		whole_pos2 = bin_offset[chr2_index] + pos2_index
		read_count_whole_genome[whole_pos1][whole_pos2] += 1
		read_count_whole_genome[whole_pos2][whole_pos1] += 1
	
	for chrn in read_count_per_chr:
		for i in range(0, len(read_count_per_chr[chrn])):
			for j in range(0, len(read_count_per_chr[chrn][i])):
				if read_count_per_chr[chrn][i][j] != 0:
					read_count_per_chr[chrn][i][j] = log(read_count_per_chr[chrn][i][j], 2)
				else:
					read_count_per_chr[chrn][i][j] = -float('inf')
	
	for i in range(0, len(read_count_whole_genome)):
		for j in range(0, len(read_count_whole_genome[i])):
			if read_count_whole_genome[i][j] != 0:
				read_count_whole_genome[i][j] = log(read_count_whole_genome[i][j], 2)
			else:
				read_count_whole_genome[i][j] = -float('inf')


	return read_count_per_chr, read_count_whole_genome


# Draw heatmap of allhic result with matplotlib
def draw_heatmap(data, chrn, bin_size, ext):
	
	import matplotlib as mpl
	mpl.use('Agg')
	import matplotlib.pyplot as plt

	short_bin_size = bin_size.upper()
	if bin_size[-9:] == '000000000':
		short_bin_size = bin_size[:-9]+'G'
	elif bin_size[-6:] == '000000':
		short_bin_size = bin_size[:-6]+'M'
	elif bin_size[-3:] == '000':
		short_bin_size = bin_size[:-3]+'K'

	ax = plt.gca()
	
	if chrn != 'all':
		file_prefix = short_bin_size + "_" + chrn
	else:
		file_prefix = short_bin_size + '_Whole_genome'
	
	print(time.strftime('[%H:%M:%S]',time.localtime(time.time()))+' Draw '+file_prefix)
	with open('log.csv', 'w') as flog:
		for i in range(0, len(data)):
			for j in range(0, len(data[i])):
				flog.write("%s,"%(str(data[i][j])))
			flog.write('\n')
	# mpl.cm.YlOrRd
	cmap = plt.get_cmap('YlOrRd')
	cmap.set_over('black')
	if chrn != 'all':
		hmap = ax.imshow(data, interpolation='nearest', origin='lower', cmap=cmap, aspect='auto')
	else:
		hmap = ax.imshow(data, interpolation='nearest', cmap=cmap, aspect='auto')
	
	plt.colorbar(mappable=hmap,cax=None, ax=None, shrink=0.5)
	plt.tick_params(labelsize=6)
	for ticks in ax.get_xticklabels():
		ticks.set_rotation(90)
	for ticks in ax.get_yticklabels():
		ticks.set_rotation(0)
	
	if chrn != 'all':
		title = chrn+'_'+short_bin_size
	else:
		title = 'Whole_genome_'+short_bin_size
	
	plt.xlabel("Bins ("+short_bin_size.lower()+"b per bin)", fontsize=8)
	if chrn == 'all':
		plt.xticks([])
		plt.yticks([])
		plt.title(title, y=1.01, fontsize=12)
	else:
		plt.title(title, y=1.1, fontsize=12)

	plt.savefig(file_prefix+'.'+ext, filetype=ext, bbox_inches='tight', dpi=200)
	plt.close('all')


if __name__ == "__main__":
	if len(sys.argv) < 6:
		print("Notice: This script is using for drawing heatmap of the all-hic reasult")
		print("Usage: python "+sys.argv[0]+" <sam/bam file> <chr_list> <bin_size> <pic_ext> <out_filter_list>")
		print("\t<sam/bam_file> is the sam or bam file filtered by allhic")
		print("\t<chr_list> is the file contain ordered chrs")
		print("\t<bin_size> is the bin size of heatmap, it can be a list splited by comma")
		print("\t<pic_ext> is the file type of picture")
		print("\t<out_filter_list> is the list of reads to be filtered")

	else:
		sam_bam_file = sys.argv[1]
		chr_list = sys.argv[2]
		bin_list = sys.argv[3]
		ext = sys.argv[4]
		out_list = sys.argv[5]

		print(time.strftime('[%H:%M:%S]',time.localtime(time.time()))+" Step 1: Get chromosome length")
		chr_len_db, chr_order = get_chr_len(chr_list)
		
		print(time.strftime('[%H:%M:%S]',time.localtime(time.time()))+" Step 2: Calculating and Drawing heatmap")

		bin_size_list = bin_list.split(',')
		for bin_size in bin_size_list:
			print(time.strftime('[%H:%M:%S]',time.localtime(time.time()))+" Get read position based on chromosome")
			read_on_chr = get_read_pos_with_sam_bam_file(sam_bam_file, chr_len_db, bin_size, out_list)
			print(time.strftime('[%H:%M:%S]',time.localtime(time.time()))+" Calculating")
			read_count_per_chr, read_count_whole_genome = calc_read_count_per_bin(chr_len_db, chr_order, read_on_chr, bin_size)
			
			print(time.strftime('[%H:%M:%S]',time.localtime(time.time()))+" Drawing heatmap")
		
			print(time.strftime('[%H:%M:%S]',time.localtime(time.time()))+" Drawing with bin size "+str(bin_size))
			for chrn in read_count_per_chr:
				draw_heatmap(read_count_per_chr[chrn], chrn, bin_size, ext)
			
			draw_heatmap(read_count_whole_genome, 'all', bin_size, ext)
			del read_count_per_chr, read_count_whole_genome
			gc.collect()
		
		del read_on_chr
		gc.collect()
		print(time.strftime('[%H:%M:%S]',time.localtime(time.time()))+" Success")
