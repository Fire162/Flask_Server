from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

def init_db():
    with sqlite3.connect('data.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS data_store (
                            key TEXT PRIMARY KEY,
                            data TEXT NOT NULL
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
            return jsonify({'data': row[0]}), 200
        return jsonify({'error': 'Key not found'}), 404

@app.route('/saveData', methods=['POST'])
def save_data():
    data = request.json
    key = data.get('key')
    value = data.get('data')
    if not key or value is None:
        return jsonify({'success': False, 'error': 'Invalid key or data'}), 400

    with sqlite3.connect('data.db') as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT OR REPLACE INTO data_store (key, data) VALUES (?, ?)', (key, value))
            conn.commit()
            return jsonify({'success': True}), 200
        except sqlite3.Error as e:
            return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=80)
