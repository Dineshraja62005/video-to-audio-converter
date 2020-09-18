from flask import Flask, request, render_template, send_from_directory, session
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import shutil
from yt import yt  # Importing the blueprint in yt.py
from trimmer import trimmer  # Importing the blueprint in trimmer.py
from loggers import log, log_this, log_visit
from werkzeug.utils import secure_filename
from time import time
from datetime import datetime
import os
import converter  # converter.py

app = Flask(__name__)
secret_key = str(os.urandom(16))
app.secret_key = secret_key
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
# Set the maximum upload size to 5 GB.
max_upload_size = 5  # in GB.
app.config['MAX_CONTENT_LENGTH'] = max_upload_size * 1000 * 1000 * 1000
# Changes to the HTML files are reflected on the website without having to restart the Flask app.
app.jinja_env.auto_reload = True

app.register_blueprint(yt)
app.register_blueprint(trimmer)

# The database object (db) needs to be defined in main.py even though we're not using the database in main.py
# Otherwise you get the following error:
# "AssertionError: The sqlalchemy extension was not registered to the current application."
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# For the chat section of the website.
socketio = SocketIO(app)
socketio.init_app(app, cors_allowed_origins="*")

SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)


# When a file has been uploaded, a POST request is sent to the homepage.
@app.route("/", methods=["POST"])
def homepage():

    # First POST request.
    if request.form['request_type'] == 'log_convert_clicked':
        log_this('clicked on the convert button.')
        return ''

    # Second POST request.
    elif request.form["request_type"] == "uploaded":

        upload_time = datetime.now().strftime('%H:%M:%S')
        log.info(f'Upload complete at {upload_time}')

        # Empty the conversions folder to ensure there's room for the file that is going to be converted.
        for file in os.listdir('conversions'):
            os.remove(f'conversions/{file}')
            log.info(f'Deleted conversions/{file}')

        uploads_folder_size = 0
        # Iterate over each file in the folder and add its size to the above variable.
        for file in os.listdir('uploads'):
            size_of_file = os.path.getsize(f'uploads/{file}') / 1_000_000
            uploads_folder_size += size_of_file
        # If there's more than 1 GB of files in the conversions folder, empty it.
        if uploads_folder_size > 1000:
            log.info(f'More than 1 GB worth of uploads found. Emptying uploads folder...')
            for file in os.listdir('uploads'):
                os.remove(f'uploads/{file}')
            log.info('Conversions folder emptied.')
        
        # Grabbing the JavaScript FormData
        chosen_file = request.files["chosen_file"]
        filesize = request.form["filesize"]

        log.info(chosen_file)
        log.info(f'Size: {filesize} MB')

        # Make the filename safe
        filename_secure = secure_filename(chosen_file.filename)
        # Save the uploaded file to the uploads folder.
        os.makedirs('uploads', exist_ok=True)
        chosen_file.save(os.path.join("uploads", filename_secure))

        conversion_progress_filename = f'{str(time())[:-8]}.txt'
        session['progress_filename'] = conversion_progress_filename

        return session['progress_filename']

    elif request.form["request_type"] == "convert":

        conversion_start_time = time()

        wav_bit_depth = request.form["wav_bit_depth"]
        filename = request.form["filename"]
        chosen_codec = request.form["chosen_codec"]
        crf_value = request.form["crf_value"]
        mp4_encoding_mode = request.form["mp4_encoding_mode"]
        is_keep_video = request.form["is_keep_video"]
        uploaded_file_path = os.path.join("uploads", secure_filename(filename))
        # MP3
        mp3_encoding_type = request.form["mp3_encoding_type"]
        mp3_bitrate = request.form["mp3_bitrate"]
        mp3_vbr_setting = request.form["mp3_vbr_setting"]
        # AAC
        fdk_type = request.form["fdk_type"]
        fdk_cbr = request.form["fdk_cbr"]
        fdk_vbr = request.form["fdk_vbr"]
        is_fdk_lowpass = request.form["is_fdk_lowpass"]
        fdk_lowpass = request.form["fdk_lowpass"]
        # Vorbis
        vorbis_encoding = request.form["vorbis_encoding"]
        vorbis_quality = request.form["vorbis_quality"]
        # Vorbis/Opus
        opus_vorbis_slider = request.form["opus_vorbis_slider"]
        # AC3
        ac3_bitrate = request.form["ac3_bitrate"]
        # FLAC
        flac_compression = request.form["flac_compression"]
        # DTS
        dts_bitrate = request.form["dts_bitrate"]
        # Opus
        opus_cbr_bitrate = request.form["opus_cbr_bitrate"]
        opus_encoding_type = request.form["opus_encoding_type"]
        # Desired filename
        output_name = request.form["output_name"]

        log.info(f'They chose {chosen_codec} | Output Filename: {output_name}')
        os.makedirs('conversions', exist_ok=True)
        output_path = os.path.join('conversions', output_name)

        def run_converter(codec, params):
            codec_to_converter = {
                                    "aac": converter.aac,
                                    "ac3": converter.ac3,
                                    "alac": converter.alac,
                                    "dts": converter.dts,
                                    "flac": converter.flac,
                                    "mka": converter.mka,
                                    "mkv": converter.mkv,
                                    "mp3": converter.mp3,
                                    "mp4": converter.mp4,
                                    "opus": converter.opus,
                                    "vorbis": converter.vorbis,
                                    "wav": converter.wav
            }
            # Pass the list of parameters (params) to the appropriate converter function.
            return codec_to_converter[codec](*params)

        # Run the appropriate function in converter.py:

        # AAC
        if chosen_codec == 'AAC':
            params = [session['progress_filename'], uploaded_file_path, is_keep_video, fdk_type, fdk_cbr,
                      fdk_vbr, is_fdk_lowpass, fdk_lowpass, output_path]
            extension = run_converter('aac', params)

        # AC3
        elif chosen_codec == 'AC3':
            params = [session['progress_filename'], uploaded_file_path, is_keep_video, ac3_bitrate, output_path]
            extension = run_converter('ac3', params)

        # ALAC
        elif chosen_codec == 'ALAC':
            params = [session['progress_filename'], uploaded_file_path, is_keep_video, output_path]
            extension = run_converter('alac', params)

        # CAF
        elif chosen_codec == 'CAF':
            params = [session['progress_filename'], uploaded_file_path, output_path]
            extension = run_converter('caf', params)

        # DTS
        elif chosen_codec == 'DTS':
            params = [session['progress_filename'], uploaded_file_path, is_keep_video, dts_bitrate, output_path]
            extension = run_converter('dts', params)

        # FLAC
        elif chosen_codec == 'FLAC':
            params = [session['progress_filename'], uploaded_file_path, is_keep_video, flac_compression,
                      output_path]
            extension = run_converter('flac', params)

        # MKA
        elif chosen_codec == 'MKA':
            params = [session['progress_filename'], uploaded_file_path, output_path]
            extension = run_converter('mka', params)

        # MKV
        elif chosen_codec == 'MKV':
            params = [session['progress_filename'], uploaded_file_path, output_path]
            extension = run_converter('mkv', params)

        # MP3
        elif chosen_codec == 'MP3':
            params = [session['progress_filename'], uploaded_file_path, is_keep_video, mp3_encoding_type,
                      mp3_bitrate, mp3_vbr_setting, output_path]
            extension = run_converter('mp3', params)

        # MP4
        elif chosen_codec == 'MP4':
            params = [session['progress_filename'], uploaded_file_path, mp4_encoding_mode, crf_value, output_path]
            extension = run_converter('mp4', params)

        # Opus
        elif chosen_codec == 'Opus':
            params = [session['progress_filename'], uploaded_file_path, opus_encoding_type, opus_vorbis_slider,
                      opus_cbr_bitrate, output_path]
            extension = run_converter('opus', params)

        # Vorbis
        elif chosen_codec == 'Vorbis':
            params = [session['progress_filename'], uploaded_file_path, vorbis_encoding, vorbis_quality,
                      opus_vorbis_slider, output_path]
            extension = run_converter('vorbis', params)

        # WAV
        elif chosen_codec == 'WAV':
            params = [session['progress_filename'], uploaded_file_path, is_keep_video, wav_bit_depth,
                      output_path]
            extension = run_converter('wav', params)

        conversion_complete_time = time()
        log.info(f'Conversion took {round((conversion_complete_time - conversion_start_time), 1)} seconds.')

        # Filename after conversion.
        converted_file_name = f'{output_name}.{extension}'

        return {
            'download_path': os.path.join('conversions', converted_file_name),
            'log_file': os.path.join('ffmpeg-progress', session["progress_filename"])
            }


@app.route("/ffmpeg-progress/<filename>")
def get_file(filename):
    return send_from_directory('ffmpeg-progress', filename)


# app.js directs the user to this URL when the conversion is complete.
@app.route("/conversions/<filename>", methods=["GET"])
def send_file(filename):
    log.info(f'https://freeaudioconverter.net/conversions/{filename}')
    extension = os.path.splitext(filename)[-1]
    if extension == ".m4a":
        return send_from_directory('conversions', filename, mimetype="audio/mp4", as_attachment=True)
    else:
        return send_from_directory('conversions', filename, as_attachment=True)


# Game 1
@app.route("/game", methods=['POST'])
def return_world_record():
    current_datetime = datetime.now().strftime('%d-%m-%y at %H:%M:%S')
    user = request.environ.get("HTTP_X_REAL_IP").split(',')[0]
    user_agent = request.headers.get('User-Agent')
    score = request.form['score']
    times_missed = request.form['times_missed']
    canvas_width = request.form['canvas_width']
    canvas_height = request.form['canvas_height']
    try:
        int(score)
        int(times_missed)
        int(canvas_width)
        int(canvas_height)
    except ValueError:
        log.error("[Game 1] The user changed something to a non-int.")
    else:
        os.makedirs('GameScores', exist_ok=True)
        with open("GameScores/HighScores.txt", "a") as f:
                f.write(f'{score} | {times_missed} | {user} | {user_agent} | {canvas_width}'
                        f'x{canvas_height} | {current_datetime}\n')
    finally:
        just_scores = []
        with open('GameScores/HighScores.txt', 'r') as f:
            lines = f.readlines()
            for line in lines:
                just_scores.append(line.split('|')[0].strip())
        return ''


# Game 2
@app.route("/game2", methods=['POST'])
def save_game2_stats():
    current_datetime = datetime.now().strftime('%d-%m-%y at %H:%M:%S')
    user = request.environ.get("HTTP_X_REAL_IP").split(',')[0]
    user_agent = request.headers.get('User-Agent')
    reaction_time = request.form['reaction_time']
    try:
        int(reaction_time)
    except ValueError:
        log.error("[Game 2] The user changed reaction_time to a non-int.")
    else:
        os.makedirs('GameScores', exist_ok=True)
        with open("GameScores/ReactionTimes.txt", "a") as f:
            f.write(f'{reaction_time} ms | {user} | {user_agent} | {current_datetime}\n')
    finally:
        reaction_times = []
        with open('GameScores/ReactionTimes.txt', 'r') as f:
            lines = f.readlines()
            for line in lines:
                reaction_times.append(line.split('|')[0][:-3].strip())
        return ''


@app.route("/")
def homepage_visited():
    log_visit("visited homepage")
    return render_template("home.html", title="Home", upload_size=max_upload_size)


@app.route("/about")
def about_page_visited():
    log_visit("visited about page")
    return render_template("about.html", title="About")


@app.route("/filetypes")
def filetypes_visited():
    log_visit("visited filetypes")
    return render_template("filetypes.html", title="Filetypes")


@app.route("/yt")
def yt_page_visited():
    log_visit("visited YT")
    return render_template("yt.html", title="YouTube downloader")


@app.route("/trimmer")
def trimmer_visited():
    log_visit("visited trimmer")
    return render_template("trimmer.html", title="File Trimmer")


@app.route("/contact")
def contact_page_visited():
    log_visit("visited contact page")
    return render_template("contact.html", title="Contact")


@app.route("/game")
def game_visited():
    log_visit("visited game")
    return render_template("game.html", title="Game")


@app.route("/game2")
def game2_visited():
    log_visit("visited game 2")
    return render_template("game2.html", title="Game 2")


@app.route("/chat")
def chat():
    log_visit("visited chat")
    return render_template("chat.html", title="Chat")

@app.route("/samples")
def samples():
    return render_template("samples.html")
    
    
# Users online counter for /chat
count = 0


@socketio.on('connect')
def connect():
    global count
    count += 1
    socketio.emit('user connected', count)


@socketio.on('disconnect')
def disconnect():
    global count
    count -= 1
    socketio.emit('user disconnected', count)


@socketio.on('typing')
def show_typing(username):
    socketio.emit('show typing', username)


@socketio.on('nottyping')
def show_typing():
    socketio.emit('show stopped typing')


@socketio.on('message sent')
def handle_message(message):
    socketio.emit('show message', message)


if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0')
