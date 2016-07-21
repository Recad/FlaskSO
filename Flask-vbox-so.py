#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

from flask import Flask, jsonify, abort, make_response, request
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
  txt = "VirtualBox Manager WebService\n"
  txt += "-----------------------------------------\n"
  txt += "curl -i http://localhost:5000/\n"
  txt += "curl -i http://localhost:5000/vms/ostypes\n"
  txt += "curl -i http://localhost:5000/vms/ostypes/families\n"
  txt += "curl -i http://localhost:5000/vms/ostypes/families/<name>\n"
  txt += "curl -i http://localhost:5000/vms\n"
  txt += "curl -i http://localhost:5000/vms/running\n"
  txt += "curl -i http://localhost:5000/info/<name>\n"
  txt += "curl -i -X POST -H 'Content-Type: application/json' -d '{name:<str>, ostype:<str>"
  txt += ", space:<int>, ram:<int>, cpus:<int>}' http://localhost:5000/vms/create\n"
  txt += "curl -i -X PUT -H 'Content-Type: application/json' -d "
  txt += "'[{number:<int>, type:<str>}]' http://localhost:5000/vms/NICs/<name>\n"
  txt += "curl -i -X DELETE http://localhost:5000/vms/delete/<name>\n"
  txt += "curl -i -X PUT http://localhost:5000/vms/star/<name>\n"
  txt += "curl -i -X PUT http://localhost:5000/vms/stop/<name>\n"
  return txt

# item 1
@app.route('/vms/ostypes', methods = ['GET'])
def ostypes():
  cmd_1 = prcspopen("VBoxManage list ostypes | grep -v -e 'Family' -e '64 bit:'")
  cmd_2 = prcspopen("VBoxManage list ostypes | grep -v -e 'Family' -e '64 bit:'")
  names = _prcsshell("grep 'ID:' | cut -d ':' -f2 | sed 's/^[[:space:]]*//'", cmd_1).split("\n")
  descriptions = _prcsshell("grep 'tion:' | cut -d ':' -f2 | sed 's/^[[:space:]]*//'", cmd_2).split("\n")
  oslist = []
  for i in range(0,len(names)-1):
    oslist.append({'Name':names[i], 'Description':descriptions[i]})
  return jsonify({'ostyes':oslist})
  
# item *
@app.route('/vms/ostypes/families', methods = ['GET'])
def ostypes_families():
  osfamilies = prcsshell("VBoxManage list ostypes | grep 'Family ID:' | uniq | tr -d ' ' | cut -d ':' -f2")
  osfamilieslist = ["Other"]
  for name in osfamilies.split("\n"):
    if name != "" and name!="Other": osfamilieslist.append(name)
  return jsonify({'families':osfamilieslist})

# item *
@app.route('/vms/ostypes/families/<name>', methods = ['GET'])
def ostypes_familie(name):
  cmd_1 = prcspopen("VBoxManage list ostypes | grep -B2 'Family ID:   "+name+"' | grep -v 'Family'")
  cmd_2 = prcspopen("VBoxManage list ostypes | grep -B2 'Family ID:   "+name+"' | grep -v 'Family'")
  names = _prcsshell("grep 'ID:' | cut -d ':' -f2 | sed 's/^[[:space:]]*//'", cmd_1).split("\n")
  descriptions = _prcsshell("grep 'tion:' | cut -d ':' -f2 | sed 's/^[[:space:]]*//'", cmd_2).split("\n")
  oslist = []
  for i in range(0,len(names)-1):
    oslist.append({'Name':names[i], 'Description':descriptions[i]})
  return jsonify({'ostypes':oslist})

# item 2a
@app.route('/vms', methods = ['GET'])
def listvms():
  vmslist = prcsshell("VBoxManage list vms | cut -d ' ' -f1 | tr -d '"+'"'+"'")
  vms = []
  for name in vmslist.split("\n"):
    if name != "": vms.append({'Name':name})
    
  return jsonify({'vms':vms})

# item 2b
@app.route('/vms/running', methods = ['GET'])
def listrunningvms():
  vmslist = prcsshell("VBoxManage list runningvms | cut -d ' ' -f1 | tr -d '"+'"'+"'")
  vms = []
  for name in vmslist.split("\n"):
    if name != "": vms.append({'Name':name})
  return jsonify({'runningvms':vms})

# item 3
@app.route('/vms/info/<name>', methods = ['GET'])
def vminfo(name):
  if not existence(name): return error("The virtual machine not exist") #404 or 400
  cmd_1 = prcspopen("VBoxManage showvminfo '"+name+"' | grep 'Number of CPUs'")
  CPUs = _prcsshell("tr -s [:space:] ' ' | cut -d ':' -f2 | tr -d [:space:]", cmd_1)
  cmd_2 = prcspopen("VBoxManage showvminfo '"+name+"' | grep 'Memory size'")
  Ms = _prcsshell("tr -s [:space:] ' ' | cut -d ':' -f2 | tr -d [:space:]", cmd_2)
  try:
    nicslist = prcsshell("VBoxManage showvminfo '"+name+"' | grep 'Attachment:'").split("\n")
  except: nicslist = [""]
  nics = []
  for i in range(0,len(nicslist)-1):
    if foundin(nicslist[i], "NAT"): nictype="NAT"
    if foundin(nicslist[i], "Bridged"): nictype="Bridge adapter"
    if foundin(nicslist[i], "Host-only"): nictype="Host-only"
    nics.append({'Number':i+1, 'Type':nictype})
  return jsonify({'Name': name, 'CPUs': CPUs, 'Memory Size': Ms, "NICs Count":len(nicslist)-1, "NICs":nics})

# item 4
@app.route('/vms/create', methods=['POST'])
def createvm():
  if not request.json or not 'name' in request.json or not 'ostype' in request.json:
    abort(400)
  else:
    name = request.json['name']
    ostype = request.json['ostype']
  if 'space' in request.json: space = request.json['space']
  else: space = 8000
  
  if existence(name): return error("The virtual machine already exists")
  
  storagectl = "VBoxManage storagectl '"+name+"' --name 'SATA Controller' --add sata --controller IntelAHCI"
  storageattach = "VBoxManage storageattach '"+name+"' --storagectl 'SATA Controller'"
  storageattach = storageattach +" --port 0 --device 0 --type hdd --medium '"+name+".vdi'"

  try:  
    prcsshell("VBoxManage createhd --filename '"+name+".vdi' --size "+space)
  except: return error("There was a problem when creating the hard disk")
  try:
    prcsshell("VBoxManage createvm --name '"+name+"' --ostype '"+ostype+"' --register")
  except: 
    prcsshell("rm "+name+".vdi")
    return error("There was a problem when creating the virtual machine")
  try:
    prcsshell(storagectl)
  except: return error("There was a problem when creating the storagectl")
  try:
    prcsshell(storageattach)
  except: return error("There was a problem in storageattach")
  try:
    if 'ram' in request.json:
      prcsshell("VBoxManage modifyvm '"+name+"' --memory '"+request.json['ram']+"' --vram 128")      
  except:
    deletevm(name)
    return error("There was a problem when modifying the memory")
  try:
    if 'cpus' in request.json:
      prcsshell("VBoxManage modifyvm '"+name+"' --cpus '"+request.json['cpus']+"'")
  except:
    deletevm(name)
    return error("There was a problem when modifying the number of cpus")
  return jsonify({'result': True}), 201

# item 5
@app.route('/vms/delete/<name>', methods=['DELETE'])
def deletevm(name):
  if not existence(name): return error("The virtual machine not exist")
  try:
    prcsshell('VBoxManage unregistervm "'+name+'" -delete')
  except: return error("There was a problem removed the virtual machine")
  return jsonify({'result': True})

# item *
@app.route('/vms/NICs/<name>', methods=['PUT'])
def nicsvm(name):
  #none|null|nat|natnetwork|bridged|intnet|hostonly|generic
  if not existence(name): return error("The virtual machine not exist")
  try:
    for nic in request.json:
      prcsshell("VBoxManage modifyvm '"+name+"' --nic"+nic["number"]+" "+nic["type"])
  except: return error("There was a problem modifying the virtual machine")
  return jsonify({'result': True})

# item *
@app.route('/vms/star/<name>', methods=['PUT'])
def starvm(name):
  if not existence(name): return error("The virtual machine not exist")
  if running(name): return error("The virtual machine is already running")
  try:
    prcsshell('VBoxManage startvm "'+name+'"')
  except: return error("There was a problem starting the virtual machine")
  return jsonify({'result': True})

# item *
@app.route('/vms/stop/<name>', methods=['PUT'])
def stopvm(name):
  if not existence(name): return error("The virtual machine not exist")
  if not running(name): return error("The virtual machine is not running")
  try:
    prcsshell('VBoxManage controlvm "'+name+'" poweroff')
  except: return error("There was a problem stopping the virtual machine")
  code = "VBoxManage controlvm  reset"
  return jsonify({'result': True})

@app.errorhandler(404)
def not_found(error):
  return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400)
def not_found(error):
  return make_response(jsonify({'error': 'Bad Request'}), 400)

def error(msg):
  return jsonify({'error': msg}), 400

def existence(name):
  if foundin(prcsshell("VBoxManage list vms"), name): return True
  else: return False

def running(name):
  if foundin(prcsshell("VBoxManage list runningvms"), name): return True
  else: return False

def foundin(txt, code):
  try:
    if prcsshell("echo '"+txt+"' | grep -c '"+code+"'") >= 1: return True
    else: return False
  except: return False

def prcsshell(cmd):
  return subprocess.check_output(cmd, shell=True)
def _prcsshell(cmd, std):
  return subprocess.check_output(cmd, stdin=std.stdout, shell=True)
def prcspopen(cmd):
  return subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)

if __name__ == '__main__':
  app.run(debug = True, host='0.0.0.0')

