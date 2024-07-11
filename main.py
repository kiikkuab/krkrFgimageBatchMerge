from PIL import Image
import os
import shutil
import csv
import time

info_dir = '.\\info\\'
pic_dir = '.\\pic\\'
output_dir = "out/"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

info_arr = os.listdir(info_dir)
pic_arr = os.listdir(pic_dir)

print("All Info:",info_arr)
for info_file in info_arr:
    with open(info_dir+info_file, encoding='utf-16 le') as cf:
        print("Open Info:",info_file)
        lines = csv.reader(cf, delimiter='\t')

        #1.Turn csv to tuple
        lines = list(lines)
        data = []
        titles = []
        for i in range(len(lines)):
            if i == 0:
                titles = lines[i]
            elif i == 1:
                continue
            else:
                local = {}
                for j in range(len(lines[i])):
                    local[titles[j]] = lines[i][j]
                data.append(local)
        ##print(titles,data)

        #2.Divide back and face
        #(1)divide layer_types
        layer_type0 = []
        layer_type2 = []
        for item in data:
            if item["\ufeff#layer_type"] == "0":
                layer_type0.append(item)
            if item["\ufeff#layer_type"] == "2":
                layer_type2.append(item)
        type2_name_data = []
        for item in layer_type2:
            back_id = item["layer_id"]
            targets = []
            for item1 in layer_type0:
                if item1["group_layer_id"] == back_id:
                    targets.append(item1)
            type2_name_data.append({"_name":item["name"],"_list":targets}) 
        #print(type2_name_data)
        #(2)divide face pics
        face_data = []
        back_list = []
        for item in type2_name_data:
            if item["_name"] == "表情":
                face_data = item["_list"]
            else:
                back_list.append({"__name":item["_name"],
                                "__back_id":item["_list"][0]["layer_id"],
                                "__left":item["_list"][0]["left"],
                                "__top":item["_list"][0]["top"]})
        #print(back_list)
        #(3)iterate back list, merge pictures together
        def mergePics(back,front,left,top):
            backdata = back.getdata()
            frontdata = front.getdata()

            width, height = backdata.size
            newpic = Image.new("RGBA",backdata.size)
            newdata = newpic.getdata()
            for x in range(width):
                for y in range(height):
                    r, g, b, a = backdata.getpixel((x, y))
                    newdata.putpixel((x, y), (r,g,b,a))
                    if (x > left and 
                        x < left + frontdata.size[0] and 
                        y > top and 
                        y < top + frontdata.size[1]):

                        r1, g1, b1, a1 = frontdata.getpixel((x - left, y - top))
                        
                        alpha = 255 - (255 - a1) * (255 - a)
                        if alpha == 0:
                            continue
                        outR = (255*r1 * a1 + r * a * (255-a1)) / alpha/255
                        outG = (255*g1 * a1 + g * a * (255-a1)) / alpha/255
                        outB = (255*b1 * a1 + b * a * (255-a1)) / alpha/255

                        newdata.putpixel((x, y), (int(outR),int(outG),int(outB),int(alpha)))
            
            newpic.putdata(newdata)
            return newpic
        def getPic(info_name,id):
            return "pic/"+info_name.split(".")[0]+"_"+id+".tlg.png"
        if face_data == []:
            for item in type2_name_data:
                outfile = output_dir+item["_list"][0]["name"]+"_"+item["_name"]+"_"+info_file.split(".")[0]+".png"
                print("no expression, copying directly:",outfile)
                shutil.copy(getPic(info_file,item["_list"][0]["layer_id"]), outfile)
            continue

        for item in back_list:
            for face in face_data:
                localpicname = output_dir+face["name"]+"_"+item["__name"]+"_"+info_file.split(".")[0]+".png"
                if os.path.exists(localpicname):
                    print(localpicname,"exists, continue...")
                    continue

                t0 = time.time()
                backimg = Image.open(getPic(info_file,item["__back_id"]))
                faceimg = Image.open(getPic(info_file,face["layer_id"]))
                
                left = int(face["left"]) - int(item["__left"])
                top = int(face["top"]) - int(item["__top"])
                xoffset,yoffset,hasOffset = 0,0,False
                if left < 0:
                    xoffset = -left
                    left = 0
                    hasOffset = True
                if top < 0:
                    yoffset = -top
                    top = 0
                    hasOffset = True
                if hasOffset:
                    enbackimg = Image.new("RGBA",(
                        backimg.size[0]+xoffset,
                        backimg.size[1]+yoffset
                        ))
                    enbackimg.paste(backimg,(xoffset,yoffset))
                else:
                    enbackimg = backimg
                newimg = mergePics(enbackimg,faceimg,left,top)
                
                newimg.save(localpicname)
                t1 = time.time()
                print("bg:",item["__name"],";face:",face["name"],";time:",t1-t0)