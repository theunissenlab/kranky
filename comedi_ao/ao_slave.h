
#ifndef _SCOPE_H_
#define _SCOPE_H_

#include <stdio.h>
#include <glib.h>

#ifdef NI625x
  /* For the NI625x M-series board (length in bytes) */
  #define AO_SUBD 1
  #define AO_FIFO_LEN 16382
  #define DIO_SUBD 7
  #define MAX_CHANS 32
  /* Use +- 5V range on M-series board because of impedance 
     load clipping issues. */
  #define AO_RANGE_INDEX 1
#else
  /* For the NI6052E board */
  #define AO_SUBD 1
  #define AO_FIFO_LEN 2048
  #define DIO_SUBD 7
  #define MAX_CHANS 16
  #define AO_RANGE_INDEX 0
#endif

struct _scope_chan {
	int show;
	double offset;
	char name[100];
        int index;
        int triggered;
        double trig_level;
        double trig_level2;
        int trig_type;
};
typedef struct _scope_chan scope_chan;

struct _stim_struct {
	char *name;
	char *basename;
	char *data;
	int n_samples;
	int index;
	int flags;
};
typedef struct _stim_struct stim_struct;

struct _display_struct {
        stim_struct *stim;
        scope_chan *chan;
        int index;
        int is_displayed;
};

typedef struct _display_struct display_struct;

/* global variables */

extern int krank_selected_channel;
extern int krank_selected_display;
extern int krank_selected_stimulus;
/* Global hash of raster display configurations. */
extern GHashTable *krank_displays;

extern double ai_freq;
extern double ao_freq;
extern double scope_freq;
extern double raster_freq;
extern int n_raster_stims;
extern int n_hist_stims;
extern int debug;
extern double ramp_time;
extern int n_trials;
extern double binsize;
extern int stim_order;
extern int output_index;
extern int reset_on_start;
extern int n_ai_chan;
extern int force_overwrite;
extern int output;
extern double attenuation;
extern double attenuation2;

/* scope.c */

extern int streaming_on;
extern int ai_n_chan;
extern comedi_range *ai_range;
extern lsampl_t ai_maxdata;
extern scope_chan scope_chans[];

void stop(char *why);
void plotupdate(void);
void dump_comments(FILE *out);
int check_file_exists(char *path);
extern int n_comments;
void scope_log(char *str);
void scope_log_args(int argc, char *argv[]);
int tokenize(char **argv, char *s);

/* vars.c */
void vars_dump(FILE *out);

/* stim.c */

extern int n_stims;
extern stim_struct *stims[];

void stim_plotdata_all(void);
void stim_stop(char *why);
void stimdata_reset(void);
void print_date_rfc822(char *s, struct timeval *tv);

/* display.c */
display_struct* display_new(void);
void display_free(display_struct *disp);
void display_free_adaptor(gpointer value);
void display_set_stim(display_struct *disp, stim_struct *stim);
void display_set_chan(display_struct *disp, scope_chan *chan);
void display_reset_stim(display_struct *disp);
void display_reset_stim_adaptor(gpointer key, gpointer value, gpointer user_data);
display_struct *display_lookup(int idx);
display_struct *display_select(int idx);
int display_init(display_struct *disp);
int display_show(display_struct *disp);
display_struct *display_create(scope_chan *chan, stim_struct *stim);
void display_destroy(display_struct *disp);
display_struct *display_clone(display_struct *disp_ref);
int display_clone_init(display_struct *disp, display_struct *disp_ref);
int display_clone_show(display_struct *disp, display_struct *disp_ref);
int display_is_valid(display_struct *disp);
int displays_get_last_index(void);


#endif

