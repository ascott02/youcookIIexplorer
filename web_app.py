import web
from web import form
import json
import csv

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

recipe_types = []
for vid in vids:
    recipe_types.append(get_recipe_name(data, vid))

render = web.template.render('templates') # your templates
urls = ("/", "index")
app = web.application(urls, globals())

index_form = form.Form(
    form.Dropdown(name='video', args=zip(vids,[str(v)+"-"+str(i) for (i,v) in zip(vids,recipe_types)])),
    form.Button("submit", type="submit"),
)

class index:
    def GET(self):
        form = index_form()
        return render.index(form, None, None)

    def POST(self):
        form = index_form()
        form.validates()
        vid_info = get_video_info(data, form.d.video)
        # print("DEBUG video:", form.d.video)
        return render.index(form, form.d.video, vid_info)

if __name__ == "__main__":
    app.run()

