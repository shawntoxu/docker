#coding=utf8

#json.dumps(data) 可以将pyhton数据装为 json 字符串
#json.loads(data)可以将json 装载为python数据类型dict
import json 

if __name__ == '__main__':
    data1 = {"a":111,"c":"d","b":"ccc","zf":"中文"}
    #indent=2 为格式化缩进2个空格  sort_keys=True 按照key排序
    jsondata = json.dumps(data1,sort_keys=True,indent=2)
    print  jsondata,"长度为:",len(jsondata)
    #对网络数据传送要求严格的情况下可以压缩数据separators，将空格去掉
    jsondata2 = json.dumps(data1,sort_keys=True,separators=(',',':'))
    print  jsondata2,"长度为:",len(jsondata2)
    
    #保存到文件中
   # with open("/javatool/json.txt","w") as j:
    #    j.write(jsondata)
        
    #加载保存的json数据
    with open("/javatool/json.txt","r") as js:
        abc = js.read()
        rs = json.loads(abc)
        print rs
    
