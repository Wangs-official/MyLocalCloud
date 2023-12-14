from flask import Flask, render_template, request, send_from_directory , jsonify , session , redirect , url_for
import yaml
import logging
import os
import time
import datetime

# logging

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s',level=logging.INFO)

# Open settings file and check

try:  

    with open('settings.yml') as f:

        y = yaml.safe_load(f)
        app_port = y['app']['port']
        app_save_path = y['app']['file_save_path']
        guest_user_enable = y['guest']['enable']

        if len(y['auth']['user_name']) == 0 :
            logging.error('未填写用户名')
            exit()

        if y['auth']['user_name'] == 'guest' :
            logging.error('用户名不得为 guest')
            exit()

        if app_port > 65535:
            logging.error('端口号不能超过65535')
            exit()

        if not os.path.exists(app_save_path):
            logging.error('存储文件路径不存在')
            exit()

except IOError:

    logging.error('未找到settings.yml文件')
    exit()

# run

logging.info(f'将在端口{app_port}上启动\n文件存储路径:{app_save_path}\n访客用户启用状态为:{guest_user_enable}')
time.sleep(1)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = app_save_path
app.secret_key = os.urandom(24)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login_auth' , methods=['POST'])
def login_auth():
    username = request.form['username']
    password = request.form['password']
    if not username:
        return jsonify({'success': False, 'message': '用户名未填写'})
    
    if username == 'guest' :
        if not guest_user_enable:
            return jsonify({'success': False, 'message': '访客访问未开启'})
        else:
            session['username'] = 'guest'
            return jsonify({'success': True})
    if username == y['auth']['user_name'] and password == y['auth']['user_password']:
        session['username'] = username
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': '用户名或密码错误'})

@app.route('/')
def index():
    if not 'username' in session :
        return redirect('/login')
    if session['username'] == 'guest' :
        ul = f'Guest - 访客用户(只读)'
    else:
        ul = f"{session['username']} - 用户(可读写)"
    files = get_files_list()
    return render_template('index.html', files=files , l_user_level=ul )

@app.route('/download/<filename>')
def download_file(filename):
    if not 'username' in session :
        return redirect('/login')
    return send_from_directory(app_save_path, filename)

@app.route('/upload', methods=['POST'])
def upload_file():
    if not 'username' in session :
        return redirect('/login')
    file = request.files['file']
    if session['username'] == 'guest':
        return render_template('upload_failed.html')
    if file:
        filename = file.filename
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    else:
        return render_template('upload_failed.html')
    return render_template('upload_complete.html')

@app.route('/delete/<filename>')
def delete_file(filename):
    if not 'username' in session :
        return redirect('/login')
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if session['username'] == 'guest':
        return render_template('delete_failed.html')
    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        return render_template('delete_failed.html')
    return render_template('delete_complete.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')


# def

def get_files_list():
    files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(filepath):
            file_size = os.path.getsize(filepath)
            upload_time_o = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
            upload_time = str(upload_time_o).split('.')[0]
            files.append({'filename': filename, 'size': file_size, 'upload_time': upload_time})
        else:
            logging.error('文件获取失败,若问题持续出现,请提交Issues')
            exit()
    return files

if __name__ == '__main__':
    app.run(debug=False , port=app_port , host='0.0.0.0')