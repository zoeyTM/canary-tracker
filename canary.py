import requests, sqlite3, sys, pprint
from bs4 import BeautifulSoup

BASE_URL = 'https://www.canarywatch.org'

conn = sqlite3.connect('birdcage.sqlite')
cur = conn.cursor()

#cur.executescript('''DROP TABLE IF EXISTS Cage;DROP TABLE IF EXISTS Type;DROP TABLE IF EXISTS 'Last Checked' ''')
cur.executescript('''
CREATE TABLE IF NOT EXISTS 'Last Checked' (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    date TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS Type (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS Cage (
    organization TEXT UNIQUE,
    date_id INTEGER,
    type_id INTEGER,
    href TEXT UNIQUE,
    canary TEXT UNIQUE
)
''')

def update_birdcage(details):
    
    for canary in details:
        org, date, typ, href = canary.findChildren('li')
        org = org.text.split(': ', maxsplit=1)
        date = date.text.split(': ', maxsplit=1)
        typ = typ.text.split(': ', maxsplit=1)
        href = BASE_URL + href.a.get('href')

        cur.execute(
        '''INSERT OR IGNORE INTO Type (name) VALUES (?)''', (typ[1], ))
        cur.execute(
        '''SELECT id FROM Type WHERE name = ?''', (typ[1], ))
        type_id = cur.fetchone()[0]

        cur.execute(
        '''INSERT OR IGNORE INTO 'Last Checked' (date) VALUES (?)''', (date[1], ))
        cur.execute(
        '''SELECT id FROM 'Last Checked' WHERE date = ?''', (date[1], ))
        date_id = cur.fetchone()[0]

        cur.execute(
        '''INSERT OR IGNORE INTO Cage (organization, date_id, type_id, href) VALUES (?,?,?,?)''',
        (org[1], date_id, type_id, href))

        conn.commit()

def update_current_canaries():
    
    cur.execute('SELECT href FROM Cage')
    links = cur.fetchall()
    for link in links:
        url = link[0]
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'lxml')
        response.close()
        alles = soup.findAll('a',{'target':'_blank'})
        href = alles[0].get('href')

        cur.execute(
            '''UPDATE Cage SET canary = ? WHERE href = ?''', (href, url))
        conn.commit()
        
        

response = requests.get(BASE_URL)
soup = BeautifulSoup(response.content, 'lxml')
canaryDetails = soup.findAll('div', {'class':'canaryDetail'})

cur.execute('SELECT Count(*) FROM Cage')
db_num = cur.fetchone()[0]
web_num = len(canaryDetails)
lastPost = canaryDetails[0].ul.li.text
tmp = lastPost.split(': ', maxsplit=1)
tmp = tmp[1]
cur.execute('SELECT * FROM Cage WHERE organization = ?', (tmp, ))
answer = cur.fetchone()


if (db_num == web_num) and (answer != None):
    print('exiting')
    sys.exit(1)
else:
    update_birdcage(canaryDetails)
    update_current_canaries()
print('success')
