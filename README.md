# ALLHiC_Evaluate_Data_Generators
## 1. Correct reads generated by sim3C

Although we can use sim3C to simulate hic reads with reference genome, the fastq we got may contain WGS reads that we do not need, and it will produce too high signal strength that do not appear in real experiment, so we wrote some scripts to filter the reads that we do not need and reduce the signal of hic to approach to the reality.

### Step 1. Use sim3C to generate hic reads

You can get [sim3C](https://github.com/cerebis/sim3C) here, and then run the command below to get hic reads.

```bash
sim3C.py -m hic -e MboI -n number_of_reads -l read_length --dist uniform ref_fasta out.fq
```

### Step 2. Split hic reads from single file two pair-end files

You can use the command below to split the fastq file generated in step1 into two fastq files with suffix "\_R1.fastq" and "\_R2.fastq"

```bash
python split_sim3C_fastq.py input_fastq output_fastq_prefix
```

### Step 3. Generate read list for filtering

You can use the command below to generate the read list for filtering

```bash
python generate_sim3C_filter_list.py input_bamfile/input_samfile chr_list pic_ext out_filter_list
```

**input_bamfile/input_samfile**  you can use bam or sam file as input, the sam file is generated by mapping hic reads to reference with bwa,  and you can use samtools to convert it to bam file.

**chr_list** is a chr list that contain two columns, the first column is the name of chromosome, and the second column is the length of chromosome.

**pic_ext** is the file type of the picture of the hic signal after filter.

**out_filter_list** is the file will contain the name of reads for filter.

### Step 4. Filter reads

You can use the command below to filter the fastq files.

```bash
python filter_fastq.py in_fastq in_list out_fastq
```

**in_fastq** is the file generated in step2.

**in_list** is the list file that generated in step3.

**out_fastq** is the fastq file after filter.



## 2. Simulate  SNPs and InDels

You can use the command below to generate SNPs and InDels with reference genome.

```bash
python sim_snp_indel.py -r reference -o out_fasta
```

default ratios of SNPs, Insertions and Deletions are 0.01, 0.01, 0.01

default value of the max length of insertions and deletions are 10, 10



## 3. Simulate collapse

### Step 1. Generate contigs with N50

You can use the command below to generate contigs with reference chromosome.

```bash
python sim_contigs.py -i reference -o out_fasta
```

default length range of contigs is (15k, 5m)

default N50 is 500k

### Step 2. Simulate collapse

You can use the command below to generate collapse between two chromosomes.

```bash
python sim_collapse.py -a contig_file1 -b contig_file2 -p A,B -o out_fasta -s blast_file -c 10
```

**-a and -b** are the contig file of chromosomes

**-p** is the prefix of two chromosomes

**-o** is the output file contain reads with collapse between chromosomes a and b

**-s** is the blast file with format 6, with contig_file1 as query and contig_file2 as database

**-c** is the percentage of collapse region size, default is 10



## 4. Simulate chimeric

You can use the command below to generate chimeric between two genome.

```bash
python sim_chimeric.py -a a.fasta -b b.fasta -o chimeric.fasta -c 5 -t 12
```

**-a and -b** are the genome file with the same count of chromosomes.

**-o** is the fasta file with chimeric

**-c** is the percentage of chimeric, default is 5

**-t** is the threads

