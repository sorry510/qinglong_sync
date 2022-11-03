import os
import requests

proxies = None

class QingLong():
    def __init__(self, url, client_id, client_secret, proxies = None, token = None):
        self.url = f"{url}/open"
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = ''
        self.proxies = None
        if proxies:
            self.proxies = proxies
        if not token:
            self.token = self._getToken()
            # self.token = self._getRootToken()

    def request(self, url, method = 'get', data = None):
        try:
            if method == 'get':
                return requests.get(url, headers = self._getHeaders(), proxies = self.proxies, params = data).json()
            elif method == 'post':
                return requests.post(url, headers = self._getHeaders(), proxies = self.proxies, json = data).json()
            elif method == 'put':
                return requests.put(url, headers = self._getHeaders(), proxies = self.proxies, json = data).json()
            elif method == 'delete':
                return requests.delete(url, headers = self._getHeaders(), proxies = self.proxies, json = data).json()
            else:
                return requests.get(url, headers = self._getHeaders(), proxies = self.proxies, params = data).json()
        except Exception as e:
            print('配置错误，请检查配置')
            print('Error:', e)
            exit()

    def _getRootToken(self):
        # 需要使用 api，不能用 open
        url = f"{self.url}/user/login"
        res = self.request(method='post', url=url, data={"username": self.client_id, "password": self.client_secret}).get('data')
        token = res['token']
        return token 

    def _getToken(self):
        url = f"{self.url}/auth/token?client_id={self.client_id}&client_secret={self.client_secret}"
        res = self.request(method='get', url=url)
        token = res["data"]['token']
        return token

    def _getHeaders(self):
        headers = {
            "Content-Type": "application/json;charset=UTF-8"
        }
        if self.token:
            headers['authorization'] = f"Bearer {self.token}"
        return headers

    def getEnv(self):
        url = f"{self.url}/envs"
        res = self.request(method='get', url=url).get("data")
        return res

    def addEnv(self, data):
        url = f"{self.url}/envs"
        res = self.request(method='post', url=url, data=data)
        return res

    def enableEnv(self, data):
        url = f"{self.url}/envs/enable"
        res = self.request(method='put', url=url, data=data)
        return res

    def disableEnv(self, data):
        url = f"{self.url}/envs/disable"
        res = self.request(method='put', url=url, data=data)
        return res

    def deleteEnv(self, data):
        url = f"{self.url}/envs"
        res = self.request(method='delete', url=url, data=data)
        return res

    def getConfigFiles(self):
        url = f"{self.url}/configs/files"
        res = self.request(method='get', url=url).get("data")
        return res

    def getConfigFile(self, name):
        url = f"{self.url}/configs/{name}"
        res = self.request(method='get', url=url).get("data")
        return res

    def saveConfigFile(self, data):
        url = f"{self.url}/configs/save"
        res = self.request(method='post', url=url, data=data)
        return res

    def getDependencies(self, data):
        url = f"{self.url}/dependencies"
        res = self.request(method='get', url=url, data=data).get("data")
        return res

    def addDependencies(self, data):
        url = f"{self.url}/dependencies"
        res = self.request(method='post', url=url, data=data)
        return res

    def delEnv(self, ids):
        url = f"{self.url}/envs"
        res = self.request(method='delete', url=url, data=ids)
        return res

    def getScript(self):
        url = f"{self.url}/scripts"
        res = self.request(method='get', url=url).get("data")
        return res

origin_url = os.environ.get("ql_origin_url")
origin_client_id = os.environ.get("ql_origin_client_id")
origin_client_secret = os.environ.get("ql_origin_client_secret")

target_url = os.environ.get("ql_target_url")
target_client_id = os.environ.get("ql_target_client_id")
target_client_secret = os.environ.get("ql_target_client_secret")

ql_sync_proxy = os.environ.get("ql_sync_proxy")
ql_sync_env = os.environ.get("ql_sync_env", "true")
# ql_delete_env = os.environ.get("ql_delete_env", "true")
ql_sync_config = os.environ.get("ql_sync_config", "true")
ql_sync_dependence = os.environ.get("ql_sync_dependence", "true")

if not origin_url:
    print('请添加环境变量:ql_origin_url')
    exit()
if not origin_client_id:
    print('请添加环境变量:ql_origin_client_id')
    exit()
if not origin_client_secret:
    print('请添加环境变量:ql_origin_client_secret')
    exit()
if not target_url:
    print('请添加环境变量:ql_target_url')
    exit()
if not target_client_id:
    print('请添加环境变量:ql_target_client_id')
    exit()
if not target_client_secret:
    print('请添加环境变量:ql_target_client_secret')
    exit()

if ql_sync_proxy:
    proxies = {
        "http": ql_sync_proxy # example: "socks5://127.0.0.1:10808"
    }

ql = QingLong(url=origin_url, client_id=origin_client_id, client_secret=origin_client_secret, proxies=proxies)
ql2 = QingLong(url=target_url, client_id=target_client_id, client_secret=target_client_secret, proxies=proxies)

if ql_sync_env == "true":
    # if ql_delete_env == "true":
    #     target_envs = ql2.getEnv()
    #     ids = list(map(lambda env: env['id'], target_envs))
    #     ql2.deleteEnv(ids)
    #     print('删除目标原有的【环境变量】成功')

    origin_envs = ql.getEnv()
    envs_status = list(map(lambda env: env['status'], origin_envs))
    target_envs = list(map(lambda env: {"value": env['value'], "name": env['name'], "remarks": env['remarks']}, origin_envs))
    res = ql2.addEnv(target_envs)
    if res['code'] == 200:
        data = res['data']
        disable_envs = []
        for i, env in enumerate(data):
            if envs_status[i] == 1:
                disable_envs.append(env['id'])
        ql2.disableEnv(disable_envs) # 同步禁用
        print('同步【环境变量】成功')
    else:
        print(f"同步【环境变量】失败,message: {res['message']} 或者 不成重复同步")

if ql_sync_config == "true":
    origin_config_filenames = ql.getConfigFiles()
    origin_config_files = []
    for file in origin_config_filenames:
        ql2.saveConfigFile({
            "name": file['value'],
            "content": ql.getConfigFile(file['value'])
        })
    print('同步【配置文件】成功')

if ql_sync_dependence == "true":
    # 多次同步会重复安装
    dependenciesTypes = ['nodejs', 'python3', 'linux']
    for t in dependenciesTypes:
        origin_dependencies = ql.getDependencies(data = {"type": t})
        origin_dependencies = list(map(lambda item: {"name": item['name'], "type": item['type'], "remark": item['remark']}, origin_dependencies))
        res = ql2.addDependencies(origin_dependencies)
    print('同步【依赖管理】成功')

print('脚本执行完毕')