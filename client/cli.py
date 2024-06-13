import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import time
import os
from datetime import datetime
import pytz
import textwrap
from colorama import init, Fore, Style

# Initialize colorama
init()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///websocket_data.db'  # Ensure this path is correct to access the server's SQLite file
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

def format_message(message, new=False):
    pst = pytz.timezone('America/Los_Angeles')
    timestamp = datetime.fromtimestamp(int(message.timestamp) / 1000).astimezone(pst).strftime('%Y-%m-%d %H:%M:%S %Z')

    msg_content = textwrap.dedent(f"""
    User Name       : {message.user_name}
    User Proxy Wallet: {message.user_proxyWallet}
    Timestamp (PST) : {timestamp}
    Market Question : {message.market_question}
    Market Slug     : {message.market_slug}
    Event Type      : {message.event_type}
    Outcome         : {message.outcome}
    Price           : {message.price}
    Side            : {message.side}
    Size            : {message.size}
    """).strip()

    box_width = max(len(line) for line in msg_content.split('\n')) + 4
    box_top = '┌' + '─' * (box_width - 2) + '┐'
    box_bottom = '└' + '─' * (box_width - 2) + '┘'
    box_lines = [f'│ {line.ljust(box_width - 4)} │' for line in msg_content.split('\n')]
    box_content = '\n'.join(box_lines)

    if new:
        box_top = Fore.RED + box_top + Style.RESET_ALL
        box_bottom = Fore.RED + box_bottom + Style.RESET_ALL
        box_lines = [Fore.RED + line + Style.RESET_ALL for line in box_lines]
        box_content = '\n'.join(box_lines)

    return f"{box_top}\n{box_content}\n{box_bottom}"

def display_new_trades(username, market_slug, last_id):
    with app.app_context():
        query = WebSocketMessage.query
        if username:
            query = query.filter_by(user_name=username)
        if market_slug:
            query = query.filter_by(market_slug=market_slug)
        messages = query.filter(WebSocketMessage.id > last_id).all()

        if messages:
            for message in messages:
                print(format_message(message, new=True))
                print('\n')  # Adding space between messages
            last_id = messages[-1].id

        return last_id

@click.command()
@click.option('-u', '--username', default=None, help='Username to filter trades')
@click.option('-m', '--market_slug', default=None, help='Market slug to filter trades')
def show_trades(username, market_slug):
    last_id = 0

    # Display all trades initially
    last_id = display_new_trades(username, market_slug, last_id)

    while True:
        time.sleep(5)  # Poll every 5 seconds
        last_id = display_new_trades(username, market_slug, last_id)

if __name__ == '__main__':
    show_trades()