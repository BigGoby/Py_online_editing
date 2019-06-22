# Py_online_editing
python web在线编辑器

思路:

​		获取到python code -> 将pycode写入临时文件中 -> 获取python编译器位置 -> 利用subprocess函数运行临时文件 -> 抓取输出信息 -> return 返回抓取的信息

代码运行步骤:
		run() -> main() -> run()

结果示意图:

![1](https://github.com/BigGoby/Py_online_editing/blob/master/static/1.png)



访问http://127.0.0.1:5000/run:

![2](https://github.com/BigGoby/Py_online_editing/blob/master/static/2.png)