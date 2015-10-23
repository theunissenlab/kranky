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
#include <plplot/plplot.h>
#include <plplot/plplotP.h>
#include <math.h>
#include <ctype.h>
#include <readline/readline.h>
#include <readline/history.h>
#include <signal.h>
#include "ao_slave.h"


/* stimulus */

#define MAX_FILENAME_LENGTH 200
int stim_init(void);
void stim_output(char *buf, int len);
void stim_output2(char *buf, int len);



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
	ao_cmd.scan_begin_arg = 1e9/ao_freq;
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
