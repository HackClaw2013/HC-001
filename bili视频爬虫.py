import requests
import os
import time
from urllib.parse import quote

# 请求头（模拟浏览器访问，防止被拦截）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/"
}

# 创建保存文件夹
SAVE_PATH = "bilibili_videos"
if not os.path.exists(SAVE_PATH):
    os.mkdir(SAVE_PATH)

def search_video_by_name(video_name):
    """根据视频名搜索B站，返回第一个匹配的视频BV号"""
    try:
        # B站搜索接口（关键词URL编码）
        url = f"https://api.bilibili.com/x/web-interface/search/all/v2?keyword={quote(video_name)}"
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        # 提取视频结果
        result = data.get("data", {}).get("result", [])
        video_items = []
        for item in result:
            if item.get("result_type") == "video":
                video_items = item.get("data", [])
                break

        if not video_items:
            return None

        # 匹配**精准视频名**
        for video in video_items:
            title = video.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", "")
            if title.strip() == video_name.strip():
                return video.get("bvid")  # 返回BV号

        return None
    except Exception as e:
        print(f"搜索出错：{str(e)}")
        return None

def get_video_download_url(bvid):
    """根据BV号获取视频下载链接"""
    try:
        # 获取视频CID
        info_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        info_data = requests.get(info_url, headers=HEADERS, timeout=10).json()
        cid = info_data["data"]["cid"]
        title = info_data["data"]["title"].replace("/", "").replace("\\", "")

        # 获取真实下载地址
        play_url = f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&qn=80"
        play_data = requests.get(play_url, headers=HEADERS, timeout=10).json()
        video_url = play_data["data"]["durl"][0]["url"]

        return title, video_url
    except Exception as e:
        print(f"获取视频地址失败：{str(e)}")
        return None, None8

def download_video(title, video_url):
    """下载视频并保存"""
    try:
        print(f"开始下载：{title}")
        file_path = os.path.join(SAVE_PATH, f"{title}.mp4")

        # 流式下载（大视频不占内存）
        with requests.get(video_url, headers=HEADERS, stream=True, timeout=30) as r:
            r.raise_for_status()
            total_size = int(r.headers.get("content-length", 0))
            downloaded_size = 0

            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        progress = int(downloaded_size / total_size * 100) if total_size else 0
                        print(f"\r下载进度：{progress}%", end="")

        print(f"\n下载完成！保存路径：{file_path}")
    except Exception as e:
        print(f"\n下载失败：{str(e)}")

def main():
    print("="*50)
    print("B站精准视频名爬虫 | 找不到自动重新输入")
    print("="*50)

    while True:
        video_name = input("\n请输入B站**精准视频名**：").strip()
        if not video_name:
            print("视频名不能为空！")
            continue

        print("正在搜索视频...")
        bvid = search_video_by_name(video_name)

        if not bvid:
            print("❌ 未找到该视频，请检查视频名是否准确！")
            continue

        # 找到视频 → 下载
        title, video_url = get_video_download_url(bvid)
        if title and video_url:
            download_video(title, video_url)
            break

if __name__ == "__main__":
    main()