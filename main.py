# This script prepares the data base for the qualitative data calibration study. Some important operations are:
# - censoring of incorrect values
# - processing videos to extract flood trend information

# ATTENTION: FFMPEG must be downloaded to process footage >> https://www.ffmpeg.org/

import os
from glob import glob

from helpers.video_decimator import VideoDecimator
from sofi_extraction.engine import CCTVFloodExtraction


def main(operations):
    # set directories
    data_dir = 'Q:/Messdaten/floodVisionData/core_2018_cq/1_data'

    # experiment info
    experiment_metadata_file = '../experiment_list.csv'
    experiment_selection = list(range(20, 25))
    relevant_conventional_sensors = ['s3_h_us_maxbotix', 'p2_h_p_nivus', 'p2_q_us_nivus', 'c3_h_us_nivus', 'c3_v_us_nivus', 's5_h_us_maxbotix_2', 's6_h_us_maxbotix']

    # Copy relevant sensor data
    if 'sensor' in operations:
        print('1 - Copying sensor data')

    # Decimate videos for SSIV processing
    if 'ssiv' in operations:
        print('2 - Decimating videos')
        video_dir_in = os.path.join(data_dir, '1_raw', 'videos', 'c3_cam3')
        video_dir_out = os.path.join(data_dir, '3_intermediate', 'for_ssiv', 'videos')
        batch_command_dir = os.path.join(data_dir, '3_intermediate', 'for_ssiv', 'commands')
        decimator = VideoDecimator(
            video_dir_in, video_dir_out, batch_command_dir,
            ffmpeg_path='C:/opt/ffmpeg.exe',
            experiment_metadata_file=experiment_metadata_file,
            experiment_selection=experiment_selection
        )
        # create commands
        decimator.create_commands(delete_old=False, force=False)
        # run commands
        decimator.run_commands(force=False, workers=4, delete_old=False)

    if 'sofi' in operations:
        # Extract frames from videos, segment frames, and extract SOFI signal
        print('3 - Segmenting videos and extracting SOFI')
        video_dir_in1 = os.path.join(data_dir, '1_raw', 'videos', 's3_cam1', '*.avi')
        video_dir_in2 = os.path.join(data_dir, '1_raw', 'videos', 's6_cam5', '*.avi')
        model_dir = "Q:/Messdaten/floodVisionData/core_2018_cq/1_data/2_processing/dcnn_water_segmentation/augmented"
        pred_dir = os.path.join(data_dir, '3_intermediate', 'for_sofi', 'prediction')
        signal_dir = os.path.join(data_dir, '3_intermediate', 'for_sofi', 'prediction')

        # Find video file names
        for loc, name in zip([video_dir_in1, video_dir_in2], ['s3_cam1', 's6_cam5']):
            video_frame_out_dir = os.path.join(data_dir, '3_intermediate', 'for_sofi', 'frames')
            cfe = None
            for file in glob(loc):
                cfe = CCTVFloodExtraction(video_name=name, video_file=file, model_dir=model_dir, signal_dir=signal_dir, pred_dir=pred_dir, frame_dir=video_frame_out_dir)
                cfe.video2frame2(step=5, force=False)
            cfe.run(['extract_trend'], max_frames=None, vid_batch=10)

if __name__ == '__main__':
    main(['sofi'])

