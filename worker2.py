import os
import json
import time
from bs4 import BeautifulSoup
import csv
import glob
import datetime

import sys
try:
    token = sys.argv[1]
except IndexError:
    print("not all parameters")
    os._exit(0)


os.system('echo '+token+'| gh auth login -h github.com --with-token')

t = datetime.datetime.today()
repoCSV = './results/repo_'+t.strftime('%Y%m%d')+'.csv'
depCSV = './results/dep_'+t.strftime('%Y%m%d')+'.csv'
repoCSVup = './results/repo_now_l.csv'
depCSVup = './results/dep_now_l.csv'
if os.path.exists(repoCSVup) and os.path.exists(depCSVup):
    os.system('cp '+repoCSVup+' '+repoCSV)
    os.system('cp '+depCSVup+' '+depCSV)


listURL = list()
for i in range(20):
    time.sleep(1)
    os.system('rm -rf /tmp/ghTMP')
    os.system('gh api -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" /search/repositories?q=language:java\&per_page=100\&page='+str(i+1)+'> /tmp/ghTMP')
    f = open('/tmp/ghTMP')
    data = json.load(f)
    if not 'items' in data:
        break
    if len(data['items']) ==0:
        break
    for j in data['items']:
        if not j['clone_url'] in listURL:
            listURL.append(j['clone_url'])
    f.close()

def depTocsv(fileNamePOM,filenameCSV):
    orCountTMP = []
    if os.path.exists(filenameCSV):
        with open(filenameCSV, newline='') as f:
            reader = csv.reader(f)
            listCSV = list(reader)
    else:
        listCSV = [['id', 'group', 'aritfact']]
    try:
        with open(fileNamePOM, 'r') as f:
            dxml = f.read()
        Bs_data = BeautifulSoup(dxml, "xml")
        b_unique = Bs_data.find_all('dependency')
    except:
        return 0
    for di in b_unique:
        grTMP = ''
        arTMP = ''
        if '<groupId>' in str(di) and '<artifactId>' in str(di):
            grTMP = str(di).split('<groupId>')[1].split('</groupId>')[0]
            arTMP = str(di).split('<artifactId>')[1].split('</artifactId>')[0]
        else:
            continue
        flag = 0
        for i in listCSV:
            if grTMP in i and arTMP in i:
                flag = 1
                if not int(i[0]) in orCountTMP:
                    orCountTMP.append(int(i[0]))
                break
        if flag==0:
            orCountTMP.append(len(listCSV)-1)
            listCSV.append([(len(listCSV)-1),grTMP,arTMP])

    with open(filenameCSV, 'w') as outcsv:
        writer = csv.writer(outcsv,  lineterminator='\n')
        for item in listCSV:
            if len(item)!=3:
                print(item)
            writer.writerow([item[0], item[1], item[2]])
    return orCountTMP

for i in listURL:
    usTMP = i.split('/')[3]
    rpTMP = i.split('/')[4]
    if os.path.exists(repoCSV):
        with open(repoCSV, newline='') as f:
            reader = csv.reader(f)
            listCSV1 = list(reader)
    else:
        listCSV1 = [['user', 'repo', 'type', 'listcount']]
    flag = 0
    for i1 in listCSV1:
        if usTMP in i1 and rpTMP in i1:
            flag = 1
            break
    if flag == 1:
        continue
    os.system('rm -rf /tmp/works')
    os.system('git clone '+i+' /tmp/works')
    tpTMP = 'unknown'
    flag = 0
    orCountRepo = []
    for file in glob.glob("/tmp/works/**/pom.xml",recursive=True):
        tpTMP ='pom.xml'
        atmp = depTocsv(file,depCSV)
        orCountRepo = orCountRepo+ atmp
        flag = 1
    if flag == 0:
        for file in glob.glob("/tmp/works/**/build.gradle", recursive=True):
            tpTMP = 'build.gradle'
    listCSV1.append([usTMP,rpTMP,tpTMP,str(sorted(list(set(orCountRepo))))])
    with open(repoCSV, 'w') as outcsv:
        writer = csv.writer(outcsv,  lineterminator='\n')
        for item in listCSV1:
            writer.writerow([item[0], item[1], item[2], item[3]])
#    os.system('git config --global http.postBuffer 524288000')
#    os.system('git config --local user.email \"klsst1nv0@gmail.com\"')
#    os.system('git config --local user.name \"klssstis\"')
#    os.system('git remote -v')
#    os.system('git add --all')
#    os.system('git commit -m \"local result\"')
#    os.system('git push "https://klssstis:'+token+'@github.com/klssstis/dependsDB.git" HEAD:main --force')


os.system('cp '+repoCSV+' '+repoCSVup)
os.system('cp '+depCSV+' '+depCSVup)
