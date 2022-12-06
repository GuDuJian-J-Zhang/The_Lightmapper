# save this as app.py
import subprocess
import os
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
import json
from gltflib import GLTF
from markupsafe import escape
import imageio

app = Flask(__name__)
#app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, logger=True, engineio_logger=True)


@app.route("/bake", methods=['POST'])
def bake():
    baking = True
    # pipe = subprocess.Popen([
    #     "C:/Program Files/Blender Foundation/Blender 3.3/blender.exe",
    #     "--background",
    #     "--python", 'C:/BlenderStuff/addons/The_Lightmapper/test.py'
    # ],
    #     shell=True,
    #     stdout=subprocess.PIPE)
    #
    # stdout = pipe.communicate()[0]
    #
    # print(stdout)

    print("Baking finished...")

    res = {
        'state': 0,
        'msg': "Baking Finished"
    }
    return res


@app.route("/baking_results", methods=['GET'])
def baking_result():
    lightmap_folder = "C:/SourceModels/GIDemoScenes/Room/Blender/Lightmaps"
    file_info_list = []
    directories = os.listdir(lightmap_folder)
    for file_name in directories:
        file_size = os.path.getsize(lightmap_folder + "/" + file_name)
        file_info = {"name": file_name, "size": file_size}
        file_info_list.append(file_info)

    res = {
        'state': 0,
        'file_info_list': file_info_list
    }
    return res


def read_in_piece(file_name, piece_size=1024):
    # lazy function to read a file piece by piece. Default piece size: 1k
    with open(file_name, 'rb') as my_file:
        while True:
            content = my_file.read(piece_size)
            if content:
                yield content
            else:
                break


@app.route("/baking_results/<file_name>", methods=['GET'])
def baking_result_(file_name):
    lightmap_folder = "C:/SourceModels/GIDemoScenes/Room/Blender/Lightmaps"
    file_path = lightmap_folder + "/" + file_name
    with open(file_path, 'rb') as my_file:
        content = my_file.read()
        return content


@app.route("/file/<file_name>", methods=['GET'])
def download_file(file_name):
    file_folder = "C:/SourceModels/GIDemoScenes/Room/Blender"
    file_path = file_folder + "/" + file_name
    split_tup = os.path.splitext(file_name)
    ext = ""
    if len(split_tup) >= 2:
        ext = split_tup[1]
    if ext == ".gltf":
       return download_gltf(file_path)
    else:
        with open(file_path, 'rb') as my_file:
            content = my_file.read()
            return content


def download_gltf(file_path):
    gltf = GLTF.load(file_path)
    gltf.export_glb(file_path+".glb")
    with open(file_path+".glb", 'rb') as my_file:
        content = my_file.read()
        return content

@socketio.on('connect')
def on_connect():
    emit('my response', {'data': 'Connected'})


@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected')


@socketio.on('dispatch')
def on_dispatch(msg):
    print(msg)
    func_and_params = json.loads(msg)
    func_name = func_and_params["Func"]
    params = func_and_params["Params"]
    if func_name == "Bake":
        emit('message', {"state": 0, "progress": "Baking"})
        return do_bake()


        #emit('message', {"state": 0})


@socketio.on('inquire')
def on_inquire(message):
    emit('my response', {'data': message['data']})


@socketio.on_error_default
def default_error_handler(e):
    print(request.event["message"]) # "my error event"
    print(request.event["args"])    # (data,)


def do_bake():
    # pipe = subprocess.Popen([
    # "C:/Program Files/Blender Foundation/Blender 3.3/blender.exe",
    # "--background",
    # "--python", 'C:/BlenderStuff/addons/The_Lightmapper/test.py'
    # ],
    # shell=True,
    # stdout=subprocess.PIPE)
    #
    # stdout = pipe.communicate()[0]
    #
    # print(stdout)
    lightmap_folder = "C:/SourceModels/GIDemoScenes/Room/Blender/Lightmaps"
    file_name = "Kitchen_baked_DIFFUSE.hdr"
    file_size = os.path.getsize(lightmap_folder + "/" + file_name)
    return file_name, file_size


def get_lightmap_file_infos():
    return


if __name__=="__main__":
    socketio.run(app, allow_unsafe_werkzeug = True)