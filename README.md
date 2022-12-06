# encodelog
A script to analyze hardware performance and vmaf scores

usage:
python main.py [video_directory]... [ffmpeg_args]....

examples:
Encode and plot 1 video
python main.py C:\videos\video1.mp4

Encode and plot 1 video with ffmpeg args
python main.py C:\videos\video1.mp4 -c:v h264_nvenc

Encode and plot 2 videos
python main.py C:\videos\video1.mp4 C:\videos\video2.mp4

Encode and plot 2 videos with ffmpeg args
python main.py C:\videos\video1.mp4 C:\videos\videos2.mp4 -c:v h264_nvenc
