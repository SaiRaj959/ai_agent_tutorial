from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/decode', methods=['POST'])
def decode_prompt():
    print(request.json)
    user_prompt = request.json.get('prompt')
   

if __name__ == '__main__':
    app.run(debug=True)
