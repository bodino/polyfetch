from flask import Flask, request, render_template_string
from flask_sqlalchemy import SQLAlchemy
import asyncio
import websockets
import json
import threading

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///websocket_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class WebSocketMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50))
    fee_rate_bps = db.Column(db.String(10))
    market_asset_id = db.Column(db.String(100))
    market_condition_id = db.Column(db.String(100))
    market_icon = db.Column(db.String(200))
    market_question = db.Column(db.String(200))
    market_slug = db.Column(db.String(100))
    outcome = db.Column(db.String(10))
    outcome_index = db.Column(db.String(10))
    price = db.Column(db.String(10))
    side = db.Column(db.String(10))
    size = db.Column(db.String(20))
    timestamp = db.Column(db.String(20))
    transaction_hash = db.Column(db.String(100))
    user_bio = db.Column(db.String(200))
    user_displayUsernamePublic = db.Column(db.Boolean)
    user_name = db.Column(db.String(50))
    user_profileImage = db.Column(db.String(200))
    user_proxyWallet = db.Column(db.String(100))
    user_pseudonym = db.Column(db.String(50))

    def __repr__(self):
        return f'<WebSocketMessage {self.id}>'

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template_string('''
        <h1>Search WebSocket Messages</h1>
        <form action="/messages" method="get">
            <label for="event_type">Event Type:</label><br>
            <input type="text" id="event_type" name="event_type"><br><br>
            <label for="market_asset_id">Market Asset ID:</label><br>
            <input type="text" id="market_asset_id" name="market_asset_id"><br><br>
            <label for="market_condition_id">Market Condition ID:</label><br>
            <input type="text" id="market_condition_id" name="market_condition_id"><br><br>
            <label for="market_slug">Market Slug:</label><br>
            <input type="text" id="market_slug" name="market_slug"><br><br>
            <label for="user_name">User Name:</label><br>
            <input type="text" id="user_name" name="user_name"><br><br>
            <input type="submit" value="Search">
        </form>
    ''')

@app.route('/messages', methods=['GET'])
def get_messages():
    query_parameters = request.args
    filters = {key: value for key, value in query_parameters.items() if value}
    messages = WebSocketMessage.query.filter_by(**filters).all()
    return render_template_string('''
        <h1>Search Results</h1>
        {% if messages %}
            <ul>
            {% for message in messages %}
                <li>
                    <strong>ID:</strong> {{ message.id }}<br>
                    <strong>Event Type:</strong> {{ message.event_type }}<br>
                    <strong>Fee Rate BPS:</strong> {{ message.fee_rate_bps }}<br>
                    <strong>Market Asset ID:</strong> {{ message.market_asset_id }}<br>
                    <strong>Market Condition ID:</strong> {{ message.market_condition_id }}<br>
                    <strong>Market Icon:</strong> {{ message.market_icon }}<br>
                    <strong>Market Question:</strong> {{ message.market_question }}<br>
                    <strong>Market Slug:</strong> {{ message.market_slug }}<br>
                    <strong>Outcome:</strong> {{ message.outcome }}<br>
                    <strong>Outcome Index:</strong> {{ message.outcome_index }}<br>
                    <strong>Price:</strong> {{ message.price }}<br>
                    <strong>Side:</strong> {{ message.side }}<br>
                    <strong>Size:</strong> {{ message.size }}<br>
                    <strong>Timestamp:</strong> {{ message.timestamp }}<br>
                    <strong>Transaction Hash:</strong> {{ message.transaction_hash }}<br>
                    <strong>User Bio:</strong> {{ message.user_bio }}<br>
                    <strong>User Display Username Public:</strong> {{ message.user_displayUsernamePublic }}<br>
                    <strong>User Name:</strong> {{ message.user_name }}<br>
                    <strong>User Profile Image:</strong> {{ message.user_profileImage }}<br>
                    <strong>User Proxy Wallet:</strong> {{ message.user_proxyWallet }}<br>
                    <strong>User Pseudonym:</strong> {{ message.user_pseudonym }}<br>
                </li>
            {% endfor %}
            </ul>
        {% else %}
            <p>No messages found.</p>
        {% endif %}
        <a href="/">Go back</a>
    ''', messages=messages)

async def store_message(uri):
    async for websocket in websockets.connect(uri):
        try:
            while True:
                message = await websocket.recv()
                data = json.loads(message)

                if isinstance(data, list):
                    for item in data:
                        await save_message_to_db(item)
                else:
                    await save_message_to_db(data)
        except websockets.ConnectionClosed:
            print("WebSocket connection closed, retrying in 5 seconds...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"An error occurred: {e}, retrying in 5 seconds...")
            await asyncio.sleep(5)

async def save_message_to_db(data):
    websocket_message = WebSocketMessage(
        event_type=data.get('event_type'),
        fee_rate_bps=data.get('fee_rate_bps'),
        market_asset_id=data['market'].get('asset_id'),
        market_condition_id=data['market'].get('condition_id'),
        market_icon=data['market'].get('icon'),
        market_question=data['market'].get('question'),
        market_slug=data['market'].get('slug'),
        outcome=data.get('outcome'),
        outcome_index=data.get('outcome_index'),
        price=data.get('price'),
        side=data.get('side'),
        size=data.get('size'),
        timestamp=data.get('timestamp'),
        transaction_hash=data.get('transaction_hash', ''),
        user_bio=data['user'].get('bio', ''),
        user_displayUsernamePublic=data['user'].get('displayUsernamePublic'),
        user_name=data['user'].get('name'),
        user_profileImage=data['user'].get('profileImage', ''),
        user_proxyWallet=data['user'].get('proxyWallet'),
        user_pseudonym=data['user'].get('pseudonym')
    )
    with app.app_context():
        db.session.add(websocket_message)
        db.session.commit()

def start_websocket_listener():
    asyncio.run(store_message("wss://ws-subscriptions-clob.polymarket.com/ws/live-activity"))

if __name__ == '__main__':
    websocket_thread = threading.Thread(target=start_websocket_listener)
    websocket_thread.start()
    app.run(debug=True)