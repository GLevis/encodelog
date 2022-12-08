from threading import Thread
from subprocess import Popen, PIPE
from asyncio import subprocess
import hardware_logger, sys, os, logging, re, errno, shutil
import numpy as np
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
import random as random

logging.basicConfig(filename="error.log",
                    format='%(asctime)s %(message)s',
                    filemode='w', level=logging.DEBUG)
hardware_logger = hardware_logger.hardware_logger()
dir = os.path.dirname(os.path.realpath(__file__))

def process_args():
    videos = []
    ffmpeg_args = []
    arg_num = 0
    
    for arg in sys.argv:
        if arg_num != 0:
            if ".y4m" in arg:
                videos.append(arg)
            else:
                break
        arg_num +=  1
    
    if len(videos) == 0:
        sys.exit(1)

    for pos in range(arg_num, len(sys.argv)):
        ffmpeg_args.append(sys.argv[pos])
    
    return videos, ffmpeg_args

def encode(videos, args):
    inputs = []
    outputs = []
    count = 0

    for video in videos:
        in_filename = video.split('\\')
        in_filename.reverse()
        in_filename = in_filename[0]
        dir_name = in_filename.split('.')[0]
        filetype = in_filename.split('.')[1]
        out_filename = dir_name + "-out." + "mp4"
        full_dir = dir + "\\" + str(count) + "-out"
        full_dir_out_file = full_dir + "\\" + out_filename
        try:
            os.mkdir(full_dir) 
        except OSError as exc:
            raise

        inputs = inputs + ["-i", video]
        outputs = outputs + args + ["-map", str(count), "-f", "mp4", full_dir_out_file]
        count = count + 1
    
    p = Popen(["ffmpeg", "-readrate", "1"] + inputs + args + outputs, stdout=subprocess.PIPE)
    p.communicate()

    hardware_logger.terminate()

def calculate_vmaf(videos):
    count = 0
    for video in videos:
        in_filename = video.split('\\')
        in_filename.reverse()
        in_filename = in_filename[0]
        dir_name = in_filename.split('.')[0]
        out_filename = dir_name + "-out." + "mp4"
        full_dir = dir + "\\" + str(count) + "-out"

        p = Popen(
        [
            "ffmpeg", 
            "-i", 
            video, 
            "-i", 
            full_dir + "\\" + out_filename, 
            "-lavfi", 
            "libvmaf=log_path=output.xml", 
            "-f", 
            "null", 
            "-"
        ], 
        stdout=subprocess.PIPE,
        )

        p.communicate()

        try:
            shutil.move("output.xml", full_dir + "\\" + "output.xml")
        except shutil.Error:        
            raise
        
        count += 1

def get_video_frame_rate(filename):
    result = Popen(
    [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        "-show_entries",
        "stream=r_frame_rate",
        filename,
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    )

    out,err = result.communicate()
    out = out.decode('utf-8').split('/')
    
    fps = float(out[0])/float(out[1])
    return fps

def parseXML(videos):
    vmaf_scores = []
    count = 0
    for video in videos:
        in_filename = video.split('\\')
        in_filename.reverse()
        in_filename = in_filename[0]
        dir_name = in_filename.split('.')[0]
        out_filename = dir_name + "-out." + in_filename.split('.')[1]
        full_dir = dir + "\\" + str(count) + "-out"
        frames_vmaf = dict()
        fps = get_video_frame_rate(sys.argv[1])

        try:
            tree = ET.parse(full_dir + '\\' + 'output.xml')
        except ET.ParseError:
            
            raise  

        root = tree.getroot()

        for frame in root.find('frames'):
            frame_num = frame.get('frameNum')
            vmaf_score = frame.get('vmaf')
            frames_vmaf[int(frame_num) / fps] = float(vmaf_score)

        vmaf_scores.append(frames_vmaf)

        count += 1

    return vmaf_scores

def plot(videos):
    vmaf_scores = parseXML(videos)
    cpu_list = sorted(hardware_logger.get_cpu_log().items())
    cpu_time, cpu_usage = zip(*cpu_list)
    gpu_list = sorted(hardware_logger.get_gpu_log().items())
    _, gpu_usage = zip(*gpu_list)
    ram_list = sorted(hardware_logger.get_ram_log().items())
    _, ram_usage = zip(*ram_list)
    time_container = []
    time_data = []

    for time in cpu_time:
        time_container.append(time.total_seconds())
        time_data = np.array(time_container)
    
    fig, ax = plt.subplots()
    vmafAx = ax.twinx()

    ax.set_ylim([0, 100])
    vmafAx.set_ylim([0, 100])
    plt.yticks(np.arange(0, 100, 5))

    plt.plot(time_data, cpu_usage, color = "red")
    plt.plot(time_data, gpu_usage, color = "green")
    plt.plot(time_data, ram_usage, color = "blue")
    
    counter = 0
    labels = []

    for scores in vmaf_scores:
        r = random.random()
        g = random.random()
        b = random.random()
        color = (r, g, b)
        scores = list(scores.items())
        label = "VMAF" + str(counter)
        labels.append(label)
        x,  y = zip(*scores)
        vplot, = vmafAx.plot(x, y, color = color, label = label) 
        counter += 1

    plt.gcf().autofmt_xdate()
    plt.xlabel('Time (Seconds)')
    plt.ylabel('Usage (%)')
    vmafAx.set_ylabel('VMAF')
    vmafAx.yaxis.label.set_color(color="black")
    plt.legend(["CPU", "GPU",  "RAM"] + labels, loc = "lower right")

    plt.savefig('usage.png')

    plt.show()

if __name__ == "__main__":
    videos, ffmpeg_args = process_args()
    log_thread = Thread(target = hardware_logger.run, daemon=True)
    log_thread.start()
    encode(videos, ffmpeg_args)
    calculate_vmaf(videos)
    plot(videos)
    sys.exit(1)
    
