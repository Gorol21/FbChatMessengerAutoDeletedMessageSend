import json,fbchat,threading,secrets
import mysql.connector
from fbchat import Client
from fbchat.models import *
thread_id = ""
thread_type = ""
cookies = {}
def usun(z):
    removeSpecialChars = z.translate({ord(c): " " for c in "\"\'`"})
    return(removeSpecialChars)
def sql(sql_text, sql_type):
    mydb = mysql.connector.connect(
        host=host,
        user="root",
        password=hostpassword,
        database=baza
    )
    try:
        mycursor = mydb.cursor()
        mycursor.execute(sql_text)
        if sql_type == "DATA":
            myresult = mycursor.fetchall()
            if myresult == []:
                return(0)
            else:
                return(myresult)
        if sql_type == "SELECT":
            myresult = mycursor.fetchall()
            if myresult == []:
                return(0)
            else:
                return(1)
        if sql_type == "DELETE":
            mydb.commit()
            return(mycursor.rowcount)
        if sql_type == "UPDATE":
            mydb.commit()
            return(mycursor.rowcount)
        if sql_type == "INSERT":
            mydb.commit()
            return(mycursor.rowcount)
    except Exception as s:
        print("Wystąpił błąd %s"%(s))
def check_link_name(code):
    return(sql("""SELECT * FROM `message_object` WHERE `mentions_hash`='{}'""".format(code),"SELECT"))
def add_ozn(user_hash,user_id,user_name,offset):
    return(sql("""INSERT INTO `message_mention`(`hash`,`user_id` ,`mention_name`, `offset`) VALUES ('{}','{}','{}','{}')""".format(user_hash,user_id,user_name,offset),"INSERT"))
def create_code():
    code = secrets.token_hex(10)
    if check_link_name(code) == 0:
        return(code)
    else:
        create_code()
def add_message(message_object):
    client = message_object[0]
    medianame = 'None'
    link = 'None'
    thread_type = 'None'
    if message_object[3] == ThreadType.USER:
        thread_type = 'ThreadType.USER'
    if message_object[3] == ThreadType.GROUP:
        thread_type = 'ThreadType.GROUP'
    if message_object[1].attachments != []:
        lol = message_object[1].attachments[0].__class__
        if lol == ImageAttachment:
            medianame = message_object[1].attachments[0].original_extension
            if message_object[1].attachments[0].original_extension == "gif":                
                link = message_object[1].attachments[0].animated_preview_url
            else:
                link = message_object[1].attachments[0].large_preview_url
        elif lol == AudioAttachment:
            link = message_object[1].attachments[0].url.replace("&dl=1","")
            medianame = message_object[1].attachments[0].filename     
    if message_object[1].sticker:
        sticker = message_object[1].sticker.uid
    else:
        sticker = None
    mentions_code = create_code()
    if message_object[1].text == None:
        sql("INSERT INTO `message_object`(`text`, `mentions_hash`, `emoji_size`, `u_id`, `author`, `timestamp`, `reactions`, `sticker`, `attachments`,`value`,`thread_id`, `thread_type`) VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(message_object[1].text,mentions_code,message_object[1].emoji_size,message_object[1].uid,message_object[1].author,message_object[1].timestamp,'None',sticker,link,medianame,message_object[2],thread_type),"INSERT")
    else:
        
        sql("INSERT INTO `message_object`(`text`, `mentions_hash`, `emoji_size`, `u_id`, `author`, `timestamp`, `reactions`, `sticker`, `attachments`,`value`,`thread_id`, `thread_type`) VALUES ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(u"{}".format(usun(message_object[1].text)),mentions_code,message_object[1].emoji_size,message_object[1].uid,message_object[1].author,message_object[1].timestamp,'None',sticker,link,medianame,message_object[2],thread_type),"INSERT")
    if message_object[1].mentions:     
        for x in message_object[1].mentions:
            add_ozn(mentions_code,x.thread_id,x.length,x.offset)
def check_wiadomosc_data(message_id,thread_type,thread_id,author_id):
   return(sql("""SELECT * FROM `message_object` WHERE `u_id`='{}' AND `thread_type`='{}' AND `thread_id`='{}' AND `author`='{}'""".format(message_id,thread_type,thread_id,author_id),"DATA"))
def check_mentions(hash):
    return(sql("""SELECT * FROM `message_mention` WHERE `hash`='{}'""".format(hash),"DATA"))
def deleted_message(message_object):
    client = message_object[0]
    try:
        wiadomosc = check_wiadomosc_data(message_object[1],message_object[4],message_object[3],message_object[2])[0]
        if wiadomosc[12] == "ThreadType.USER":
            thread_type = ThreadType.USER
        if wiadomosc[12] == "ThreadType.GROUP":
            thread_type = ThreadType.GROUP
            
        data = check_mentions(wiadomosc[2])
        if not isinstance(data,int):
            if len(data) > 0: 
                memtn = []
                for inf in data:
                    memtn.append(Mention(int(inf[2]),int(inf[3])+20,int(inf[4])))
                client.send(Message(("Usunięta wiadomość: {} ".format(wiadomosc[1])),memtn),message_object[3],thread_type)
        else:
            if wiadomosc[10] == 'png' or wiadomosc[10] == 'jpg':
                client.sendRemoteImage(wiadomosc[9], "Usunięte zdjęcie;",message_object[3],thread_type)
            elif wiadomosc[10] == 'gif':
                client.sendRemoteImage(wiadomosc[9], "Usunięty gif;",message_object[3],thread_type)
            elif wiadomosc[10][0:9] == 'audioclip':
                client.sendRemoteVoiceClips(wiadomosc[9],"Usunięta wiadomość głsoowa;",message_object[3],thread_type)
            else:
                if wiadomosc[8] != 'None':
                    if wiadomosc[4] != 'None':
                        client.send(Message(sticker=Sticker(wiadomosc[8])),message_object[3],thread_type)
                    else:
                        client.send(Message(sticker=Sticker(wiadomosc[8])),message_object[3],thread_type)
                else:
                    client.send(Message("Usunięta wiadomość: {}".format(wiadomosc[1])),message_object[3],thread_type)
    except Exception as s:
        client.send(Message("Wystąpił błąd z przechwytywaniem wiadomości: {}".format(s)),message_object[3],thread_type)
        
class Bot(Client):


    def mentions(self, thread_id):
        thread = list(self.fetchThreadInfo(thread_id)[thread_id].participants)
        mention = []
        for i in range(len(thread)):
            mention.append(Mention(thread[i], 0, 9))
        return mention


    def onListenError(self, exception=None):
        print(exception)
        if self.isLoggedIn():
            pass
        else:
            self.login(email, password)
    def onMessageUnsent(self, mid=None, author_id=None, thread_id=thread_id, thread_type=thread_type, ts=None, msg=None):
        send = [(self,mid,author_id,thread_id,thread_type)]

        threading.Thread(target=deleted_message, args=((send))).start()  

    def onMessage(self, mid=None, author_id=None, message=None, message_object=None, thread_id=thread_id,
                  thread_type=ThreadType.GROUP, ts=None, metadata=None, msg=None):
        add_message((client,message_object,thread_id,thread_type))

if __name__ == '__main__':
    print("Startuję...")
    try:
        with open('config.json', 'r') as f:
            conf = json.load(f)
            email  = conf['fblogin'] 
            password = conf['fbpass'] 
            host =  conf['host'] 
            hostpassword = conf['hostpass']
            baza = conf['base']
    except:
        config = []
        print("Facebook login: ")
        email = input()
        print("Facebook Password: ")
        password = input()
        print("Database host(Normally: localhost): ")
        localhost = input()
        print("Database Password: ")
        passhost = input()
        print("Database(Normally: delete_messages): ")
        base = input()
        config =  {
            'fblogin' :  email,
            'fbpass' : password,
            'host'  : localhost,
            'hostpass' :  passhost,
            'base' : base,
        }
        with open('config.json', 'w') as f:
            json.dump(config, f)
    try:
        with open('session.json', 'r') as f:
            cookies = json.load(f)
            print("Znalezino sesję.")
    except:
        print("Nie znelezino sesji, logowanie...")
        pass
    print("Trwa logowanie...")
    try:
        client = Bot(email, password, session_cookies=cookies, logging_level=20)
        with open('session.json', 'w') as f:
            json.dump(client.getSession(), f)
        client.listen()
    except Exception as s:
        print("Wystąpił błąd: {}, sprawdź plik konfiguracyjny.".format(s))
