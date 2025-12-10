import os
os.environ["PATH"] += r";D:\ffmpeg\ffmpeg-2025-12-07-git-c4d22f2d2c-full_build\bin"
import json
import whisper  # 导入本地 Whisper 库
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# 1. 初始化硅基流动 API 客户端 (用于 LLM)
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

# 2. 加载本地 Whisper 模型 (懒加载，第一次调用时才会下载模型)
# "base" 模型速度快且精度尚可；如果电脑配置好可用 "small" 或 "medium"
print("⏳ 正在加载本地 Whisper 模型 (首次运行会下载 ~140MB)...")
whisper_model = whisper.load_model("base") 

def transcribe_audio(audio_path):
    """
    使用本地 Whisper 模型将音频转为带时间戳的文字
    """
    print(f"🎤 正在本地转录音频: {audio_path} ...")
    
    # 调用本地模型进行转录
    result = whisper_model.transcribe(audio_path)
    
    # Whisper 本地库返回的 segments 格式本身就是 list of dict
    return result['segments']

def analyze_segments(segments):
    """
    调用硅基流动大模型 (DeepSeek/Qwen) 分析哪些片段需要保留
    """
    print("🧠 正在请求硅基流动 (DeepSeek) 分析剪辑方案 ...")
    
    # 简化一下数据发送给 LLM，节省 token
    simple_segments = [
        {"start": round(s['start'], 2), "end": round(s['end'], 2), "text": s['text'].strip()} 
        for s in segments
    ]
    input_text = json.dumps(simple_segments, ensure_ascii=False)

    system_prompt = """
    你是一个专业的视频剪辑师。你的任务是根据字幕时间戳，去除"无意义的废话"、"重复啰嗦"、"口误"以及"长时间静默"的片段。
    
    【输入】一段视频的字幕列表 JSON。
    【输出】严格的 JSON 格式，包含一个 "keep_ranges" 列表，代表需要**保留**的时间段（秒）。
    
    规则：
    1. 保留核心信息，切除 "呃、那个、就是" 等填充词。
    2. 如果有自我修正（如"我想要...我希望"），只保留修正后的版本。
    3. 合并相邻的保留片段，避免过度细碎的剪辑。
    4. 输出格式必须为: {"keep_ranges": [[0, 5.2], [8.4, 15.0]]}
    """

    try:
        # 获取 .env 里配置的模型名字
        model_name = os.getenv("LLM_MODEL_NAME", "deepseek-ai/DeepSeek-V2.5")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text}
            ],
            response_format={"type": "json_object"}, # 确保返回 JSON
            temperature=0.1 # 温度低一点，保证输出稳定
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # 简单的容错处理
        if "keep_ranges" not in result:
            print("⚠️ LLM 返回格式异常，尝试修复...")
            # 如果模型没返回 keep_ranges，这里可以加兜底逻辑，比如返回原视频
            return [[0, segments[-1]['end']]]
            
        return result['keep_ranges']
        
    except Exception as e:
        print(f"❌ LLM 调用失败: {e}")
        # 如果报错，为了不让程序崩溃，返回全片保留
        return [[0, segments[-1]['end']]]