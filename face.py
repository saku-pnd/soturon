#このプログラムは，csvファイルに，6秒おきに顔写真を取得し，FaceAPIの分析結果を記録し，その後，覚醒度を算出します．
#ループ処理が施してあるので，終了する場合は，「ctrl+C」を押してください
#「ctrl+C」を押したのち，覚醒度が算出され，出力されます．
# 「####」で囲まれている部分は，各PCで変更する必要があります

from contextlib import nullcontext
from operator import mod
import requests
import time
import math
import numpy as np
import cv2
from datetime import datetime
import pandas as pd
import datetime
from pandas._libs.tslibs import timestamps
##参考サイトURL
"""
https://qiita.com/daiarg/items/0fa6759e450c18c502b3
"""
##初期設定

#保存データの名前設定
data_name = ["time","anger","contempt","disgust","fear","happiness",'sadness','surprise','neutral']
#数値データの初期化
emotion_data =[0,0,0,0,0,0,0,0,0]
#撮影回数を示すカウンタ
count = 0
#データ記録用配列
resultData = []

#opencv初期設定

#カメラ設定　0→内臓カメラ　1→USBカメ
cap=cv2.VideoCapture(0,cv2.CAP_DSHOW)

#haarcascade_frontalface_alt.xmlへの絶対パス．
####################################
cascade_path = r'C:\Users\k1802\AppData\Local\Programs\Python\Python310\Lib\site-packages\cv2\data\haarcascade_frontalface_alt.xml'
####################################

cascade = cv2.CascadeClassifier(cascade_path)



#FaceAPIに登録することで，取得した，サブスクキーとエンドポイント
#プログラムの確認する際は，私のものをそのまま使っていただいて問題ありません．
#####################################
subscription_key = 'bdd238ae7b7a4e3fb38bf7a2012da33a'
assert subscription_key
face_api_url ='https://saku.cognitiveservices.azure.com/face/v1.0/detect'
######################################
try:
    while True:
        r, img = cap.read()
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)#グレースケールに変換
        faces=cascade.detectMultiScale(img_gray, scaleFactor=1.1, minNeighbors=1, minSize=(100, 100))
        #顔判定 minSizeで顔判定する際の最小の四角の大きさを指定できる。(小さい値を指定し過ぎると顔っぽい小さなシミのような部分も判定されてしまう。)
        if len(faces) > 0: #顔を検出した場合
            for face in faces:
                #撮影時間の記録
                now = datetime.now()
                now = pd.Timestamp(now)
                #filenameの設定
                filename = str(count)+'.jpg'
                #顔画像の書き出し
                cv2.imwrite(filename, img)
                #処理をする画像を選択また，顔画像をFaceAPIに送信
                image_data = open(filename, "rb").read()
                headers = {'Ocp-Apim-Subscription-Key': subscription_key,
                        'Content-Type': 'application/octet-stream'}
                params = {
                    'returnFaceId': 'false',
                    'returnFaceLandmarks': 'false',
                    'returnFaceAttributes': 'emotion',
                    }
                response = requests.post(face_api_url, headers=headers, params=params, data=image_data)
                response.raise_for_status()
                #json出力
                analysis = response.json()
                #分析結果を出力
                try:
                    result = [now,analysis[0]['faceAttributes']['emotion']['anger'],analysis[0]['faceAttributes']['emotion']['contempt'],
                                analysis[0]['faceAttributes']['emotion']['disgust'],analysis[0]['faceAttributes']['emotion']['fear'],
                                analysis[0]['faceAttributes']['emotion']['happiness'],analysis[0]['faceAttributes']['emotion']['sadness'],
                                analysis[0]['faceAttributes']['emotion']['surprise'],analysis[0]['faceAttributes']['emotion']['neutral']]
                    emotion_data = np.array(result)
                    #dataframe生成

                    df = pd.DataFrame({"valu":emotion_data},
                                    index=data_name)
                    if count == 0:
                        pass
                    else:
                        df = pd.concat([df_past,df],axis = 1, sort = False)

                    df_past = df#df_pastを更新

                    #分析結果をcsvファイルに格納
                    df.T.to_csv('emotion_analysis.csv')
                    #6秒置きに更新
                    count = count + 1
                    print(count)
                    time.sleep(6)
                #顔が読み込めてない場合のエラー表示   
                except IndexError:
                    time.sleep(6)
                    print("顔が読み込めてません")
#「ctrl+C」を押した後，得られた感情データを用いて一分毎に覚醒度を算出
except KeyboardInterrupt:

    #保存したcsvを読み込む
    csv_input = pd.read_csv(filepath_or_buffer="emotion_analysis.csv",encoding="ms932",sep=",")
    
    #得られた感情データを一分毎に平均化
    csv_input = csv_input.assign(
        timestamp=lambda df: pd.to_datetime(df['time'])
    )
    result = csv_input.set_index('timestamp')
    del result['time']
    del result['Unnamed: 0']
    result =result.resample('1T').mean()

    #覚醒度を格納する配列
    when =[]
    Arousal= []
    #覚醒度計算
    for data in result.itertuples():
        when.append(data.Index)
        Arousal.append(data.happiness*math.sin(math.radians(20))+data.surprise*math.sin(math.radians(80))+data.fear*math.sin(math.radians(110))+data.anger*math.sin(math.radians(135))+data.contempt*math.sin(math.radians(150))+data.disgust*math.sin(math.radians(160))+data.sadness*math.sin(math.radians(190)))
    #配列をもとにデータフレーム作成
    dic_arr={'time':when,'Arousal':Arousal}
    result=pd.DataFrame(dic_arr)
    #出力
    result.T.to_csv('result_Arousal.csv')
    print(result)
