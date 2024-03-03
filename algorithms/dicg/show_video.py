# Helper function to show videos in-line
from IPython.display import HTML
from base64 import b64encode
import os
from envs.utils import record_gym_video

def show_video(video_file, video_width = 400):
    compressed_path = video_file.replace('.mp4','_compressed.mp4')
    os.system(f"ffmpeg -i {video_file} -vcodec libx264 {compressed_path}")
    mp4 = open(compressed_path,'rb').read()
    data_url = "data:video/mp4;base64," + b64encode(mp4).decode()
    return HTML("""
        <video width=%i controls><source src="%s" type="video/mp4"></video>
        """ % (video_width,data_url))


if __name__ == "__main__":
    record_gym_video(env, path='./save/predprey/recordings/random_policy')
    show_video('./save/predprey/recordings/random_policy/rl-video-episode-0.mp4')