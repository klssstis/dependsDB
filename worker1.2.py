import os
import json
import time
from bs4 import BeautifulSoup
import csv
import glob
import datetime
os.system('pip3 install requests')
os.system('pip3 install PyGithub')
os.system('pip3 install gensim')
os.system('apt-get install -y gh')
import requests
from github import Github
from github import Auth


import sys
try:
    token = sys.argv[1]
except IndexError:
    print("not all parameters")
    os._exit(0)



os.system('echo '+token+'| gh auth login -h github.com --with-token')

fileTitle = './results/title_corpus'
fileRepo = './results/repo_corpus'
if os.path.exists(fileTitle):
    with open(fileTitle) as f:
        title_corpus = f.read().split('_|_')
    title_corpus.pop()
else:
    title_corpus = []
if os.path.exists(fileRepo):
    with open(fileRepo) as f:
        repo_corpus = f.read().splitlines()
else:
    repo_corpus = []
stoplist = set('for a of the and to in'.split(' '))
texts = [[word for word in document.lower().split() if word not in stoplist]
         for document in title_corpus]
from collections import defaultdict
frequency = defaultdict(int)
for text in texts:
    for tkn in text:
        frequency[tkn] += 1

processed_corpus = [[tkn for tkn in text if frequency[tkn] > 1] for text in texts]
from gensim import corpora

dictionary = corpora.Dictionary(processed_corpus)
bow_corpus = [dictionary.doc2bow(text) for text in processed_corpus]
from gensim import models

tfidf = models.TfidfModel(bow_corpus)
from gensim import similarities

index = similarities.SparseMatrixSimilarity(tfidf[bow_corpus], num_features=len(dictionary))


t = datetime.datetime.today()
repoCSV = './results/repo_'+t.strftime('%Y%m%d')+'_hn.csv'
depCSV = './results/dep_'+t.strftime('%Y%m%d')+'_hn.csv'
repoCSVup = './results/repo_now_hn.csv'
depCSVup = './results/dep_now_hn.csv'
if os.path.exists(repoCSVup) and os.path.exists(depCSVup):
    os.system('cp '+repoCSVup+' '+repoCSV)
    os.system('cp '+depCSVup+' '+depCSV)

listURL = list()
for i in range(9):
    time.sleep(1)
    os.system('rm -rf /tmp/ghTMP')
    os.system('gh api -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" /search/repositories?q=language:java\&sort=updated\&per_page=100\&page='+str(i+1)+'> /tmp/ghTMP')
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
    orCountTMP = 0
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
                orCountTMP |= 2**int(i[0],16)
                break
        if flag==0:
            orCountTMP |= 2**(len(listCSV)-1)
            listCSV.append([str(len(listCSV)-1),grTMP,arTMP])

    with open(filenameCSV, 'w') as outcsv:
        writer = csv.writer(outcsv, lineterminator='\n')
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
        listCSV1 = [['user', 'repo', 'type', 'orcount']]
    flag = 0
    for i1 in listCSV1:
        if usTMP in i1 and rpTMP in i1:
            flag = 1
            break
    if flag == 1:
        continue
    try:
        os.system('rm -rf /tmp/works')
        os.system('git clone '+i+' /tmp/works')
        auth = Auth.Token(token)
        g = Github(auth=auth)
#    try:
        repo = g.get_repo(usTMP+"/"+rpTMP.split('.git')[0])
    except:
        print(usTMP+"/"+rpTMP)
        continue
    if not repo.description is None:
        query_document = repo.description.split()
        query_bow = dictionary.doc2bow(query_document)
        sims = index[tfidf[query_bow]]
        lRes = []
        maxScore = 0
        for document_number, score in sorted(enumerate(sims), key=lambda x: x[1], reverse=True):
            if maxScore == 0:
                maxScore = score
            if score>0.8:
                lRes.append(document_number)
        repoSIM = './results/repo_sim_'+t.strftime('%Y%m%d')+'.csv'
        if os.path.exists(repoSIM):
            with open(repoSIM, newline='') as f:
                reader = csv.reader(f)
                listSIM = list(reader)
        else:
            listSIM = [['user','repo','simTL','maxSC']]
        listSIM.append([usTMP,rpTMP,str(lRes),maxScore])
        with open(repoSIM, 'w') as outcsv:
            writer = csv.writer(outcsv,  lineterminator='\n')
            for item in listSIM:
                writer.writerow([item[0], item[1], item[2], item[3]])        
    orCountRepo=0
    tpTMP = 'unknown'
    flag = 0
    for file in glob.glob("/tmp/works/**/pom.xml",recursive=True):
        tpTMP ='pom.xml'
        atmp = depTocsv(file,depCSV)
        orCountRepo |= int(atmp)
        flag = 1
    if flag == 0:
        for file in glob.glob("/tmp/works/**/build.gradle", recursive=True):
            tpTMP = 'build.gradle'
    listCSV1.append([usTMP,rpTMP,tpTMP,hex(orCountRepo)])
    with open(repoCSV, 'w') as outcsv:
        writer = csv.writer(outcsv,  lineterminator='\n')
        for item in listCSV1:
            writer.writerow([item[0], item[1], item[2], item[3]])



os.system('cp '+repoCSV+' '+repoCSVup)
os.system('cp '+depCSV+' '+depCSVup)
