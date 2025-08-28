from flask import Flask, request, jsonify, send_from_directory
import os
from gtts import gTTS
import uuid
import shutil
import subprocess
import random
import pandas as pd
app = Flask(__name__)


LEXICON = "japanese_mfa.dict"
MFA_MODEL = "japanese_mfa_acoustic"
UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


vocab_df = pd.read_csv("genki1vocab.csv")

@app.route("/debug_tmp")
def debug_tmp():
    files = os.listdir("/tmp")
    return {"tmp_files": files}

@app.route("/random_word")
def random_word():
    # Pick a random row
    row = vocab_df.sample(1).iloc[0]

    # Use hiragana if kanji is blank
    display_word = row["kanji"] if pd.notna(row["kanji"]) and row["kanji"].strip() != "" else row["hiragana"]

    return jsonify({
        "hiragana": row["hiragana"],
        "kanji_or_hiragana": display_word,
        "meaning": row["meaning"],
        "chapter": int(row["chapter"])
    })


@app.route("/align", methods=["POST"])
def align():

    audio_file = request.files["audio"]
    target_word = request.form.get("target_word")

    session_id = str(uuid.uuid4())[:8]
    session_path = os.path.join(UPLOAD_FOLDER, session_id)
    os.makedirs(session_path, exist_ok=True)

    user_wav = os.path.join(session_path, "user.wav")
    convert_to_wav(audio_file, user_wav)

    user_lab = os.path.join(session_path, "user.lab")
    make_lab(target_word, user_lab)

    ref_wav = os.path.join(session_path, "ref.wav")
    text_to_wav(target_word, ref_wav)


    ref_lab = os.path.join(session_path, "ref.lab")
    make_lab(target_word, ref_lab)

    run_mfa(session_path, LEXICON, MFA_MODEL, session_path)

    random_score = random.randint(1, 100)
    feedback = f"Your pronunciation score is {random_score}/100 for {target_word}. Session ID: {session_id}"

    shutil.rmtree(session_path, ignore_errors=True)


    return jsonify({
        "status": "ok",
        "feedback": feedback
    })

@app.route("/download/<session_id>/<filename>")
def download_file(session_id, filename):
    file_path = os.path.join(UPLOAD_FOLDER, session_id, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return "File not found", 404


def text_to_wav(text, output_file):
    tts = gTTS(text, lang="ja")
    tts.save(output_file)


def make_lab(word, save_path):
    with open(save_path, "w", encoding="utf-8") as f:
        f.write(word + "\n")


def run_mfa(corpus_dir, dict_path, model_path, output_dir):
    mfa_cmd = [
        "mfa", "align",
        corpus_dir,
        dict_path,
        model_path,
        output_dir
    ]

    try:
        result = subprocess.run(
            mfa_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout 
    except subprocess.CalledProcessError as e:
        return f"MFA alignment failed:\n{e.stderr}"



def convert_to_wav(file_storage, output_path):

    command = [
        "ffmpeg",
        "-y",              
        "-i", "pipe:0",    
        "-ac", "1",        
        "-ar", "16000",    
        "-sample_fmt", "s16",  
        output_path
    ]

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    out, err = process.communicate(file_storage.read())

    if process.returncode != 0:
        print("FFmpeg error:", err.decode())
        raise RuntimeError("Audio conversion failed")

    return output_path




# if __name__ == "__main__":
#     print("Starting Flask test server...")
#     app.run(host="0.0.0.0", port=5000, debug=True)


