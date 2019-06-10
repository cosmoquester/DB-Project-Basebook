from flask import render_template, Flask, request, make_response, jsonify
from flaskext.mysql import MySQL
from datetime import datetime
from hashlib import md5

import os

# app = Flask(__name__, static_url_path = "/static", static_folder = "static")
app = Flask(__name__)

app.config['MYSQL_DATABASE_USER'] = # mysql user
app.config['MYSQL_DATABASE_PASSWORD'] = # mysql password
app.config['MYSQL_DATABASE_DB'] = # mysql DB name
app.config['MYSQL_DATABASE_HOST'] = # mysql host

mysql = MySQL(app)
sessions = {}

def execute_sql(sql):
    connection = mysql.get_db()
    cur = connection.cursor()
    cur.execute(sql)

    if sql[:6]=='select':
        cur.close()

        return cur.fetchall()
    else:
        connection.commit()
        cur.close()


@app.route('/')
@app.route('/index')
def index():

    sess_id = request.cookies.get('SESSION_ID')

    if not sess_id or sess_id not in sessions:
        return '<script>alert("로그인 해주세요.");location.href="/login"</script>'

    sql = "select name, content, datetime, Post.pid, uid, profile, '{0}' in (select liker from Postlike where Post.pid=Postlike.pid), count(liker), uid='{0}' \
        from Post\
            join User on User.uid=Post.poster\
            left join Postlike on Post.pid=Postlike.pid\
            group by Post.pid\
            having uid = '{0}' or uid in (select friend from Friends where user='{0}')\
            order by datetime desc".format(sessions[sess_id])
    results = execute_sql(sql)
    posts = []

    for post in results:
        sql = "select uid, name, content, C.cid, '{0}' in (select liker from Commentlike CL where CL.pid=L.pid and CL.cid=L.cid), count(liker), uid='{0}' from User\
            join Comment C on commenter=uid\
            left join Commentlike L on C.pid=L.pid and C.cid=L.cid\
            group by C.cid, C.pid\
            having pid={1}\
            order by datetime".format(sessions[sess_id], post[3])
        comments = execute_sql(sql)

        if not comments: comments=(tuple(),)
        posts.append(post+(comments,))

    return render_template(
        'feed.html',
        posts=posts
    )

@app.route('/search', methods=["POST", "GET"])
def search():

    sess_id = request.cookies.get('SESSION_ID')

    if not sess_id or sess_id not in sessions:
        return '<script>alert("로그인 해주세요.");location.href="/login"</script>'

    sql = "select name, content, datetime, Post.pid, uid, profile, '{0}' in (select liker from Postlike where Post.pid=Postlike.pid), count(liker), uid='{0}' \
        from Post\
            join User on User.uid=Post.poster\
            left join Postlike on Post.pid=Postlike.pid\
            group by Post.pid\
            having content like '%{1}%' or name='{1}'\
            order by datetime desc".format(sessions[sess_id], request.args['command'])
    results = execute_sql(sql)
    posts = []

    for post in results:
        sql = "select uid, name, content, C.cid, '{0}' in (select liker from Commentlike CL where CL.pid=L.pid and CL.cid=L.cid), count(liker), uid='{0}' from User\
            join Comment C on commenter=uid\
            left join Commentlike L on C.pid=L.pid and C.cid=L.cid\
            group by C.cid, C.pid\
            having pid={1}\
            order by datetime".format(sessions[sess_id], post[3])
        comments = execute_sql(sql)

        if not comments: comments=(tuple(),)
        posts.append(post+(comments,))

    return render_template(
        'feed.html',
        posts=posts
    )

@app.route('/friends')
def friends():

    sess_id = request.cookies.get('SESSION_ID')

    if not sess_id or sess_id not in sessions:
        return '<script>alert("로그인 해주세요.");location.href="/login"</script>'

    sql = 'select name, friend from Friends, User where user="{}" and Friends.friend=User.uid'.format(sessions[sess_id])
    results = execute_sql(sql)
    
    return render_template(
        'friends.html',
        friends = results                                                                                                                                                                                                                                                                                                                                                                         
    )

@app.route('/mypage', methods=["GET", "POST"])
@app.route('/people', methods=["GET", "POST"])
def people():
    uid = request.args.get('uid')
    sess_id = request.cookies.get('SESSION_ID')
    oneself = False

    if not uid:
        if sess_id in sessions:
            uid = sessions[sess_id]
            oneself = True
        else:
            return '<script>alert("로그인 해주세요.");location.href="/login"</script>'
    elif sess_id in sessions and uid == sessions[sess_id]:
        oneself=True

    sql = 'select name, age, phone, profile from User where uid="{}"'.format(uid)
    results = execute_sql(sql)

    friends = ()
    if sess_id in sessions:
        friends = execute_sql('select friend from Friends where user="{}"'.format(sessions[sess_id]))

    if not results:
        return '<script>alert("잘못된 접근입니다.");location.href="/"</script>'

    name, age, phone, profile = results[0]

    return render_template(
        'person.html',
        name=name,
        age=age,
        phone=phone,
        profile=profile,
        uid=uid,
        oneself = oneself,
        isfriend = (uid,) in friends
    )

@app.route('/signup')
def signup():
    return render_template(
        'signup.html'
    )   

@app.route('/signup_request', methods=["POST"])
def signup_request():

    sql = "insert into User(uid, password, name, age, phone, profile) values ('{}', '{}', '{}', {}, '{}', 'default.png')".format(
        request.form['id'], request.form['pass'], request.form['name'], request.form['age'], request.form['phone'])
    execute_sql(sql)

    return '<script>location.href="/login"</script>'

@app.route('/login')
def login():

    return render_template(
        'login.html'
    )

@app.route('/login_request', methods=["POST"])
def login_req():
    
    results = execute_sql('select uid, password from User where uid="{}" and password="{}"'.format(request.form['id'], request.form['pass']))

    if results and results[0] == (request.form['id'], request.form['pass']):
        sess_id = md5((str(datetime.now()) + request.form['id']).encode()).hexdigest()
        resp = make_response('<script>location.href="/index"</script>')
        resp.set_cookie('SESSION_ID', sess_id)
        sessions[sess_id] = request.form['id']

    else:
        resp = '<script>alert("ID또는 비밀번호가 일치하지 않습니다.");location.href="/login"</script>'

    return resp

@app.route('/logout')
def logout():
    sess_id = request.cookies.get('SESSION_ID')

    if sess_id in sessions:
        del sessions[sess_id]
    
    resp = make_response('<script>location.href="/login"</script>')
    resp.set_cookie('SESSION_ID', '')

    return resp

@app.route('/write_post', methods=["POST"])
def write_post():
    sess_id = request.cookies.get('SESSION_ID')

    if not sess_id or sess_id not in sessions:
        return '<script>alert("로그인 해주세요.");location.href="/login"</script>'

    sql = "insert into Post(poster, content, datetime) values ('{}', '{}', now())".format(
        sessions[sess_id], request.form['post_cont']
    )
    execute_sql(sql)

    return '<script>location.href="/"</script>'

@app.route('/write_comment', methods=["POST"])
def write_comment():
    sess_id = request.cookies.get('SESSION_ID')

    if not sess_id or sess_id not in sessions:
        return '<script>alert("로그인 해주세요.");location.href="/login"</script>'

    sql = "insert into Comment(pid, content, commenter, datetime) values ('{}', '{}', '{}', now())".format(
        request.form['pid'], request.form['content'], sessions[sess_id]
    )
    execute_sql(sql)

    return '<script>location.href="{}"</script>'.format(request.headers.get("Referer"))

@app.route('/profile_update', methods=["POST"])
def profile_update():
    sess_id = request.cookies.get('SESSION_ID')
    f = request.files['profile_photo']
    fname = sessions[sess_id] + f.filename[f.filename.rfind('.'):]
    fpath = "./static/profiles/" + fname
    f.save(fpath)

    sql = "update User set profile='{}' where uid='{}'".format(fname, sessions[sess_id])
    execute_sql(sql)
    
    return '<script>location.href="/mypage"</script>'

@app.route('/add_friend', methods=["POST"])
def add_friend():
    sess_id = request.cookies.get('SESSION_ID')

    if not sess_id or sess_id not in sessions:
        return '<script>alert("로그인 해주세요.");location.href="/login"</script>'

    user = sessions[sess_id]
    sql = "insert into Friends(user, friend) values('{}', '{}')".format(user, request.form['uid'])
    execute_sql(sql)

    return '<script>location.href="/people?uid={}"</script>'.format(request.form['uid'])

@app.route('/delete_friend', methods=["POST"])
def delete_friend():
    sess_id = request.cookies.get('SESSION_ID')

    if not sess_id or sess_id not in sessions:
        return '<script>alert("로그인 해주세요.");location.href="/login"</script>'

    user = sessions[sess_id]
    sql = "delete from Friends where user='{}' and friend='{}'".format(user, request.form['uid'])
    execute_sql(sql)

    return '<script>location.href="/people?uid={}"</script>'.format(request.form['uid'])

@app.route('/like', methods=["POST"])
def like():
    sess_id = request.cookies.get('SESSION_ID')

    if not sess_id or sess_id not in sessions:
        return '<script>alert("로그인 해주세요.");location.href="/login"</script>'
    
    user = sessions[sess_id]

    if request.json['like']:
        sql = "insert into Postlike(pid, liker) values ({}, '{}')".format(request.json['pid'], sessions[sess_id])
    else:
        sql = "delete from Postlike where pid={} and liker='{}'".format(request.json['pid'], sessions[sess_id])
    execute_sql(sql)

    results = execute_sql('select count(*) from Postlike where pid="{}"'.format(request.json['pid']))

    return jsonify(liked=results[0][0])

@app.route('/likeC', methods=["POST"])
def likeC():
    sess_id = request.cookies.get('SESSION_ID')

    if not sess_id or sess_id not in sessions:
        return '<script>alert("로그인 해주세요.");location.href="/login"</script>'
    
    user = sessions[sess_id]

    if request.json['like']:
        sql = "insert into Commentlike(pid, cid, liker) values ({}, {}, '{}')".format(request.json['pid'], request.json['cid'], sessions[sess_id])
    else:
        sql = "delete from Commentlike where pid={} and cid={} and liker='{}'".format(request.json['pid'], request.json['cid'], sessions[sess_id])
    execute_sql(sql)

    results = execute_sql('select count(*) from Commentlike where pid="{}" and cid={}'.format(request.json['pid'], request.json['cid']))

    return jsonify(liked=results[0][0])

@app.route('/delete', methods=["POST", "GET"])
def delete():
    sess_id = request.cookies.get('SESSION_ID')

    if not sess_id or sess_id not in sessions:
        return '<script>alert("로그인 해주세요.");location.href="/login"</script>'
    
    user = sessions[sess_id]

    execute_sql("delete from Comment where pid={}".format(request.json['pid']))
    execute_sql("delete from Post where pid={} and poster='{}'".format(request.json['pid'], user))

    return 'OK'

@app.route('/deleteC', methods=["POST", "GET"])
def deleteC():
    sess_id = request.cookies.get('SESSION_ID')

    if not sess_id or sess_id not in sessions:
        return '<script>alert("로그인 해주세요.");location.href="/login"</script>'
    
    user = sessions[sess_id]

    execute_sql("delete from Comment where pid={} and cid={}".format(request.json['pid'], request.json['cid']))

    return 'OK'

@app.route('/delete_account', methods=["POST"])
def delete_acc():
    sess_id = request.cookies.get('SESSION_ID')

    if not sess_id or sess_id not in sessions:
        return '<script>alert("로그인 해주세요.");location.href="/login"</script>'
    
    user = sessions[sess_id]

    execute_sql("delete from Comment where commenter='{0}' or pid in (select pid from Post where poster='{0}')".format(user))
    execute_sql("delete from Post where poster='{}'".format(user))
    execute_sql("delete from Friends where user='{0}' or friend='{0}'".format(user))
    execute_sql("delete from User where uid='{}'".format(user))

    return '<script>alert("계정 삭제가 완료되었습니다");location.href="/login"</script>'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)