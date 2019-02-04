'''A few initial things are not included in my submitted script, and parts of the script are commented out. 
Not included in the script are me: copy and pasting the the complete angiosperm genus list from the website 
into a text document and removing leading whitespace and all genera starting with an 'x '. 
The cleaning was done in bash (sed 's/^[ \t]*//g' angiosperm_genus_list.txt|grep '^[A-Z]'|sed 's/[\(\)]//g' > angiosperm_genus_list_clean.txt).
'''


import time
import urllib
import pandas as pd
import os
from collections import defaultdict
import random
import socket
import stats

def make_family_genus(fg_file):

    with open(fg_file,'r') as fg:
        family_dict=defaultdict(list)
        for fg_line in fg.read().splitlines():
            genus_family=fg_line.split(' ')
            family_dict[genus_family[1]].append(genus_family[0])
    return family_dict

#print(make_family_genus('angiosperm_genus_list_clean.txt'))
 


def make_genus_list(family_genus_dict):
    
    family_list=[*family_genus_dict]

    random_families=random.sample(family_list,5)

    if 'Compositae' not in random_families:
        random_families.append('Compositae')

    genus_count=0

    while genus_count == 0:
        for random_family in random_families:
            genus_count=genus_count+len(family_genus_dict[random_family])
        if genus_count >2000:
            genus_count=0
        elif genus_count <300:
            genus_count=0
        random_families=random.sample(family_list,5)

    used_file=open('Families_Used.txt','w')
    genera=[]
    
    for family in random_families:
        used_file.write('%s\n'%family)
        for genus in family_genus_dict[family]:
           genera.append(genus)
    used_file.close()
    
    return genera

def fetch_genera(genus):
    '''I was actually unable to obtain all the files I wanted to because I kept on having a time out error. 
    I could not figure out if it was on my end or the website's end, and simply worked with what I could get
    for the sake of time'''
    
    try:
        handle=urllib.request.urlretrieve('http://www.theplantlist.org/tpl1.1/search?q=%s&csv=true'%genus,'%s_db.csv'%genus)

        time.sleep(8)
    except socket.timeout: #did not catch error correctly.
        return 'skipped %s'%genus
        pass
    return genus

def main():
    '''infile = 'angiosperm_genus_list_clean.txt'

    families = make_family_genus(infile)

    genera_used = make_genus_list(families)
    with open('Genera_Used.txt','w') as gu_file:

        for genus in genera_used:
            gu_file.write('%s\n'%genus)
            fetch_genera(genus)

    os.system("cat *db.csv >Genera_Database.csv")'''
    
    gdb=pd.read_csv('Genera_Database.csv',na_values='nan').drop_duplicates(keep=False) #remove headers from cat
    gdb=gdb[gdb['Date']!='Date']

    fix_date=gdb.replace({"[0-9]+ publ. ":""},regex=True)
    fix_dates=fix_date.replace({"[0-9]+-":""},regex=True)
    fix_dates[['Date']]=fix_dates[['Date']].astype(float) #so that we can 
    rm_hybrids_variants=fix_dates[fix_dates['Genus hybrid marker'].isnull() & fix_dates['Species hybrid marker'].isnull() & 
        fix_dates['Infraspecific rank'].isnull()]
    #hybrids and varieties/subspecies probably will probably inflate the name changes, etc. I am less interested in these when doing this
    #more general overview.
    working_db=rm_hybrids_variants[['ID','Family','Genus','Species','Taxonomic status in TPL','Nomenclatural status from original data source',
        'Date', 'Accepted ID']]

    #I will only be looking at accepted and synonyms for this project.

    accepted=working_db[working_db['Taxonomic status in TPL']=='Accepted'][['ID','Family','Genus','Species',
        'Taxonomic status in TPL','Nomenclatural status from original data source','Date']]
    synonym=working_db[working_db['Taxonomic status in TPL']=='Synonym']

    accepted.columns=['ID', 'Family', 'Genus','Species', 'Status', 'Original Status', 'Date']
    synonym.columns=['Syn ID', 'Syn Family', 'Syn Genus','Syn Species', 'Syn Status', 'Syn Original Status', 'Syn Date','Accepted ID']

   
    accepted_syn_db=pd.merge(accepted, synonym, left_on='ID',right_on='Accepted ID', how='outer') 
    accepted_syn_db['Time Diff']=abs(accepted_syn_db['Syn Date']-accepted_syn_db['Date'])
    accepted_syn_db=accepted_syn_db[accepted_syn_db['Time Diff']<300] #remove any bad dates--linaeus would be earliest in 1700s
    
    moved_family=accepted_syn_db[accepted_syn_db['Family'] != accepted_syn_db['Syn Family']]
    same_family=accepted_syn_db[accepted_syn_db['Family'] != accepted_syn_db['Syn Family']]
    moved_genus=accepted_syn_db[accepted_syn_db['Genus'] != accepted_syn_db['Syn Genus']]
    same_genus=accepted_syn_db[accepted_syn_db['Genus'] == accepted_syn_db['Syn Genus']]

    moved_family_not_genus=moved_family[moved_family['Genus'] == moved_family['Syn Genus']] #nobody did this

    species_syncount=accepted_syn_db.groupby(['ID','Genus','Family'])[['Syn ID']].count()

    genus_syncount=accepted_syn_db.groupby(['Genus','Family'])[['Syn ID']].count()

main()