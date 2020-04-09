import sys
import os
import web
from web import form
import json
import csv
import operator

# for video explorer
types = {}
f = open('label_foodtype.csv', mode='r') 
reader = csv.reader(f)
types = dict((rows[0],rows[1]) for rows in reader)

vids = []
vid_files = ['train_list.txt','val_list.txt']
for vid_file in vid_files:
    fh = open(vid_file, mode='r')
    for vid in fh.readlines():
        parts = vid.split("/")
        vids.append(parts[1].strip()) 
    fh.close()

json_file = open('youcookii_annotations_trainval.json')
data = json.load(json_file)

# for keyframe score explorer
# training_keyframe_scores_file = "/mnt/sda1/youcookII/YouCookII/scripts/training_keyframe_scores_all.txt"
# validation_keyframe_scores_file = "/mnt/sda1/youcookII/YouCookII/scripts/validation_keyframe_scores_all.txt"
training_keyframe_scores_file = "static/training_keyframe_scores_all.txt"
validation_keyframe_scores_file = "static/validation_keyframe_scores_all.txt"

# training_keyframe_images_dir = "/mnt/sda1/youcookII/YouCookII/keyframes/training_copy_flat"
# validation_keyframe_images_dir = "/mnt/sda1/youcookII/YouCookII/keyframes/validation_copy_flat"

url = "http://localhost:8080/"

def print_video_info(data, video):
    vid_element = data['database'][video]
    print("video:", video) 
    print("subset:",vid_element['subset'], 'set')
    print("duration:",vid_element['duration'], 'seconds')
    print("video_url:",vid_element['video_url'])
    print("recipe_type:",types[vid_element['recipe_type']], "("+str(vid_element['recipe_type'])+")" )
    for i in vid_element['annotations']:
        print("  seg:", i['id'], "sec:", i['segment'][0], i['segment'][1], i['sentence'])

def get_video_info(data, video):
    vid_element = data['database'][video]
    output = []
    output.append("video_url: <a href=" + vid_element['video_url'] + '>' + vid_element['video_url'] + '</a><br>')
    output.append("share: <a href=http://" + web.ctx.host + "/view/" + video + ">http://" + web.ctx.host + "/view/" + video + "</a><br>")
    output.append("video: " +  video + "<br>")
    output.append("subset: " + vid_element['subset'] + ' set' + "<br>")
    output.append("duration: " + str(format(int(vid_element['duration']//60),"02d")) + ":" + str(format(int(vid_element['duration']%60), "02d")) + ' minutes ' + "<br>")
    output.append("recipe: " + types[vid_element['recipe_type']] + " (" + str(vid_element['recipe_type']) + ")<br>")
    for i in vid_element['annotations']:
        output.append("seg: " + str(i['id']) + 
            " span: " + str(format(int(i['segment'][0]//60),"02d")) + ":" + str(format(int(i['segment'][0]%60),"02d")) + " " + 
            str(format(int(i['segment'][1]//60),"02d")) + ":" + str(format(int(i['segment'][1]%60),"02d")) + " " + i['sentence'] +"<br>")
    return(output)

def get_recipe_name(data, video):
    vid_element = data['database'][video]
    return types[vid_element['recipe_type']]

def get_keyframes_sentences_and_scores(data, video):
    keyframes, vid_sentences, vid_scores = [], [], []
    vid_element = data['database'][video]
    subset = vid_element['subset']

    sentences = {}
    scores = {}
    filename = ''
    if subset == "training":
        filename = training_keyframe_scores_file
        pathname = url + "static/training/"
    elif subset == "validation":
        filename = validation_keyframe_scores_file
        pathname = url + "static/validation/"

    fh = open(filename, 'r')
    lines = fh.readlines()
    fh.close()

    for line in lines:
        line = line.strip()
        line = line.split(" ")
        score, image, sentence=line[0], line[1], line[2:]

        image = image.split("/")
        sub, vid, seg, img = image[-4], image[-3], image[-2], image[-1]

        index = "_".join([sub, vid, seg, img])
        sentences[index] = sentence
        scores[index] = float(score)

    for index in scores.keys():
        # print("DEBUG index, video:", index, video)
        start = subset + "_" + video
        if index.startswith(start):
            filename = index.lstrip(subset + "_")
            keyframes.append(pathname + filename)
            vid_sentences.append(sentences[index])
            vid_scores.append(scores[index])

    return keyframes, vid_sentences, vid_scores

recipe_types = []
for vid in vids:
    recipe_types.append(get_recipe_name(data, vid))

render = web.template.render('templates') # your templates
urls = ("/", "index", "/view/(.*)", "view", "/keyframe_scores/(.*)/(\d+)", "keyframe_scores")
app = web.application(urls, globals())

index_form = form.Form(
    form.Dropdown(name='video', args=zip(vids,[str(v)+"-"+str(i) for (i,v) in zip(vids,recipe_types)])),
    form.Button("submit", type="submit"),
)

class index:

    def GET(self):
        form = index_form()
        return render.index(form, None, None, None, None, None)

    def POST(self):
        form = index_form()
        form.validates()
        vid_info = get_video_info(data, form.d.video)

        keyframes,sentences,scores = get_keyframes_sentences_and_scores(data, form.d.video)
        # print("DEBUG video:", form.d.video)
        print("DEBUG keyframes, sentences, scores:", keyframes, sentences, scores)
        return render.index(form, form.d.video, vid_info, keyframes, sentences, scores)

class view:
    def GET(self, video):
        # form = index_form()
        # form.validates()
        form = web.form.Form(
            web.form.Dropdown(name='video', args=zip(vids,[str(v)+"-"+str(i) for (i,v) in zip(vids,recipe_types)]), value=video),
            web.form.Button("submit", type="submit"),
        )

        vid_info = get_video_info(data, video)
        keyframes,sentences,scores = get_keyframes_sentences_and_scores(data, form.d.video)

        return render.index(form, form.d.video, vid_info, keyframes, sentences, scores)

class keyframe_scores:

    def GET(self, subset="training", pagenum=1):

        if pagenum == None:
            pagenum = 1

        if subset == None:
            subset = "training"

        web.debug("DEBUG subset:", subset)
        web.debug("DEBUG pagenum:", pagenum)

        sentences = {}
        scores = {}

        filename = ''
        if subset == "training":
            filename = training_keyframe_scores_file
            pathname = url + "static/training/"
        elif subset == "validation":
            filename = validation_keyframe_scores_file
            pathname = url + "static/validation/"

        fh = open(filename, 'r')
        lines = fh.readlines()
        fh.close()

        for line in lines:
            line = line.strip()
            line = line.split(" ")
            score, image, sentence=line[0], line[1], line[2:]

            image = image.split("/")
            sub, vid, seg, img = image[-4], image[-3], image[-2], image[-1]

            index = "/".join([sub, vid, seg, img])
            sentences[index] = sentence
            scores[index] = float(score)

        sorted_indexes = sorted(scores.items(), key=operator.itemgetter(1))

        bottom = sorted_indexes[:10]
        top = sorted_indexes[-10:]
        # content = bottom + top

        # print("Bottom 10")
        # for i,v in bottom:
        #     print("<a href="+i+">"+i+"</a>", str(scores[i]), " ".join(sentences[i]))

        # print("Top 10")
        # for i,v in top:
        #     print("<a href="+i+">"+i+"</a>", str(scores[i]), " ".join(sentences[i]))

        content = []
        content.append("<div style='text-align: justify; width: 480px'><a href=" + url + "keyframe_scores/"+subset+"/"+str(1)+">begining</a>")
        content.append("&nbsp;<a href=" + url + "keyframe_scores/"+subset+"/"+str(int(pagenum)-1)+">previous</a>")
        content.append("&nbsp;<a href=" + url + "keyframe_scores/"+subset+"/"+str(int(pagenum)-10)+">-10</a>")
        content.append("&nbsp;<a href=" + url + "keyframe_scores/"+subset+"/"+str(int(len(scores)//10)//2)+">middle</a>")
        content.append("&nbsp;<a href=" + url + "keyframe_scores/"+subset+"/"+str(int(pagenum)+10)+">+10</a>")
        content.append("&nbsp;<a href=" + url + "keyframe_scores/"+subset+"/"+str(int(pagenum)+1)+">next</a>")
        content.append("&nbsp;<a href=" + url + "keyframe_scores/"+subset+"/"+str(int(len(scores)//10)+1)+">end</a>")
        if subset == "training":
            content.append(" - <a href=" + url + "keyframe_scores/validation/1>switch to validation</a>")
        else:
            content.append(" - <a href=" + url + "keyframe_scores/training/1>switch to training</a>")
        content.append("</div><br>")
        navigation = []
        navigation += content

        # for i,v in bottom + top:
        start = (int(pagenum)-1)*10
        for i,v in sorted_indexes[start:start+10]:
            
            image = i.split("/")
            sub, vid, seg, img = image[-4], image[-3], image[-2], image[-1]
            image_filename = vid + "_" + seg + "_" + img
            image = pathname + image_filename

            content.append("<a href='" + image + "'><img width='480px' src='"+image+"'></a><br>" + str(format(scores[i], ".8f")) + ", " + " ".join(sentences[i]) + "<br><br>")
        content += navigation

        return render.keyframe_scores(pagenum,content)


if __name__ == "__main__":
    app.run()

