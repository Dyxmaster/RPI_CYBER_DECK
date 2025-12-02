import os
import sqlite3
import datetime
import requests
import feedparser  # 解析 RSS 新闻
from zhipuai import ZhipuAI  # 智谱官方 SDK
from dotenv import load_dotenv

# --- 配置部分 ---
# 数据库会直接在当前文件夹生成一个 nexus.db 文件，不用管它
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "nexus.db")
DEFAULT_MODEL = "glm-4-flash"

class NexusCore:
    def __init__(self):
        # 加载 .env 文件里的变量
        load_dotenv()
        
        # 1. 获取 API Key
        self.api_key = os.getenv("ZHIPUAI_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                self.client = ZhipuAI(api_key=self.api_key)
            except Exception as e:
                print(f"⚠️ Nexus AI 初始化失败: {e}")
        else:
            print("⚠️ 警告: 环境变量 ZHIPUAI_API_KEY 未找到，AI 功能将不可用。")
        
        # 2. 初始化数据库（自动创建文件）
        self.init_db()

    def init_db(self):
        """
        初始化数据库：
        如果 nexus.db 不存在，会自动创建，并新建一张 tasks 表用来存任务。
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            # 创建一个表：id(序号), content(内容), status(状态:0未做/1已做), created_at(时间)
            c.execute('''CREATE TABLE IF NOT EXISTS tasks
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          content TEXT, 
                          status INTEGER DEFAULT 0, 
                          created_at TEXT)''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"数据库初始化失败: {e}")

    # --- AI 通讯模块 ---
    def chat_with_ai(self, messages):
        """调用智谱 AI 进行对话"""
        if not self.client:
            return "⚠️ 系统离线：未配置 ZHIPUAI_API_KEY"
        
        try:
            response = self.client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                temperature=0.7,
            )
            # 官方 SDK 返回的是对象，不是字典
            return response.choices[0].message.content
        except Exception as e:
            return f"通讯链路故障: {str(e)}"

    # --- 数据获取模块 ---
    def get_weather(self):
        """获取天气 (使用 OpenMeteo 免费接口)"""
        try:
            # 默认北京坐标，你可以改成你所在城市的经纬度
            url = "https://api.open-meteo.com/v1/forecast?latitude=31.317987&longitude=120.619907&current=temperature_2m,weather_code&timezone=auto"
            r = requests.get(url, timeout=3)
            data = r.json()
            curr = data.get('current', {})
            code = curr.get('weather_code', 0)
            
            # 天气代码映射
            cond = "晴朗"
            if code in [1,2,3]: cond = "多云"
            elif code in [45,48]: cond = "雾"
            elif 51 <= code <= 67: cond = "雨"
            elif code >= 95: cond = "雷暴"
            
            return {
                "temp": curr.get('temperature_2m', "--"),
                "condition": cond
            }
        except:
            return {"temp": "--", "condition": "信号中断"}

    def get_news(self):
        """获取 IT之家 新闻 (RSS)"""
        try:
            feed = feedparser.parse("https://www.ithome.com/rss/")
            # 只取前 3 条
            return [{"title": entry.title, "link": entry.link} for entry in feed.entries[:3]]
        except:
            return [{"title": "无法建立新闻数据链路", "link": "#"}]

    # --- 任务管理模块 (增删改查) ---
    def get_tasks(self):
        """读取所有未完成任务"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id, content FROM tasks WHERE status=0 ORDER BY id DESC")
        tasks = [{"id": r[0], "content": r[1]} for r in c.fetchall()]
        conn.close()
        return tasks

    def add_task(self, content):
        """添加新任务"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO tasks (content, created_at) VALUES (?, ?)", 
                  (content, datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def complete_task(self, task_id):
        """删除/完成任务"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.commit()
        conn.close()

    # --- 核心业务：生成简报 ---
    def generate_briefing(self):
        weather = self.get_weather()
        tasks = self.get_tasks()
        news = self.get_news()
        
        task_str = ", ".join([t['content'] for t in tasks]) if tasks else "无待办任务"
        news_str = ", ".join([n['title'] for n in news])
        
        prompt = [
            {"role": "system", "content": "你是一个赛博朋克风格的飞船 AI 副官 'NEXUS'。不要使用Markdown格式，直接输出纯文本。"},
            {"role": "user", "content": f"""
            [传感器数据] 温度 {weather['temp']}C, 天气 {weather['condition']}
            [任务协议] {task_str}
            [外部情报] {news_str}
            
            请向指挥官汇报：
            1. 一句话锐评天气。
            2. 如果有任务，催促执行；没任务建议待机。
            3. 总结一条最重要的新闻。
            4. 字数限制 120 字。
            """}
        ]
        
        ai_msg = self.chat_with_ai(prompt)
        return {"weather": weather, "tasks": tasks, "news": news, "ai_msg": ai_msg}

    # --- 核心业务：对话路由 ---
    def chat_router(self, user_input):
        # 1. 简单的关键词拦截（为了响应快）
        if user_input.startswith(("添加", "提醒")):
            content = user_input.replace("添加", "").replace("提醒", "").strip()
            self.add_task(content)
            return f"指令确认。任务协议 [{content}] 已写入核心数据库。"
            
        # 2. 如果不是指令，就闲聊
        prompt = [
            {"role": "system", "content": "你是 NEXUS，树莓派中枢 AI。请用赛博朋克风格回答。"},
            {"role": "user", "content": user_input}
        ]
        return self.chat_with_ai(prompt)

# 实例化单例，供其他文件引用
nexus_brain = NexusCore()

# --- 测试代码 ---
# 如果你直接运行 python modules/nexus_core.py，下面的代码会执行
if __name__ == "__main__":
    print(">>> 正在测试 NEXUS 核心模块...")
    
    # 1. 测试数据库
    print("1. 测试数据库写入...")
    nexus_brain.add_task("测试任务 - 核查系统核心")
    tasks = nexus_brain.get_tasks()
    print(f"   当前任务列表: {tasks}")
    
    # 2. 测试 API Key
    print("2. 测试 AI 连接...")
    if nexus_brain.api_key:
        reply = nexus_brain.chat_router("你好，汇报系统状态")
        print(f"   AI 回复: {reply}")
    else:
        print("   [跳过] 未配置 API Key")
        
    print(">>> 测试完成。")