from __future__ import unicode_literals
import ffmpeg
import youtube_dl
from pydub import AudioSegment
import streamlit as st
import time
import azure.cognitiveservices.speech as speechsdk
import pymsteams

speech_key = "f476c82f7e1242308bab15e791ea2600"
service_region = "japaneast"

output_file_path="./audio_file/audio_sample"
output_path = 'audio_sample_w.wav'
url=""
progress = False

#サイドバーの設定

def recognize_audio(output, speech_key, service_region, filename, recognize_time=100):
    """
    wav形式のデータから文字を起こす関数
    ---------------------------
    Parameters
    output: str
        音声から起こしたテキスト（再帰的に取得する）
    speech_key: str
        Azure Speech SDKのキー
    service_region: str
        Azure Speech SDKのリージョン名
    filename: str
        音声ファイルのパス
    recognize_time: int
        音声認識にかける時間（秒）
    """
    # Speech to Text 設定周り
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_recognition_language="ja-JP"

    # 認識器の設定
    audio_input = speechsdk.AudioConfig(filename=filename)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

    def recognized(evt):
        nonlocal output
        output += evt.result.text
        
    # 音声認識の実行
    # recognize_timeの時間、継続して文字起こしを行う
    speech_recognizer.recognized.connect(recognized)
    speech_recognizer.start_continuous_recognition()
    time.sleep(recognize_time)

    return output

up_option = st.sidebar.selectbox(
    "選択肢からお選びください",
    ("動画/音声ファイルから", "YoutubeのURLから")
)

if up_option=="YoutubeのURLから":
    url = st.text_input("書き起こしをしたいYoutubeのURLを記載してください", "https://www.youtube.com/watch?v=hR3tAX3pfZE")

    video_field = st.empty()

    if len(url) > 0:
        try:
            # url2 = url.replace("https://www.youtube.com/watch?v=", "https://youtu.be/")
            video_field.video(url)
        except:
            st.error('おっと、なにかビデオ表示でエラーがでてます')

    if st.button("音声を取得して書き起こしを取得"):
        st.write("Youtubeから音声を取得します！！")
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl':  output_file_path + '.%(ext)s',   # 出力先パス
            'postprocessors': [
                {'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',                # 出力ファイル形式
                'preferredquality': '192'},             # 出力ファイルの品質
                {'key': 'FFmpegMetadata'},
            ],
        }

        ydl = youtube_dl.YoutubeDL(ydl_opts)

        # 指定したパスに音声ファイルが格納される
        _ = ydl.extract_info(url, download=True)

        # 格納された音声ファイルをpydubで読み込む
        audio = AudioSegment.from_mp3(output_file_path + '.mp3')

        audio_file = './audio_file/audio_sample.mp3'

        audio = AudioSegment.from_mp3(audio_file)
        audio.export(output_path, format='wav')

        st.write("YoutubeのURLからwavできたよ")
        progress = True

if up_option=="動画/音声ファイルから":
    byte_file = st.file_uploader('こちらからファイルを読み込み')
    if byte_file is not None:
        audio = AudioSegment.from_file(byte_file)
        audio.export(output_path, format='wav')
        st.write("動画/音声ファイルからwavできたよ")
        progress = True

if progress:

    st.write("書き起こしを開始します！！")
    filename = "audio_sample_w.wav"

    # 音声ファイルの読み込み
    sound = AudioSegment.from_file(filename, "wav")

    # 情報の取得
    # time = sound.duration_seconds # 再生時間(秒)
    times = int(sound.duration_seconds)+10

    output = ""

    output = recognize_audio(output, speech_key, service_region, filename, recognize_time=times)

    print(output)

    with open("output.txt", "w", encoding="utf-8") as f:
        f.write(output)
    st.write("書き起こしが終了したので、Teamsにお送りします")
    st.write(output)

    #Teamsへ通知
    incoming_webhook_url = "https://microsoft.webhook.office.com/webhookb2/8fcf88ae-bc6b-42c6-8722-cb8ffaac5925@72f988bf-86f1-41af-91ab-2d7cd011db47/IncomingWebhook/aae1bc717eab4328ba4d823864eed281/f9c3128a-2ec3-4f82-aea5-9b4fc35f420a" # 作成したIncoming WebhookのURLを指定(適宜変更)

    teams_obj = pymsteams.connectorcard(incoming_webhook_url)
    teams_obj.title("Message Title")
    teams_obj.text(output)
    teams_obj.send()
    print("Python経由でTeamsにメッセージを通知(送信)しました。")


