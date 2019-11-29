import requests
import urllib3
import ipaddress
import getpass
import xmltodict
import sys
import argparse
import time


def get_api_key():
    try:
        keygen=requests.get('https://'+fw_active+'/api/?type=keygen&user='+username+'&+password='+password,verify=False,timeout=10)
        if keygen.status_code == 200:
            key_dict=xmltodict.parse(keygen.text)
            key=key_dict['response']['result']['key']
            return key
        else:
            key_dict=xmltodict.parse(keygen.text)
            msg=key_dict['response']['result']['msg']
            return msg
    except requests.exceptions.ConnectTimeout:
        print('Connection timeout')
        sys.exit()

def getapikey(fw):
    try:
        keygen=requests.get('https://'+fw+'/api/?type=keygen&user='+username+'&+password='+password,verify=False,timeout=10)
        if xmltodict.parse(keygen.text)['response']['@status']=='success':
            return True
    except:
        return False
    

def ha_status(fw):
    ha_status=requests.get('https://'+fw+'/api/?type=op&cmd=<show><high-availability><state></state></high-availability></show>&key='+apikey,verify=False)
    ha_dict=xmltodict.parse(ha_status.text)
    return str(ha_dict['response']['result']['group']['mode'])


def os_check(fw):
    os_list=[]
    os_check=requests.get('https://'+fw+'/api/?type=op&cmd=<request><system><software><check></check></software></system></request>&key='+apikey,verify=False)
    os_check_dict=xmltodict.parse(os_check.text)
    for j in os_check_dict['response']['result']['sw-updates']['versions']['entry']:
        os_list.append(j['version'])
    return os_list

def download_os(fw):
    download_os=requests.get('https://'+fw+'/api/?type=op&cmd=<request><system><software><download><version>'+version+'</version></download></software></system></request>&key='+apikey,verify=False)
    if xmltodict.parse(download_os.text)['response']['@status']=='success':
        msg_download=xmltodict.parse(download_os.text)['response']['result']['msg']['line']
        jobid_download=xmltodict.parse(download_os.text)['response']['result']['job']
        return [jobid_download, msg_download]
    elif xmltodict.parse(download.os.text)['response']['@status'] == 'error':
        print(api_call_dict['response']['result']['msg'])
        sys.exit()

def job_status(fw,job_id):
    job_status=requests.get('https://'+fw+'/api/?type=op&cmd=<show><jobs><id>'+str(job_id)+'</id></jobs></show>&key='+apikey,verify=False)
    job_status_dict=xmltodict.parse(job_status.text)
    status=job_status_dict['response']['result']['job']['status']
    result=job_status_dict['response']['result']['job']['result']
    return [status,result]

def suspend_ha(fw):
    suspend_ha=requests.get('https://'+fw+'/api/?type=op&cmd=<request><high-availability><state><suspend></suspend></state></high-availability></request>&key='+apikey,verify=False)
    suspend_ha_dict=xmltodict.parse(suspend_ha.text)
    if suspend_ha_dict['response']['@status']=='success':
        return suspend_ha_dict['response']['result']
    elif suspend_ha_dict['response']['@status']=='error':
        print(suspend_ha_dict['response'])
        sys.exit()

def install_os(fw):
    install_os=requests.get('https://'+fw+'/api/?type=op&cmd=<request><system><software><install><version>'+version+'</version></install></software></system></request>&key='+apikey,verify=False)
    install_os_dict=xmltodict.parse(install_os.text)
    if install_os_dict['response']['@status'] == 'success':
        install_os_jobid=install_os_dict['response']['result']['job']
        install_os_msg=install_os_dict['response']['result']['msg']
        return [install_os_jobid,install_os_msg]
    elif install_os_dict['response']['@status'] == 'error':
        print(install_os_dict['response']['result']['msg'])
        sys.exit()

def ha_preempt(fw,preempt_value):
    api_call=requests.get('https://'+fw+'/api/?type=config&action=set&xpath=/config/devices/entry[@name="localhost.localdomain"]/deviceconfig/high-availability/group/election-option&element=<preemptive>'+preempt_value+'</preemptive>&key='+apikey,verify=False)
    api_call_dict=xmltodict.parse(api_call.text)
    return api_call_dict['response']['msg']


def commit(fw):
    api_call=requests.get('https://'+fw+'/api/?type=commit&cmd=<commit><partial><admin><member>'+username+'</member></admin><shared-object>excluded</shared-object><policy-and-objects>excluded</policy-and-objects></partial></commit>&key='+apikey,verify=False)
    api_call_dict=xmltodict.parse(api_call.text)
    if api_call_dict['response']['@status'] == 'success':
        return [api_call_dict['response']['result']['job'],api_call_dict['response']['result']['msg']['line']]
    elif api_call_dict['response']['@status'] == 'error':
        print(api_call_dict['response']['result']['msg'])
        sys.exit()

def sys_restart(fw):
    api_call=requests.get('https://'+fw+'/api/?type=op&cmd=<request><restart><system></system></restart></request>&key='+apikey,verify=False)
    pass

def verify_os(fw):
    api_call=requests.get('https://'+fw+'/api/?type=op&cmd=<show><system><info></info></system></show>&key='+apikey,verify=False)
    api_call_dict=xmltodict.parse(api_call.text)
    return str(api_call_dict['response']['result']['system']['sw-version'])




def main():
    global fw_active,fw_passive,username,password,apikey,version,jobstatus

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    username=input('enter the ADM username >')
    password=getpass.getpass('enter the ADM password >')
    version=str(input('enter the PAN OS version to upgrade the Firewall  >'))
    try:
        fw_active=str(ipaddress.IPv4Address(input('enter the active firewall IP address  >')))

    except ipaddress.AddressValueError:
        print('enter the valid IPv4 ip address')
    try:
        fw_passive=str(ipaddress.IPv4Address(input('enter the passive firewall IP address  >')))

    except ipaddress.AddressValueError:
        print('enter the valid IPv4 IP address')

    apikey=get_api_key()
    


    os_check_primary=os_check(fw_active)
    os_check_passive=os_check(fw_passive)


    fw_list=[fw_active,fw_passive]
    for i in fw_list:
            if version in os_check_primary and os_check_passive:
                print('Downloading the new OS version on'+' '+i)
                download=download_os(i)
                print(download[1])
                
                jobstatus=[]
                jobstatus.insert(0,'')
                jobstatus.insert(1,'')
                jobstatus=job_status(i,download[0])
                print('Checking the Job status,wait for sometime ')
                while (jobstatus[0] != 'FIN' and jobstatus[1] != 'OK'):
                    jobstatus=job_status(i,download[0])

                    if (jobstatus[0] == 'FIN' and jobstatus[1] == 'OK'):
                        print('Download completed on '+' '+i)

                    if jobstatus[1] == 'FAIL':
                        print('Download Failed on '+' '+i)
                        sys.exit()
            else:
                print(version+'  '+'is not available on the PAN firewalls')
                sys.exit()

    print('disabling the Preempt on Firewalls to avoid unnecessary fail-overs during the reboot')

    for i in fw_list:
        ha_preempt_status=ha_preempt(i,'no')
        print(ha_preempt_status+' '+'on'+' '+i)


    for i in fw_list:
        commit_status=commit(i)
        print('Commiting the changes after disabling the preempt on '+' '+i)
        jobstatus3=job_status(i,commit_status[0])

        while (jobstatus3[0] != 'FIN' and jobstatus3[1] != 'OK'):
            jobstatus3=job_status(i,commit_status[0])
            if (jobstatus3[0] == 'FIN' and jobstatus3[1] == 'OK'):
                print('Commit is completed on '+' '+i)
            if jobstatus3[1] == 'FAIL':
                print('Commit failed on '+' '+i)
                sys.exit()

    print('Suspending the HA on active firewall'+' '+fw_active)
    suspend_ha_active=suspend_ha(fw_active)
    print(suspend_ha_active)
    time.sleep(60)
    print('Installing the New OS on active_firewall'+' '+fw_active)
    install_os_active=install_os(fw_active)
    jobstatus2=job_status(fw_active,install_os_active[0])
    while jobstatus2[0] != 'FIN' and jobstatus2[1] != 'OK':
        jobstatus2=job_status(fw_active,install_os_active[0])
        if (jobstatus2[0] == 'FIN' and jobstatus2[1] == 'OK'):
            print('OS Installation is completed on '+' '+fw_active)
        if jobstatus2[1] == 'FAIL':
            print('Installation Failed on '+' '+fw_active)
            sys.exit()
    
    print('Rebooting the Active Firewall, wait for sometime')
    sys_restart(fw_active)
    time.sleep(240)
    
    while(True):
        if getapikey(fw_active):
            print('active firewall is up now')
            break
        else:
            print('firewall is still down')
            time.sleep(300)
            continue
    
    if version == verify_os(fw_active):
        print('Active Firewall came up with the new version')
    else:
        print('Upgrade is not successful on Active firewall')
        sys.exit()

    print('wait for sometime for HA state transition from init to active/passive')
    time.sleep(180)

    print('Suspending the HA on passive firewall'+' '+fw_passive)
    suspend_ha_passive=suspend_ha(fw_passive)
    print(suspend_ha_passive)
    time.sleep(60)
    print('Installing the New OS on passive_firewall'+' '+fw_passive)
    install_os_passive=install_os(fw_passive)
    jobstatus4=job_status(fw_passive,install_os_passive[0])
    while (jobstatus4[0] != 'FIN' and jobstatus4[1] != 'OK'):
        jobstatus4=job_status(fw_passive,install_os_passive[0])
        if (jobstatus4[0] == 'FIN' and jobstatus4[1] == 'OK'):
            print('OS Installation is completed on '+' '+fw_passive)

        if jobstatus4[1] == 'FAIL':
            print('Installation Failed on '+' '+fw_passive)
            sys.exit()
    
    print('Rebooting the passive firewall,wait for sometime')
    sys_restart(fw_passive)
    time.sleep(240)
    
    while(True):
        if getapikey(fw_passive):
            print('passive firewall is up now')
            break
        else:
            print('passive firewall is still down')
            time.sleep(300)
            continue

    print('wait for sometime for HA state transition from init to active/passive')
    time.sleep(180)   

    if version == verify_os(fw_passive):
        print('Passive Firewall came up with the new version')
    else:
        print('Upgrade is not successful on Passive firewall')
        sys.exit()

    print('Enable the HA Preempt on both the firewalls')
 
    for i in fw_list:
        ha_preempt_status=ha_preempt(i,'yes')
        print(ha_preempt_status+' '+'on'+' '+i)


    for i in fw_list:
        commit_status=commit(i)
        print('Commiting the changes after enabling the preempt on '+' '+i)
        jobstatus5=job_status(i,commit_status[0])

        while (jobstatus5[0] != 'FIN' and jobstatus5[1] != 'OK'):
            jobstatus5=job_status(i,commit_status[0])
            if (jobstatus5[0] == 'FIN' and jobstatus5[1] == 'OK'):
                print('Commit is completed on '+' '+i)
            if jobstatus5[1] == 'FAIL':
                print('Commit failed on '+' '+i)
                sys.exit()


    print('Firewall code upgrade is completed successfully')
    
    
if __name__ == '__main__':
    main()