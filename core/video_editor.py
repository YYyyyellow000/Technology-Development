import ffmpeg
import os

def extract_audio(video_path, audio_path):
    """从视频中提取音频"""
    try:
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, ac=1, ar='16k') # 单声道 16k 采样，省体积
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return True
    except ffmpeg.Error as e:
        print("❌ 提取音频失败:", e.stderr.decode())
        return False

def cut_and_merge_video(video_path, output_path, keep_ranges):
    """根据保留时间段剪辑视频"""
    print(f"✂️ 开始剪辑视频，保留片段数: {len(keep_ranges)}")
    
    input_stream = ffmpeg.input(video_path)
    streams = []
    
    for start, end in keep_ranges:
        # 视频切片
        v = input_stream.video.trim(start=start, end=end).setpts('PTS-STARTPTS')
        # 音频切片
        a = input_stream.audio.filter_('atrim', start=start, end=end).filter_('asetpts', 'PTS-STARTPTS')
        streams.append(v)
        streams.append(a)
    
    # 拼接所有片段
    try:
        joined = ffmpeg.concat(*streams, v=1, a=1).node
        v = joined[0]
        a = joined[1]
        
        (
            ffmpeg
            .output(v, a, output_path)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        print(f"✅ 剪辑完成！输出文件: {output_path}")
        return True
    except ffmpeg.Error as e:
        print("❌ 剪辑失败:", e.stderr.decode())
        return False