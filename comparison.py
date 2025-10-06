import parselmouth 
from praatio import textgrid

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
#     return [(label, end - start, get_formants(start, end)) for start, end, label in segments]
    return [(label, end - start) for start, end, label in segments]


def compare_infos(user_wav, user_textgrid, ref_wav, ref_textgrid):
    user_info = get_info(user_wav, user_textgrid)
    ref_info = get_info(ref_wav, ref_textgrid)
    comparisons = []
    for (u_label, u_dur), (r_label, r_dur) in zip(user_info, ref_info):
        if u_label == r_label and u_f1 and r_f1:
            diff_length = u_dur - r_dur
            # diff_f1 = u_f1 - r_f1
            # diff_f2 = u_f2 - r_f2
            comparisons.append(f"{u_label}: ΔLength = {diff_length:.2f}")
    return "\n ".join(comparisons)

