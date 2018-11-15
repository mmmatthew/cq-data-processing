# divide videos into short segments to be processed by ssiv
import datetime as dt
import os
from glob import glob

import pandas as pd

from helpers.multithread import run_processes


class VideoDecimator:
    def __init__(self, video_source_dir, video_output_dir, batch_command_dir, ffmpeg_path='c:/opt/ffmpeg', experiment_selection=None, experiment_metadata_file=None):
        self.source_dir = video_source_dir
        self.output_dir = video_output_dir
        self.batch_command_dir = batch_command_dir
        self.ffmpeg_path = ffmpeg_path
        self.created_command_list = []

        if experiment_metadata_file:
            self.experiments = pd.read_csv(
                experiment_metadata_file,
                sep=';',
                parse_dates=[1, 2],
                date_parser=parse_dates)
            if experiment_selection:
                self.experiments = self.experiments[self.experiments['id'].isin(experiment_selection)]
        else:
            self.experiments = None

    def create_commands(self, clip_duration=5, video_selector_regex='*.avi', force=False, delete_old=False):
        clip_command = '{ffmpeg_path} -y -ss {start_time} -i {input_file} -t {duration} -c:v libx264 -strict experimental {output_file} \n'
        clip_duration = pd.to_timedelta('0:0:{}'.format(clip_duration))
        # make dirs
        if not (make_or_empty_dir(self.batch_command_dir, empty=delete_old) or force):
            return 0

        # Loop through video files
        for video_file in glob(os.path.join(self.source_dir, video_selector_regex)):
            basename = os.path.basename(os.path.splitext(video_file)[0])
            location, camera, make, date, time, *_ = basename.split('_')
            video_start_time = getdatetime(date, time)

            # write batch file to write
            batch_file_path = os.path.join(self.batch_command_dir, 'decimate_{}.bat'.format(basename))
            # save file name to object
            self.created_command_list.append(batch_file_path)
            with open(batch_file_path, 'w+') as batch_file:
                batch_file.write('rem Automatically generated batch file\n')
                fromtime = pd.to_timedelta('00:00:00')
                maxtime = pd.to_timedelta('00:10:00')  # all videos are 10 minutes long

                while fromtime < maxtime:
                    # check if clip is within an experiment
                    if self.is_in_experiment(video_start_time + fromtime):
                        s = {
                            'ffmpeg_path': self.ffmpeg_path,
                            'input_file': video_file,
                            'start_time': str(fromtime)[-8:],
                            'duration': str(clip_duration)[-8:],
                            'output_file': os.path.join(
                                self.output_dir,
                                '{}_{}_{}.avi'.format(
                                    location,
                                    camera,
                                    (video_start_time+fromtime+clip_duration).strftime('%Y%m%d_%H%M%S')))
                        }
                        batch_file.write(clip_command.format(**s))
                        # increment time
                    fromtime += clip_duration

                # batch_file.write('pause')

    def is_in_experiment(self, datetime):
        # test if clip is part of experiment by checking start and end dates of experiments
        for index, row in self.experiments.iterrows():
            if row['start_datetime'] <= datetime <= row['end_datetime']:
                return True
        return False

    def run_commands(self, workers=4, onlyjustcreated=False, force=False, delete_old=False):
        # Runs all decimation commands

        # Check folder
        if not make_or_empty_dir(self.output_dir, empty=delete_old) and not force:
            return 0

        # First get commands
        if onlyjustcreated:
            commands = self.created_command_list
        else:
            commands = glob(os.path.join(self.batch_command_dir, '*.bat'))

        # then run all of them with workers
        run_processes(commands, worker_count=workers)

        pass


def getdatetime(date, time, dateformat='%y%m%d', timeformat='%H%M%S'):
    return dt.datetime.strptime(date+time, dateformat+timeformat)


def make_or_empty_dir(dirname, empty=False):
    # returns True if directory is empty
    if not os.path.exists(dirname):
        os.makedirs(dirname)
        return True
    elif empty:
        for the_file in os.listdir(dirname):
            file_path = os.path.join(dirname, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    # elif os.path.isdir(file_path): shutil.rmtree(file_path)
            except Exception as e:
                print(e)
        return True
    elif len(os.listdir(dirname)) == 0:
        return True
    else:
        return False


def parse_dates(x):
    return dt.datetime.strptime(x, '%d.%m.%y %H:%M')
