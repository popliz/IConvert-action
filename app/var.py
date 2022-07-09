import argparse
from uuid import uuid4

from app.firebase import Firebase

parser = argparse.ArgumentParser(
    description="使用firebase跟github action转换视频的python脚本")
parser.add_argument(
    "--role", choices=["converter", "indexer"], default="converter")
parser.add_argument("--min-size", type=int, default=0, help="脚本处理的最小文件大小，单位MB")
parser.add_argument(
    "--max-size", type=int, default=10240, help="脚本处理的最大文件大小，单位MB")
parser.add_argument("--thread", type=int, default=0)
parser.add_argument("--keep-origin", action="store_true", help="是否保留原始文件")
# mp4格式使用h264 + aac编码，webm格式使用vp9 + opus编码
parser.add_argument("--format", choices=["mp4", "webm"], default="mp4")
parser.add_argument("--crf", type=int, default=20)
parser.add_argument("--input-dir", default="/iconvert_input", help="输入文件目录")
parser.add_argument("--output-dir", default="/iconvert_output", help="输出文件目录")
parser.add_argument("--remote-output-dir", help="rclone的远程输出路径，用来检测文件是否上传完成")
parser.add_argument(
    "--log-level",
    choices=["CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG"],
    default="DEBUG",
    help="日志等级")
parser.add_argument("--firebase-api-key", required=True)
parser.add_argument("--firebase-db-url", required=True)
parser.add_argument("--firebase-project-id", required=True)
parser.add_argument("--firebase-email", required=True)
parser.add_argument("--firebase-password", required=True)
parser.add_argument("--owner-repo")
parser.add_argument("--workflow-id")
parser.add_argument("--github-token")

CONFIG = parser.parse_args()
APPID = uuid4().hex
# 初始化数据库
DB = Firebase(
    CONFIG.firebase_api_key,
    CONFIG.firebase_db_url,
    CONFIG.firebase_project_id,
    CONFIG.firebase_email,
    CONFIG.firebase_password,
)
