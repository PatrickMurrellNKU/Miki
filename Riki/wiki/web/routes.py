"""
    Routes
    ~~~~~~
"""
import io
import os
import sqlite3

from flask import Blueprint, send_file
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_required
from flask_login import login_user
from flask_login import logout_user
from werkzeug.utils import secure_filename

from wiki.core import Processor
from wiki.web.forms import EditorForm
from wiki.web.forms import LoginForm
from wiki.web.forms import SearchForm
from wiki.web.forms import URLForm
from wiki.web.forms import RegisterForm
from wiki.web import current_wiki
from wiki.web import current_users
from wiki.web.user import protect, User, UserManager
from wiki.web.featured import feature

from wiki.web.forms import UploadForm

import html2text

bp = Blueprint('wiki', __name__)


@bp.route('/')
@protect
def home():
    page = current_wiki.get('home')
    if page:
        return display('home')
    return render_template('home.html')


@bp.route('/index/')
@protect
def index():
    pages = current_wiki.index()
    return render_template('index.html', pages=pages)


@bp.route('/<path:url>/')
@protect
def display(url):
    if url == 'feature':
        page = feature()
    else:
        page = current_wiki.get_or_404(url)
    return render_template('page.html', page=page)


@bp.route('/create/', methods=['GET', 'POST'])
@protect
def create():
    form = URLForm()
    if form.validate_on_submit():
        return redirect(url_for(
            'wiki.edit', url=form.clean_url(form.url.data)))
    return render_template('create.html', form=form)


@bp.route('/edit/<path:url>/', methods=['GET', 'POST'])
@protect
def edit(url):
    page = current_wiki.get(url)
    form = EditorForm(obj=page)
    if form.validate_on_submit():
        if not page:
            page = current_wiki.get_bare(url)
        form.populate_obj(page)
        page.save()
        flash('"%s" was saved.' % page.title, 'success')
        return redirect(url_for('wiki.display', url=url))
    return render_template('editor.html', form=form, page=page)


@bp.route('/preview/', methods=['POST'])
@protect
def preview():
    data = {}
    processor = Processor(request.form['body'])
    data['html'], data['body'], data['meta'] = processor.process()
    return data['html']


@bp.route('/move/<path:url>/', methods=['GET', 'POST'])
@protect
def move(url):
    page = current_wiki.get_or_404(url)
    form = URLForm(obj=page)
    if form.validate_on_submit():
        newurl = form.url.data
        current_wiki.move(url, newurl)
        return redirect(url_for('wiki.display', url=newurl))
    return render_template('move.html', form=form, page=page)


@bp.route('/delete/<path:url>/')
@protect
def delete(url):
    page = current_wiki.get_or_404(url)
    current_wiki.delete(url)
    flash('Page "%s" was deleted.' % page.title, 'success')
    return redirect(url_for('wiki.home'))


@bp.route('/tags/')
@protect
def tags():
    tags = current_wiki.get_tags()
    return render_template('tags.html', tags=tags)


@bp.route('/tag/<string:name>/')
@protect
def tag(name):
    tagged = current_wiki.index_by_tag(name)
    return render_template('tag.html', pages=tagged, tag=name)


@bp.route('/search/', methods=['GET', 'POST'])
@protect
def search():
    form = SearchForm()
    if form.validate_on_submit():
        results = current_wiki.search(form.term.data, form.ignore_case.data)
        return render_template('search.html', form=form,
                               results=results, search=form.term.data)
    return render_template('search.html', form=form, search=None)


@bp.route('/user/login/', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        user = current_users.get_user(form.name.data)
        login_user(user)
        user.set('authenticated', True)
        flash('Login successful.', 'success')
        return redirect(request.args.get("next") or url_for('wiki.index'))
    return render_template('login.html', form=form)


@bp.route('/user/logout/')
@login_required
def user_logout():
    current_user.set('authenticated', False)
    logout_user()
    flash('Logout successful.', 'success')
    return redirect(url_for('wiki.index'))


@bp.route('/user/')
@login_required
def user_index():
    username = current_user.get_id()
    active = current_user.is_active()
    return render_template('profile.html', username=username, active=active)


@bp.route('/user/register/', methods=['GET', 'POST'])
def user_register():
    form = RegisterForm()
    if form.validate_on_submit():
        usermanager = UserManager()
        user = usermanager.add_user(name=form.name.data, password=form.password.data)
        user.set('authenticated', True)
        flash('Account creation successful.', 'success')
        return redirect(request.args.get("next") or url_for('wiki.index'))
    return render_template('register.html', form=form)


@bp.route('/user/<int:user_id>/')
def user_admin(user_id):
    pass


@bp.route('/user/unregister/', methods=['GET', 'POST'])
@login_required
def user_unregister():
    form = LoginForm()
    if form.validate_on_submit():
        usermanager = UserManager()
        usermanager.delete_user(form.name.data)
        flash('Account deleted.', 'success')
        return redirect(request.args.get("next") or url_for('wiki.index'))
    return render_template('unregister.html', form=form)


@bp.route('/files/')
@protect
def files():
    try:
        con = sqlite3.connect('./Database/database.db')
        c = con.cursor()
        c.execute('select * from files')
        data = c.fetchall()
    except Exception as e:
        print(e)
        flash('There was an error displaying files')
        return render_template('files.html')
    return render_template('files.html', data=data)


@bp.route('/files/<int:fid>')
@protect
def file_display(fid):
    try:
        con = sqlite3.connect('./Database/database.db')
        c = con.cursor()
        c.execute('select * from files where id = ?', [fid])
        data = [dict(id=row[0], name=row[1], desc=row[2], date=row[3], user=row[4]) for row in c.fetchall()]
        if not data:
            return redirect(url_for('wiki.files'))
    except Exception as e:
        print(e)
        flash('There was an error displaying your file')
        return redirect(url_for('wiki.files'))
    return render_template('file_display.html', fid=fid, data=data)


@bp.route('/files/upload/', methods=['GET', 'POST'])
@protect
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        f = request.files['file']
        description = form.description.data
        filename = secure_filename(f.filename)
        user = current_user.get_id()
        try:
            con = sqlite3.connect('./Database/database.db')
            c = con.cursor()
            c.execute("""INSERT INTO files(filename, description, user) 
                           VALUES (?,?, ?);""", (filename, description, user))
            con.commit()
            upload_folder = "../Riki/wiki/web/static/uploads/"
            f.save(os.path.join(upload_folder, filename))
            fid = c.lastrowid
            return redirect(url_for('wiki.file_display', fid=fid))
        except Exception as e:
            print(e)
            flash('There was an error uploading your file')
            return render_template('upload.html', form=form)
            # flash error message
    return render_template('upload.html', form=form)


@bp.route('/download/<name>')
@protect
def download(name):
    try:
        return send_file('./static/uploads/%s' % name)
    except Exception as e:
        print(e)
        flash('There was an error downloading your file')
        return redirect(url_for('wiki.files'))


@bp.route('/convert/txt/<url>')
def convert_txt(url):
    page = current_wiki.get_or_404(url)
    url = url + '.txt'

    converted_folder = "../Riki/wiki/web/static/converted/"

    file = open(converted_folder + url, 'w')
    file.write(html2text.html2text(render_template('bare.html', page=page)))
    file.close()

    return send_file('./static/converted/' + url, as_attachment=True)


"""
    Error Handlers
    ~~~~~~~~~~~~~~
"""


@bp.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
