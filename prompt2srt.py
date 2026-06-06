import json, argparse

from datetime import timedelta
def format_result(result):
    seconds = int(result)
    mm, ss = divmod(seconds, 60)
    hh, mm= divmod(mm, 60)
    ms = (result * 1000) % 1000
    return "%02d:%02d:%02d,%03d"%(hh,mm,ss,ms)

def format_result_lrc(result):
    seconds = int(result)
    mm, ss = divmod(seconds, 60)
    ms = (result * 1000) % 1000
    return "%02d:%02d.%03d"%(mm,ss,ms)

def make_srt(input_file, output_file):
    with open(input_file, encoding='utf-8') as f:
        data = json.load(f)

    with open(output_file, 'w', encoding="utf-8") as f:
        for i, d in enumerate(data):
            print(i+1, file=f)
            print(format_result(d["start"])+" --> "+format_result(d["end"]),file=f)
            print(d["message"], file=f)
            print("", file=f)
        
def make_lrc(input_file, output_file):
    with open(input_file, encoding='utf-8') as f:
        data = json.load(f)

    with open(output_file, 'w', encoding="utf-8") as f:
        for i, d in enumerate(data):
            print("["+format_result_lrc(d["start"])+"] "+d["message"], file=f)

def merge_lrc_files(input_files, output_file, duration=0):
    lines = []
    offset = 0
    for input_file in input_files:
        with open(input_file, encoding='utf-8') as f:
            readlines = f.readlines()

        if duration > 0:
            for line in readlines:
                if line.startswith('['):
                    time_str = line.split(']')[0][1:]
                    mm, ss_ms = time_str.split(':')
                    ss, ms = ss_ms.split('.')
                    total_seconds = int(mm) * 60 + int(ss) + int(ms) / 1000 + offset
                    new_time_str = format_result_lrc(total_seconds)
                    line = line.replace(time_str, new_time_str)
                lines.append(line)
            offset += duration
        else:
            lines.extend(readlines)

    # Sort lines by timestamp (string sort works for [mm:ss.xx])
    lines.sort()

    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i","--input_file", type=str, required=True)
    parser.add_argument("-o","--output_file", type=str, required=True)
    args = parser.parse_args()
    make_srt(args.input_file, args.output_file)