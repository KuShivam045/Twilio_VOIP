from flask import Flask, render_template, jsonify
from flask import request
from twilio.rest import Client
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from twilio.twiml.voice_response import VoiceResponse, Dial
from dotenv import load_dotenv
import os
import pprint as p



load_dotenv()
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
api_key = os.environ['TWILIO_API_KEY_SID']
api_key_secret = os.environ['TWILIO_API_KEY_SECRET']
twiml_app_sid = os.environ['TWIML_APP_SID']
twilio_number = os.environ['TWILIO_NUMBER']

client = Client(account_sid, auth_token)


app = Flask(__name__)

@app.route('/')
def home():
    return render_template(
        'home.html',
        title="In browser calls",
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


# @app.route('/handle_calls', methods=['POST'])
# def call():
#     p.pprint(request.form)
#     response = VoiceResponse()
    
#     # Enable recording for the Dial action
#     dial = Dial(callerId=twilio_number, record=True)

#     if 'To' in request.form and request.form['To'] != twilio_number:
#         print('outbound call')
#         # Record the outbound call to the provided number
#         dial.number(request.form['To'])
#     else:
#         print('incoming call')
#         caller = request.form['Caller']
#         # Record the incoming call when connecting to the client
#         dial = Dial(callerId=caller, record=True)
#         dial.client(twilio_number)

#     # Append the dial to the VoiceResponse and return it
#     response.append(dial)
#     return str(response)


@app.route('/handle_calls', methods=['POST'])
def call():
    p.pprint(request.form)
    response = VoiceResponse()

    # Check if it's an incoming or outgoing call
    if 'To' in request.form and request.form['To'] != twilio_number:
        # Outbound call logic
        print('outbound call')
        dial = Dial(callerId=twilio_number, record=True)
        dial.number(request.form['To'])
    else:
        # Incoming call logic
        print('incoming call')
        caller = request.form.get('Caller', twilio_number)
        response.say('You have an incoming call, connecting you now.')

        # Enable recording for the incoming call to the client
        dial = Dial(callerId=caller, record=True)
        dial.client(twilio_number)

    # Append the dial to the VoiceResponse and return it
    response.append(dial)
    return str(response)


@app.route('/send_sms', methods=['POST'])
def send_sms():
    try:
        # Extract data from the request
        data = request.json
        to_number = data.get('to')
        message_body = data.get('message')
        media_url = data.get('media_url', None)  # Optional for MMS

        if not to_number or not message_body:
            return jsonify({'error': 'Both "to" and "message" fields are required'}), 400

        # Send SMS or MMS based on the presence of media_url
        if media_url:
            message = client.messages.create(
                body=message_body,
                from_=twilio_number,
                to=to_number,
                media_url=media_url  # MMS if media_url is provided
            )
        else:
            message = client.messages.create(
                body=message_body,
                from_=twilio_number,
                to=to_number
            )

        return jsonify({
            'message': 'Message sent successfully',
            'sid': message.sid,
            'status': message.status
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug=True)
