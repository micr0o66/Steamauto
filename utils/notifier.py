import os

import apprise
import json5

from utils import static
from utils.logger import PluginLogger, handle_caught_exception
from utils.static import CONFIG_FILE_PATH
from utils.tools import get_encoding

logger = PluginLogger("通知服务")
config = {}
try:
    if os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, "r", encoding=get_encoding(CONFIG_FILE_PATH)) as file:
            config = json5.load(file)
        config = config.get("notify_service", {})
        if config == {}:
            logger.warning("未配置通知服务，通知功能将不可用，请在配置文件中配置通知服务")
        elif config.get("notifiers"):
            logger.info(f"已配置{len(config.get('notifiers'))}个通知服务")
except Exception as e:
    logger.warning("通知服务异常，请检查配置文件是否正确配置")
    handle_caught_exception(e)
    pass


def send_notification(steam_client, message, title=""):
    steam_64_id = "未登录"
    steam_username = "暂未登录"

    if steam_client:
        try:
            steam_64_id = steam_client.get_steam64id_from_cookies()
        except:
            pass
        steam_username = steam_client.username

    if not config.get("notifiers"):
        return

    # 黑名单过滤
    for black in config.get("blacklist_words", []):
        if black in message or black in title:
            logger.debug(f"消息中包含黑名单词: {black}，已被过滤")
            return

    proxy = config.get("proxy", "").strip()

    # 备份旧环境变量
    old_http_proxy = os.environ.get("HTTP_PROXY")
    old_https_proxy = os.environ.get("HTTPS_PROXY")

    try:
        # 如果 proxy 非空才启用
        if proxy:
            os.environ["HTTP_PROXY"] = proxy
            os.environ["HTTPS_PROXY"] = proxy

        for notifier in config.get("notifiers", []):
            try:
                send_title = title if title else "Steamauto 通知"
                send_message = message

                if config.get("custom_title"):
                    send_message = f"{send_title}\n{send_message}"
                    send_title = config.get("custom_title")

                if config.get("include_steam_info", False):
                    send_message += f"\nSteam 用户名：{steam_username}\nSteam ID：{steam_64_id}"

                apobj = apprise.Apprise()
                apobj.add(notifier)
                apobj.notify(title=send_title, body=send_message)

            except Exception as e:
                handle_caught_exception(e)
                logger.error(f"发送通知失败: {str(e)}")

    finally:
        # 恢复环境变量，避免影响其他代码
        if old_http_proxy is None:
            os.environ.pop("HTTP_PROXY", None)
        else:
            os.environ["HTTP_PROXY"] = old_http_proxy

        if old_https_proxy is None:
            os.environ.pop("HTTPS_PROXY", None)
        else:
            os.environ["HTTPS_PROXY"] = old_https_proxy
