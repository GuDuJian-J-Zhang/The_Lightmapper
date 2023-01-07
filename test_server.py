# save this as app.py
import subprocess
import os
from flask import Flask, jsonify, request, Response, stream_with_context, send_file
from flask_socketio import SocketIO, emit
import json
from gltflib import GLTF
import psutil
import time
import signal
from markupsafe import escape
import imageio

app = Flask(__name__)
#app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, logger=True, engineio_logger=True)


class EngineStatus:
    mbUseable = True
    mSid = ""
    cloudModel = ""
    mPid =""

engine_list = {}

master_slaves = {}

"""
set below four variables as your local setting
"""
appinfo_path = "C:/GWCPEngine/Render/build/bin/Debug/DeviceAssets/AppInfo_desktop.txt"
gm_path = "C:/GWCPEngine/Render/build/bin/Debug/CPRenderInstance.exe"
gltf_folder = "C:/SourceModels/GIDemoScenes/Room/Sponza/glTF"
lightmaps_folder = "C:/SourceModels/GIDemoScenes/Room/Blender/Lightmaps"
blender_path = "C:/Program Files/Blender Foundation/Blender 3.3/blender.exe"
clouding_rendering_result_path = "C:/GWCPEngine/Render/build/bin/Debug/files/CloudingRendering"

def modify_app_info(new_value):
    config_lines = []
    with open(appinfo_path, 'r', encoding='utf-8') as read_file:
        while True:
            # Get next line from file
            line = read_file.readline()
            if "-cloudmode" in line:
                line = '"-cloudmode"=\"' + new_value + "\"\n"
            if not line:
                break
            else:
                config_lines.append(line)
    read_file.close()

    with open(appinfo_path, 'w+') as write_file:
        for line in config_lines:
            write_file.write(line)
    write_file.close()

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
    file_info_list = []
    directories = os.listdir(lightmaps_folder)
    for file_name in directories:
        file_size = os.path.getsize(lightmaps_folder + "/" + file_name)
        file_info = {"name": file_name, "size": file_size}
        file_info_list.append(file_info)

    res = {
        'state': 0,
        'file_info_list': file_info_list
    }
    return res


@app.route("/baking_results/<file_name>", methods=['GET'])
def baking_result_(file_name):
    file_path = lightmaps_folder + "/" + file_name
    with open(file_path, 'rb') as my_file:
        content = my_file.read()
        return content


@app.route("/file/<file_name>", methods=['GET', 'HEAD'])
def download_file(file_name):
    file_folder = gltf_folder
    file_path = file_folder + "/" + file_name
    split_tup = os.path.splitext(file_name)
    ext = ""
    if len(split_tup) >= 2:
        ext = split_tup[1]
    if ext == ".gltf":
        if not os.path.exists(file_path+".glb"):
            gltf = GLTF.load(file_path)
            gltf.export_glb(file_path+".glb")
        return do_download(file_path + ".glb")
    else:
        return do_download(file_path)
        # with open(file_path, 'rb') as my_file:
        #     content = my_file.read()
        #     return content


@app.route("/file/CloudingRendering/<file_name>", methods=['GET', 'HEAD'])
def download_cloud_rendering_file(file_name):
    file_folder = clouding_rendering_result_path
    file_path = file_folder + "/" + file_name
    return do_download(file_path)


def read_file_in_chunks(file_path, chunk_size=1024 * 10):
    with open(file_path, 'rb') as my_file:
        while True:
            chunk = my_file.read(chunk_size)
            if chunk:
                yield chunk
            else:  # The chunk was empty, which means we're at the end of the file
                break #my_file.close()


def do_download(file_path):
    if request.method == "HEAD":
        file_size = os.path.getsize(file_path)
        resp = Response()
        resp.headers['Content-Length'] = file_size
        return resp
    else:
        return app.response_class(stream_with_context(read_file_in_chunks(file_path)))


@socketio.on('connect')
def on_connect():
    pid = request.values.get("pid")
    e = EngineStatus()
    e.mbUseable = True
    e.mSid = request.sid
    e.mPid = int(pid)
    engine_list[e.mPid]=e

    emit('message', {'data': ""})


@socketio.on('disconnect')
def on_disconnect():
    del engine_list[request.sid]
    print('Client disconnected')


"""
example for Bake command
{
    "Func": "Bake"
    "Params": {
        "ObjectIds": []
        ...other parameters for bakeing...
    }
}

example for StartEngine command
{
    "Func": "StartEngine"
    "Params": {
        "EngineType": "GM" or "Blender"
    }
}

example for Shutdown command
{
    "Func": "Shutdown"
    "Params": {
    }
}

example for SyncWithEngine command
{
    "Func": "SyncWithEngine"
    "Params": {
        "Sid": "TQq6uZgitUNVQOV4AAAC"
        "Type": "Camera",
        "Data": []
    }
}
"""
@socketio.on('dispatch')
def on_dispatch(msg):
    #emit('message', {"state": 0, "progress": "Baking"}, to=request.sid)
    func_and_params = json.loads(msg)
    func_name = func_and_params["Func"]
    if func_name == "Bake":
        emit('message', {"state": 0, "progress": "Baking"})
        return do_bake()
    elif func_name == "StartEngine":
        params = func_and_params["Params"]
        return do_start_engine(params)
    elif func_name == "Shutdown":
        return do_shutdown()
    else:
        return do_sync_status(msg)

@socketio.on('response')
def on_response(msg):
    do_response(msg)


@socketio.on('inquire')
def on_inquire(msg):
    func_and_params = json.loads(msg)
    func_name = func_and_params["Func"]
    params = func_and_params["Params"]
    if func_name == "GetEngineID":
        return do_get_enigne_id()


@socketio.on_error_default
def default_error_handler(e):
    print(request.event["message"]) # "my error event"
    print(request.event["args"])    # (data,)


def do_get_enigne_id():
    return


def do_bake():
    # pipe = subprocess.Popen([
    # blender_path,
    # "--background",
    # "--python", 'C:/BlenderStuff/addons/The_Lightmapper/test.py'
    # ],
    # shell=True,
    # stdout=subprocess.PIPE)
    #
    # stdout = pipe.communicate()[0]
    #
    # print(stdout)
    file_name = "Kitchen_baked_DIFFUSE.hdr"
    file_size = os.path.getsize(lightmaps_folder + "/" + file_name)
    return file_name, file_size


"""
{
    "EngineType": "GW" or "Blender" or 
}
"""
def do_start_engine(json_params):
    if json_params["EngineType"] == "GM":
        modify_app_info("server")
        pipe = subprocess.Popen([
            gm_path],
            shell=False,
            stdout=subprocess.PIPE)
        master_sid = request.sid
        slave_pid = pipe.pid
        time.sleep(2)
        modify_app_info("client")
        slaves = master_slaves.get(master_sid)
        if slaves is None:
            slaves = [slave_pid]
            master_slaves[master_sid] = slaves
        else:
            slaves.append(slave_pid)
        return slave_pid

    return 0


def do_shutdown():
    master_sid = request.sid
    slaves = master_slaves.get(master_sid)
    for pid in slaves:
        p = psutil.Process(pid)
        p.terminate()  # or p.kill()
    slaves = []


def do_sync_status(msg):
    master_sid = request.sid
    slaves = master_slaves.get(master_sid)
    if slaves is not None:
        for pid in slaves:
            engine = engine_list.get(pid)
            if engine is not None:
                emit('message', msg, to=engine.mSid)

def do_response(msg):
    slave_sid = request.sid
    # emit('response', msg, to=slave_sid)
    # return
    master_mid = None
    for key in master_slaves:
        value = master_slaves[key]
        for pid in value:
            engine = engine_list.get(pid)
            if engine is not None:
                if engine.mSid == slave_sid:
                    master_mid = key
                    break
        if master_mid is not None:
            emit('response', msg, to=master_mid)
            break

def get_lightmap_file_infos():
    return


if __name__=="__main__":
    socketio.run(app, allow_unsafe_werkzeug = True)