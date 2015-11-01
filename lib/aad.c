#include <stdio.h>	/* for printf() */
#include <comedilib.h>
#include <math.h>

int subdev_ai = 0;		/* change this to your input subdevice */
unsigned int subdev_dio = 2;
int chan = 0;		/* change this to your channel */
int range = 0;		/* more on this later */
int aref = AREF_GROUND;	/* more on this later */
int main(int argc,char *argv[])
{
	comedi_t *it;
	int chan = 0;
	lsampl_t data;
	int retval;
	unsigned int bitint;
	unsigned int write_mask = 15;
	unsigned int base_channel = 0;
	long aadfactor = 4369;
	it = comedi_open("/dev/comedi0");
	if(it == NULL)
	{
		comedi_perror("comedi_open");
		return -1;
	}
	while ( 1 ){
		retval = comedi_data_read(it, subdev_ai, chan, range, aref, &data);
		if(retval < 0)
		{
			comedi_perror("comedi_data_read");
			return -1;
		}
		bitint = (unsigned int) lroundf(data/(float)aadfactor);
		retval = comedi_dio_bitfield2(it, subdev_dio, write_mask, &bitint, base_channel);	
		// printf("%d\n", bitint);
    }

	return 0;
}

