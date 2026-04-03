from flask import Flask, request, jsonify, render_template_string, session, redirect
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.secret_key = "securechatkey"
DB = "chat.db"


def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password TEXT,
        photo TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS messages(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        text TEXT,
        time TEXT,
        seen INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()


init_db()

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<title>Secure Chat Pro+</title>
<style>
body{margin:0;font-family:Arial;background:#0b141a;color:white}
.header{background:#202c33;padding:15px;display:flex;justify-content:space-between;align-items:center}
#chat{height:72vh;overflow-y:auto;padding:15px}
.msg{background:#005c4b;padding:10px;margin:10px 0;border-radius:12px;max-width:75%}
.time{font-size:11px;opacity:.7;margin-top:4px}
.input-box{position:fixed;bottom:0;width:100%;display:flex;background:#202c33;padding:8px;box-sizing:border-box}
input{flex:1;padding:12px;border:none;border-radius:8px}
button{padding:12px;margin-left:5px;background:#00a884;color:white;border:none;border-radius:8px}
#typing{font-size:12px;padding:0 15px;color:#9ca3af}
</style>
</head>
<body>
<div class=\"header\">🔥 Secure Chat Pro+ <span>🟢 Online</span></div>
<div id=\"typing\"></div>
<div id=\"chat\"></div>
<div class=\"input-box\">
<input id=\"msg\" placeholder=\"Type message 😊\" oninput=\"typing()\">
<button onclick=\"addEmoji()\">😊</button>
<button onclick=\"document.getElementById('fileInput').click()\">📎</button>
<button onclick=\"clearChat()\">🗑 Clear</button>
<button onclick=\"sendMsg()\">Send</button>
<input id=\"fileInput\" type=\"file\" style=\"display:none\" onchange=\"sendFile()\">
</div>
<script>
function loadMessages(){
 fetch('/messages').then(r=>r.json()).then(data=>{
   let chat=document.getElementById('chat');
   chat.innerHTML='';
   data.forEach(m=>{
     chat.innerHTML += `<div class=\"msg\"><b>${m.user}</b><br>${m.text}<div class=\"time\">${m.time} ${m.seen ? '✓✓' : '✓'}</div></div>`;
   });
   chat.scrollTop=chat.scrollHeight;
 });
}
function sendMsg(){
 let msg=document.getElementById('msg').value;
 fetch('/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})})
 .then(()=>{document.getElementById('msg').value='';loadMessages();});
}
function typing(){
 document.getElementById('typing').innerText='typing...';
 setTimeout(()=>document.getElementById('typing').innerText='',800);
}
function addEmoji(){
 document.getElementById('msg').value += ' 😊';
}
function sendFile(){
 let file=document.getElementById('fileInput').files[0];
 if(!file) return;
 let msg='📎 File shared: '+file.name;
 fetch('/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})})
 .then(()=>loadMessages());
}
function clearChat(){
 fetch('/clear',{method:'POST'}).then(()=>loadMessages());
}
function deleteMsg(id){
 fetch('/delete_message/'+id,{method:'POST'}).then(()=>loadMessages());
}
function replyMsg(user,text){
 let box=document.getElementById('msg');
 box.value = '↩️ Reply to '+user+': '+text+' ';
 box.focus();
}

function editMsg(id){
 let newText = prompt('Edit your message:');
 if(!newText) return;
 fetch('/edit_message/'+id,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:newText})}).then(()=>loadMessages());
}
setInterval(loadMessages,1000);
loadMessages();
</script>
</body>
</html>
"""

LOGIN_HTML = """
<!DOCTYPE html><html><body style='background:#0b141a;color:white;font-family:Arial;text-align:center;padding-top:100px'>
<h1>🔥 Secure Chat Login</h1>
<form method='POST' action='/login' enctype='multipart/form-data'>
<input name='username' placeholder='Username'><br><br>
<input name='password' type='password' placeholder='Password'><br><br>
<label style='display:block;margin-bottom:10px'>📷 Upload Profile Photo</label>
<input name='photo' type='file' accept='image/*'><br><br>
<button type='submit'>Login / Signup</button>
</form></body></html>
"""

@app.route('/')
def home():
    if 'username' not in session:
        return LOGIN_HTML
    return render_template_string(HTML)


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    photo = request.files.get('photo')
    photo_name = photo.filename if photo else ""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    row = c.fetchone()
    if row and row[0] != password:
        conn.close()
        return "Wrong password"
    if not row:
        c.execute("INSERT INTO users VALUES(?,?,?)", (username, password, photo_name))
        conn.commit()
    conn.close()
    session['username'] = username
    session['photo'] = photo_name
    return redirect('/')


@app.route('/send', methods=['POST'])
def send():
    data = request.json
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT INTO messages(username,text,time,seen) VALUES(?,?,?,?)",
        (session['username'], data['message'], datetime.now().strftime('%I:%M %p'), 1)
    )
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok'})


@app.route('/clear', methods=['POST'])
def clear_chat():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM messages")
    conn.commit()
    conn.close()
    return jsonify({'status':'cleared'})


@app.route('/messages')
def messages():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT username,text,time,seen FROM messages")
    rows = c.fetchall()
    conn.close()
    return jsonify([
        {'user': r[0], 'text': r[1], 'time': r[2], 'seen': bool(r[3])}
        for r in rows
    ])


@app.route('/delete_message/<int:msg_id>', methods=['POST'])
def delete_message(msg_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()
    return jsonify({'status':'deleted'})

@app.route('/edit_message/<int:msg_id>', methods=['POST'])
def edit_message(msg_id):
    data = request.json
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE messages SET text=? WHERE id=?", (data['message'], msg_id))
    conn.commit()
    conn.close()
    return jsonify({'status':'edited'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
