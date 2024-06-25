from flask import Flask, request, jsonify, render_template
import sqlite3
import json
import telebot

app = Flask(__name__)

@app.before_request
def init_db():
    with sqlite3.connect('data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS data_store (
                            key TEXT PRIMARY KEY,
                            data TEXT NOT NULL
                        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            bot_id TEXT,
                            user_id TEXT,
                            UNIQUE(bot_id, user_id)
                        )''')
        conn.commit()

@app.route('/getData', methods=['GET'])
def get_data():
    key = request.args.get('key')
    if not key:
        return jsonify({'error': 'Key is required'}), 400

    with sqlite3.connect('data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT data FROM data_store WHERE key = ?', (key,))
        row = cursor.fetchone()
        if row:
            value = json.loads(row[0])
            return jsonify({'data': value}), 200
        return jsonify({'error': 'Key not found'}), 404

@app.route('/saveData', methods=['POST'])
def save_data():
    data = request.json
    key = data.get('key')
    value = data.get('data')
    if not key or value is None:
        return jsonify({'success': False, 'error': 'Invalid key or data'}), 400

    value_str = json.dumps(value)

    with sqlite3.connect('data.db') as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT OR REPLACE INTO data_store (key, data) VALUES (?, ?)', (key, value_str))
            conn.commit()
            return jsonify({'success': True}), 200
        except sqlite3.Error as e:
            return jsonify({'success': False, 'error': str(e)}), 500

def validate_bot_token(bot_token):
    bot = telebot.TeleBot(bot_token)
    try:
        user = bot.get_me()
        return True, user
    except telebot.apihelper.ApiException:
        return False, None

def save_user_to_db(bot_id, user_id):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (bot_id, user_id)
        VALUES (?, ?)
    ''', (bot_id, user_id))
    conn.commit()
    conn.close()

def get_users_from_db(bot_id):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id FROM users WHERE bot_id = ?
    ''', (bot_id,))
    users = cursor.fetchall()
    conn.close()
    return [user[0] for user in users]

def broadcast_message(bot_token, user_ids, message):
    bot = telebot.TeleBot(bot_token)
    for user_id in user_ids:
        try:
            bot.send_message(user_id, message, parse_mode='HTML')
        except telebot.apihelper.ApiException as e:
            print(f"Failed to send message to {user_id}: {e}")

@app.route('/saveUser', methods=['POST'])
def save_user():
    try:
        data = json.loads(request.data)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON"}), 400

    bot_token = data.get('bot_token')
    user_ids = data.get('user_ids')

    if not bot_token or not user_ids:
        return jsonify({"error": "Missing bot_token or user_ids"}), 400

    if not isinstance(user_ids, list):
        return jsonify({"error": "user_ids should be a list"}), 400

    valid, user = validate_bot_token(bot_token)
    if not valid:
        return jsonify({"error": "Invalid bot token"}), 400

    bot_id = user.id
    for user_id in user_ids:
        save_user_to_db(bot_id, user_id)

    return jsonify({"status": "Users saved"}), 200

@app.route('/broadcast', methods=['POST'])
def broadcast():
    try:
        data = json.loads(request.data)
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON"}), 400

    bot_token = data.get('bot_token')
    message = data.get('message')

    if not bot_token or not message:
        return jsonify({"error": "Missing bot_token or message"}), 400

    valid, user = validate_bot_token(bot_token)
    if not valid:
        return jsonify({"error": "Invalid bot token"}), 400

    bot_id = user.id
    user_ids = get_users_from_db(bot_id)
    broadcast_message(bot_token, user_ids, message)
    return jsonify({"status": "Message broadcasted"}), 200

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.route('/documentation')
def documentation():
    return render_template('documentation.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
    
