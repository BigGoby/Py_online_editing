# Py_online_editing
python web在线编辑器

思路:
获取到python code -> 将pycode写入临时文件中 -> 获取python编译器位置 -> 利用subprocess函数运行临时文件 -> 抓取输出信息 -> return 返回抓取的信息
