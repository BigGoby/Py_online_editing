# -*- coding: utf-8 -*-
# __author__="siso"
import subprocess
import tempfile
import json
import time
import sys
import os

from flask import Flask

# 保存原始控制台对象
__console__ = sys.stdout
BASEDIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)

# 创建临时文件夹,返回临时文件夹路径
TempFile = tempfile.mkdtemp(suffix='_test', prefix='python_')
# 文件名
FileNum = int(time.time() * 1000)
# python编译器位置
EXEC = sys.executable


# 获取python版本
def get_version():
    v = sys.version_info
    version = "python %s.%s" % (v.major, v.minor)
    return version


# 接收代码写入文件
def write_file(pyname, code, path):
    fpath = os.path.join(path, '%s.py' % pyname)
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(code)
    print('file path: %s' % fpath)
    return fpath


# 编码
def decode(s):
    try:
        return s.decode('utf-8')
    except UnicodeDecodeError:
        return s.decode('gbk')


# 主执行函数
def main(code, path):
    r = dict()
    r["version"] = get_version()
    fpath = write_file(FileNum, code, path)
    try:
        # subprocess.check_output 是 父进程等待子进程完成，返回子进程向标准输出的输出结果
        # stderr是标准输出的类型
        # outdata = decode(subprocess.check_output([EXEC, fpath], stderr=subprocess.STDOUT, timeout=5))
        outdata = subprocess.check_output([EXEC, fpath], shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        # e.output是错误信息标准输出
        # 错误返回的数据
        r["code"] = 'error'
        r["output"] = decode(e.output)
        # r["output"] = wrongcustom.WrongCustom(decode(e.output))
        return r
    else:
        # 成功返回的数据
        r['output'] = decode(outdata)
        r["code"] = "success"
        return r
    finally:
        # 删除文件(其实不用删除临时文件会自动删除)
        try:
            os.remove(fpath)
        except Exception as e:
            exit(1)


# python 在线编辑器
@app.route('/run', methods=['POST', 'GET'])
def run():
    codes = "print(123)"
    re = main(codes, TempFile)
    return json.dumps(re, ensure_ascii=False)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=50001)