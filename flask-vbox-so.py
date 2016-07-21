#!/usr/bin/python
from flask import Flask, jsonify, abort, make_response, request
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
	return "Metodos en Python para la gestion de maquina virtuales a traves de Web Services usando Flask"

# item 1
# VBoxManage list ostypes | grep 'ID:          ' | cut -d ' ' -f11 | tr -s '\n' ' '
@app.route('/vms/ostypes',methods = ['GET'])
def ostypes():
	output = subprocess.Popen(['VBoxManage','list','ostypes'], stdout = subprocess.PIPE)
	

# item 2a
@app.route('/vms',methods = ['GET'])
def listvms():
	output = subprocess.check_output(['VBoxManage','list','vms'])
	return output

# item 2b
@app.route('/vms/running',methods = ['GET'])
def runningvms():
	output = subprocess.check_output(['VBoxManage','list','runningvms'])
	return output

# item 3
# VBoxManage list vms | grep -c 'name'
# VBoxManage showvminfo Win7 | grep 'Number of CPUs' | tr -s [:space:] ' ' | cut -d ':' -f2 | tr -d [:space:]
# VBoxManage showvminfo Win7 | grep 'Memory size' | tr -s [:space:] ' ' | cut -d ':' -f2 | tr -d [:space:]
# VBoxManage showvminfo Win7 | grep -c 'Attachment:'
@app.route('/vms/info/<string:vmname>', methods = ['GET'])
def vminfo(vmname):
	try:
		listvms = subprocess.Popen(['VBoxManage','list','vms'], stdout = subprocess.PIPE)
		existingvm = subprocess.check_output(["grep","-c",vmname], stdin = listvms.stdout)
		if int (existingvm) == 1:
			

			info = subprocess.Popen(['VBoxManage','showvminfo', vmname], stdout = subprocess.PIPE)
			Ncpu1 = subprocess.Popen(['grep', 'Number of CPUs'], stdin = info.stdout, stdout = subprocess.PIPE)
			Ncpu2 = subprocess.Popen(['tr', '-s', '[:space:]', " "], stdin = Ncpu1.stdout, stdout = subprocess.PIPE)
			Ncpu3 = subprocess.Popen(['cut', '-d', ':', '-f2'], stdin = Ncpu2.stdout, stdout = subprocess.PIPE)
			Ncpu = subprocess.check_output(['tr', '-d', '[:space:]'], stdin = Ncpu3.stdout)
			
			info2 = subprocess.Popen(['VBoxManage','showvminfo', vmname], stdout = subprocess.PIPE)
			Ms1 = subprocess.Popen(['grep', 'Memory size'], stdin = info2.stdout, stdout = subprocess.PIPE)			
			Ms2 = subprocess.Popen(['tr', '-s', '[:space:]', " "], stdin = Ms1.stdout, stdout = subprocess.PIPE)			
			Ms3 = subprocess.Popen(['cut', '-d', ':', '-f2'], stdin = Ms2.stdout, stdout = subprocess.PIPE)
			Ms = subprocess.check_output(['tr', '-d', '[:space:]'], stdin = Ms3.stdout)
			
			
			
			try:
				
				info3 = subprocess.Popen(['VBoxManage','showvminfo', vmname], stdout = subprocess.PIPE)
				NIC = subprocess.check_output(['grep', '-c', 'Attachment:'], stdin = info3.stdout)
			except subprocess.CalledProcessError as e:
				NIC = 0
			
			try:	
				info4 = subprocess.Popen(['VBoxManage','showvminfo', vmname], stdout = subprocess.PIPE)
				Nat1 = subprocess.Popen(['grep','Attachment:'], stdin = info4.stdout, stdout = subprocess.PIPE)	
				Nat	= subprocess.check_output(['grep', '-c', 'NAT'], stdin = Nat1.stdout)
			except subprocess.CalledProcessError as e:	
				Nat = 0
				
			try:	
				info5 = subprocess.Popen(['VBoxManage','showvminfo', vmname], stdout = subprocess.PIPE)
				Bridged1 = subprocess.Popen(['grep','Attachment:'], stdin = info5.stdout, stdout = subprocess.PIPE)	
				Bridged	= subprocess.check_output(['grep', '-c', 'Bridged'], stdin = Bridged1.stdout)
			except subprocess.CalledProcessError as e:
				Bridged = 0
				
			


			
			
			return jsonify({'name': vmname, 'CPUs': Ncpu,'Memory Size':Ms, 'Numero de Interfaces': int(NIC), 'Interfaces NAT':int (Nat),'Interfaces Bridge':int (Bridged)})

			
		if int (existingvm) == 0:
			abort(404)
	
	except subprocess.CalledProcessError as e:
		abort(404)

# item 4
#VM=$1
#ESPACIORAM=$2
#ESPACIODISCO=$3
#VBoxManage createhd --filename $VM.vdi --size $ESPACIODISCO
#VBoxManage createvm --name $VM --ostype "Ubuntu" --register
#VBoxManage storagectl $VM --name "SATA Controller" --add sata --controller IntelAHCI
#VBoxManage storageattach $VM --storagectl "SATA Controller" --port 0 --device 0 --type hdd --medium $VM.vdi
#VBoxManage modifyvm $VM --memory $ESPACIORAM --vram 128
@app.route('/vms/create', methods=['POST'])
def createvm():
	if not request.json or not 'name' in request.json or not 'ram' in request.json or not 'space' in request.json or not 'ostype' in request.json:
		abort(400)
		
	cmd1 = subprocess.check_output(['VBoxManage','createhd','--filename', request.json['name']+'.vdi', '--size', request.json['space']])
	cmd2 = subprocess.check_output(['VBoxManage','createvm','--name', request.json['name'], '--ostype', request.json['ostype'], '--register'])
	cmd3 = subprocess.check_output(['VBoxManage','storagectl', request.json['name'], '--name', "'SATA Controller'", '--add', 'sata', '--controller', 'IntelAHCI'])
	cmd4 = subprocess.check_output(['VBoxManage','storageattach', request.json['name'], '--storagectl', "'SATA Controller'", '--port', '0', '--device', '0', '--type', 'hdd', '--medium', request.json['name']+'.vdi'])
	cmd5 = subprocess.check_output(['VBoxManage','modifyvm', request.json['name'], '--memory', request.json['ram'], '--vram', '128'])
	
	return jsonify({'result': True}), 201

# item 5
# VBoxManage unregistervm vmname -delete
@app.route('/vms/delete/<vmname>', methods=['DELETE'])
def deletevm(vmname):
    task = [task for task in tasks if task['id'] == task_id]
    if len(task) == 0:
        abort(404)
    tasks.remove(task[0])
    return jsonify({'result': True})

@app.errorhandler(404)
def not_found(error):
 return make_response(jsonify({'error': 'Not found'}), 404)
 
@app.route('/vms', methods = ['GET'])
def listvms():
	vmslist = prcsshell("VBoxManage list vms | cut -d ' ' -f1 | tr -d '"+'"'+"'")
	vms = []
	for name in vmslist.split("\n"):
		if name != "": vms.append({'Name':name})
return jsonify(vms)

if __name__ == '__main__':
        app.run(debug = True, host='0.0.0.0')
