from flask import Flask, render_template, jsonify, request
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from twilio.twiml.voice_response import VoiceResponse, Dial, Conference
from dotenv import load_dotenv
import os
import pprint as p

# Load environment variables
load_dotenv()
account_sid = os.environ['TWILIO_ACCOUNT_SID']
api_key = os.environ['TWILIO_API_KEY_SID']
api_key_secret = os.environ['TWILIO_API_KEY_SECRET']
twiml_app_sid = os.environ['TWIML_APP_SID']
twilio_number = os.environ['TWILIO_NUMBER']

app = Flask(__name__)

@app.route('/')
def home():
    return render_template(
        'home.html',
        title="In-browser Calls",
    )

@app.route('/token', methods=['GET'])
def get_token():
    identity = twilio_number
    outgoing_application_sid = twiml_app_sid

    access_token = AccessToken(account_sid, api_key,
                               api_key_secret, identity=identity)

    voice_grant = VoiceGrant(
        outgoing_application_sid=outgoing_application_sid,
        incoming_allow=True,
    )
    access_token.add_grant(voice_grant)

    response = jsonify(
        {'token': access_token.to_jwt(), 'identity': identity})

    return response


@app.route('/handle_calls', methods=['POST'])
def handle_calls():
    p.pprint(request.form)
    response = VoiceResponse()
    dial = Dial(callerId=twilio_number)

    if 'To' in request.form and request.form['To'] != twilio_number:
        print('outbound call')
        dial.number(request.form['To'])
    else:
        print('incoming call')
        caller = request.form['Caller']
        dial = Dial(callerId=caller)
        dial.client(twilio_number)

    return str(response.append(dial))

# New API to create or join a conference
@app.route('/create_conference', methods=['POST'])
def create_conference():
    conference_name = request.form.get('conference_name', 'DefaultConference')
    response = VoiceResponse()

    dial = Dial()
    dial.conference(conference_name, start_conference_on_enter=True, end_conference_on_exit=True)

    response.append(dial)
    return str(response)


# New API to add a participant to an existing conference
@app.route('/join_conference', methods=['POST'])
def join_conference():
    conference_name = request.form.get('conference_name', 'DefaultConference')
    from_number = request.form.get('from', twilio_number)
    to_number = request.form.get('to')

    response = VoiceResponse()
    dial = Dial(callerId=from_number)

    # If `to_number` is provided, it dials the number to join the conference.
    if to_number:
        dial.conference(conference_name)
        response.append(dial)
        return str(response)
    else:
        return jsonify({"error": "The 'to' field is required to join the conference"}), 400

# New API to list active conferences (for debugging)
@app.route('/list_conferences', methods=['GET'])
def list_conferences():
    from twilio.rest import Client
    client = Client(account_sid, api_key, api_key_secret)
    conferences = client.conferences.list(status="in-progress")

    active_conferences = [{"sid": conf.sid, "friendly_name": conf.friendly_name, "status": conf.status} for conf in conferences]

    return jsonify({"conferences": active_conferences})


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug=True)
