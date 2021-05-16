from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from datetime import date

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150))
    review = db.relationship('Feedback', backref='user_detail')

class Places(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    location = db.Column(db.String(255))
    lat = db.Column(db.Float)
    long = db.Column(db.Float)
    description = db.Column(db.String(255))
    image_path = db.Column(db.String(255), unique=True)
    review = db.relationship('Feedback', backref='place_detail')

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.Integer, db.ForeignKey('places.id'))
    image_path = db.Column(db.String(255), unique=True)
    content_description = db.Column(db.String(255))
    place_name = db.relationship('Places', backref='image_url')

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    place_id = db.Column(db.Integer, db.ForeignKey('places.id'))
    rating = db.Column(db.Float)
    desc = db.Column(db.String(255))
    date = db.Column(db.Date)
    name = db.relationship('Places', backref='reviews')
    user = db.relationship('User', backref='reviewer')

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'username')

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    place_id = db.Column(db.Integer, db.ForeignKey('places.id'))
    place_detail = db.relationship('Places', backref='place_detail')

class PlacesDetail(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'location', 'lat', 'long', 'description', 'image_path', 'links')

class FeedbackSchema(ma.Schema):
    class Meta:
        fields = ('id', 'user_id', 'place_id', 'rating', 'desc', 'date', 'place_detail', 'user_detail')
    
    place_detail = ma.Nested(PlacesDetail, only=("id", "name"))
    user_detail = ma.Nested(UserSchema)
        
class WishlistSchema(ma.Schema):
    class Meta:
        fields = ('id', 'user_id', 'place_id', 'place_detail', 'links')
    
    place_detail = ma.Nested(PlacesDetail, only=("id", "name", "image_path"))
    links = ma.Hyperlinks(
        {
            'next': ma.URLFor('place', values=dict(id="<id>"))
        }
    )

class ImageSchema(ma.Schema):
    class Meta:
        fields = ('id', 'place_id', 'image_path', 'content_description')

class PlacesSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'location', 'lat', 'long', 'description', 'image_path', 'image_url', 'reviews', 'links')
    
    image_url = ma.Nested(ImageSchema, many=True, only=("image_path", "content_description"))
    reviews = ma.Nested(FeedbackSchema, many=True, exclude=['place_id', 'user_id',])
    links = ma.Hyperlinks(
        {
            'next': ma.URLFor('place', values=dict(id="<id>"))
        }
    )

@app.route('/', methods=['GET'])
def homepage():
    return f'Hello World! OK'

@app.route('/home', methods=['GET'])
def home():
    user_id = request.args.get('user')
    home_schema = PlacesSchema(many=True, only=("id", "name", "image_path", 'links'))
    result = Places.query.all()
    response = home_schema.dump(result)
    return jsonify({
        'status': 200,
        'message': 'OK',
        'data': response
    })

@app.route('/wishlist')
def wishlist():
    user_id = request.args.get('user')
    wishlist_schema = WishlistSchema(many=True, only=('id', 'place_detail', 'links'))
    result = Wishlist.query.filter_by(user_id=user_id).all()
    response = wishlist_schema.dump(result)
    return jsonify({
        'status': 200,
        'message': 'OK',
        'data': response
    })   

@app.route('/feedback', methods=['GET'])
def feedback():
    user_id = request.args.get('user')
    feedback_schema = FeedbackSchema(many=True, exclude=['user_detail', 'user_id', 'place_id'])
    result = Feedback.query.filter_by(user_id=user_id).all()
    response = feedback_schema.dump(result)
    return jsonify({
        'status': 200,
        'message': 'OK',
        'data': response
    })

@app.route('/place/<int:id>', methods=['GET'])
def place(id):
    place_schema = PlacesSchema(exclude=['image_path', 'links'])
    result = Places.query.get(id)
    response = place_schema.dump(result)
    return jsonify({
        'status': 200,
        'message': 'OK',
        'data': response
    })

@app.route('/place/<int:id>/feedback', methods=['GET'])
def get_feedback(id):
    feedback_schema = FeedbackSchema(many=True, exclude=['user_id', 'place_id', 'place_detail'])
    result = Feedback.query.filter_by(place_id=id).all()
    response = feedback_schema.dump(result)
    return jsonify({
        'status': 200,
        'message': 'OK',
        'data': response
    })

@app.route('/place/<int:id>/feedback/create', methods=['POST'])
def create_feedback(id):
    feedback_schema = FeedbackSchema()
    user_id = request.args.get('user')
    rate = request.args.get('rate')
    desc = request.args.get('desc')
    hari = date.today()
    new_feedback = Feedback(user_id=user_id, place_id=id, rating=rate, desc=desc, date=hari)
    db.session.add(new_feedback)
    db.session.commit()
    response = feedback_schema.dump(new_feedback)
    return jsonify({
        'status': 200,
        'message': 'OK',
        'data': response
    })

if __name__ == '__main__':
    app.run()