import requests
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import configparser
from Log import logger

global code
code = None

class AuthHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_GET(self):
        global code
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h1>Authorization is being processed, you can close this page.</h1>")
        print(self.path)
        code = self.path.split("=")[1]
        print(f"Authorization code: {code}")
        self.server.waitevent.set()

class AuthServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.waitevent = threading.Event()


class TickTickManager:
    def __init__(self, client_id, client_secret, config=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        if not config:
            self.config = configparser.ConfigParser()
            self.config.read("src/config.ini")
        else:
            self.config = config
        if self.config.get("TickTick","access_token",fallback=None):
            self.access_token = self.config["TickTick"]["access_token"]
        else:
            logger.info("Access token为空，需要进行认证获取。")
            self.get_access_token()

    def get_access_token(self):
        global code
        host = self.config.get("TickTick", "host", fallback="127.0.0.1")
        logger.info(f"使用的 host: {host}")
        port = self.config.getint("TickTick", "port", fallback=8080)
        logger.info(f"使用的 port: {port}")
        redirect_url = f"http://{host}:{port}"
        with AuthServer((host, port), AuthHandler) as httpd:
            logger.trace(f"Server running at {redirect_url}")
            server_thread = threading.Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()

            authorize_url = f"https://ticktick.com/oauth/authorize??scope=tasks:write tasks:read&client_id={self.client_id}&response_type=code&redirect_uri={redirect_url}"
            # 构建授权 URL
            logger.info(f"请访问以下 URL 授权：{authorize_url}")

            # 打开授权页面
            webbrowser.open(authorize_url)

            httpd.waitevent.wait()  # 等待用户授权
            httpd.shutdown()  # 关闭服务器

        logger.info(f"获取到 Authorization code: {code}")

        # 构建请求数据
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_url,
        }

        # 发送 POST 请求获取访问令牌
        response = requests.post("https://ticktick.com/oauth/token", data=data)
        logger.info(response.text)
        self.access_token = response.json().get("access_token")
        logger.info(f"获取到 Access token: {self.access_token}")

        self.config["TickTick"]["access_token"] = self.access_token
        self.config.write(open("src/config.ini", "w"))

    def create_task(self, task_name, task_content,duetime=None ,project_id=None):
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        data = {
            "title": task_name,
            "content": task_content,
            "dueDate": duetime
        }
        if project_id:
            data["projectId"] = project_id
        response = requests.post(
            "https://api.ticktick.com/open/v1/task", headers=headers, json=data
        )
        logger.info(f"创建任务 {task_name} 状态码： {response.status_code}")
        # print(response.text)
        return response
    
    def get_project_id(self, project_name):
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        projects_response = requests.get(
            f"https://api.ticktick.com/open/v1/project", headers=headers
        )
        print(projects_response.status_code)
        print(projects_response.json())
        for project in projects_response.json():
            if project.get("name") == project_name:
                return project.get("id")
        logger.warning("未找到该 Project。")
        return None
    
    def get_project_tasks(self, project_id):
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        tasks_response = requests.get(
            f"https://api.ticktick.com/open/v1/project/{project_id}/data", headers=headers
        )
        # print(tasks_response.status_code)
        # print(tasks_response.json())
        return tasks_response.json()

    def complete_task(self, project_id, task_id):
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            f"https://api.ticktick.com/open/v1/project/{project_id}/task/{task_id}/complete", headers=headers
        )

if __name__ == "__main__":
    client_id = "2pC52UdklSAhhmeoU9"
    client_secret = "((+%L+ni4s+P80IA2X_tEYi8^7qR2IOr"

    tm = TickTickManager(client_id, client_secret)
    # tm.get_access_token()
    print(f"Access token: {tm.access_token}")
    pj_id = tm.get_project_id("✏️作业")
    print(f"Project ID: {pj_id}")
    tm.get_project_tasks(pj_id)
