from flask import Flask, request, jsonify, send_file
import os
import sys
from gtts import gTTS
import uuid
import shutil
import subprocess
import random
import pandas as pd
import parselmouth 
from praatio import textgrid
app = Flask(__name__)


LEXICON = "japanese_mfa.dict"
MFA_MODEL = "japanese_mfa_acoustic"
UPLOAD_FOLDER = "/tmp/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


vocab_df = pd.read_csv("genki1vocab.csv")

@app.route("/debug_tmp/<session_id>")
def debug_tmp(session_id):
    files = os.listdir(f"/tmp/uploads/{session_id}")
    return {"tmp_files": files}

@app.route("/random_word")
def random_word():
    row = vocab_df.sample(1).iloc[0]
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

    user_textgrid = os.path.join(session_path, "user.TextGrid") 
    ref_textgrid = os.path.join(session_path, "ref.TextGrid")
    user_info = get_info(user_wav, user_textgrid)
    ref_info = get_info(ref_wav, ref_textgrid)


    diff_summary = compare_infos(user_info, ref_info)

    random_score = random.randint(1, 100)
    feedback = f"Differences: {diff_summary}. Session ID: {session_id}"

    shutil.rmtree(session_path, ignore_errors=True)


    return jsonify({
        "status": "ok",
        "feedback": feedback
    })

def get_info(audio_path, textgrid_path, tier_name="phones"):
    snd = parselmouth.Sound(audio_path)

    def get_phoneme_segments(tg_path, tier_name):
        tg = textgrid.openTextgrid(tg_path, True)
        entries = tg._tierDict[tier_name].entries
        return [(start, end, label) for start, end, label in entries if label.strip()]

    def get_formants(start, end):
        segment = snd.extract_part(from_time=start, to_time=end, preserve_times=True)
        formant = segment.to_formant_burg()
        times = segment.xs()
        if not times:
            return (None, None)
        f1 = [formant.get_value_at_time(1, t) for t in times]
        f2 = [formant.get_value_at_time(2, t) for t in times]
        f1 = [x for x in f1 if x > 0]
        f2 = [x for x in f2 if x > 0]
        if not f1 or not f2:
            return (None, None)
        return (sum(f1)/len(f1), sum(f2)/len(f2))

    segments = get_phoneme_segments(textgrid_path, tier_name)
    return [(label, end - start, get_formants(start, end)) for start, end, label in segments]

def compare_infos(user_info, ref_info):
    comparisons = []
    for (u_label, u_dur, (u_f1, u_f2)), (r_label, r_dur, (r_f1, r_f2)) in zip(user_info, ref_info):
        if u_label == r_label and u_f1 and r_f1:
            diff_f1 = abs(u_f1 - r_f1)
            diff_f2 = abs(u_f2 - r_f2)
            comparisons.append(f"{u_label}: ΔF1={diff_f1:.1f}, ΔF2={diff_f2:.1f}")
    return "; ".join(comparisons)

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

    # try:
    #     result = subprocess.run(
    #         mfa_cmd,
    #         capture_output=True,
    #         text=True,
    #         check=True
    #     )
    #     return result.stdout 
    # except subprocess.CalledProcessError as e:
    #     return f"MFA alignment failed:\n{e.stderr}"
    process = subprocess.Popen(
    mfa_cmd,
    stdout=sys.stdout,
    stderr=sys.stderr
    )
    process.wait()

    if process.returncode != 0:
        raise RuntimeError(f"MFA failed with return code {process.returncode}")



def convert_to_wav(file_storage, output_path):
    temp_input = output_path + ".tmp"
    file_storage.save(temp_input)

    command = [
        "ffmpeg",
        "-y",
        "-i", temp_input,
        "-ac", "1",
        "-ar", "16000",
        "-sample_fmt", "s16",
        output_path
    ]

    process = subprocess.run(command, capture_output=True, text=True)
    if process.returncode != 0:
        print("FFmpeg error:", process.stderr)
        raise RuntimeError("Audio conversion failed")

    os.remove(temp_input)  
    return output_path




# if __name__ == "__main__":
#     print("Starting Flask test server...")
#     app.run(host="0.0.0.0", port=5000, debug=True)









