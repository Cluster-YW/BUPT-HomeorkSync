import TickTickHandler
import UcloudHandler
import configparser

from Log import logger

config = configparser.ConfigParser()

def sync_homework():
    config.read('src/config.ini')

    client_id = config.get('TickTick', 'client_id', fallback=None)
    client_secret = config.get('TickTick', 'client_secret', fallback=None)
    username = config.get('UCloud', 'username', fallback=None)
    password = config.get('UCloud', 'password', fallback=None)
    if not config.has_section("TickTick"):
        config.add_section('TickTick')
    if not config.has_section("UCloud"):
        config.add_section('UCloud')
    if not config.has_section("settings"):
        config.add_section('settings')

    if client_id is None:
        client_id = input("请输入TickTick的client_id: ")
        config.set('TickTick', 'client_id', client_id)
    if client_secret is None:
        client_secret = input("请输入TickTick的client_secret: ")
        config.set('TickTick', 'client_secret', client_secret)
        client_secret = config.get('TickTick', 'client_secret', fallback=None)
    if config.get("TickTick","host",fallback=None) is None:
        config.set('TickTick', 'host', input("请输入TickTick的重定向主机地址: "))
    if config.get("TickTick","port",fallback=None) is None:
        config.set('TickTick', 'port', input("请输入TickTick的重定向端口: "))
    if username is None:
        username = input("请输入UCloud的username: ")
        config.set('UCloud', 'username', username)
    if password is None:
        password = input("请输入UCloud的password: ")
        config.set('UCloud', 'password', password)

    logger.info("配置：TickTick client_id: "+config['TickTick']['client_id'])
    logger.info("配置：TickTick client_secret: "+config['TickTick']['client_secret'])
    config.write(open("src/config.ini", "w"))

    tm = TickTickHandler.TickTickManager(client_id=client_id, client_secret=client_secret,config=config)
    homeworks = UcloudHandler.get_bupt_homework(username=username, password=password)[0]
    HWproject_id = tm.get_project_id("✏️作业")
    tasks = tm.get_project_tasks(HWproject_id)["tasks"]
    tasks_title = [task['title'] for task in tasks]
    homeworks_title = [homework['title'] for homework in homeworks]
    logger.info("当前的作业："+str(homeworks_title))
    logger.info("当前的任务列表："+str(tasks_title))
    for homework in homeworks:
        homework_title = homework['title']
        homework_content = homework['content']
        homework_content += "\n【有附件】" if homework['attach'] else "\n【无附件】"
        homework_due_date = homework['dateline']
        #去掉日期中的汉字
        homework_due_date = homework_due_date.replace('截止','+0800')
        homework_due_date = homework_due_date[0:10]+"T"+homework_due_date[11:]
        homework_url = homework['url']
        homework_content = homework_url + "\n" + homework_content
        if homework_title not in tasks_title:
            tm.create_task(homework_title, homework_content, duetime=homework_due_date, project_id=HWproject_id)
            logger.info(f"创建了新任务：{homework_title}")
        else:
            logger.info(f"任务已存在：{homework_title}")
    
    for task in tasks:
        if task['title'] not in homeworks_title:
            tm.complete_task(HWproject_id, task['id'])
            logger.info(f"完成了任务：{task['title']}")

if __name__ == '__main__':
    logger.trace("开始同步作业")
    config.read('src/config.ini')
    sync_homework()