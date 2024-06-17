from flask import (
	Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from hashlib import md5
from short_url.auth import login_required
from short_url.db import get_db

bp = Blueprint('url', __name__)


@bp.route('/', methods=('GET', 'POST'))
def index_anonymous(short_url = None):
	if request.method == 'POST':
		long_url = request.form['long_url']
		error = None

		if not long_url:
			error = 'La url es obligatoria.'

		if error is not None:
			flash(error)
		else:
			short_url = create_short_url(long_url)
			db = get_db()
			db.execute(
				'INSERT INTO url (short_url, long_url)'
				' VALUES (?, ?)',
				(short_url, long_url)
			)
			db.commit()
			return render_template('url/index_anonymous.html', short_url=short_url)

	return render_template('url/index_anonymous.html', short_url=short_url)


@bp.route('/my-urls')
@login_required
def index_logged():
	db = get_db()
	urls = db.execute(
		'SELECT url.id, short_url, long_url, author_id, username'
		' FROM url JOIN user u ON url.author_id = u.id'
		' ORDER BY url.id DESC'
	).fetchall()
	return render_template('url/index_logged.html', urls=urls)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
	if request.method == 'POST':
		long_url = request.form['long_url']
		error = None

		if not long_url:
			error = 'La url es obligatoria.'

		if error is not None:
			flash(error)
		else:
			short_url = create_short_url(long_url)
			db = get_db()
			db.execute(
				'INSERT INTO url (short_url, long_url, author_id)'
				' VALUES (?, ?, ?)',
				(short_url, long_url, g.user['id'])
			)
			db.commit()
			return redirect(url_for('url.index_logged'))

	return render_template('url/create.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
	print(id)
	url = get_url(id)

	if request.method == 'POST':
		long_url = request.form['long_url']
		error = None

		if not long_url:
			error = 'La URL es obligatoria.'

		if error is not None:
			flash(error)
		else:
			short_url = create_short_url(long_url)
			db = get_db()
			db.execute(
				'UPDATE url SET long_url = ?, short_url = ?'
				' WHERE id = ?',
				(long_url, short_url, id)
			)
			db.commit()
			return redirect(url_for('url.index_logged'))

	return render_template('url/update.html', url=url)



@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
	get_url(id)
	db = get_db()
	db.execute('DELETE FROM url WHERE id = ?', (id,))
	db.commit()
	return redirect(url_for('url.index_logged'))



@bp.route('/<short_url>', methods=('GET',))
def redirect_to_url(short_url):
	error = None

	if not short_url:
		error = 'La url es obligatoria.'

	if error is not None:
		flash(error)
	else:
		db = get_db()
		url = db.execute(
			'SELECT long_url'
			' FROM url'
			' WHERE url.short_url = ?',
			(short_url,)
			).fetchone()
		if not "http://" in url['long_url']:
			return redirect(f"https://{url['long_url']}")
		else:
			return redirect(f"{url['long_url']}")




def get_url(id, check_author=True):
	url = get_db().execute(
		'SELECT url.id, short_url, long_url, author_id, username'
		' FROM url JOIN user u ON url.author_id = u.id'
		' WHERE url.id = ?',
		(id,)
	).fetchone()

	if url is None:
		abort(404, f"URL id {id} doesn't exist.")

	if check_author and url['author_id'] != g.user['id']:
		abort(403)

	return url



def create_short_url(long_url):
	"""
	Crea la url acortada.

	Args:
		long_url (str): url larga.

	returns:
		str: los 6 primeros caracteres de la cadena que genera la url con el hash md5.
	"""
	return md5(long_url.encode('utf-8')).hexdigest()[:6]