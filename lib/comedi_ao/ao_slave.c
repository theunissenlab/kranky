#include <stdio.h>
#include <comedilib.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <ctype.h>
#include <readline/readline.h>
#include <readline/history.h>
#include <signal.h>
#include "ao_slave.h"

/* misc */

int streaming_on = 0;
int notify_done = 0;

/* comedi stuff */

char *comedi_filename = "/dev/comedi0";
comedi_t *dev;
unsigned int trig_rt = 0;

void comedi_init(void);
void start(void);
int comedi_internal_trigger(comedi_t *dev, unsigned int subd, unsigned int trignum);

double scope_max = 10.0;
double scope_min = -10.0;

/* ao stuff */

int go;
int debug = 3;
unsigned int ao_subd;
unsigned int ao_range_index;
unsigned int ao_chanlist[1];
char *ao_buf = NULL;
unsigned int ao_buf_len;
unsigned int ao_buf_offset;
comedi_range *ao_range;
lsampl_t ao_maxdata;
comedi_cmd ao_cmd;

void ao_init(void);
void ao_stop(void);
void output_some(void);

/* stimulus */

// #define MAX_FILENAME_LENGTH 200
// int stim_init(void);
// void stim_output(char *buf, int len);
void stim_output2(char *buf, int len);




int main(int argc, char *argv[])
{

	
	// signal(SIGINT,sig_intr);
	comedi_init();
	main_loop(dev);
	exit(0);
}


void main_loop(comedi_t *dev)
{
    fd_set rdset;
	fd_set wrset;
	// struct timeval timeout;
	go = 1;
	// ai_buf_offset = 0;
	ao_buf_offset = 0;
	while(go){
		// FD_ZERO(&rdset);
		FD_ZERO(&wrset);
		// FD_SET(0,&rdset);
		if(streaming_on){
			// FD_SET(comedi_fileno(dev),&rdset);
			FD_SET(comedi_fileno(dev),&wrset);
		}
		// timeout.tv_sec = 0;
		// timeout.tv_usec = 50000;
		// ret = select(comedi_fileno(dev) + 1, &rdset, &wrset, NULL, &timeout);
		// if(debug>=3)printf("select returned %d\n",ret);
		
		if(FD_ISSET(comedi_fileno(dev), &wrset)){
			if(debug>=3)printf("select: ao ready\n");
			output_some();
		}
		/* Make each plplot stream respond to window events? */
		// plgstrm(&cur_strm);
		// plsstrm(0);
		// plP_esc(PLESC_EH,NULL);
		// g_hash_table_foreach(krank_displays, set_plesc, NULL);
		// plsstrm(cur_strm);
	}
}


void comedi_init(void)
{
	int ret;

	dev = comedi_open(comedi_filename);
	if(!dev){
		comedi_perror(comedi_filename);
		exit(1);
	}

	/* Set digital channel 6 to be an output. (for triggering?) */ 
	ret = comedi_dio_config(dev,DIO_SUBD,6,COMEDI_OUTPUT);
	if(ret<0){
		comedi_perror("comedi_dio_config");
	}

	comedi_set_global_oor_behavior(COMEDI_OOR_NUMBER);

	/* This sets the buffer size for analog output */
	comedi_set_buffer_size(dev, AO_SUBD, 65536*4);
}


void start(void)
{
	int ret;

	if(streaming_on){
		printf("Unable to comply: already running.  Run 'stop' first.\n");
		return;
	}

	// if(reset_on_start)stimdata_reset();
	// ai_buf_offset = 0;
	ao_buf_offset = 0;
	/* Redefined here to account ofr changed user settings; 
	   same as in main */
	ret = stim_init();
	if(ret<0){
		return;
	}
	ao_init();

	streaming_on = 1;

	ret = comedi_internal_trigger(dev, ao_subd, 0);
	if(ret<0){
		comedi_perror("comedi_internal_trigger");
	}
}

void ao_stop(void)
{
	comedi_cancel(dev, ao_subd);
}

void stop(char *why)
{
	streaming_on = 0;
	ao_stop();
	// if(notify_done){
	// 	printf("\a");
	// 	fflush(stdout);
	// }
	/* free(ai_buf);
	   free(ao_buf);
	   ai_buf = NULL;
	   ao_buf = NULL;
	*/
}

void ao_init(void)
{
	int i;
	int err;

	ao_buf_len = AO_FIFO_LEN;
	ao_buf = realloc(ao_buf,ao_buf_len);

	ao_subd = 1;
	ao_maxdata = comedi_get_maxdata(dev,ao_subd,0);
	ao_range_index = AO_RANGE_INDEX;
	ao_range = comedi_get_range(dev,ao_subd,0,ao_range_index);
	if (debug > 0) printf("ao_range (volts): %g : %g.\n", ao_range->min, ao_range->max);

	memset(&ao_cmd, 0, sizeof(ao_cmd));

	ao_cmd.subdev = ao_subd;
	ao_cmd.flags = trig_rt;
	ao_cmd.start_src = TRIG_INT;
	ao_cmd.start_arg = 0;
	ao_cmd.scan_begin_src = TRIG_TIMER;
	// ao_cmd.scan_begin_arg = 1e9/ao_freq;
	ao_cmd.convert_src = TRIG_NOW;
	ao_cmd.convert_arg = 0;
	ao_cmd.scan_end_src = TRIG_COUNT;
	ao_cmd.scan_end_arg = 1;
	ao_cmd.stop_src = TRIG_NONE;
	ao_cmd.stop_arg = 0;

	ao_cmd.chanlist = ao_chanlist;
	ao_cmd.chanlist_len = 1;

	ao_chanlist[0] = CR_PACK(0, ao_range_index, AREF_GROUND);

	err = comedi_command_test(dev, &ao_cmd);
	if(err != 0){
		printf("bad ao cmd\n");
	}

	if(debug>=1){
		fprintf(stderr,"ao: test returned %d (%s)\n",err,
			cmdtest_messages[err]);
		dump_cmd(stderr,&ao_cmd);
	}

	ao_freq = 1e9/ao_cmd.scan_begin_arg;
	printf("actual AO rate = %g\n",ao_freq);

	err = comedi_command(dev, &ao_cmd);
	if(err != 0){
		comedi_perror("ao comedi_command");
	}

	stim_output2(ao_buf, ao_buf_len/2);

	for(i=0;i<5;i++){
		output_some();
	}
}


void output_some(void)
{
	int ret;

	ret = write(comedi_fileno(dev), ao_buf + ao_buf_offset, ao_buf_len - ao_buf_offset);
	if(debug>=3)printf("output_some: write returned %d\n",ret);
	if(ret<0){
	        fprintf(stderr, "write error: buffer offset: %d, buffer len: %d.\n", ao_buf_offset, ao_buf_len);
		perror("write");
		stop("error");
		return;
	}else if(ret == 0){
		return;
	}else{
		ao_buf_offset += ret;
	}

	/* Refill the stimulus buffer if the end was reached */
	if(ao_buf_offset >= ao_buf_len){
		ao_buf_offset = 0;
		stim_output2(ao_buf, ao_buf_len/2);
	}
}
