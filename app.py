from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_swagger_ui import get_swaggerui_blueprint
import datetime
from functools import wraps

app = Flask(__name__)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # Change this to a strong secret key
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)
jwt = JWTManager(app)

client = MongoClient("mongodb+srv://suptotthitachakraborty:jWQEXt3z5BlEUBdY@flaskmongocluster.vtgxqfq.mongodb.net/?retryWrites=true&w=majority&appName=flaskmongocluster")
db = client.get_database('student_db')
collection = db['student_records']
user_collection = db['users']  # user collection is named 'users'

###swagger specific##
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Student API"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
### End Swagger specific ###

@app.route('/')
def hello():
    return "Hello World"

def generate_token(operation):
    access_token = create_access_token(identity={"operation": operation})
    return jsonify(access_token=access_token)

def verify_operation_token(operation):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims['sub']['operation'] != operation:
                return jsonify({"msg": "Invalid token for this operation"}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/token/<operation>', methods=['GET'])
def get_operation_token(operation):
    if operation not in ['add', 'get', 'update', 'delete']:
        return jsonify({"msg": "Invalid operation"}), 400
    return generate_token(operation)

@app.route('/addstudent', methods=['POST'])
@jwt_required()
def add_student():
    data = request.get_json()
    result = collection.insert_one(data)
    return jsonify({"_id": str(result.inserted_id)}), 201

@app.route('/student', methods=['GET'])
@jwt_required()
def get_student():
    items = list(collection.find())
    for item in items:
        item['_id'] = str(item['_id'])
    return jsonify(items), 200


@app.route('/update/<id>', methods=['PUT'])
@jwt_required()
def update_student(id):
    data = request.get_json()
    result = collection.update_one({"_id": ObjectId(id)}, {"$set": data})
    if result.matched_count > 0:
        return jsonify({"msg": "Item updated"}), 200
    else:
        return jsonify({"error": "Item not found"}), 404

@app.route('/delete/<id>', methods=['DELETE'])
@jwt_required()
def delete_student(id):
    result = collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count > 0:
        return jsonify({"msg": "Item deleted"}), 200
    else:
        return jsonify({"error": "Item not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)