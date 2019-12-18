import json
from urllib import request, parse
from retry import retry


class DeptPoster(object):
    api = 'dept_classify'

    def __init__(self, logger=None):
        self.logger = logger
        self.ip = '172.27.249.130'
        self.port = '3000'
        self.url = 'http://' + self.ip + ':' + self.port + '/' + self.api
        self.data = {}

        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Connection': 'keep-alive',
        }

    @retry(tries=3)
    def post(self):
        req = request.Request(self.url, data=self.data)

        log_info = 'request url: {}, data length: {}'.format(self.url, len(self.data))
        if self.logger is not None:
            self.logger.info(log_info)
        else:
            print(log_info)

        page = request.urlopen(req, timeout=2000).read()
        page = json.loads(page.decode('utf-8'))
        return page

    def set_param(self, param):
        data_string = parse.urlencode(param)
        self.url += '?' + data_string

    def set_data(self, data):
        assert isinstance(data, dict)
        self.data = json.dumps(data).encode()


def post():
    a = (1, 2, 3)
    data = {'q': str(a), 'rows': 2}
    poster = DeptPoster()
    poster.set_param(data)
    result = poster.post()
    print(result)


if __name__ == '__main__':
    post()
