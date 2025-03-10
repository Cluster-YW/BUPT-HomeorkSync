import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
from Log import logger

def get_bupt_homework(username,password):
    # 登录页面URL
    login_url = "https://auth.bupt.edu.cn/authserver/login?service=http://ucloud.bupt.edu.cn"

    # 创建会话
    session = requests.Session()

    # 获取登录页面
    try:
        response = session.get(login_url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"无法获取登录页面：{e}")
        exit()

    login_page = response.content

    # 解析执行token和事件ID
    soup = BeautifulSoup(login_page, 'html.parser')
    execution = soup.find('input', {'name': 'execution'})['value']
    event_id = soup.find('input', {'name': '_eventId'})['value']

    logger.trace(f"Execution: {execution}")
    logger.trace(f"EventID: {event_id}")

    # 构造登录数据
    login_data = {
        'username': username,
        'password': password,
        'submit': '登录',
        'type': 'username_password',
        'execution': execution,
        '_eventId': event_id
    }

    # 登录请求
    try:
        login_response = session.post(login_url, data=login_data)
        login_response.raise_for_status()
        print(f"登录成功，响应状态码：{login_response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"登录失败：{e}")
        exit()

    # 如果登录后需要重定向，可能需要再次检查响应
    if login_response.history:
        print("登录重定向路径：", login_response.url)

    # 配置 Selenium WebDriver
    # 确保你已经安装了 ChromeDriver 并且路径正确
    options = Options()
    options.add_argument("--start-maximized")  # 最大化浏览器窗口
    options.add_argument("--disable-extensions")  # 禁用扩展
    options.add_argument("--disable-gpu")  # 禁用 GPU 加速
    # options.add_argument("--headless")  # 无头模式
    driver = webdriver.Chrome(options=options)


    # 重新加载目标页面，使 Cookies 生效
    try:
        driver.get(login_response.url)
        time.sleep(0.3)  # 等待页面加载完成
    except Exception as e:
        logger.error(f"无法加载目标页面：{e}")
        driver.quit()
        exit()

    # 等待页面动态加载内容
    time.sleep(0.6)  # 等待足够时间，确保页面内容加载完成

    # 点击云邮
    button = driver.find_element(By.XPATH, '//span[text()="云邮"]')
    button.click()
    # print("点击云邮按钮")
    time.sleep(0.5)

    # 跳转到新的标签页 
    driver.switch_to.window(driver.window_handles[1])
    # print("切换到新的标签页")

    if soup.find('div', {'class': 'no-more-data-tips-text'}):
        logger.info("所有作业已完成")
        driver.quit()
        return set()

    homework_items = driver.find_elements(By.XPATH, '//div[contains(@class, "in-progress-item")]')

    homework_results = []

    for i in range(len(homework_items)):
        homework_items = driver.find_elements(By.XPATH, '//div[contains(@class, "in-progress-item")]')
        item = homework_items[i]
        title = item.find_element(By.XPATH, './/div[contains(@class, "activity-title")]').text.strip()
        dateline = item.find_element(By.XPATH, './/div[contains(@class, "acitivity-dateline")]').text.strip()
        # print(f"作业标题：{title}  截止日期：{dateline}")
        item.click()
        itemurl = driver.current_url
        time.sleep(1)
        # print("切换到新的标签页")
        assignment = driver.find_element(By.CLASS_NAME, 'assignment-content')
        attach = driver.find_element(By.CLASS_NAME, 'attachment')
        assignment_content = assignment.text.strip()
        # 去掉<p>和</p>标签
        assignment_text = assignment_content.replace('<p>', '').replace('</p>', '')
        # print(f"作业内容：{assignment_text}")
        attach_exist = not "无" in attach.text.strip()
        # if attach_exist:
            # print("有附件")
        # else:
            # print("无附件")
        homework_results.append({"title": title, "dateline": dateline, "url": itemurl, "content": assignment_text, "attach": attach_exist})
        # 返回上一页
        driver.execute_script("window.history.go(-1)")
        time.sleep(1)
        # print("返回上一页")


    # 保存页面内容
    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')


    # 关闭浏览器
    driver.quit()

    return homework_results, soup

if __name__ == '__main__':
    homework_results, soup = get_bupt_homework()
    print(soup.prettify())
    print(homework_results)