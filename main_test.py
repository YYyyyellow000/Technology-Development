import os
from core.ai_agent import transcribe_audio, analyze_segments
from core.video_editor import extract_audio, cut_and_merge_video

def main():
    # 1. 准备测试文件
    # 请找一个只有 30-60秒 的包含说话的 mp4 放在项目根目录，命名为 test.mp4
    video_file = "test.mp4"
    audio_file = "temp_audio.mp3"
    output_file = "final_result.mp4"

    if not os.path.exists(video_file):
        print(f"❌ 找不到 {video_file}，请先在目录下放一个测试视频！")
        return

    # 2. 提取音频
    print("--- Step 1: 提取音频 ---")
    extract_audio(video_file, audio_file)

    # 3. AI 识别与思考
    print("--- Step 2: AI 识别与思考 ---")
    segments = transcribe_audio(audio_file)
    keep_ranges = analyze_segments(segments)
    
    print(f"🎯 AI 建议保留的时间段: {keep_ranges}")

    # 4. 物理剪辑
    print("--- Step 3: 执行剪辑 ---")
    cut_and_merge_video(video_file, output_file, keep_ranges)

    # 清理临时文件
    if os.path.exists(audio_file):
        os.remove(audio_file)

if __name__ == "__main__":
    main()