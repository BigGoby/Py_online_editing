# -*- coding: utf-8 -*-
# __author__="siso"
import logconf
import error
import subprocess
import tempfile
import time
import json
import sys
import os
import pwd
import logging
import re
import pandas as pd
import wrongcustom

from flask import Flask, request, Response, jsonify

# 保存原始控制台对象
__console__ = sys.stdout

BASEDIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
logger = logconf.get_logger(__name__)

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


# 获得py文件名
def get_pyname():
    global FileNum
    return 'test_%d' % FileNum


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
def main(code, path, id):
    r = dict()
    r["version"] = get_version()
    pyname = get_pyname()
    fpath = write_file(pyname, code, path)
    try:
        # subprocess.check_output 是 父进程等待子进程完成，返回子进程向标准输出的输出结果
        # stderr是标准输出的类型
        # outdata = decode(subprocess.check_output([EXEC, fpath], stderr=subprocess.STDOUT, timeout=5))

        mingling = 'chown {0}:pang {1};chmod 700 {2};sudo -u {3} python3 {4}'.format(id, fpath, fpath, id, fpath)
        outdata = subprocess.check_output(mingling, shell=True, stderr=subprocess.STDOUT)
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


# 检查用户文件夹是否存在
def checkfolder(name, uid, gid):
    path = os.getcwd() + r'/user/' + str(name)
    upath = os.path.exists(path)
    if not upath:
        os.makedirs(path, mode=0o700)
        os.chown(path, uid, gid)
    return path


# 检查用户是否已经存在
def checkuid(name):
    info = None
    try:
        info = pwd.getpwnam(name)
    except:
        pass
    if info:
        path = checkfolder(name, info.pw_uid, info.pw_gid)
        return path
    else:
        name = name
        ugroup = "pang"
        password = "chinacpda"
        command = 'useradd -g {0} {1};usermod -a -G {2} {3};echo {4}:{5} | chpasswd'.format(ugroup, name, ugroup, name
                                                                                            , name, password)
        subprocess.check_output(command, shell=True)
        uid = pwd.getpwnam(name).pw_uid
        gid = pwd.getpwnam(name).pw_gid
        path = checkfolder(name, uid, gid)
        return path


# 监督读取文件
def supervision_read_data(path, li):
    try:
        try:
            data = pd.read_csv(path, dtype=str, encoding='gbk').fillna("'nan'")
        except:
            data = pd.read_csv(path, dtype=str, encoding='uth8').fillna("'nan'")
        data1 = []
        data2 = []
        if 'x' in li.keys():
            x1 = [int(x) for x in li['x']]
            label = [list(data.columns)[x2] for x2 in x1]
            data1 = [label] + data[label].values.tolist()
        if 'y' in li.keys():
            x2 = [int(x) for x in li['y']]
            label1 = [list(data.columns)[x3] for x3 in x2]
            data2 = [label1] + data[label1].values.tolist()
        return data1, data2
    except Exception as e:
        print(e)
        return False, False


# 非监督读取文件
def nosupervision_read_data(path, li):
    try:
        try:
            data = pd.read_csv(path, dtype=str, encoding='gbk').fillna("'nan'")
        except:
            data = pd.read_csv(path, dtype=str, encoding='uth8').fillna("'nan'")
        data1 = []
        if 'x' in li.keys():
            x1 = [int(x) for x in li['x']]
            label = [list(data.columns)[x2] for x2 in x1]
            data1 = [label] + data[label].values.tolist()
        return data1
    except Exception as e:
        print(e)
        return False


# 获取文件表头
def readuserlabel(path):
    try:
        try:
            data = pd.read_csv(path, dtype=str, encoding='gbk').head()
        except:
            data = pd.read_csv(path, dtype=str, encoding='uth8').head()
        label = list(data.columns)
        return label
    except Exception as e:
        print(e)
        return False


# 用于判断文件后缀
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ["CSV", "csv"]


# python 在线编辑器
@app.route('/run', methods=['POST'])
def run():
    if request.method == 'POST':
        code = request.values['code']
        id = request.values['id']
        cn_list = json.loads(request.values['cn_list'])
        file_name = request.values['file_name']
        # 判断用户是否存在目录,不存在就创建
        path = checkuid(id)
        if file_name != 'none':
            # 方案一
            # cn_list = {"x": ["0", "1", "2", "3", "4"], "y": ["5"]}
            if not 'y' in cn_list.keys():
                cn_list['y'] = []
            file_path = path + r'/' + file_name
            if len(cn_list['y']) != 0:
                datax, datay = supervision_read_data(file_path, cn_list)
                codes = code.replace('supervision_read_data()', '%s,%s' % (datax, datay))
            else:
                datax = nosupervision_read_data(file_path, cn_list)
                codes = code.replace('nosupervision_read_data()', '%s' % datax)
            if datax == False:
                data = {}
                data['version'] = 'python 3.5'
                data['code'] = '获取数据失败'
                return json.dumps(data)
            # 以下为方案二
            # data1_found = "nosupervision_read_data()"
            # data1_notfound = re.findall(data1_found, code)
            # if len(data1_notfound) != 0:
            #    datax = nosupervision_read_data(file_path, cn_list)
            #    codes = code.replace('nosupervision_read_data()', '%s' % datax)
            # else:
            #    data_found = "supervision_read_data()"
            #    data_notfound = re.findall(data_found, code)
            #    if len(data_notfound) != 0:
            #        datax, datay = supervision_read_data(file_path, cn_list)
            #        codes = code.replace('supervision_read_data()', '%s,%s' % (datax, datay))
            #    else:
            #        codes = code
        else:
            codes = code
        jsondata = main(codes, path, id)
        data = {}
        data['output'] = jsondata['output']
        data['version'] = jsondata['version']
        data['code'] = jsondata['code']
        # print(data)
        logger.info('用户：%s,在线运行成功请求成功' % id)
        return json.dumps(data)
    else:
        return Response({'msg': 'GET请求不被允许', 'status': False})


# 获取用户文件夹下面的数据文件
@app.route('/get/datalsit/', methods=['POST', 'GET'])
def getuserdata():
    # 获取账户下面的数据
    if request.method == 'GET':
        id = request.values['id']
        checkuid(id)
        path = os.getcwd() + '/user/' + str(id)
        file = os.listdir(path)
        data = {}
        fe = []
        for l in file:
            file_path = os.path.join(path, l)
            if os.path.isfile(file_path):
                fe.append(l)
        data = fe
        # return json.dumps(data)
        logger.info('用户：%s,获取数据列表', id)
        return jsonify({'status': True, 'data': data})

    # 获取操作行的数据
    if request.method == "POST":
        id = request.values['id']
        file_name = request.values['name']
        cn_list = eval(request.values['cn_list'])
        # print(id,file_name,cn_list)
        path = os.getcwd() + '/user/' + str(id) + '/' + file_name
        data = {}
        data['data'] = readuserfile(path, cn_list)
        # return json.dumps(data)
        return jsonify({'status': True, 'data': data})
    else:
        return Response({'msg': '%s请求不被允许' % request.method, 'status': False})


# 获取文件的表头及上传文件
@app.route('/get/datalabel/', methods=['POST', 'GET'])
def getuserdatalabel():
    # 获取表头
    if request.method == 'GET':
        id = request.values['id']
        file_name = request.values['name']
        path = os.getcwd() + '/user/' + str(id) + '/' + file_name
        data = readuserlabel(path)
        logger.info('用户：%s,获取%s文件表头成功' % (id, file_name))
        return jsonify({'status': True, 'label': data})

    # 上传文件
    if request.method == 'POST':
        id = request.values.get('id')
        dataname = request.values.get('file_name')
        file = request.files['files']
        # 判断是否是允许上传的文件类型
        if file and allowed_file(dataname):
            path = os.getcwd() + '/user/' + str(id) + '/' + dataname
            #  判断文件是否存在
            if os.path.exists(path):
                data = "文件名已存在请修改文件名"
                return jsonify({'msg': data})
            file.save(path)
        else:
            data = "文件上传类型暂不支持"
            return jsonify({'status': False, 'msg': data})
        label = readuserlabel(path)
        data = "文件上传成功"
        logger.info('用户：%s,上传%s文件成功' % (id, dataname))
        return jsonify({'status': True, 'msg': data, 'label': label})


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=50001)
