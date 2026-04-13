from flask import Blueprint, render_template, session, redirect, url_for

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main.hub'))
    return redirect(url_for('auth.login'))

@main_bp.route('/hub')
def hub():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('hub.html', name=session.get('user_name'))
