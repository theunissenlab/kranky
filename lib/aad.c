#include <stdio.h>	/* for printf() */
#include <comedilib.h>
#include <math.h>
#include <time.h>
#include <stdint.h>
#include <stdlib.h> 


#define BILLION 1000000000L

int subdev_ai = 0;		/* change this to your input subdevice */
unsigned int subdev_dio = 2;
int chan = 0;		/* change this to your channel */
int range = 0;		/* more on this later */
int aref = AREF_GROUND;	/* more on this later */



int main(int argc,char *argv[])
{
	comedi_t *itai, *itdio;
	int chan = 0;
	lsampl_t data;
	long datatemp;
	int retval;
	unsigned int bitint;
	unsigned int write_mask = 15;
	unsigned int base_channel = 0;
	long aadfactor = 4369;
	long aadoffset=0;


	struct timespec start, end, startl;
	// long aadfactor=2184;
	// long aadoffset = 32768;
	itai = comedi_open("/dev/comedi0_subd0");
	if(itai == NULL)
	{
		comedi_perror("comedi_open");
		return -1;
	}
	itdio = comedi_open("/dev/comedi0_subd2");
	if(itdio == NULL)
	{
		comedi_perror("comedi_open");
		return -1;
	}
	long count = 0;
	clock_gettime(CLOCK_MONOTONIC, &startl);
	uint64_t maxdur = 0; 
	uint64_t dur = 0; 
	float durl;
	while ( 1 ){
		clock_gettime(CLOCK_MONOTONIC, &start);
		count +=1;
		retval = comedi_data_read(itai, subdev_ai, chan, range, aref, &data);
		if(retval < 0)
		{
			comedi_perror("comedi_data_read");
			return -1;
		}
		data = 1000;
		datatemp = lroundf(data-aadoffset)/(float)aadfactor;
		bitint = (unsigned int) lroundf((data-aadoffset)/(float)aadfactor);
		// retval = comedi_dio_bitfield2(itdio, subdev_dio, write_mask, &bitint, base_channel);	
		// if(retval < 0)
		// {
		// 	comedi_perror("comedi_dio_bitfield2");
		// 	return -1;
		// }
		clock_gettime(CLOCK_MONOTONIC, &end);
		dur = (end.tv_sec - start.tv_sec)*BILLION + end.tv_nsec - start.tv_nsec;
		if (dur > maxdur){maxdur=dur;};
		if (count>=1e6)
		{
		durl = (float)(end.tv_sec - startl.tv_sec) + (float)(end.tv_nsec - startl.tv_nsec) / BILLION; 
		printf("aveduration: %f (us)  max duration %d (us) \n", durl, maxdur/1000);
		count = 0;
		maxdur=0;
		clock_gettime(CLOCK_MONOTONIC, &startl);
		}
		// printf("%d %d, %d\n", data, datatemp, bitint);
    }

	return 0;
}

