from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import post_load, fields, ValidationError
from flask_migrate import Migrate
from flask_restful import Api, Resource
from dotenv import load_dotenv
from os import environ

load_dotenv()

# Create App instance
app = Flask(__name__)

# Add DB URI from .env
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('SQLALCHEMY_DATABASE_URI')

# Registering App w/ Services
db = SQLAlchemy(app)
ma = Marshmallow(app)
api = Api(app)
CORS(app)
Migrate(app, db)

# Models
class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    artist = db.Column(db.String(255), nullable=False)
    album = db.Column(db.String(255), nullable=False)
    release_date = db.Column(db.Date(), nullable=False)
    genre = db.Column(db.String(255))
    running_time = db.Column(db.Integer)

    def __repr__(self) -> str:
        return f"Title: {self.title} Artist: {self.artist} Album: {self.album} Release Date: {self.release_date} Genre: {self.genre} Running Time: {self.running_time}"

# Schemas
class SongSchema(ma.Schema):
    id = fields.Integer(primary_key=True)
    title = fields.String(required=True)
    artist = fields.String(required=True)
    album = fields.String(required=True)
    release_date = fields.Date(required=True)
    genre = fields.String()
    running_time = fields.Integer()

    class Meta:
        fields = ("id", "title", "artist", "album", "release_date", "genre", "running_time")

    @post_load
    def create_song(self, data, **kwargs):
        return Song(**data)

song_schema = SongSchema()
songs_schema = SongSchema(many=True)

# Resources
class SongListResource(Resource):
    def get(self):
        all_songs = Song.query.all()
        total_run_time = sum(song.running_time for song in all_songs)
        custom_response = {
            'songs': songs_schema.dump(all_songs),
            'total_running_time': round(float(total_run_time / 60), 2)
        }
        return custom_response, 200
    
    def post(self):
        form_data = request.get_json()
        try:
            new_song = song_schema.load(form_data)
            db.session.add(new_song)
            db.session.commit()
            return song_schema.dump(new_song), 201
        except ValidationError as err:
            return err.messages, 400
        
class SongResource(Resource):
    def get(self, pk):
        song_from_db = Song.query.get_or_404(pk)
        return song_schema.dump(song_from_db)

    def delete(self, pk):
        song_from_db = Song.query.get_or_404(pk)
        db.session.delete(song_from_db)
        db.session.commit()
        return '', 204
    
    def put(self, pk):
        song_from_db = Song.query.get_or_404(pk)

        if 'title' in request.json:
            song_from_db.title = request.json['title']
        if 'artist' in request.json:
            song_from_db.artist = request.json['artist']
        if 'album' in request.json:
            song_from_db.album = request.json['album']
        if 'release_date' in request.json:
            song_from_db.release_date = request.json['release_date']
        if 'genre' in request.json:
            song_from_db.genre = request.json['genre']
        if 'running_time' in request.json:
            song_from_db.running_time = request.json['running_time']

        db.session.commit()
        return song_schema.dump(song_from_db)

# Routes
api.add_resource(SongListResource, '/api/songs')
api.add_resource(SongResource, '/api/songs/<int:pk>')


