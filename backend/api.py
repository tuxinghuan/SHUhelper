"""
Define all api
"""

import datetime
import json
import os.path as op
import random

from flask import Flask, Response, jsonify, request, session, flash, render_template

import empty_room
import find_free_time
import schooltime
from adminview import *
from client import *
from config import CACHE, app
from flask_admin import Admin
from flask_admin.contrib.fileadmin import FileAdmin
from flask_admin.contrib.mongoengine import ModelView
from flask_login import LoginManager, login_required, login_user
import flask_login
from flask_babelex import Babel
from models import *
import adminview as av


app.config.from_pyfile('config.py')

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(card_id):
    return User.objects(card_id=card_id).first()

babel = Babel(app)
app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'
# mail = Mail(app)
"""
admin view start 
"""
admin = Admin(app, name='SHUhelper', template_mode='bootstrap3')
admin.add_view(av.UserView(User))
admin.add_view(av.UserDataView(UserData))
admin.add_view(av.MessagesView(Messages))
admin.add_view(av.BasicPrivateModelView(Sweetie))
admin.add_view(av.BasicPrivateModelView(SecurityMap))
admin.add_view(av.BasicPrivateModelView(WoodsHole))
admin.add_view(av.BasicPrivateModelView(Functions))
admin.add_view(av.BasicPrivateModelView(MessageBoard))
admin.add_view(av.PostView(Post))
path = op.join(op.dirname(__file__), 'static')
admin.add_view(av.BasicPrivateFileAdminView(path, '/static/', name='Static Files'))
admin.add_link(av.NotAuthenticatedMenuLink(name='登录',
                                            endpoint='login_view'))
admin.add_link(av.AuthenticatedMenuLink(name='注销',
                                         endpoint='logout_view'))
"""
end adminview defines
"""



PUBLICATIONS = ['123']

def token():
    """
    generate random token, lenth is 8.
    """
    import random
    import string
    seed = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    sa = []
    for i in range(8):
        sa.append(random.choice(seed))
    salt = ''.join(sa)
    return salt

def validate(card_id, password):
    client = Services()
    client.card_id = card_id
    client.password = password
    if client.login() and client.get_data():
        result = {
            'success': True,
            'name': client.data['name'],
            'card_id': card_id
        }
    else:
        result = {
            'success': False
        }
    return result

@app.route('/login', methods=['GET','POST'])
def login_view():
    if request.method == 'POST':
            card_id = request.form['card_id']
            password = request.form['password']
            user = User.objects(card_id=card_id).first()
            result = validate(card_id, password)
            if result['success']:
                if user == None or not av.has_auth(user.role, 'basic'):
                    flash('无权限')
                    return redirect('/admin')
                flask_login.login_user(user)
            else:
                user = User()
            return redirect('/admin')
    else:
        return redirect(url_for('admin.index'))

@app.route('/logout')
def logout_view():
    flask_login.logout_user()
    return redirect(url_for('admin.index'))

@app.route('/')
@login_required
def test():
    """
    just a test
    """
    return 'hey~it\'s working'

@app.route('/messages/<oid>', methods=['GET'])
@login_required
def read_message(oid):
    message = Messages.objects(id=usoider).first()
    message.is_read = True
    message.save()
    return jsonify({'success':True})

@app.route('/messages/inbox', methods=['GET'])
@login_required
def get_inbox_messages():
    """
    not enabled yet, for private messages and publication and paper airplane and so on...
    """
    card_id = current_user.card_id
    user = User.objects(card_id=card_id).first()
    messages = Messages.objects(receiver=user)
    return jsonify(messages)

@app.route('/messages/outbox', methods=['GET'])
@login_required
def get_outbox_messages():
    """
    not enabled yet, for private messages and publication and paper airplane and so on...
    """
    card_id = current_user.card_id
    user = User.objects(card_id=card_id).first()
    messages = Messages.objects(sender=user)
    return jsonify(messages)

@app.route('/messages/new', methods=['POST'])
@login_required
def send_message():
    post_data = json.loads(request.get_data().decode('utf-8'))
    receiver = User.objects(card_id=post_data['receiver']).first()
    if receiver == None:
        return jsonify({
            'success': False,
            'status': 'Ta 还未使用过Helper，所以无法向TA传达您的消息。'
        })
    sender = User.objects(card_id=current_user.card_id).first()
    title = post_data['title']
    content = post_data['content']
    message = Messages(title=title, content=content, sender=sender, receiver=receiver)
    message.save()
    return jsonify({'success': True})

@app.route('/publications')
def publication():
    """
    get publications from db
    """
    return random.choice(PUBLICATIONS)

@app.route('/sweetie')
def random_sweetie():
    """
    a sweet word, wish you a good day
    """
    if CACHE.get('sweetie') == None:
        CACHE.set('sweetie', Sweetie.objects(visible=True), timeout=3000)
    sweetie = CACHE.get('sweetie')
    return random.choice(sweetie).content

@app.route('/functions')
def get_functions():
    """
    get functions list for index page, havn't enabled now
    """
    functions = Functions.objects()
    result = []
    for function in functions:
        result.append({ 
            'tittle': function.tittle,
            'icon': function.icon,
            'url': function.url,
            'desc':function.desc
        })
    return jsonify(result)

@app.route('/accounts/login', methods=['POST'])
def login():
    """
    use services.shu.edu.cn to validate user login
    """
    post_data = json.loads(request.get_data().decode('utf-8'))
    client = Services()
    client.card_id = post_data['card_id']
    client.password = post_data['password']
    if client.login() and client.get_data():
        user = User.objects(card_id=post_data['card_id']).first()
        if user == None:
            user = User(name=client.data['name'], nickname=client.data['nickname'], card_id=post_data['card_id'],role='student')
        user.token = token()
        result = {
            'success': True,
            'token': user.token,
            'name': user.name,
            'nickname': user.nickname
        }
        session['card_id'] = user.card_id
        CACHE.set(user.token, post_data['card_id'], timeout=86400)
        user.save()
        flask_login.login_user(user)
    else:
        result = {
            'success': False,
        }
    return jsonify(result)

@app.route('/accounts/logout')
def logout():
    """
    pop the cardID if in session
    """
    token = request.args.get('token')
    CACHE.delete(token)
    session.pop('card_id', None)
    flask_login.logout_user()
    return jsonify({
        'success': True
    })
@app.route('/accounts/login-with-token')
def token_login():
    """
    use token to verify user, token expired in 2 days
    """
    token = request.args.get('token')
    if CACHE.get(token) != None:
        card_id = CACHE.get(token)
        CACHE.set(token, card_id, timeout=86400)
        session['card_id'] = card_id
        user = User.objects(card_id=card_id).first()
        login_user(user)
        result = {
            'success': True,
            }
    else:
        result = {
                'success': False,
                'status':'token_expired'
            }
    return jsonify(result)

@app.route( '/accounts/update')
def update_account():
    """
    not enabled yet
    """
    post_data = json.loads(request.get_data().decode('utf-8'))
    card_id = session['card_id']
    user = User.objects(card_id=post_data['card_id']).first()
    user.email = post_data['email']
    user.phone = post_data['phone']
    user.save()
    result = {
        'success': True
    }
    return json.dumps(result)

@app.route('/accounts/clear')
def delete_account():
    """
    considering
    """
    # later
    pass

@app.route('/messageboard',methods=['POST', 'GET'])
def message_board():
    if request.method == 'GET':
        messages_set = MessageBoard.objects().order_by('-create_time')
        messages = []
        for message in messages_set:
            messages.append({
                'name':message.name,
                'content':message.content
            })
        return jsonify(messages)
    else:
        post_data = json.loads(request.get_data().decode('utf-8'))
        message = MessageBoard(name=post_data['name'],content=post_data['content'])
        message.save()
        return jsonify({'success':True})

@app.route('/woods-hole',methods=['POST', 'GET'])
def woods_hole():
    if request.method == 'GET':
        page = int(request.args.get('page'))
        messages_set = WoodsHole.objects().order_by('-create_time').paginate(page=page, per_page=10)
        messages = []
        for message in messages_set.items :
            messages.append({
                'id': str(message.id),
                'content': message.content,
                'like': message.like,
                'time': message.create_time,
                'comments': len(message.comments)
            })
        return jsonify(messages)
    else:
        post_data = json.loads(request.get_data().decode('utf-8'))
        message = WoodsHole(title=post_data['title'],content=post_data['content'])
        message.save()
        return jsonify({'success':True})

@app.route('/woods-hole/<oid>', methods=['GET', 'POST'])
def get_or_add_comment(oid):
    if request.method == 'GET':
        message = WoodsHole.objects(id=oid).first()
        result = {
            'id': str(message.id),
            'content': message.content,
            'like': message.like,
            'time': message.create_time,
            'comments': [{'name':comment.name, 'content':comment.content} for comment in message.comments]
        }
        return jsonify(result)
    else:
        post_data = json.loads(request.get_data().decode('utf-8'))
        message = WoodsHole.objects(id=oid).first()
        comment = Comment(name=post_data['name'], content=post_data['content'])
        message.comments.append(comment)
        message.save()
        return jsonify({'success': True})

@app.route('/woods-hole/<oid>/like', methods=['GET'])
def message_like(oid):
    message = WoodsHole.objects(id=oid).first()
    message.like += 1
    message.save()
    return jsonify({'success': True})

@app.route('/security-map/latest')
def get_latest_security_events():
    now = datetime.datetime.now()
    timedelta = datetime.timedelta(days=30)
    events = SecurityMap.objects(event_time__gte=now-timedelta)
    result = {}
    for event in events:
        position = event.position
        result[str(event.id)]={
            'id': str(event.id),
            'title': event.title,
            'type': event.event_type,
            'position': [float(position.lng), float(position.lat)],
            'datetime': event.event_time,
            'detail': event.detail,
            'detailedLocation': event.detailed_location,
        }
        print(event.event_time)
    return jsonify(result)

@app.route('/security-map/new', methods=['POST'])
def add_new_security_evnet():
    post_data = json.loads(request.get_data().decode('utf-8'))
    position = Position(lng=str(post_data['position'][0]),
                                lat=str(post_data['position'][1]))
    new_event = SecurityMap(title=post_data['title'], 
                            event_type=post_data['event_type'], 
                            position=position,
                            event_time=post_data['datetime'], 
                            detail=post_data['detail'], 
                            detailed_location=post_data['detailed_location'])
    new_event.save()
    return jsonify({'success':True})


@app.route('/classrooms/empty')
def findemptyroom():
    week = request.args.get('week')
    day = request.args.get('day')
    time = request.args.get('time')
    if (not week or not day or not time):
        result = {
            'week': schooltime.this_week(),
            'day': schooltime.this_day(),
            'time': schooltime.this_class(),
            'rooms': empty_room.get_emptyroom_now()
        }
    else:
        result = {
            'week': week,
            'day': day,
            'time': time,
            'rooms': empty_room.get_emptyroom(int(week), int(day), int(time))
        }
    return jsonify(result)

@app.route('/classrooms/<room>')
def room_schedule(room):
    result = {
        'room': room,
        'schedule': empty_room.get_room_schedule(room)
    }
    return jsonify(result)

# @app.route('/findemptyroom/room')
# def get_room_schedule():
#     result = {
#         'room': schooltime.this_week(),
#         'week': schooltime.this_day(),
#         'schedule': emptyroom.get_room_schedule(room, week)
#     }
#     return jsonify(result)


@app.route('/findfreetime', methods=['POST', 'GET'])
def findfreetime_member():
    if request.method == 'POST':
        usr = session['card_id']
        post_data = json.loads(request.get_data().decode('utf-8'))
        schedule = post_data['schedule']
        week = post_data['week']
        code = post_data['code']
        time_list = find_free_time.get_binary_json_from_course_table(schedule,week)
        time_lists = [] if CACHE.get(code) is None else CACHE.get(code)
        time_lists.append(time_list)
        CACHE.set(code, time_lists,timeout = 600)
        return jsonify({
                'success':True
            })
    elif request.method == 'GET':
        code = request.args.get('code')
        if CACHE.get(code) is not None:
            time_lists = CACHE.get(code)
            count = len(time_lists)
            raw_list =  find_free_time.detect_conflict(time_lists)
            Traverse_list = [([1] * 5) for i in range(0,13)]
            for j in range(0,5):
                for i in range(0,13):
                    Traverse_list[i][j]=raw_list[j][i]
            return jsonify({
                'success':True,
                'answer': Traverse_list,
                'count': count
            })
        else:
            return jsonify({
                'success':False
            })


@app.route('/queries/<site>')
@login_required
def get_query(site):
    """
    get encrypted cached query result from database
    """
    if ('card_id' in session) :
        card_id = session['card_id']
    else:
        return jsonify({
            'success': False,
        })
    user = User.objects(card_id=card_id).first()
    data = UserData.objects(site=site,user=user).first()
    if data != None:
        result = {
            'success': True,
            'card_id': card_id,
            'content':data.data,
            'date':data.last_modified.timestamp()
        }
    else:
        result = {
            'success': True,
            'status':'no records',
            'card_id': card_id
        }
    return json.dumps(result)

@app.route('/queries/<site>/refresh', methods=['POST', 'GET'])
@login_required
def refresh_query(site):
    """
    update query result if it doesn't exists or expried, use user ID and password and captcha (if there is)
    """
    card_id = session['card_id']
    if request.method == 'GET':
        if site == 'tiyu':
            client = Tiyu()
        elif site == 'xk':
            client = XK()
        elif site == 'cj':
            client = CJ()
        elif site == 'fin':
            client = Fin()
        elif site == 'phylab':
            client = Phylab()
        elif site == 'lehu':
            client = Lehu()
        elif site == 'services':
            client = Services() 
        CACHE.set(card_id + site, client, timeout=300)
        return jsonify({
            'success': True,
            'captcha_img':client.captcha_img
        })
    else:
        post_data = json.loads(request.get_data().decode('utf-8'))
        client = CACHE.get(card_id + site)
        client.set_account(post_data['card_id'], post_data['password'], post_data['captcha'])
        if client.login():
            if client.get_data():
                result = {
                    'success':True,
                    'content':{
                        'type': 'html',
                        'data': client.to_html()
                    }
                }
            else:
                result = {
                    'success': False,
                    'status': 'fail in get data'
                }
        else:
            result = {
                    'success': False,
                    'status': '请检查用户名密码验证码是否正确，也可能是服务器宕机'
                }
        return jsonify(result)

@app.route('/queries/<site>/save', methods=['POST', 'GET'])
def cache_query_result(site):
    """
    save encrypted query result sent from client to database 
    """
    card_id = session['card_id']
    post_data = json.loads(request.get_data().decode('utf-8'))
    user = User.objects(card_id=card_id).first()
    data = UserData.objects(site=site,user=user).first()
    if data != None:
        data.data = post_data['data']
        data.last_modified = datetime.datetime.now
    else:
        data = UserData(data=post_data['data'], site=site, user=user, last_modified=datetime.datetime.now)
    data.save()
    result = {'success':True}
    # result = {'success':False}
    return jsonify(result)

@app.route('/services/quit')
def quit_shu():
    """
    one key to quit SHU
    """
    pass

if __name__ == '__main__':
    """
    here, begins
    """
    app.debug = True
    app.run()