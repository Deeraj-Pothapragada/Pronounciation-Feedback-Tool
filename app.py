from flask import Flask, request, jsonify
import os
import io
from gtts import gTTS
import subprocess


app = Flask(__name__)


@app.route("/generate_reference", methods=["POST"])
def generate_reference():
    data = request.json
    word = data["word"]
    output_path = f"reference/{word}.wav"

    # synthesis_input = texttospeech.SynthesisInput(text=word)
    # voice = texttospeech.VoiceSelectionParams(
    #     language_code="te-IN",
    #     ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    # )
    # audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16)

    # response = tts_client.synthesize_speech(
    #     input=synthesis_input,
    #     voice=voice,
    #     audio_config=audio_config
    # )

    # with open(output_path, "wb") as out:
    #     out.write(response.audio_content)

    text_to_wav(word, output_path)

    return jsonify({"reference_path": output_path})

@app.route("/upload_user_audio", methods=["POST"])
def upload_user_audio():
    audio_file = request.files["audio"]
    filename = audio_file.filename
    filepath = os.path.join("uploads", filename)
    audio_file.save(filepath)
    return jsonify({"user_audio_path": filepath})

import subprocess

MFA_MODEL = "telugu_model"   # path to MFA-trained model
LEXICON = "lexicon.txt"

@app.route("/align", methods=["POST"])
def align():
    data = request.json
    user_audio = data["user_audio_path"]
    word = data["word"]
    reference_audio = f"reference/{word}.wav"

    # Prepare MFA input folder
    input_dir = "mfa_input"
    os.makedirs(input_dir, exist_ok=True)

    # MFA expects .lab file with transcription
    lab_path = os.path.join(input_dir, f"{word}.lab")
    with open(lab_path, "w", encoding="utf-8") as f:
        f.write(word)

    # Copy audio into input dir
    import shutil
    shutil.copy(user_audio, os.path.join(input_dir, f"{word}.wav"))

    output_dir = "mfa_output"
    os.makedirs(output_dir, exist_ok=True)

    # Run MFA alignment
    subprocess.run([
        "mfa", "align",
        input_dir,
        LEXICON,
        MFA_MODEL,
        output_dir
    ], check=True)

    textgrid_path = os.path.join(output_dir, f"{word}.TextGrid")
    return jsonify({"textgrid_path": textgrid_path})



def text_to_wav(text, output_file):
    tts = gTTS(text=text, lang="ja")
    mp3_data = io.BytesIO()
    tts.write_to_fp(mp3_data)
    mp3_data.seek(0)

    from pydub import AudioSegment
    audio = AudioSegment.from_mp3(mp3_data)
    audio.export(output_file, format="wav")
